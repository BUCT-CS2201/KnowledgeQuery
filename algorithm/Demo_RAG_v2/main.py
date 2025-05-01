import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_milvus import Milvus
import gradio as gr
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
import requests
import json

# 加载环境变量
load_dotenv()

# 配置Milvus连接
MILVUS_HOST = os.getenv("MILVUS_HOST", "127.0.0.1")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")

# 大语言模型 API 配置
ONEAPI_BASE_URL = os.getenv("ONEAPI_BASE_URL", "https://api.siliconflow.cn/v1")
ONEAPI_API_KEY = os.getenv("ONEAPI_API_KEY", "")  # 从环境变量加载API密钥
ONEAPI_MODEL = os.getenv("ONEAPI_MODEL", "Qwen/Qwen2.5-VL-72B-Instruct") 

# 初始化嵌入模型 - 使用可靠的公开模型，带错误处理
def initialize_embedding_model():
    # 首选模型列表，按优先级排序
    model_options = [
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",  # 多语言支持，384维
        "sentence-transformers/all-MiniLM-L6-v2",                        # 英文，384维
        "sentence-transformers/all-mpnet-base-v2"                        # 备选高质量模型，768维
    ]
    
    for model_name in model_options:
        try:
            print(f"尝试加载嵌入模型: {model_name}")
            embeddings = HuggingFaceEmbeddings(model_name=model_name)
            print(f"成功加载模型: {model_name}")
            return embeddings, model_name, get_embedding_dimension(model_name)
        except Exception as e:
            print(f"加载模型 {model_name} 失败: {str(e)}")
    
    # 如果所有模型都失败，抛出异常
    raise RuntimeError("无法加载任何嵌入模型，请检查网络连接或Hugging Face访问权限")

# 获取模型的嵌入维度
def get_embedding_dimension(model_name):
    # 常见模型维度映射
    model_dimensions = {
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": 384,
        "sentence-transformers/all-MiniLM-L6-v2": 384,
        "sentence-transformers/all-mpnet-base-v2": 768
    }
    return model_dimensions.get(model_name, 384)  # 默认384维

# 初始化嵌入模型
try:
    embeddings, actual_model_name, EMBEDDING_DIMENSION = initialize_embedding_model()
    print(f"使用嵌入模型: {actual_model_name}, 维度: {EMBEDDING_DIMENSION}")
except Exception as e:
    print(f"初始化嵌入模型失败: {str(e)}")
    print("使用默认值，但程序可能无法正常运行")
    actual_model_name = "加载失败"
    EMBEDDING_DIMENSION = 384

# Milvus部署信息
MILVUS_DEPLOYMENT_GUIDE = """
## Milvus部署指南

### 使用Docker部署Milvus

项目目录中包含`docker-compose.yml`文件，您可以使用以下命令启动Milvus:

```bash
cd /Users/sanshi/Desktop/软件工程/CODE/RAG
docker-compose up -d
```

### 重要端口:
- Milvus服务: 19530 (应用程序连接端口)
- Attu管理界面: 8000 (Web界面端口)
- Minio界面: 9001 (对象存储管理)

### 访问管理界面:
- Milvus Attu: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Minio控制台: [http://127.0.0.1:9001](http://127.0.0.1:9001) (minioadmin/minioadmin)

### 停止Milvus:
```bash
docker-compose down
```
"""

# 调用大语言模型API
def query_llm(prompt, temperature=0.7, max_tokens=1024):
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ONEAPI_API_KEY}"
        }
        
        payload = {
            "model": ONEAPI_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "max_tokens": max_tokens,
            "enable_thinking": False,
            "thinking_budget": 512,
            "min_p": 0.05,
            "stop": None,
            "temperature": temperature,
            "top_p": 0.7,
            "top_k": 50,
            "frequency_penalty": 0.5,
            "n": 1,
            "response_format": {"type": "text"}
        }
        
        response = requests.post(f"{ONEAPI_BASE_URL}/chat/completions", 
                                headers=headers, 
                                json=payload)
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        elif response.status_code == 401:
            # 处理认证错误，如令牌额度用尽
            error_data = response.json()
            error_message = error_data.get("error", {}).get("message", "未知错误")
            return f"API认证错误: {error_message}\n\n请检查API密钥是否有效或账户余额是否充足。"
        else:
            return f"API调用失败: {response.status_code} - {response.text}"
    except Exception as e:
        return f"调用LLM时出错: {str(e)}"

# 基于检索增强生成的知识库问答
def rag_qa(query, collection_name, host=MILVUS_HOST, port=MILVUS_PORT, top_k=3):
    try:
        # 检查连接
        connected, msg = check_milvus_connection(host, port)
        if not connected:
            return f"错误: {msg}"
            
        # 检索相关文档
        docs_with_scores = query_documents(query, collection_name, host, port, top_k)
        
        if not docs_with_scores:
            return "未找到匹配的文档，无法生成回答。请尝试修改您的查询或确保已索引相关内容。"
            
        # 文档去重和过滤
        unique_docs = {}
        filtered_docs = []
        for doc, score in docs_with_scores:
            # 使用文档内容的前100个字符作为去重键
            doc_key = doc.page_content[:100]
            # 仅保留未见过的文档
            if doc_key not in unique_docs:
                # 相似度过滤（可选）：只保留相似度较高的文档
                similarity = max(0, min(100, 100 * (1 - score / 100)))
                if similarity > 60:  # 只保留相似度高于60%的文档
                    unique_docs[doc_key] = (doc, score)
                    filtered_docs.append((doc, score))
        
        # 如果过滤后没有文档，使用原始文档集
        if not filtered_docs:
            filtered_docs = docs_with_scores[:1]  # 至少保留最相关的一个
            
        # 构建提示词
        context_texts = []
        for i, (doc, score) in enumerate(filtered_docs):
            # 计算相似度用于在上下文中显示
            similarity = max(0, min(100, 100 * (1 - score / 100)))
            # 加入相似度信息帮助模型判断内容可靠性
            context_texts.append(f"文档 {i+1} (相似度: {similarity:.2f}%):\n{doc.page_content}")
        
        context = "\n\n".join(context_texts)
        
        # 改进提示词模板，更明确地指导模型
        prompt = f"""请作为一个专业的文档问答助手，基于以下参考文档回答用户的问题。
        如果参考文档中包含问题的答案，请详细解释。
        如果参考文档中没有与问题直接相关的信息，请明确回答"根据提供的文档无法回答这个问题"。
        
        请仔细分析每个参考文档的内容和相关性，重点关注相似度较高的文档。
        不要编造信息，如果不确定，请说明。
        
        用户问题: {query}
        
        参考文档:
        {context}
        
        基于上述文档的专业回答:"""
        
        # 添加调试信息
        print(f"提问: {query}")
        print(f"检索到 {len(filtered_docs)} 个去重后的相关文档")
        
        # 调用大语言模型生成回答
        answer = query_llm(prompt)
        
        # 构建结果显示
        result = f"### 问题: {query}\n\n"
        result += f"### 回答:\n{answer}\n\n"
        result += "### 参考文档:\n"
        
        for i, (doc, score) in enumerate(filtered_docs):
            # 计算相似度百分比
            similarity = max(0, min(100, 100 * (1 - score / 100)))
            metadata = doc.metadata if hasattr(doc, "metadata") else {}
            source = metadata.get("source", "未知来源")
            
            result += f"#### 文档 {i+1} (相似度: {similarity:.2f}%)\n"
            result += f"**来源**: {source}\n"
            result += f"**内容**: {doc.page_content[:200]}...\n\n"
        
        return result
    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        return f"知识库问答出错: {str(e)}\n\n调试信息:\n{trace}"

# 检查Milvus连接状态
def check_milvus_connection(host, port):
    try:
        connections.connect(host=host, port=port, timeout=5)
        # 尝试获取集合列表，验证连接是否有效
        utility.list_collections()
        return True, "连接成功！Milvus服务器运行正常。"
    except Exception as e:
        return False, f"无法连接到Milvus服务器: {str(e)}\n\n故障排除建议:\n1. 确保Milvus服务器已启动\n2. 检查主机和端口是否正确\n3. 检查网络连接"

# 文档加载函数 - 根据文件类型选择合适的加载器
def load_document(file_path):
    _, file_extension = os.path.splitext(file_path)
    
    if file_extension.lower() == ".txt":
        loader = TextLoader(file_path, encoding="utf-8")
    elif file_extension.lower() == ".pdf":
        loader = PyPDFLoader(file_path)
    elif file_extension.lower() in [".docx", ".doc"]:
        loader = Docx2txtLoader(file_path)
    else:
        raise ValueError(f"不支持的文件类型: {file_extension}")
    
    documents = loader.load()
    return documents

# 文档分块
def split_documents(documents, chunk_size=1000, chunk_overlap=150):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    chunks = text_splitter.split_documents(documents)
    return chunks

# 将文档块存入Milvus - 使用正确的Milvus类
def store_in_milvus(chunks, collection_name, host=MILVUS_HOST, port=MILVUS_PORT):
    vectorstore = Milvus.from_documents(
        documents=chunks,
        embedding=embeddings,
        connection_args={"host": host, "port": port},
        collection_name=collection_name,
    )
    return vectorstore

# 根据问题查询相关文档 - 使用正确的Milvus类
def query_documents(query_text, collection_name, host=MILVUS_HOST, port=MILVUS_PORT, top_k=3):
    vectorstore = Milvus(
        embedding_function=embeddings,
        collection_name=collection_name,
        connection_args={"host": host, "port": port},
    )
    
    # 相似性搜索并返回相似度得分
    docs_with_scores = vectorstore.similarity_search_with_score(query_text, k=top_k)
    return docs_with_scores

# 处理上传文件并索引
def process_file(file_path, collection_name, host=MILVUS_HOST, port=MILVUS_PORT):
    try:
        # 检查连接
        connected, msg = check_milvus_connection(host, port)
        if not connected:
            return f"错误: {msg}"
        
        # 加载文档
        documents = load_document(file_path)
        
        # 分块
        chunks = split_documents(documents)
        
        # 存入Milvus
        store_in_milvus(chunks, collection_name, host, port)
        
        return f"成功处理文件并索引到 {collection_name}，共 {len(chunks)} 个文本块"
    except Exception as e:
        return f"处理文件时出错: {str(e)}"

# 处理用户查询
def process_query(query, collection_name, host=MILVUS_HOST, port=MILVUS_PORT, top_k=3):
    try:
        # 检查连接
        connected, msg = check_milvus_connection(host, port)
        if not connected:
            return f"错误: {msg}"
            
        docs_with_scores = query_documents(query, collection_name, host, port, top_k)
        
        if not docs_with_scores:
            return "未找到匹配的文档。请尝试修改您的查询或确保已索引相关内容。"
            
        # 添加搜索方法信息
        search_method = "向量相似度搜索 (Vector Similarity Search)"
        results = [f"### 搜索方法: {search_method}\n### 查询: '{query}'\n\n"]
        
        # 详细展示结果
        for i, (doc, score) in enumerate(docs_with_scores):
            # 计算相似度百分比 (Milvus使用L2距离，值越小越相似，转换为相似度得分)
            similarity = max(0, min(100, 100 * (1 - score / 100)))
            
            # 提取文档信息
            text_content = doc.page_content
            metadata = doc.metadata if hasattr(doc, "metadata") else {}
            source = metadata.get("source", "未知来源")
            
            # 构建结果显示
            results.append(f"## 结果 {i+1} (相似度: {similarity:.2f}%)")
            results.append(f"**来源**: {source}")
            results.append("**内容**:")
            results.append(f"```\n{text_content}\n```\n")
        
        return "\n".join(results)
    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        return f"查询时出错: {str(e)}\n\n调试信息:\n{trace}"

# 创建空集合
def create_empty_collection(collection_name, host=MILVUS_HOST, port=MILVUS_PORT):
    try:
        # 检查连接
        connected, msg = check_milvus_connection(host, port)
        if not connected:
            return f"错误: {msg}"
            
        # 检查集合是否已存在
        if utility.has_collection(collection_name):
            return f"集合 '{collection_name}' 已存在"
        
        # 定义集合结构
        dim = EMBEDDING_DIMENSION  # 使用当前加载的模型维度
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dim)
        ]
        schema = CollectionSchema(fields=fields, description=f"Text collection: {collection_name}")
        
        # 创建集合
        collection = Collection(name=collection_name, schema=schema)
        
        # 创建索引
        index_params = {
            "metric_type": "L2",
            "index_type": "HNSW",
            "params": {"M": 8, "efConstruction": 64}
        }
        collection.create_index(field_name="vector", index_params=index_params)
        
        return f"已成功创建集合 '{collection_name}'"
    except Exception as e:
        return f"创建集合时出错: {str(e)}\n\n如果是连接问题，请检查Milvus服务器是否启动。"

# 列出所有集合
def list_collections(host=MILVUS_HOST, port=MILVUS_PORT):
    try:
        # 检查连接
        connected, msg = check_milvus_connection(host, port)
        if not connected:
            return f"错误: {msg}"
            
        collections = utility.list_collections()
        if not collections:
            return "没有找到集合"
        return "可用集合:\n" + "\n".join(collections)
    except Exception as e:
        return f"获取集合列表时出错: {str(e)}"

# Gradio界面
def create_ui():
    with gr.Blocks() as demo:
        gr.Markdown("# RAG 文档检索系统")
        
        with gr.Tab("服务器设置"):
            gr.Markdown("## Milvus 服务器配置")
            milvus_host = gr.Textbox(label="Milvus 主机", value=MILVUS_HOST)
            milvus_port = gr.Textbox(label="Milvus 端口", value=MILVUS_PORT)
            check_connection_button = gr.Button("测试连接")
            connection_status = gr.Textbox(label="连接状态")
            
            # 添加Milvus部署指南
            gr.Markdown(MILVUS_DEPLOYMENT_GUIDE)
            
            # 显示当前使用的嵌入模型
            gr.Markdown(f"""
            ## 系统状态
            当前使用的嵌入模型: **{actual_model_name}**  
            嵌入维度: **{EMBEDDING_DIMENSION}**
            
            ## Milvus Web界面
            访问Milvus管理界面: [http://{MILVUS_HOST}:8000](http://{MILVUS_HOST}:8000)
            
            在Web界面中您可以:
            - 查看和管理所有集合
            - 监控系统状态
            - 执行查询
            - 查看数据分布
            """)
            
            check_connection_button.click(
                fn=check_milvus_connection,
                inputs=[milvus_host, milvus_port],
                outputs=connection_status
            )
        
        with gr.Tab("集合管理"):
            gr.Markdown("## 创建新集合")
            new_collection_name = gr.Textbox(label="新建集合名称", placeholder="输入集合名称")
            create_collection_button = gr.Button("创建空集合")
            create_collection_output = gr.Textbox(label="创建结果")
            
            gr.Markdown("## 查看现有集合")
            list_collections_button = gr.Button("列出所有集合")
            list_collections_output = gr.Textbox(label="现有集合")
            
            create_collection_button.click(
                fn=create_empty_collection,
                inputs=[new_collection_name, milvus_host, milvus_port],
                outputs=create_collection_output
            )
            
            list_collections_button.click(
                fn=list_collections,
                inputs=[milvus_host, milvus_port],
                outputs=list_collections_output
            )
        
        with gr.Tab("文档上传与索引"):
            file_input = gr.File(label="上传文件")
            collection_name_input = gr.Textbox(label="集合名称", value="default_collection")
            upload_button = gr.Button("处理并索引文件")
            upload_output = gr.Textbox(label="处理结果")
            
            upload_button.click(
                fn=lambda file, coll_name, host, port: process_file(file.name, coll_name, host, port),
                inputs=[file_input, collection_name_input, milvus_host, milvus_port],
                outputs=upload_output
            )
        
        with gr.Tab("文档查询"):
            query_collection_name = gr.Textbox(label="集合名称", value="default_collection")
            query_input = gr.Textbox(label="查询问题")
            top_k_slider = gr.Slider(minimum=1, maximum=10, step=1, value=3, label="返回结果数量")
            query_button = gr.Button("搜索")
            query_output = gr.Markdown(label="搜索结果", elem_id="query_results")
            
            # 添加搜索方法说明
            gr.Markdown("""
            ### 搜索方法说明
            
            本系统使用**向量相似度搜索**方法检索文档:
            1. 将查询文本转换为向量表示
            2. 在向量空间中查找最相似的文档向量
            3. 返回最相似的文档片段及其相似度得分
            
            相似度得分表示查询和文档的语义接近程度，100%表示完全匹配。
            
            ### 结果解读
            - 每个结果都显示文本源文件和内容
            - 代码块中包含原始检索到的文本内容
            - 相似度越高，越可能与您的查询相关
            """)
            
            query_button.click(
                fn=process_query,
                inputs=[query_input, query_collection_name, milvus_host, milvus_port, top_k_slider],
                outputs=query_output
            )
        
        with gr.Tab("知识库问答"):
            gr.Markdown("## 基于文档的AI问答")
            qa_collection_name = gr.Textbox(label="集合名称", value="default_collection")
            qa_query_input = gr.Textbox(label="您的问题", placeholder="请输入您的问题...")
            qa_top_k_slider = gr.Slider(minimum=1, maximum=10, step=1, value=3, label="参考文档数量")
            qa_button = gr.Button("提问")
            qa_output = gr.Markdown(label="AI回答")
            
            # 添加知识库问答说明
            gr.Markdown("""
            ### 知识库问答说明
            
            本功能结合了向量检索和大语言模型能力:
            1. 系统首先检索与您问题最相关的文档
            2. 将这些文档作为上下文提供给AI模型
            3. AI模型基于检索到的文档生成回答
            
            此功能依赖于:
            - 大语言模型: Qwen2.5 14B
            - 向量嵌入模型: BGE-M3
            - Milvus向量数据库
            
            为获得最佳效果，请确保您已经上传并索引了相关文档。
            """)
            
            qa_button.click(
                fn=rag_qa,
                inputs=[qa_query_input, qa_collection_name, milvus_host, milvus_port, qa_top_k_slider],
                outputs=qa_output
            )
    
    return demo

# 主函数
def main():
    ui = create_ui()
    ui.launch(share=True)

if __name__ == "__main__":
    main()
