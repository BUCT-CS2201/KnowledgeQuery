# 知识问答子系统

这是一个知识问答子系统，模仿DeepSeek的界面风格，包含用户认证和问答功能。系统使用FastAPI作为后端，Vue.js 3作为前端。

## 项目结构

```
auth_system/
├── backend/              # 后端代码
│   ├── database/         # 数据库配置
│   ├── models/           # 数据模型
│   ├── routes/           # API路由
│   ├── schemas/          # Pydantic模式
│   ├── utils/            # 工具函数
│   ├── main.py           # 后端入口文件
│   ├── requirements.txt  # 后端依赖
│   └── setup.py          # 数据库初始化脚本
└── frontend/             # 前端代码
    ├── src/              # 源代码
    │   ├── assets/       # 静态资源
    │   ├── components/   # Vue组件
    │   ├── router/       # 路由配置
    │   ├── store/        # 状态管理
    │   ├── views/        # 页面视图
    │   ├── App.vue       # 主应用组件
    │   └── main.js       # 前端入口文件
    ├── index.html        # HTML入口
    ├── package.json      # 前端依赖
    └── vite.config.js    # Vite配置
```

## 功能特性

- **用户认证**
  - 用户注册
  - 用户登录
  - JWT认证
  - 个人资料查看
  - 安全登出

- **知识问答**
  - 创建对话会话
  - 历史会话管理
  - 问答对话界面
  - 实时消息交互
  - 会话删除与管理
  - 文件上传分析
  - 多种模型选择（通用知识、代码助手、文档理解）
  - 联网搜索功能
  - 来源引用显示

## 运行说明

### 后端运行步骤

1. 进入后端目录
   ```bash
   cd auth_system/backend
   ```

2. 创建并激活虚拟环境（推荐）
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```
   
   注意：requirements.txt 已更新，包含所有必要的依赖，包括email-validator。

4. 初始化数据库
   ```bash
   python setup.py
   ```

5. 启动服务器
   ```bash
   python main.py
   ```
   或使用uvicorn直接启动：
   ```bash
   uvicorn main:app --reload
   ```
   服务器将在 http://localhost:8000 上运行

### 前端运行步骤

1. 进入前端目录
   ```bash
   cd auth_system/frontend
   ```

2. 安装依赖
   ```bash
   npm install
   ```
   
   如遇到权限问题，可尝试以下解决方案：
   ```bash
   # Windows下使用管理员权限运行命令提示符，然后执行安装
   
   # 或使用--no-optional跳过可选依赖
   npm install --no-optional
   
   # 清除npm缓存
   npm cache clean --force
   
   # 或切换npm镜像源
   npm config set registry https://registry.npmmirror.com
   ```

3. 启动开发服务器
   ```bash
   npm run dev
   ```
   前端将在 http://localhost:5173 上运行

## 系统界面

### 登录界面
用户可以通过用户名和密码登录系统，新用户可以点击"立即注册"链接进入注册页面。

### 注册界面
新用户可以通过提供用户名、邮箱和密码注册账号。

### 主界面
登录后，用户将进入类似DeepSeek的问答界面：
- 左侧：会话列表，显示所有历史对话，可以创建新对话
- 右侧：聊天区域，显示当前会话的消息记录，用户可以输入问题并获取回答
- 顶部：模型选择和联网搜索开关
- 底部：文件上传功能和发送按钮

### 高级功能

#### 文件上传分析
用户可以上传文件，系统会分析文件内容并回答相关问题。

#### 模型选择
系统提供三种不同的模型：
- 通用知识模型：回答一般性问题
- 代码助手：提供代码示例和技术解答
- 文档理解：分析和总结文档内容

#### 联网搜索
用户可以启用联网搜索功能，系统会从网络获取最新信息，并在回答中提供引用来源。

### 个人资料
用户可以查看自己的账号信息，包括用户名、邮箱和注册时间。

## API文档

启动后端服务后，可以通过以下URL访问API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 技术栈

### 后端
- FastAPI - 现代Python Web框架
- SQLAlchemy - SQL工具包和ORM
- Pydantic - 数据验证和设置管理
- JWT - JSON Web Token认证
- Python-Multipart - 文件上传支持

### 前端
- Vue.js 3 - 渐进式JavaScript框架
- Vue Router - 路由管理
- Pinia - 状态管理
- Element Plus - UI组件库
- Axios - HTTP客户端

## 常见问题解决

1. **后端启动报错缺少email-validator**
   已在requirements.txt中添加email-validator库，请确保运行`pip install -r requirements.txt`安装所有依赖。

2. **前端npm安装权限问题**
   在Windows系统中，尝试使用管理员权限运行命令提示符，然后执行npm install。
   或者使用`npm install --no-optional`跳过可选依赖。

3. **文件上传相关问题**
   确保backend目录下的uploads文件夹存在且有写入权限。系统会自动创建此文件夹，但如遇权限问题，请手动创建并设置适当权限。

4. **创建会话失败：no such table: chat_sessions**
   这是因为数据库中缺少聊天相关的表。请确保在运行系统前执行以下步骤：
   ```bash
   cd auth_system/backend
   python setup.py
   ```
   如果已经运行过setup.py但仍然有这个错误，请检查setup.py是否正确导入了所有模型（包括ChatSession和ChatMessage）。
   您也可以尝试删除现有的auth_system.db文件，然后重新运行setup.py来重新创建所有表。

5. **消息发送失败：AttributeError: 'Session' object has no attribute 'func'**
   这是因为SQLAlchemy的Session对象没有直接的func属性。此问题已在最新版本中修复，使用datetime.now()替代了db.func.now()。
   如果您遇到此问题，请修改routes/chat.py文件，导入datetime模块，并将所有的db.func.now()替换为datetime.now()。

## 模型说明

系统现在支持以下模型：

1. **通用知识模型** - 回答一般性问题
2. **DeepSeek** - 高级人工智能语言模型，提供详细准确的回答
3. **代码助手** - 专注于编程相关问题，提供代码示例
4. **文档理解** - 专注于分析和总结文档内容

## DeepSeek API配置

系统支持调用真实的DeepSeek API，需要进行以下配置：

1. 在DeepSeek官网注册并获取API密钥：https://deepseek.com
2. 在后端目录创建`.env`文件，添加以下内容：
   ```
   DEEPSEEK_API_KEY=your-api-key-here
   DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions
   ```
3. 安装必要的依赖：
   ```bash
   pip install httpx
   ```
   
系统会优先使用DeepSeek API，如果没有配置API密钥或请求失败，会使用模拟的回答。 