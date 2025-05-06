from sqlalchemy.orm import Session
from core.databases import User
import hashlib
from fastapi import HTTPException, status
from datetime import timedelta
from core.auth.jwt import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

# 密码加密函数
def hash_password(password: str) -> str:
    """对密码进行MD5加密"""
    md5 = hashlib.md5()
    md5.update(password.encode('utf-8'))
    return md5.hexdigest()

# 注册服务
def register_user(db: Session, phone_number: str, password: str, id_number: str, name: str):
    # 检查电话号码是否已被注册
    existing_user = db.query(User).filter(User.phone_number == phone_number).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该电话号码已被注册"
        )
    
    # 创建新用户
    hashed_password = hash_password(password)
    new_user = User(
        phone_number=phone_number,
        password=hashed_password,
        id_number=id_number,
        name=name
    )
    
    # 添加到数据库
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # 返回用户信息（不包含密码）
    user_dict = {
        "user_id": new_user.user_id,
        "name": new_user.name,
        "phone_number": new_user.phone_number,
        "role_type": new_user.role_type,
        "status": new_user.account_status
    }
    return user_dict

# 登录服务
def login_user(db: Session, phone_number: str, password: str):
    # 查找用户
    user = db.query(User).filter(User.phone_number == phone_number).first()
    
    # 用户不存在或密码错误
    if not user or user.password != hash_password(password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="电话号码或密码不正确"
        )
    
    # 检查用户状态
    if user.account_status == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用"
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "user_id": user.user_id,
            "phone_number": user.phone_number,
            "role_type": user.role_type
        },
        expires_delta=access_token_expires
    )
    
    # 返回用户信息和访问令牌
    user_dict = {
        "user_id": user.user_id,
        "name": user.name,
        "phone_number": user.phone_number,
        "role_type": user.role_type,
        "access_token": access_token,
        "token_type": "bearer"
    }
    return user_dict
