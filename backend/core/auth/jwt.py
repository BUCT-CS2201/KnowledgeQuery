from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from config.config_info import settings

# 配置参数
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/api/account/token")

class TokenData(BaseModel):
    user_id: int = None
    phone_number: str = None
    role_type: int = None

def create_access_token(data: dict, expires_delta: timedelta = None):
    """创建JWT访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """验证JWT令牌并返回当前用户信息"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的身份凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        phone_number: str = payload.get("phone_number")
        role_type: int = payload.get("role_type")
        if user_id is None or phone_number is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id, phone_number=phone_number, role_type=role_type)
    except JWTError:
        raise credentials_exception
    return token_data
