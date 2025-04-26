# 知识问答子系统

## 后端启动

进入后端目录
```bash
cd backend
```

创建虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 Windows下
# venv\Scripts\activate
```

安装依赖
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

配置.env文件
```bash
cp .env_copy .env
vim .env
```

必要的环境变量配置：
```ini
# 数据库配置
MYSQL_IP=localhost  # 本地部署使用localhost
MYSQL_PORT=3306
MYSQL_BASE=chat2anything_db
MYSQL_USER=root  # 或您创建的用户
MYSQL_PASSWORD=your_password
```

运行后端服务
```bash
python main.py
```

开发测试建议运行
```bash
uvicorn main:app --reload --port 9988
```

## 前端部署
进入前端目录
```bash
cd frontend
```

安装依赖
```bash
npm install
```

开发模式运行
```bash
npm run dev
```