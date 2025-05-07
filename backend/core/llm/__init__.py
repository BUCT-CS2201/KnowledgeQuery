import logging
from openai import OpenAI
from config.config_info import settings

logger = logging.getLogger(__name__)

class AiHubMixLLM:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.AIHUBMIX_API_KEY,
            base_url=settings.AIHUBMIX_BASE_URL,
        )
        self.model = settings.AIHUBMIX_MODEL
    
    async def get_response(self, messages):
        """
        获取AiHubMix API的回复
        :param messages: 消息列表，格式为[{"role": "user", "content": "你好"}, ...]
        :return: AI的回复文本
        """
        try:
            completion = self.client.chat.completions.create(
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
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                timeout=120  # 增加超时时间，单位为秒
            )
            
            full_response = ""
            # 处理流式响应
            for chunk in completion:
                if hasattr(chunk.choices, '__len__') and len(chunk.choices) > 0:
                    if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        yield content
            
            # 如果流式响应完全失败，返回错误信息
            if not full_response:
                yield "抱歉，我暂时无法回答您的问题。请稍后再试。"
                
        except Exception as e:
            logger.error(f"调用AiHubMix API流式响应失败: {str(e)}")
            yield "抱歉，我暂时无法回答您的问题。请稍后再试。"

# 创建一个单例实例
ai_llm = AiHubMixLLM()
