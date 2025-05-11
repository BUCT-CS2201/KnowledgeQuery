from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.databases import get_db, User
from services.account import register_user, login_user, hash_password
from pydantic import BaseModel
from core.auth.jwt import get_current_user, TokenData
from fastapi.security import OAuth2PasswordRequestForm

# 定义请求模型
class UserRegisterRequest(BaseModel):
    phone_number: str
    password: str
    id_number: str
    name: str

class UserLoginRequest(BaseModel):
    phone_number: str
    password: str

# 新增请求模型
class CheckUserRequest(BaseModel):
    phone_number: str
    id_number: str

# 新增请求模型
class ResetPasswordRequest(BaseModel):
    phone_number: str
    new_password: str

router = APIRouter()

@router.post("/register", summary="用户注册")
async def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    try:
        user = register_user(db, request.phone_number, request.password, request.id_number, request.name)
        return {
            "code": 200,
            "message": "注册成功",
            "data": user
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
            "message": f"注册失败: {str(e)}",
            "data": None
        }

# 修改登录接口，支持表单登录和JWT
@router.post("/login", summary="用户登录")
async def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    try:
        user = login_user(db, request.phone_number, request.password)
        return {
            "code": 200,
            "message": "登录成功",
            "data": user
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
            "message": f"登录失败: {str(e)}",
            "data": None
        }

# 添加OAuth2兼容的登录端点（可选，用于swagger文档）
@router.post("/token", summary="OAuth2兼容登录")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        user = login_user(db, form_data.username, form_data.password)
        return {
            "access_token": user["access_token"],
            "token_type": "bearer"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )

# 测试受保护的接口
@router.get("/me", summary="获取当前用户信息")
async def read_users_me(current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db)):
    return {
        "code": 200,
        "message": "获取成功",
        "data": {
            "user_id": current_user.user_id,
            "phone_number": current_user.phone_number,
            "role_type": current_user.role_type
        }
    }

# 新增接口
@router.post("/check_user", summary="检查用户是否存在")
async def check_user(request: CheckUserRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.phone_number == request.phone_number, User.id_number == request.id_number).first()
        return {
            "code": 200,
            "message": "查询成功",
            "data": {"exist": user is not None}
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"查询失败: {str(e)}",
            "data": None
        }

# 新增接口
@router.post("/reset_password", summary="重置密码")
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.phone_number == request.phone_number).first()
        if not user:
            return {
                "code": 404,
                "message": "用户不存在",
                "data": None
            }
        user.password = hash_password(request.new_password)
        db.commit()
        return {
            "code": 200,
            "message": "密码重置成功",
            "data": None
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"密码重置失败: {str(e)}",
            "data": None
        }

# @router.get("/")
# async def read_root():
#     return {"message": "欢迎使用账户API!"}