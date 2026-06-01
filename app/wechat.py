from fastapi import APIRouter, Request, Query
import xml.etree.ElementTree as ET
import requests
import tempfile
import os

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

async def download_file(media_id: str, access_token: str) -> str:
    """下载企业微信文件"""
    url = "https://qyapi.weixin.qq.com/cgi-bin/media/get"
    params = {
        "access_token": access_token,
        "media_id": media_id
    }
    response = requests.get(url, params=params)

    if response.status_code != 200:
        raise Exception("文件下载失败")

    # 使用 tempfile 创建临时文件
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"{media_id}.pdf")
    with open(temp_path, "wb") as f:
        f.write(response.content)

    return temp_path

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
