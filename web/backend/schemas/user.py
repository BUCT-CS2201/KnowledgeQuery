from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# 用户注册请求模式
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)

# 用户登录请求模式
class UserLogin(BaseModel):
    username: str
    password: str

# 用户基本信息模式
class UserBase(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    
    class Config:
        orm_mode = True

# 令牌响应模式
class Token(BaseModel):
    access_token: str
    token_type: str

# 令牌数据模式
class TokenData(BaseModel):
    username: Optional[str] = None 