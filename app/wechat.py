from fastapi import APIRouter, Request, Query
import xml.etree.ElementTree as ET

router = APIRouter()

def parse_file_message(xml_data: str) -> dict:
    """解析企业微信文件消息"""
    root = ET.fromstring(xml_data)
    return {
        "to_user": root.find("ToUserName").text,
        "from_user": root.find("FromUserName").text,
        "create_time": root.find("CreateTime").text,
        "msg_type": root.find("MsgType").text,
        "media_id": root.find("MediaId").text,
        "file_name": root.find("FileName").text,
        "file_size": root.find("FileSize").text
    }

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
