import os
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_community.embeddings import HuggingFaceEmbeddings
# 新路径
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Milvus
import gradio as gr
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility

# 配置Milvus连接
MILVUS_HOST = "127.0.0.1"  # Milvus服务器地址
MILVUS_PORT = "19530"       # Attu界面端口
MILVUS_SERVICE_PORT = "19530"  # Milvus服务端口

# 初始化嵌入模型
model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"  # 多语言支持
embeddings = HuggingFaceEmbeddings(model_name=model_name)

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

# 将文档块存入Milvus
def store_in_milvus(chunks, collection_name, host=MILVUS_HOST, port=MILVUS_PORT):
    vectorstore = Milvus.from_documents(
        documents=chunks,
        embedding=embeddings,
        connection_args={"host": host, "port": port},
        collection_name=collection_name,
    )
    return vectorstore

# 根据问题查询相关文档
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
        dim = 384  # 对应于默认嵌入模型的维度
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
            
            # 添加Milvus Web界面链接
            gr.Markdown(f"""
            ## Milvus Web界面
            访问Milvus管理界面: [http://{MILVUS_HOST}:{MILVUS_PORT}/#/collections](http://{MILVUS_HOST}:{MILVUS_PORT}/#/collections)
            
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
    
    return demo

# 主函数
def main():
    ui = create_ui()
    ui.launch(share=True)

if __name__ == "__main__":
    main()
