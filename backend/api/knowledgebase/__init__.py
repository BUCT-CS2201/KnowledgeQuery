from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.databases import get_db
from core.auth.jwt import get_current_user, TokenData

router = APIRouter()

@router.get("/", summary="获取知识库列表")
async def get_knowledge_bases(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 临时返回空列表，后续可以实现具体逻辑
    return {
        "code": 200,
        "message": "获取成功",
        "data": []
    }