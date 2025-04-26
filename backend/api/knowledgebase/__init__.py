from fastapi import APIRouter, Depends, HTTPException, status


router = APIRouter()

@router.get("/")
async def read_root():
    return {"message": "Welcome to the API!"}