from sqlalchemy.orm import Session
from core.databases import ChatSession, ChatMessage
from fastapi import HTTPException, status
from core.llm import ai_llm
from typing import List, Optional
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

# 创建聊天会话
def create_chat_session(db: Session, user_id: int, title: str = "新对话", session_type: int = 1):
    try:
        new_session = ChatSession(
            user_id=user_id,
            title=title,
            type=session_type
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return new_session
    except Exception as e:
        logger.error(f"创建聊天会话失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建聊天会话失败: {str(e)}"
        )

# 获取用户的所有聊天会话
def get_user_chat_sessions(db: Session, user_id: int):
    try:
        return db.query(ChatSession).filter(
            ChatSession.user_id == user_id
        ).order_by(ChatSession.updated_at.desc()).all()
    except Exception as e:
        logger.error(f"获取用户聊天会话失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取聊天会话失败: {str(e)}"
        )

# 获取单个聊天会话及其消息
def get_chat_session(db: Session, session_id: int, user_id: int):
    try:
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="聊天会话不存在"
            )
        
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at).all()
        
        return {
            "session": session,
            "messages": messages
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"获取聊天会话详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取聊天会话详情失败: {str(e)}"
        )

# 删除聊天会话
def delete_chat_session(db: Session, session_id: int, user_id: int):
    try:
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="聊天会话不存在"
            )
        
        db.delete(session)
        db.commit()
        return {"message": "删除成功"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"删除聊天会话失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除聊天会话失败: {str(e)}"
        )

# 更新聊天会话标题
def update_chat_session(db: Session, session_id: int, user_id: int, title: str):
    try:
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="聊天会话不存在"
            )
        
        session.title = title
        db.commit()
        db.refresh(session)
        return session
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"更新聊天会话失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新聊天会话失败: {str(e)}"
        )

# 发送聊天消息并获取AI回复
async def send_message(db: Session, session_id: int, user_id: int, content: str):
    try:
        # 检查会话是否存在且属于当前用户
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="聊天会话不存在"
            )
        
        # 保存用户消息
        user_message = ChatMessage(
            session_id=session_id,
            content=content,
            is_user=True
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)
        
        # 获取历史消息，构建上下文
        history_messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at).all()
        
        # 将历史消息转换为DeepSeek API所需的格式
        messages_for_api = []
        for msg in history_messages:
            role = "user" if msg.is_user else "assistant"
            messages_for_api.append({"role": role, "content": msg.content})
        
        # 如果历史消息为空，添加当前消息
        if not messages_for_api:
            messages_for_api.append({"role": "user", "content": content})
            
        # 获取AI回复
        ai_response = await ai_llm.get_response(messages_for_api)
        
        # 保存AI回复
        ai_message = ChatMessage(
            session_id=session_id,
            content=ai_response,
            is_user=False
        )
        db.add(ai_message)
        
        # 更新会话标题（如果是第一条消息且标题是默认的）
        if session.title == "新对话" and len(messages_for_api) <= 2:
            # 使用用户的第一条消息的前20个字符作为标题
            new_title = content[:20] + ("..." if len(content) > 20 else "")
            session.title = new_title
        
        # 更新会话
        db.commit()
        db.refresh(ai_message)
        
        return {
            "user_message": user_message,
            "ai_message": ai_message
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"发送消息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送消息失败: {str(e)}"
        )

# 发送聊天消息并获取AI流式回复
async def send_streaming_message(db: Session, session_id: int, user_id: int, content: str):
    try:
        # 检查会话是否存在且属于当前用户
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="聊天会话不存在"
            )
        
        # 保存用户消息
        user_message = ChatMessage(
            session_id=session_id,
            content=content,
            is_user=True
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)
        
        # 获取历史消息，构建上下文
        history_messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at).all()
        
        # 将历史消息转换为API所需的格式
        messages_for_api = []
        for msg in history_messages:
            if msg.id != user_message.id:  # 排除刚刚添加的用户消息
                role = "user" if msg.is_user else "assistant"
                messages_for_api.append({"role": role, "content": msg.content})
        
        # 添加当前用户消息
        messages_for_api.append({"role": "user", "content": content})
        
        # 创建AI消息记录，先保存空内容
        ai_message = ChatMessage(
            session_id=session_id,
            content="",
            is_user=False
        )
        db.add(ai_message)
        db.commit()
        db.refresh(ai_message)
        
        # 收集完整的AI回复
        full_response = ""
        
        # 使用任务接管响应生成过程
        response_task = None
        
        # 根据会话类型选择不同的处理方式
        try:
            if session.type == 1:  # 普通问答
                # 创建一个生成器对象，但不立即开始迭代
                response_gen = ai_llm.get_streaming_response(messages_for_api)
            elif session.type == 2:  # 知识库问答
                # 创建知识库问答的生成器
                response_gen = ai_llm.get_kb_streaming_response(messages_for_api)
            elif session.type == 3:  # 知识图谱问答
                # 创建知识图谱问答的生成器
                response_gen = ai_llm.get_kg_streaming_response(messages_for_api)
            else:
                # 默认使用普通问答
                response_gen = ai_llm.get_streaming_response(messages_for_api)
                
            # 迭代生成器，处理每个响应块
            async for chunk in response_gen:
                full_response += chunk
                yield chunk
                
                # 定期更新AI消息内容，但不用每次都提交
                if len(full_response) % 100 == 0:  # 每100个字符更新一次
                    ai_message.content = full_response
                    try:
                        db.commit()
                    except Exception as e:
                        logger.warning(f"更新中间AI消息内容失败: {str(e)}")
                
                # 让出控制权，允许其他请求处理
                await asyncio.sleep(0.01)
                
        except Exception as e:
            logger.error(f"获取AI流式回复失败: {str(e)}")
            error_msg = "抱歉，获取回答时出现错误，请稍后再试。"
            full_response = error_msg
            yield error_msg
        
        # 更新AI消息内容
        try:
            ai_message.content = full_response
            
            # 更新会话标题（如果是第一条消息且标题是默认的）
            if session.title == "新对话" or session.title == "新知识库问答" or session.title == "新知识图谱问答":
                if len(messages_for_api) <= 2:
                    # 使用用户的第一条消息的前20个字符作为标题
                    new_title = content[:20] + ("..." if len(content) > 20 else "")
                    session.title = new_title
            
            # 更新会话
            db.commit()
        except Exception as e:
            logger.error(f"更新AI消息内容失败: {str(e)}")
            # 尝试再次提交，防止数据库会话状态异常
            try:
                db.rollback()
                ai_message.content = full_response
                db.commit()
            except Exception as inner_e:
                logger.error(f"重试更新AI消息内容失败: {str(inner_e)}")
        
    except Exception as e:
        logger.error(f"流式消息处理失败: {str(e)}")
        yield json.dumps({"error": f"处理消息失败: {str(e)}"})
