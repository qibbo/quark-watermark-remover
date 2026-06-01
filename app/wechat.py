from fastapi import APIRouter, Request

router = APIRouter()

@router.post("/callback")
async def wechat_callback(request: Request):
    return "success"
