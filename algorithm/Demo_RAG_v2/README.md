# RAG 文档检索系统

基于检索增强生成（Retrieval-Augmented Generation, RAG）的智能文档检索和问答系统。利用向量数据库Milvus存储文档向量，结合大语言模型提供准确的文档搜索和基于知识库的智能问答功能。

## 功能特点

- 支持多种文档格式（PDF、Word、TXT）的上传和索引
- 向量化检索，基于语义相似度查找文档
- 知识库增强的AI问答，使AI回答更准确，有事实依据
- 易用的图形界面，集成完整的文档管理和查询系统

## 安装指南

### 前提条件

- Python 3.8+
- Docker 和 Docker Compose（用于运行Milvus）

### 步骤1：克隆项目

```bash
git clone https://your-repository-url/RAG.git
cd RAG
```

### 步骤2：创建虚拟环境（推荐）

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 步骤3：安装依赖

```bash
pip install -r requirements.txt
```

### 步骤4：配置环境变量

1. 复制示例环境变量文件：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入您的API密钥和其他配置：
```
# Milvus配置
MILVUS_HOST=127.0.0.1
MILVUS_PORT=19530

# API配置
ONEAPI_BASE_URL=https://api.siliconflow.cn/v1
ONEAPI_API_KEY=your_api_key_here
ONEAPI_MODEL=Qwen/Qwen2.5-VL-72B-Instruct
```

## 启动Milvus向量数据库

使用Docker Compose启动Milvus：

```bash
docker-compose up -d
```

这将启动以下服务：
- Milvus服务 (端口19530)
- Attu管理界面 (端口8000)
- Minio对象存储 (端口9001)

### 验证Milvus是否正常运行

访问Milvus Attu管理界面：[http://localhost:8000](http://localhost:8000)

## 运行应用程序

启动RAG系统：

```bash
python main.py
```

应用程序将在本地启动，通常可以通过以下地址访问：
[http://localhost:7860](http://localhost:7860)

## 使用说明

### 1. 集合管理

在"集合管理"标签页中：
- 创建新的集合用于存储文档向量
- 列出所有现有集合

### 2. 文档上传与索引

在"文档上传与索引"标签页中：
- 上传PDF、Word或文本文件
- 选择要存储的目标集合
- 点击"处理并索引文件"

### 3. 文档查询

在"文档查询"标签页中：
- 输入查询文本
- 选择要搜索的集合
- 调整返回结果数量
- 查看语义相似度最高的文档片段

### 4. 知识库问答

在"知识库问答"标签页中：
- 输入问题
- 系统会从索引文档中检索相关内容
- 大语言模型基于检索到的文档生成回答

## 故障排除

### Milvus连接问题

- 确保Docker服务正在运行
- 验证端口19530没有被其他应用占用
- 检查Docker容器状态：`docker-compose ps`
- 查看容器日志：`docker-compose logs milvus-standalone`

### 嵌入模型加载失败

如果遇到嵌入模型加载失败：
- 检查网络连接
- 确保安装了所有依赖
- 考虑使用离线嵌入模型（修改代码中的模型路径）

### API调用错误

如果遇到API调用错误：
- 验证API密钥是否正确
- 检查账户余额
- 确认模型名称是否有效

## 停止服务

停止RAG应用程序：按`Ctrl+C`

停止Milvus：
```bash
docker-compose down
```

## 技术栈

- Langchain：文档处理和AI集成框架
- Hugging Face：模型加载和本地推理
- Milvus：向量数据库，用于高效相似度搜索
- Gradio：简单易用的Web界面
- Docker：容器化部署Milvus服务

## 许可证

本项目采用MIT许可证
