import logging
from openai import OpenAI, AsyncOpenAI
from config.config_info import settings
from typing import List, Dict, Any, AsyncGenerator
from .rag.cypher_generator import CypherGenerator
from .rag.knowledge_graph import KnowledgeGraph
from .rag.prompts import ANSWER_GENERATION_SYSTEM_PROMPT, FORMAT_RESULTS_PROMPT
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class AiHubMixLLM:
    def __init__(self):
        # 初始化同步客户端
        self.client = OpenAI(
            api_key=settings.AIHUBMIX_API_KEY,
            base_url=settings.AIHUBMIX_BASE_URL,
        )
        # 初始化异步客户端
        self.async_client = AsyncOpenAI(
            api_key=settings.AIHUBMIX_API_KEY,
            base_url=settings.AIHUBMIX_BASE_URL,
        )
        self.model = settings.AIHUBMIX_MODEL
        # 线程池，用于执行可能阻塞的操作
        self._executor = ThreadPoolExecutor(max_workers=10)
    
    async def get_response(self, messages):
        """
        获取AiHubMix API的回复
        :param messages: 消息列表，格式为[{"role": "user", "content": "你好"}, ...]
        :return: AI的回复文本
        """
        try:
            # 使用异步客户端发送请求
            completion = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False
            )
            
            # 非流式响应直接返回内容
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"调用AiHubMix API失败: {str(e)}")
            return "抱歉，我暂时无法回答您的问题。请稍后再试。"
    
    async def get_streaming_response(self, messages):
        """
        获取AiHubMix API的流式回复
        :param messages: 消息列表，格式为[{"role": "user", "content": "你好"}, ...]
        :yield: 生成AI回复的每个部分
        """
        try:
            # 使用异步客户端创建流式请求
            stream = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                timeout=120  # 增加超时时间，单位为秒
            )
            
            full_response = ""
            
            # 使用异步迭代器处理流式响应
            async for chunk in stream:
                if hasattr(chunk.choices, '__len__') and len(chunk.choices) > 0:
                    if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        # 通过yield将每个块发送给客户端而不阻塞
                        yield content
                
                # 添加一个小延迟，允许其他任务执行
                await asyncio.sleep(0.01)
            
            # 如果流式响应完全失败，返回错误信息
            if not full_response:
                yield "抱歉，我暂时无法回答您的问题。请稍后再试。"
                
        except asyncio.TimeoutError:
            logger.error("调用AiHubMix API流式响应超时")
            yield "抱歉，响应超时。请尝试简化您的问题或稍后再试。"
        except Exception as e:
            logger.error(f"调用AiHubMix API流式响应失败: {str(e)}")
            yield "抱歉，我暂时无法回答您的问题。请稍后再试。"
    
    async def get_kb_streaming_response(self, messages, collection_name=None, top_k=3):
            """
            获取结合知识库的AiHubMix API流式回复
            :param messages: 消息列表，格式为[{"role": "user", "content": "你好"}, ...]
            :param collection_name: Milvus集合名称，默认从环境变量获取
            :param top_k: 返回的最相关文档数量
            :yield: 生成AI回复的每个部分
            """
            try:
                # 从消息中提取最后一个用户问题
                query = ""
                for msg in reversed(messages):
                    if msg["role"] == "user":
                        query = msg["content"]
                        break
                
                if not query:
                    yield "未找到有效的用户问题，请重新提问。"
                    return
                
                # 尝试导入必要的库，提供明确的安装指导
                try:
                    import os
                    from pymilvus import connections
                    
                    # 尝试导入LangChain相关库
                    try:
                        from langchain_huggingface import HuggingFaceEmbeddings
                        from langchain_milvus import Milvus
                    except ImportError:
                        installation_guide = """缺少必要的依赖包。请执行以下命令安装:
                        
                        pip install langchain-community langchain-milvus sentence-transformers pymilvus
                        
                        安装完成后重新启动服务。"""
                        
                        logger.error("缺少langchain相关依赖包")
                        yield installation_guide
                        return
                    
                    # 从settings或环境变量获取Milvus配置
                    from config.config_info import settings
                    host = settings.MILVUS_HOST
                    port = settings.MILVUS_PORT
                    db_name = settings.MILVUS_DATABASE
                    
                    # 如果未指定集合名称，则使用配置中的值
                    if collection_name is None:
                        collection_name = settings.MILVUS_COLLECTION
                    
                    # 尝试连接Milvus - 使用线程池避免阻塞
                    try:
                        # 将可能阻塞的操作移到线程池中执行
                        def connect_milvus():
                            connections.connect(
                                host=host, 
                                port=port,
                                db_name=db_name,
                                timeout=5
                            )
                        
                        # 异步执行连接操作
                        await asyncio.get_event_loop().run_in_executor(
                            self._executor, connect_milvus
                        )
                    except Exception as e:
                        logger.error(f"连接Milvus失败: {str(e)}")
                        yield f"无法连接到Milvus向量数据库，请确保服务已启动。详细错误: {str(e)}"
                        return
                    
                    # 初始化嵌入模型 - 使用线程池避免阻塞
                    try:
                        # 将模型加载操作移到线程池中执行
                        def init_embeddings():
                            model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
                            return HuggingFaceEmbeddings(model_name=model_name)
                        
                        # 异步执行模型加载
                        embeddings = await asyncio.get_event_loop().run_in_executor(
                            self._executor, init_embeddings
                        )
                    except Exception as e:
                        logger.error(f"加载嵌入模型失败: {str(e)}")
                        yield "嵌入模型加载失败，可能需要安装sentence-transformers或检查网络连接。"
                        return
                    
                    # 初始化向量存储
                    vectorstore = Milvus(
                        embedding_function=embeddings,
                        collection_name=collection_name,
                        connection_args={"host": host, "port": port, "db_name": db_name},
                    )
                    
                    # 查询相关文档 - 使用线程池避免阻塞
                    def perform_search():
                        return vectorstore.similarity_search_with_score(query, k=top_k)
                    
                    # 异步执行向量搜索
                    docs_with_scores = await asyncio.get_event_loop().run_in_executor(
                        self._executor, perform_search
                    )
                    
                    if not docs_with_scores:
                        # 如果没有找到相关文档，直接调用普通流式响应
                        logger.warning("知识库中未找到相关文档，使用普通回复")
                        async for content in self.get_streaming_response(messages):
                            yield content
                        return
                    
                    # 文档去重和过滤
                    unique_docs = {}
                    filtered_docs = []
                    for doc, score in docs_with_scores:
                        # 使用文档内容的前100个字符作为去重键
                        doc_key = doc.page_content[:100]
                        # 仅保留未见过的文档
                        if doc_key not in unique_docs:
                            # 相似度过滤：只保留相似度较高的文档
                            similarity = max(0, min(100, 100 * (1 - score / 100)))
                            if similarity > 60:  # 只保留相似度高于60%的文档
                                unique_docs[doc_key] = (doc, score)
                                filtered_docs.append((doc, score))
                    
                    # 如果过滤后没有文档，使用原始文档集
                    if not filtered_docs:
                        filtered_docs = docs_with_scores[:1]  # 至少保留最相关的一个
                    
                    # 构建上下文
                    context_texts = []
                    for i, (doc, score) in enumerate(filtered_docs):
                        # 计算相似度
                        similarity = max(0, min(100, 100 * (1 - score / 100)))
                        # 加入相似度信息
                        context_texts.append(f"文档 {i+1} (相似度: {similarity:.2f}%):\n{doc.page_content}")
                    
                    context = "\n\n".join(context_texts)
                    
                    # 构建增强提示词
                    enhanced_messages = messages.copy()
                    system_prompt = f"""请作为一个专业的文档问答助手，基于以下参考文档回答用户的问题。
                    如果参考文档中包含问题的答案，请详细解释。
                    如果参考文档中没有与问题直接相关的信息，请明确回答"根据提供的文档无法回答这个问题"。
                    
                    参考文档:
                    {context}
                    """
                    
                    # 将system prompt放在最前面
                    enhanced_messages.insert(0, {"role": "system", "content": system_prompt})
                    
                    # 使用异步客户端创建流式请求
                    stream = await self.async_client.chat.completions.create(
                        model=self.model,
                        messages=enhanced_messages,
                        stream=True,
                        timeout=120
                    )
                    
                    full_response = ""
                    # 使用异步迭代器处理流式响应
                    async for chunk in stream:
                        if hasattr(chunk.choices, '__len__') and len(chunk.choices) > 0:
                            if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content is not None:
                                content = chunk.choices[0].delta.content
                                full_response += content
                                # 通过yield将每个块发送给客户端而不阻塞
                                yield content
                        
                        # 添加一个小延迟，允许其他任务执行
                        await asyncio.sleep(0.01)
                    
                    # 如果流式响应完全失败，返回错误信息
                    if not full_response:
                        yield "抱歉，我暂时无法基于知识库回答您的问题。请稍后再试。"
                        
                except Exception as e:
                    logger.error(f"初始化知识库组件失败: {str(e)}")
                    yield f"初始化知识库组件时出错: {str(e)}\n可能需要安装必要的依赖包。"
                    return
                    
            except Exception as e:
                logger.error(f"知识库流式响应失败: {str(e)}")
                yield "抱歉，在查询知识库时遇到问题。请稍后再试。"

    async def get_kg_streaming_response(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """
        基于知识图谱的问答响应生成器
        
        Args:
            messages: 对话历史消息列表
            
        Yields:
            str: 生成的回答片段
        """
        try:
            # 验证消息格式
            if not messages or not isinstance(messages, list):
                yield "消息格式错误，请提供有效的对话历史。"
                return
                
            # 获取最后一个用户问题
            last_message = None
            for msg in reversed(messages):
                if msg.get("role") == "user" and msg.get("content"):
                    last_message = msg["content"]
                    break
                    
            if not last_message:
                yield "未找到有效的用户问题，请重新提问。"
                return
            
            # 初始化Cypher生成器
            cypher_generator = CypherGenerator(self)
            
            try:
                # 生成Cypher查询 - 异步执行
                cypher_query = await cypher_generator.generate_cypher(last_message)
                logger.info(f"生成的Cypher查询语句: {cypher_query}")
                
                if not cypher_query:
                    yield "无法生成有效的查询语句，请重新提问。"
                    return
                    
                # 初始化知识图谱连接
                kg = KnowledgeGraph()
                
                try:
                    # 执行查询 - 可能是阻塞操作，但KnowledgeGraph类已经使用异步实现
                    results = await kg.execute_query(cypher_query)
                    logger.info(f"查询结果: {results}")
                    
                    # 允许其他请求处理
                    await asyncio.sleep(0.01)
                    
                    # 格式化查询结果
                    formatted_results = await kg.format_results(results)
                    logger.info(f"格式化后的结果: {formatted_results}")
                    
                    # 构建完整的消息列表
                    enhanced_messages = [
                        {"role": "system", "content": ANSWER_GENERATION_SYSTEM_PROMPT},
                        {"role": "user", "content": f"""问题：{last_message}

知识图谱查询结果：
{formatted_results}

请基于以上信息回答用户的问题。"""}
                    ]
                    
                    # 使用流式响应生成回答 - 采用改进的流式响应方法
                    stream = await self.async_client.chat.completions.create(
                        model=self.model,
                        messages=enhanced_messages,
                        stream=True,
                        timeout=120
                    )
                    
                    # 使用异步迭代器处理流式响应
                    async for chunk in stream:
                        if hasattr(chunk.choices, '__len__') and len(chunk.choices) > 0:
                            if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content is not None:
                                content = chunk.choices[0].delta.content
                                # 通过yield将每个块发送给客户端而不阻塞
                                yield content
                                
                                # 添加一个小延迟，允许其他任务执行
                                await asyncio.sleep(0.01)
                        
                except Exception as e:
                    logger.error(f"知识图谱查询失败: {str(e)}")
                    yield f"查询知识图谱时出错: {str(e)}"
                    
                finally:
                    # 关闭知识图谱连接
                    await kg.close()
                    
            except Exception as e:
                logger.error(f"生成Cypher查询失败: {str(e)}")
                yield f"生成查询语句时出错: {str(e)}"
                
        except Exception as e:
            logger.error(f"知识图谱问答处理失败: {str(e)}")
            yield "处理您的问题时遇到错误，请稍后重试。"

# 创建一个单例实例
ai_llm = AiHubMixLLM()
