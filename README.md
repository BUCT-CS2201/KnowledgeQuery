# 👾 KnowledgeQuery—知识问答子系统

## 项目介绍

### 技术方案

+ 前后端：FastAPI+Vue3+Python

+ 数据库：MySQL+neo4j+Milvus

### 核心功能

- [x] 🧩 普通问答
- [x] 📂  知识库问答
- [x] 🌐 知识图谱问答

## 后端启动

+ **STEP 1 进入后端目录**

```bash
cd backend
```

+ **STEP 2 创建虚拟环境**

```bash
python3 -m venv venv
# Linux/Mac
source venv/bin/activate  
# Windows下
venv\Scripts\activate
```

+ **STEP 3 安装依赖**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

+ **STEP 4 配置.env文件**

```bash
cp .env_copy .env
vim .env
```

必要的环境变量配置：
```ini
# 数据库配置
MYSQL_IP=
MYSQL_PORT=
MYSQL_BASE=
MYSQL_USER=
MYSQL_PASSWORD=

# JWT设置
SECRET_KEY=

# 大模型API配置
AIHUBMIX_API_KEY=
AIHUBMIX_BASE_URL=
AIHUBMIX_MODEL=

# Milvus配置
MILVUS_HOST=
MILVUS_PORT=
MILVUS_DATABASE=
MILVUS_COLLECTION=

# Neo4j配置
NEO4J_URI=
NEO4J_USERNAME=
NEO4J_PASSWORD=
NEO4J_MAX_CONNECTION_LIFETIME=
NEO4J_MAX_CONNECTION_POOL_SIZE=
NEO4J_CONNECTION_TIMEOUT=

```

+ **STEP 5 开发测试建议运行**

```bash
uvicorn main:app --reload --port 9988
```


## 前端部署
+ **STEP 1 进入前端目录**

```bash
cd frontend
```

+ **STEP 2 安装依赖**

```bash
npm install
```

如果安装依赖报错
1. 检查node版本：
```bash
node --version
v22.12.0
```

2. 检查npm源
```bash
npm config set registry https://registry.npmmirror.com/
npm install
```

3. 清理缓存和重新安装（适用于常见安装问题）：

   Windows PowerShell:
   ```powershell
   Remove-Item -Recurse -Force node_modules
   Remove-Item package-lock.json
   npm cache clean --force
   npm install
   ```

   Windows 命令行:
   ```cmd
   rd /s /q node_modules
   del package-lock.json
   npm cache clean --force
   npm install
   ```

   Linux/Mac:
   ```bash
   rm -rf node_modules
   rm package-lock.json
   npm cache clean --force
   npm install
   ```

+ **STEP 3 开发模式运行**

```bash
npm run dev
```