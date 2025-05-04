from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

# 创建聊天会话请求
class ChatSessionCreate(BaseModel):
    title: Optional[str] = "新对话"

# 文件信息
class FileInfo(BaseModel):
    name: str
    size: int
    type: Optional[str] = None

# 引用来源
class SourceInfo(BaseModel):
    title: Optional[str] = None
    url: str
    snippet: Optional[str] = None  # 搜索结果摘要

# 创建聊天消息请求
class ChatMessageCreate(BaseModel):
    content: str
    model: Optional[str] = "general"
    web_search: Optional[bool] = False
    files: Optional[List[FileInfo]] = None

# 上传的文件数据
class UploadFile(BaseModel):
    file_data: bytes
    file_info: FileInfo

# 聊天消息响应
class ChatMessage(BaseModel):
    id: int
    content: str
    is_user: bool
    created_at: datetime
    web_search: Optional[bool] = None
    sources: Optional[List[SourceInfo]] = None
    files: Optional[List[FileInfo]] = None
    
    class Config:
        from_attributes = True

# 聊天会话列表响应
class ChatSessionBrief(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# 聊天会话详情响应
class ChatSession(ChatSessionBrief):
    messages: List[ChatMessage]
    
    class Config:
        from_attributes = True 