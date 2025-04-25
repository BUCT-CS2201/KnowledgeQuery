# RAG文档检索系统

基于Milvus向量数据库和Hugging Face嵌入模型的文档检索系统。

## 功能

- 支持多种文件格式：PDF、DOCX、TXT
- 多语言支持
- 文档分块和向量化
- 基于语义的相似度搜索
- 友好的Web界面

## 系统要求

- Python 3.8+
- Docker和Docker Compose

## 安装依赖

```bash
pip install langchain langchain_community langchain_text_splitters langchain_huggingface pymilvus gradio
```

## 部署Milvus

系统使用Milvus作为向量数据库。使用提供的Docker Compose配置可以轻松部署：

```bash
cd /Users/sanshi/Desktop/软件工程/CODE/RAG
docker-compose up -d
```

### Milvus组件:

- **etcd**: 元数据存储
- **minio**: 对象存储
- **standalone**: Milvus主服务
- **attu**: Web管理界面

### 访问端口:

- Milvus服务: 19530
- Attu管理界面: 8000
- Minio控制台: 9001 (用户名/密码: minioadmin/minioadmin)

## 启动应用

```bash
python main.py
```

应用将在http://127.0.0.1:7860启动。

## 使用流程

1. 先测试Milvus连接
2. 创建一个新的集合
3. 上传并索引文档
4. 执行文档查询
