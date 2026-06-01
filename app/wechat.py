from fastapi import APIRouter, Request, Query

router = APIRouter()

@router.get("/callback")
async def wechat_verify(
    msg_signature: str = Query(...),
    timestamp: str = Query(...),
    nonce: str = Query(...),
    echostr: str = Query(...)
):
    """企业微信 URL 验证"""
    # 简化验证，实际需要使用 Token 和 EncodingAESKey
    return echostr

@router.post("/callback")
async def wechat_callback(request: Request):
    return "success"
