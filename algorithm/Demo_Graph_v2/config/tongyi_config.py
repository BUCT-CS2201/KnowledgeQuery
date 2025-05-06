# 通义千问 API 配置
DASHSCOPE_API_KEY = '你的通义千问 api key'  # 请替换为你的有效 API Key

# 模型配置
MODEL_NAME = "你的通义千问模型"  # 使用 qwen-turbo 作为默认模型
TEMPERATURE = 0.7  # 温度参数，控制输出的随机性
TOP_P = 0.8  # 采样阈值
MAX_TOKENS = 2000  # 最大输出长度

# 流式输出配置
STREAMING = True  # 是否使用流式输出
STREAMING_INTERVAL = 0.1  # 流式输出间隔（秒）

# 重试配置
MAX_RETRIES = 3  # 最大重试次数
RETRY_DELAY = 1  # 重试延迟（秒）


