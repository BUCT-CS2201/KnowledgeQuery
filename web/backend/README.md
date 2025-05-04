# 知识问答系统后端

## 功能特性

- 用户认证系统
  - 注册、登录、JWT认证
- 聊天会话管理
  - 创建、查询、更新和删除会话
- 消息处理
  - 发送和接收消息
  - 文件上传分析
- 多模型支持
  - 通用知识模型
  - DeepSeek集成
  - 代码助手
  - 文档理解
- 联网搜索
  - 支持Google搜索API
  - 支持Bing搜索API
  - 回退到DuckDuckGo搜索
  - 显示来源引用

## 环境配置

1. 复制环境变量模板并填写
   ```bash
   cp .env.template .env
   ```

2. 编辑`.env`文件，填入:
   - 数据库连接信息
   - 搜索API密钥
   - DeepSeek API密钥（可选）

## 联网搜索配置

系统支持多种搜索API，按以下优先级使用:

1. **Google自定义搜索**
   - 需要注册[Google Cloud](https://cloud.google.com)
   - 创建[自定义搜索引擎](https://programmablesearchengine.google.com/about/)
   - 获取API密钥和搜索引擎ID
   - 在`.env`中配置:
     ```
     GOOGLE_SEARCH_API_KEY=your_google_api_key
     GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id
     ```

2. **Bing搜索API**
   - 注册[Bing Search API](https://www.microsoft.com/en-us/bing/apis/bing-web-search-api)
   - 获取API密钥
   - 在`.env`中配置:
     ```
     BING_SEARCH_API_KEY=your_bing_api_key
     ```

3. **DuckDuckGo搜索**
   - 不需要API密钥
   - 当其他搜索API未配置时自动使用

如果以上搜索API都未配置或都不可用，系统会回退到模拟搜索结果。

## 使用说明

### 搜索示例

当用户启用"联网搜索"功能时，系统会:

1. 根据用户问题进行网络搜索
2. 从搜索结果中提取相关信息
3. 基于提取的信息生成回答
4. 在回答底部显示信息来源

用户可以点击来源链接查看原始信息。

### DeepSeek集成

系统支持集成DeepSeek API进行更高级的问答:

1. 注册[DeepSeek API](https://deepseek.com)并获取API密钥
2. 在`.env`中配置:
   ```
   DEEPSEEK_API_KEY=your_deepseek_api_key
   DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions
   ```

## 运行指南

1. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

2. 初始化数据库
   ```bash
   python setup.py
   ```

3. 启动服务器
   ```bash
   python main.py
   ```
   或
   ```bash
   uvicorn main:app --reload
   ``` 