from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from routes import auth_router, chat_router

# 创建FastAPI应用
app = FastAPI(title="知识问答子系统 API", version="1.0.0")

# 配置CORS
origins = [
    "http://localhost:5173",  # 前端默认地址
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"])

# 根路径
@app.get("/")
async def root():
    return {"message": "知识问答子系统 API is running"}

# 启动服务器
if __name__ == "__main__":
    config = uvicorn.Config("main:app", host="0.0.0.0", port=8000, reload=True)
    server = uvicorn.Server(config)
    server.run() 