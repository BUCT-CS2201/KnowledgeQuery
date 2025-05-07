from langchain_community.chat_models import ChatZhipuAI
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_openai.chat_models import ChatOpenAI
from streamlit.runtime.uploaded_file_manager import UploadedFile
import time
from typing import Optional, Dict, Any, Generator
import asyncio
from functools import wraps

from config import openai_config
from config import tongyi_config
from config import zhipu_config

from audio import Audio
from CS2201_RAG import CS2201_RAG

cs2201_rag = CS2201_RAG()
audio = Audio()

def retry_on_failure(max_retries: int = 3, delay: int = 1):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        print(f"尝试 {attempt + 1}/{max_retries} 失败，{delay}秒后重试...")
                        await asyncio.sleep(delay)
            raise last_exception
        return wrapper
    return decorator

class QwenChat:
    """通义千问聊天类"""
    
    def __init__(self):
        self.llm = self._init_llm()
        self.streaming = tongyi_config.STREAMING
        self.streaming_interval = tongyi_config.STREAMING_INTERVAL
        
    def _init_llm(self) -> ChatTongyi:
        """初始化通义千问模型"""
        try:
            # 验证 API Key
            if not tongyi_config.DASHSCOPE_API_KEY or tongyi_config.DASHSCOPE_API_KEY.startswith('sk-xxxxxxxx'):
                raise ValueError("请配置有效的通义千问 API Key")
                
            return ChatTongyi(
                api_key=tongyi_config.DASHSCOPE_API_KEY,
                model=tongyi_config.MODEL_NAME,
                temperature=tongyi_config.TEMPERATURE,
                top_p=tongyi_config.TOP_P,
                max_tokens=tongyi_config.MAX_TOKENS
            )
        except Exception as e:
            print(f"通义千问模型初始化失败: {str(e)}")
            raise

    @retry_on_failure(max_retries=tongyi_config.MAX_RETRIES, delay=tongyi_config.RETRY_DELAY)
    async def chat(self, query: str, history: Optional[Dict[str, Any]] = None) -> str:
        """聊天接口"""
        try:
            if not query or not isinstance(query, str):
                raise ValueError("无效的查询输入")
                
            if self.streaming:
                return await self._stream_chat(query, history)
            else:
                return await self._normal_chat(query, history)
        except Exception as e:
            print(f"通义千问调用失败: {str(e)}")
            raise

    async def _normal_chat(self, query: str, history: Optional[Dict[str, Any]] = None) -> str:
        """普通聊天模式"""
        try:
            response = self.llm.invoke(query)
            if not response or not hasattr(response, 'content'):
                raise ValueError("无效的模型响应")
            return response.content
        except Exception as e:
            print(f"通义千问普通模式调用失败: {str(e)}")
            raise

    async def _stream_chat(self, query: str, history: Optional[Dict[str, Any]] = None) -> str:
        """流式聊天模式"""
        try:
            full_response = ""
            async for chunk in self.llm.astream(query):
                if not chunk or not hasattr(chunk, 'content'):
                    continue
                full_response += chunk.content
                await asyncio.sleep(self.streaming_interval)
            return full_response
        except Exception as e:
            print(f"通义千问流式模式调用失败: {str(e)}")
            raise

    def stream_chat(self, query: str) -> Generator[str, None, None]:
        """同步流式输出接口"""
        try:
            for chunk in self.llm.stream(query):
                if chunk and hasattr(chunk, 'content'):
                    yield chunk.content
        except Exception as e:
            print(f"通义千问流式输出失败: {str(e)}")
            raise

# 创建全局实例
qwen_chat = QwenChat()

def chat(query: str):
    """ 对话接口
    query: 问题
    return: 回答
    """
    return cs2201_rag.chat(query=query,stream='no')

def chat_stream(query: str):
    """同步流式输出对话接口"""
    try:
        return cs2201_rag.chat(query=query, stream='stream')
    except Exception as e:
        print(f"当前模型调用失败: {str(e)}")
        if "insufficient_quota" in str(e) or "RateLimitError" in str(e):
            print("检测到 OpenAI 配额不足，尝试切换到通义千问...")
            try:
                # 使用新的通义千问调用方式
                return qwen_chat.stream_chat(query)
            except Exception as qwen_error:
                print(f"通义千问模型调用也失败: {str(qwen_error)}")
                # 如果通义千问也失败，尝试使用默认模型
                try:
                    print("尝试使用默认模型...")
                    llm = ChatTongyi(api_key=tongyi_config.DASHSCOPE_API_KEY)
                    cs2201_rag.change_model(llm=llm)
                    return cs2201_rag.chat(query=query, stream='stream')
                except Exception as default_error:
                    print(f"默认模型也初始化失败: {str(default_error)}")
                    raise default_error
        raise e

def chat_astream(query):
    """ 异步流式输出 对话接口
    query: 问题
    return: 答案的异步生成器
    """
    # 定义一个异步生成器
    async def generation():
        astream = cs2201_rag.chat(query,'astream')
        async for chunk in astream:
            # yield 表示该函数不是'函数', 而是生成器
            # yield 在每次调用时起到return作用
            # 返回后会使生成器停滞在yield语句之后
            yield chunk.content
    # 返回生成器
    g = generation()
    return g

def save_history(query: str, answer: str):
    """ 保存对话历史接口

    query: human的提问
    answer: ai的回答
    """
    cs2201_rag.save_history(query, answer)

def refresh_history(k: int):
    """刷新对话历史
    
    k: 记忆的轮数
    """
    cs2201_rag.refresh_history(k=k)

def start_audio():
    """ 开始语音识别接口
    """
    audio.start()

def stop_audio():
    """ 停止语音识别接口
    """
    text = audio.stop()
    return text

def change_model(model: str):
    """ 修改模型接口

    model: 模型名称
    """
    print(f"\n{'='*50}")
    print(f"正在切换模型到: {model}")
    print(f"{'='*50}\n")
    
    llm = None
    try:
        if model == 'qwen':
            print("正在初始化通义千问模型...")
            if not tongyi_config.DASHSCOPE_API_KEY:
                raise ValueError("通义千问 API Key 未配置")
            llm = ChatTongyi(api_key=tongyi_config.DASHSCOPE_API_KEY)
            print("✅ 通义千问模型初始化成功")
        elif model in ['gpt-4', 'gpt-4o', 'gpt-3.5-turbo']:
            print(f"正在初始化 OpenAI {model} 模型...")
            if not openai_config.OPENAI_API_KEY:
                raise ValueError("OpenAI API Key 未配置")
            llm = ChatOpenAI(model=model,
                           api_key=openai_config.OPENAI_API_KEY,
                           base_url=openai_config.base_url)
            print(f"✅ OpenAI {model} 模型初始化成功")
        elif model == 'glm-4':
            print("正在初始化智谱 GLM-4 模型...")
            if not zhipu_config.ZHIPU_API_KEY:
                raise ValueError("智谱 API Key 未配置")
            llm = ChatZhipuAI(model="glm-4",
                           api_key=zhipu_config.ZHIPU_API_KEY)
            print("✅ 智谱 GLM-4 模型初始化成功")
        else:
            print("未知模型，默认使用通义千问")
            if not tongyi_config.DASHSCOPE_API_KEY:
                raise ValueError("通义千问 API Key 未配置")
            llm = ChatTongyi(api_key=tongyi_config.DASHSCOPE_API_KEY)
            print("✅ 通义千问模型初始化成功")

        if llm is None:
            raise ValueError("模型初始化失败")

        # 修改模型 
        cs2201_rag.change_model(llm=llm)
        print(f"\n{'='*50}")
        print(f"✅ 模型切换成功: {llm.get_name()}")
        print(f"{'='*50}\n")
        
    except Exception as e:
        print(f"\n{'='*50}")
        print(f"❌ 模型切换失败: {str(e)}")
        print(f"{'='*50}\n")
        
        # 如果切换失败，尝试使用默认模型
        try:
            print("尝试使用默认模型...")
            if not tongyi_config.DASHSCOPE_API_KEY:
                raise ValueError("通义千问 API Key 未配置")
            llm = ChatTongyi(api_key=tongyi_config.DASHSCOPE_API_KEY)
            cs2201_rag.change_model(llm=llm)
            print("✅ 默认模型初始化成功")
        except Exception as default_error:
            print(f"默认模型也初始化失败: {str(default_error)}")
            raise default_error

def change_limit(limit: str):
    """ 修改cypher语句的limit接口

    limit: 数量
    """
    cs2201_rag.change_limit(limit=limit)
