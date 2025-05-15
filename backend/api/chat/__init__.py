from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from core.databases import get_db
from core.auth.jwt import get_current_user, TokenData
from pydantic import BaseModel
from typing import List, Optional
import time  # 添加time模块导入
import asyncio  # 添加asyncio模块导入
from services.chat import (
    create_chat_session, 
    get_user_chat_sessions, 
    get_chat_session, 
    delete_chat_session, 
    update_chat_session,
    send_message,
    send_streaming_message
)

router = APIRouter()

# 定义请求/响应模型
class ChatSessionCreate(BaseModel):
    title: str = "新对话"
    type: int = 1  # 默认为普通问答

class ChatSessionUpdate(BaseModel):
    title: str

class MessageCreate(BaseModel):
    content: str
    model: Optional[str] = None  # 添加可选的模型参数

class MessageResponse(BaseModel):
    id: int
    content: str
    is_user: bool
    created_at: str

class ChatSessionResponse(BaseModel):
    id: int
    title: str
    type: int
    created_at: str
    updated_at: str

# 创建新聊天会话
@router.post("/sessions", summary="创建新聊天会话")
async def create_session(
    request: ChatSessionCreate, 
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        session = create_chat_session(db, current_user.user_id, request.title, request.type)
        return {
            "code": 200,
            "message": "创建成功",
            "data": {
                "id": session.id,
                "title": session.title,
                "type": session.type,
                "created_at": session.created_at,
                "updated_at": session.updated_at
            }
        }
    except HTTPException as e:
        return {
            "code": e.status_code,
            "message": e.detail,
            "data": None
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"创建失败: {str(e)}",
            "data": None
        }

# 获取用户的所有聊天会话
@router.get("/sessions", summary="获取用户聊天会话列表")
async def get_sessions(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        sessions = get_user_chat_sessions(db, current_user.user_id)
        return {
            "code": 200,
            "message": "获取成功",
            "data": [
                {
                    "id": session.id,
                    "title": session.title,
                    "type": session.type,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at
                } for session in sessions
            ]
        }
    except HTTPException as e:
        return {
            "code": e.status_code,
            "message": e.detail,
            "data": None
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取失败: {str(e)}",
            "data": None
        }

# 获取单个聊天会话及其消息
@router.get("/sessions/{session_id}", summary="获取聊天会话详情")
async def get_session(
    session_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = get_chat_session(db, session_id, current_user.user_id)
        session = result["session"]
        messages = result["messages"]
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": {
                "session": {
                    "id": session.id,
                    "title": session.title,
                    "type": session.type,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at
                },
                "messages": [
                    {
                        "id": msg.id,
                        "content": msg.content,
                        "is_user": msg.is_user,
                        "created_at": msg.created_at
                    } for msg in messages
                ]
            }
        }
    except HTTPException as e:
        return {
            "code": e.status_code,
            "message": e.detail,
            "data": None
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取失败: {str(e)}",
            "data": None
        }

# 删除聊天会话
@router.delete("/sessions/{session_id}", summary="删除聊天会话")
async def delete_session(
    session_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = delete_chat_session(db, session_id, current_user.user_id)
        return {
            "code": 200,
            "message": "删除成功",
            "data": None
        }
    except HTTPException as e:
        return {
            "code": e.status_code,
            "message": e.detail,
            "data": None
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"删除失败: {str(e)}",
            "data": None
        }

# 更新聊天会话标题
@router.put("/sessions/{session_id}", summary="更新聊天会话标题")
async def update_session(
    session_id: int,
    request: ChatSessionUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        session = update_chat_session(db, session_id, current_user.user_id, request.title)
        return {
            "code": 200,
            "message": "更新成功",
            "data": {
                "id": session.id,
                "title": session.title,
                "created_at": session.created_at,
                "updated_at": session.updated_at
            }
        }
    except HTTPException as e:
        return {
            "code": e.status_code,
            "message": e.detail,
            "data": None
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"更新失败: {str(e)}",
            "data": None
        }

# 发送消息并获取AI回复
@router.post("/sessions/{session_id}/messages", summary="发送消息")
async def create_message(
    session_id: int,
    request: MessageCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = await send_message(db, session_id, current_user.user_id, request.content)
        user_message = result["user_message"]
        ai_message = result["ai_message"]
        
        return {
            "code": 200,
            "message": "发送成功",
            "data": {
                "user_message": {
                    "id": user_message.id,
                    "content": user_message.content,
                    "is_user": user_message.is_user,
                    "created_at": user_message.created_at
                },
                "ai_message": {
                    "id": ai_message.id,
                    "content": ai_message.content,
                    "is_user": ai_message.is_user,
                    "created_at": ai_message.created_at
                }
            }
        }
    except HTTPException as e:
        return {
            "code": e.status_code,
            "message": e.detail,
            "data": None
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"发送失败: {str(e)}",
            "data": None
        }

# 发送消息并获取AI流式回复
@router.post("/sessions/{session_id}/stream", summary="发送消息并获取流式回复")
async def create_stream_message(
    session_id: int,
    request: MessageCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # 保存用户消息并获取流式响应
        async def event_generator():
            # 发送开始标记，帮助前端识别响应开始
            yield f"data: [START]\n\n"
            
            # 传递模型参数，生成流式响应
            async for chunk in send_streaming_message(
                db, session_id, current_user.user_id, request.content, model=request.model
            ):
                if chunk:
                    yield f"data: {chunk}\n\n"
            
            # 发送结束标记，帮助前端识别响应结束
            yield f"data: [DONE]\n\n"
        
        # 设置正确的响应头，确保浏览器不缓存流
        return StreamingResponse(
            event_generator(), 
            media_type="text/event-stream",
            headers={
                'Cache-Control': 'no-cache, no-transform, must-revalidate',
                'Connection': 'keep-alive',
                'Content-Type': 'text/event-stream',
                'X-Accel-Buffering': 'no',  # 禁用Nginx的缓冲
                'Transfer-Encoding': 'chunked'
            }
        )
    except HTTPException as e:
        return {
            "code": e.status_code,
            "message": e.detail,
            "data": None
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"发送失败: {str(e)}",
            "data": None
        }