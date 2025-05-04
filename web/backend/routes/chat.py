from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, AsyncGenerator
from database.db import get_db
from models.user import User
from models.chat import ChatSession, ChatMessage
from schemas.chat import (
    ChatSessionCreate, 
    ChatSessionBrief, 
    ChatSession as ChatSessionSchema,
    ChatMessageCreate,
    ChatMessage as ChatMessageSchema,
    FileInfo,
    SourceInfo,
    StreamResponse,
    StreamChoice,
    StreamDelta
)
from utils.security import get_current_active_user
from utils.web_search import web_search, generate_answer_from_search_results
import os
import shutil
from pathlib import Path
import json
import random
from datetime import datetime
import httpx
import asyncio
from dotenv import load_dotenv
import uuid
import time

# 加载环境变量
load_dotenv()

# DeepSeek API配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")

router = APIRouter()

# 确保上传目录存在
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# 调用DeepSeek API（非流式）
async def call_deepseek_api(query: str) -> str:
    """调用DeepSeek API获取回答（非流式）"""
    if not DEEPSEEK_API_KEY:
        # 如果没有配置API密钥，返回模拟回答
        return f"DeepSeek模型的回答（模拟）：\n\n关于'{query}'的分析结果如下：\n\n这是一个基于深度学习的高级语言模型回答。我能够理解复杂的问题，并提供详细、准确的回答。我的知识库涵盖了广泛的领域，包括科学、技术、历史、文化等。\n\n如有更多问题，欢迎继续提问。"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": query}
                ],
                "temperature": 0.7,
                "max_tokens": 800,
                "stream": False
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
            }
            
            response = await client.post(
                DEEPSEEK_API_URL,
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("choices", [{}])[0].get("message", {}).get("content", "无法获取回答")
            else:
                # API调用失败时返回错误信息
                return f"DeepSeek API调用失败（状态码：{response.status_code}）。使用备用回答：\n\n这是一个模拟的DeepSeek回答。实际使用时，您需要配置有效的DeepSeek API密钥。"
    
    except Exception as e:
        # 出现异常时返回错误信息
        return f"调用DeepSeek API时发生错误：{str(e)}。使用备用回答：\n\n这是一个模拟的DeepSeek回答。请检查您的网络连接和API配置。"

# 调用DeepSeek API（流式）
async def call_deepseek_api_stream(query: str) -> AsyncGenerator[str, None]:
    """调用DeepSeek API获取流式回答"""
    print(f"开始DeepSeek流式调用: query={query[:30]}...")
    
    if not DEEPSEEK_API_KEY:
        # 如果没有配置API密钥，返回模拟回答（分段模拟流式效果）
        print("没有找到DeepSeek API密钥，使用模拟数据")
        chunks = [
            "DeepSeek模型的回答（模拟）：\n\n",
            "关于'", query, "'的分析结果如下：\n\n",
            "这是一个基于深度学习的高级语言模型回答。",
            "我能够理解复杂的问题，",
            "并提供详细、准确的回答。",
            "我的知识库涵盖了广泛的领域，",
            "包括科学、技术、历史、文化等。\n\n",
            "如有更多问题，欢迎继续提问。"
        ]
        
        for chunk in chunks:
            print(f"发送模拟块: {chunk}")
            yield chunk
            await asyncio.sleep(0.2)  # 模拟网络延迟
        return
    
    try:
        print(f"使用DeepSeek API: URL={DEEPSEEK_API_URL}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": query}
                ],
                "temperature": 0.7,
                "max_tokens": 800,
                "stream": True
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
            }
            
            print("发送DeepSeek API请求...")
            
            async with client.stream("POST", DEEPSEEK_API_URL, json=payload, headers=headers) as response:
                print(f"收到DeepSeek API响应: 状态码={response.status_code}")
                
                if response.status_code != 200:
                    # API调用失败时返回错误信息
                    error_msg = f"DeepSeek API调用失败（状态码：{response.status_code}）。使用备用回答：这是一个模拟的DeepSeek回答。实际使用时，您需要配置有效的DeepSeek API密钥。"
                    print(f"API错误: {error_msg}")
                    yield error_msg
                    return
                
                # 处理流式响应
                buffer = ""
                print("开始处理流式响应...")
                
                async for chunk in response.aiter_text():
                    print(f"原始块: {chunk}")
                    if not chunk.strip():
                        continue
                    
                    # 处理SSE格式的数据
                    if chunk.startswith("data: "):
                        chunk = chunk[6:]  # 去掉 "data: " 前缀
                    
                    if chunk.strip() == "[DONE]":
                        print("收到[DONE]信号")
                        break
                    
                    try:
                        chunk_data = json.loads(chunk)
                        content = chunk_data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if content:
                            print(f"解析的内容块: {content}")
                            yield content
                    except json.JSONDecodeError as e:
                        # 解析JSON失败，尝试作为纯文本处理
                        print(f"JSON解析失败: {e}, 原始数据: {chunk}")
                        if chunk.strip():
                            yield chunk.strip()
    
    except Exception as e:
        # 出现异常时返回错误信息
        error_msg = f"调用DeepSeek API时发生错误：{str(e)}。使用备用回答：这是一个模拟的DeepSeek回答。请检查您的网络连接和API配置。"
        print(f"DeepSeek API异常: {str(e)}")
        yield error_msg

# 获取用户所有聊天会话
@router.get("/sessions", response_model=List[ChatSessionBrief])
async def get_chat_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id,
        ChatSession.is_active == True
    ).order_by(ChatSession.updated_at.desc()).all()
    
    return sessions

# 创建新的聊天会话
@router.post("/sessions", response_model=ChatSessionBrief, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    new_session = ChatSession(
        title=session_data.title,
        user_id=current_user.id
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return new_session

# 获取特定聊天会话及其消息
@router.get("/sessions/{session_id}", response_model=ChatSessionSchema)
async def get_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
        ChatSession.is_active == True
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天会话不存在"
        )
    
    return session

# 删除聊天会话（软删除）
@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
        ChatSession.is_active == True
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天会话不存在"
        )
    
    session.is_active = False
    db.commit()
    
    return None

# 发送消息并获取流式回复
@router.get("/sessions/{session_id}/messages/stream")
async def create_message_stream_get(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """处理GET请求的流式响应，主要用于EventSource连接"""
    
    # 验证会话存在且属于当前用户
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
        ChatSession.is_active == True
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天会话不存在"
        )
    
    # 获取最新的未回复用户消息
    latest_user_message = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id,
        ChatMessage.is_user == True
    ).order_by(ChatMessage.id.desc()).first()
    
    if not latest_user_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未找到用户消息"
        )
    
    # 创建AI回复消息
    ai_message = ChatMessage(
        session_id=session_id,
        content="",
        is_user=False
    )
    db.add(ai_message)
    db.commit()
    db.refresh(ai_message)
    
    # 创建响应ID和时间戳
    response_id = str(uuid.uuid4())
    created_time = int(time.time())
    
    # 流式响应生成器
    async def stream_generator():
        full_response = ""
        
        # 调试信息
        print(f"GET流式输出: 会话ID={session_id}, 用户ID={current_user.id}")
        print(f"用户消息ID={latest_user_message.id}, 内容={latest_user_message.content[:30]}...")
        
        # 生成DeepSeek回答
        try:
            async for text_chunk in call_deepseek_api_stream(latest_user_message.content):
                full_response += text_chunk
                
                # 构建流式响应格式
                try:
                    chunk_response = StreamResponse(
                        id=response_id,
                        created=created_time,
                        model="deepseek-chat",
                        choices=[
                            StreamChoice(
                                delta=StreamDelta(content=text_chunk),
                                index=0
                            )
                        ]
                    )
                    
                    # 检查Pydantic v2的序列化方法
                    response_dict = chunk_response.model_dump()
                    print(f"响应数据结构: {response_dict}")
                    
                    # 发送JSON格式的数据块
                    yield f"data: {json.dumps(response_dict)}\n\n"
                except Exception as e:
                    print(f"构建流式响应出错: {str(e)}")
                    # 使用原始方式构建响应
                    fallback_response = {
                        "id": response_id,
                        "created": created_time,
                        "model": "deepseek-chat",
                        "choices": [
                            {
                                "delta": {"content": text_chunk},
                                "index": 0
                            }
                        ],
                        "object": "chat.completion.chunk"
                    }
                    yield f"data: {json.dumps(fallback_response)}\n\n"
        except Exception as e:
            print(f"GET流式输出错误: {str(e)}")
            error_chunk = StreamResponse(
                id=response_id,
                created=created_time,
                model="deepseek-chat",
                choices=[
                    StreamChoice(
                        delta=StreamDelta(content=f"流式输出错误: {str(e)}"),
                        index=0
                    )
                ]
            )
            yield f"data: {json.dumps(error_chunk.model_dump())}\n\n"
            full_response += f"流式输出错误: {str(e)}"
        
        # 发送完成信号
        yield f"data: [DONE]\n\n"
        print(f"GET流式输出完成，总长度: {len(full_response)}")
        
        # 更新AI消息内容
        ai_message.content = full_response
        db.commit()
    
    # 设置响应头，支持CORS和认证
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization"
    }
    
    # 返回流式响应
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers=headers
    )

# 发送消息并获取流式回复 (POST方法)
@router.post("/sessions/{session_id}/messages/stream")
async def create_message_stream(
    session_id: int,
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """处理POST请求的流式响应"""
    # 验证会话存在且属于当前用户
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
        ChatSession.is_active == True
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天会话不存在"
        )
    
    # 处理消息内容
    content = message_data.content.strip()
    
    # 如果没有内容但有文件，设置一个默认内容
    if not content and message_data.files:
        content = "请分析这些文件"
    
    # 保存用户消息
    user_message = ChatMessage(
        session_id=session_id,
        content=content,
        is_user=True
    )
    db.add(user_message)
    
    # 预创建AI回复消息（内容先为空）
    ai_message = ChatMessage(
        session_id=session_id,
        content="",
        is_user=False
    )
    db.add(ai_message)
    
    # 更新会话时间
    session.updated_at = datetime.now()
    db.commit()
    db.refresh(user_message)
    db.refresh(ai_message)
    
    # 创建响应ID
    response_id = str(uuid.uuid4())
    created_time = int(time.time())
    model_name = message_data.model or "general"
    
    # 流式响应生成器
    async def stream_generator():
        full_response = ""
        
        # 调试信息
        print(f"开始流式输出: 模型={model_name}, 内容={content[:30]}...")
        
        # 根据模型类型生成响应
        if model_name == "deepseek":
            try:
                async for text_chunk in call_deepseek_api_stream(content):
                    full_response += text_chunk
                    print(f"收到流式块: {text_chunk[:20]}...")
                    
                    # 构建流式响应格式
                    chunk_response = StreamResponse(
                        id=response_id,
                        created=created_time,
                        model="deepseek-chat",
                        choices=[
                            StreamChoice(
                                delta=StreamDelta(content=text_chunk),
                                index=0
                            )
                        ]
                    )
                    
                    # 检查Pydantic v2的序列化方法
                    response_dict = chunk_response.model_dump()
                    print(f"响应数据结构: {response_dict}")
                    
                    # 发送JSON格式的数据块
                    yield f"data: {json.dumps(response_dict)}\n\n"
            except Exception as e:
                print(f"流式输出错误: {str(e)}")
                error_chunk = StreamResponse(
                    id=response_id,
                    created=created_time,
                    model="deepseek-chat",
                    choices=[
                        StreamChoice(
                            delta=StreamDelta(content=f"流式输出错误: {str(e)}"),
                            index=0
                        )
                    ]
                )
                yield f"data: {json.dumps(error_chunk.model_dump())}\n\n"
                full_response += f"流式输出错误: {str(e)}"
        else:
            # 其他模型暂不支持流式输出，使用简单模拟
            chunks = []
            if model_name == "code":
                chunks = [
                    "以下是针对'", content, "'的代码示例：\n\n",
                    "```python\ndef example_function():\n    ",
                    "print('这是一个针对您问题的代码示例')\n    ",
                    "return True\n```\n\n",
                    "您可以根据需要进行修改。"
                ]
            elif model_name == "doc":
                chunks = [
                    "我已分析了文档中关于'", content, "'的内容。主要观点是：\n\n",
                    "1. 首先...\n",
                    "2. 其次...\n",
                    "3. 最后...\n\n",
                    "希望这个总结对您有帮助！"
                ]
            else:  # general
                chunks = [
                    "这是对'", content, "'的回复。\n\n",
                    "在实际应用中，这里应该调用知识库问答API获取更准确的回答。\n\n",
                    "您可以继续提问，或者尝试其他模型。"
                ]
            
            for chunk in chunks:
                full_response += chunk
                
                # 构建流式响应格式
                chunk_response = StreamResponse(
                    id=response_id,
                    created=created_time,
                    model=model_name,
                    choices=[
                        StreamChoice(
                            delta=StreamDelta(content=chunk),
                            index=0
                        )
                    ]
                )
                
                # 检查Pydantic v2的序列化方法
                response_dict = chunk_response.model_dump()
                print(f"响应数据结构: {response_dict}")
                
                # 发送JSON格式的数据块
                yield f"data: {json.dumps(response_dict)}\n\n"
                await asyncio.sleep(0.1)  # 模拟网络延迟
        
        # 发送完成信号
        yield f"data: [DONE]\n\n"
        print(f"流式输出完成，总长度: {len(full_response)}")
        
        # 更新AI消息内容
        ai_message.content = full_response
        db.commit()
    
    # 返回流式响应
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream"
    )

# 发送消息并获取回复
@router.post("/sessions/{session_id}/messages", response_model=List[ChatMessageSchema])
async def create_message(
    session_id: int,
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # 如果请求流式响应，重定向到流式API
    if message_data.stream and message_data.model == "deepseek":
        return await create_message_stream(
            session_id=session_id,
            message_data=message_data,
            current_user=current_user,
            db=db
        )
    
    # 验证会话存在且属于当前用户
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
        ChatSession.is_active == True
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天会话不存在"
        )
    
    # 处理消息内容
    content = message_data.content.strip()
    
    # 如果没有内容但有文件，设置一个默认内容
    if not content and message_data.files:
        content = "请分析这些文件"
    
    # 保存用户消息
    user_message = ChatMessage(
        session_id=session_id,
        content=content,
        is_user=True
    )
    db.add(user_message)
    
    # 更新会话时间
    session.updated_at = datetime.now()
    
    # 获取AI响应
    model = message_data.model or "general"
    web_search_enabled = message_data.web_search or False
    
    # 根据不同模型和是否联网生成不同回复
    if model == "code":
        ai_response = f"以下是针对'{content}'的代码示例：\n\n```python\ndef example_function():\n    print('这是一个针对您问题的代码示例')\n    return True\n```\n\n您可以根据需要进行修改。"
        sources = []
    elif model == "doc":
        ai_response = f"我已分析了文档中关于'{content}'的内容。主要观点是：\n\n1. 首先...\n2. 其次...\n3. 最后...\n\n希望这个总结对您有帮助！"
        sources = []
    elif model == "deepseek":
        # 调用DeepSeek API
        ai_response = await call_deepseek_api(content)
        sources = []
    else:  # general
        if web_search_enabled:
            # 进行实际的联网搜索
            sources = await web_search(content)
            # 根据搜索结果生成回答
            ai_response = await generate_answer_from_search_results(content, sources)
        else:
            ai_response = f"这是对'{content}'的回复。在实际应用中，这里应该调用知识库问答API获取更准确的回答。"
            sources = []
    
    # 创建AI回复消息
    ai_message = ChatMessage(
        session_id=session_id,
        content=ai_response,
        is_user=False
    )
    db.add(ai_message)
    
    db.commit()
    db.refresh(user_message)
    db.refresh(ai_message)
    
    # 将消息对象转换为schema，添加sources数据
    user_message_schema = ChatMessageSchema.model_validate(user_message)
    ai_message_schema = ChatMessageSchema.model_validate(ai_message)
    
    # 只有在启用联网搜索时才添加sources
    if web_search_enabled:
        ai_message_schema.web_search = True
        ai_message_schema.sources = sources
    
    # 返回用户消息和AI回复
    return [user_message_schema, ai_message_schema]

# 发送带文件的消息
@router.post("/sessions/{session_id}/messages/with-files", response_model=List[ChatMessageSchema])
async def create_message_with_files(
    session_id: int,
    content: str = Form(""),
    model: str = Form("general"),
    web_search: bool = Form(False),
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # 验证会话存在且属于当前用户
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
        ChatSession.is_active == True
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天会话不存在"
        )
    
    # 创建用户目录
    user_upload_dir = UPLOAD_DIR / str(current_user.id) / str(session_id)
    user_upload_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存上传的文件
    saved_files = []
    for file in files:
        file_path = user_upload_dir / file.filename
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        saved_files.append({
            "name": file.filename,
            "path": str(file_path),
            "size": os.path.getsize(file_path),
            "type": file.content_type
        })
    
    # 如果没有内容，设置一个默认内容
    if not content.strip():
        content = "请分析这些文件"
    
    # 保存用户消息，包含文件信息
    user_message = ChatMessage(
        session_id=session_id,
        content=content,
        is_user=True
    )
    db.add(user_message)
    
    # 更新会话时间
    session.updated_at = datetime.now()
    
    # 为文件生成AI响应
    file_list = "\n".join([f"- {f['name']} ({f['size']} 字节)" for f in saved_files])
    ai_response = f"我已收到您上传的{len(saved_files)}个文件：\n\n{file_list}\n\n正在分析文件内容，请稍候..."
    
    # 创建AI回复消息
    ai_message = ChatMessage(
        session_id=session_id,
        content=ai_response,
        is_user=False
    )
    db.add(ai_message)
    
    db.commit()
    db.refresh(user_message)
    db.refresh(ai_message)
    
    # 将消息对象转换为schema
    user_message_schema = ChatMessageSchema.model_validate(user_message)
    ai_message_schema = ChatMessageSchema.model_validate(ai_message)
    
    # 添加联网搜索和来源信息（如果启用了联网搜索）
    if web_search:
        sources = await web_search(content)
        ai_message_schema.web_search = True
        ai_message_schema.sources = sources
    
    # 返回用户消息和AI回复
    return [user_message_schema, ai_message_schema]

# 修改会话标题
@router.put("/sessions/{session_id}", response_model=ChatSessionBrief)
async def update_session_title(
    session_id: int,
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
        ChatSession.is_active == True
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天会话不存在"
        )
    
    session.title = session_data.title
    db.commit()
    db.refresh(session)
    
    return session 