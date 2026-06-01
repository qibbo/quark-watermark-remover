from fastapi import APIRouter, Request, Query, BackgroundTasks
import xml.etree.ElementTree as ET
import requests
import tempfile
import os
import time
import hashlib
import base64
from datetime import datetime
from Crypto.Cipher import AES
from app.pdf_processor import process_pdf

router = APIRouter()

# 缓存 access_token
_access_token_cache = {
    "token": None,
    "expires_at": 0
}

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

async def get_access_token() -> str:
    """获取企业微信 access_token"""
    # 检查缓存
    if _access_token_cache["token"] and time.time() < _access_token_cache["expires_at"]:
        return _access_token_cache["token"]

    # 获取新 token
    corp_id = os.getenv("CORP_ID")
    secret = os.getenv("SECRET")

    url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
    params = {
        "corpid": corp_id,
        "corpsecret": secret
    }

    response = requests.get(url, params=params)
    result = response.json()

    if "access_token" not in result:
        raise Exception(f"获取 access_token 失败: {result}")

    # 更新缓存
    _access_token_cache["token"] = result["access_token"]
    _access_token_cache["expires_at"] = time.time() + result["expires_in"] - 200

    return result["access_token"]

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

async def upload_file(file_path: str, access_token: str) -> str:
    """上传文件到企业微信"""
    url = "https://qyapi.weixin.qq.com/cgi-bin/media/upload"
    params = {
        "access_token": access_token,
        "type": "file"
    }

    with open(file_path, "rb") as f:
        files = {"media": (os.path.basename(file_path), f)}
        response = requests.post(url, params=params, files=files)

    if response.status_code != 200:
        raise Exception("文件上传失败")

    result = response.json()
    if "media_id" not in result:
        raise Exception(f"上传失败: {result}")

    return result["media_id"]

async def send_file_message(to_user: str, media_id: str, access_token: str) -> bool:
    """发送文件消息给用户"""
    url = "https://qyapi.weixin.qq.com/cgi-bin/message/send"
    params = {
        "access_token": access_token
    }

    data = {
        "touser": to_user,
        "msgtype": "file",
        "agentid": int(os.getenv("AGENT_ID", "0")),
        "file": {
            "media_id": media_id
        }
    }

    response = requests.post(url, params=params, json=data)

    if response.status_code != 200:
        raise Exception("消息发送失败")

    result = response.json()
    if result.get("errcode") != 0:
        raise Exception(f"发送失败: {result}")

    return True

async def send_text_message(to_user: str, content: str, access_token: str = None) -> bool:
    """发送文本消息给用户"""
    if access_token is None:
        access_token = await get_access_token()

    url = "https://qyapi.weixin.qq.com/cgi-bin/message/send"
    params = {
        "access_token": access_token
    }

    data = {
        "touser": to_user,
        "msgtype": "text",
        "agentid": int(os.getenv("AGENT_ID", "0")),
        "text": {
            "content": content
        }
    }

    response = requests.post(url, params=params, json=data)

    if response.status_code != 200:
        raise Exception("消息发送失败")

    result = response.json()
    if result.get("errcode") != 0:
        raise Exception(f"发送失败: {result}")

    return True

def log_process(user: str, file_name: str, cost: float, result: str):
    """记录运行日志"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    log_line = f"{now} | user={user} | file={file_name} | cost={cost}s | {result}"
    print(log_line)

def cleanup_temp_files(*file_paths):
    """清理临时文件"""
    for file_path in file_paths:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"清理文件失败 {file_path}: {e}")

async def async_process_pdf(from_user: str, media_id: str, file_name: str):
    """异步处理 PDF"""
    try:
        # 获取 access_token
        access_token = await get_access_token()

        # 下载文件
        input_path = await download_file(media_id, access_token)

        # 处理 PDF
        output_path = input_path.replace(".pdf", "_processed.pdf")
        result = await process_pdf(input_path, output_path)

        if result["success"]:
            # 上传文件
            new_media_id = await upload_file(output_path, access_token)

            # 发送消息
            await send_file_message(from_user, new_media_id, access_token)

            # 记录日志
            log_process(from_user, file_name, result["cost"], "success")
        else:
            # 发送错误消息
            await send_text_message(from_user, result["error"], access_token)

            # 记录日志
            log_process(from_user, file_name, 0, f"error: {result['error']}")

        # 清理临时文件
        cleanup_temp_files(input_path, output_path)

    except Exception as e:
        # 记录错误日志
        log_process(from_user, file_name, 0, f"error: {str(e)}")

@router.get("/callback")
async def wechat_verify(
    msg_signature: str = Query(...),
    timestamp: str = Query(...),
    nonce: str = Query(...),
    echostr: str = Query(...)
):
    """企业微信 URL 验证"""
    token = os.getenv("WECHAT_TOKEN", "")
    encoding_aes_key = os.getenv("WECHAT_ENCODING_AES_KEY", "")
    corp_id = os.getenv("CORP_ID", "")

    # 签名验证：将 token、timestamp、nonce、echostr 排序后拼接，进行 SHA1 哈希
    params = sorted([token, timestamp, nonce, echostr])
    sign_str = "".join(params)
    sign = hashlib.sha1(sign_str.encode("utf-8")).hexdigest()

    if sign != msg_signature:
        return "签名验证失败"

    # 解密 echostr
    try:
        # 将 EncodingAESKey 转换为 AES 密钥
        aes_key = base64.b64decode(encoding_aes_key + "=")
        iv = aes_key[:16]

        # 解密
        cipher = AES.new(aes_key, AES.MODE_CBC, iv)
        plain_text = cipher.decrypt(base64.b64decode(echostr))

        # 去除填充
        pad_len = plain_text[-1]
        content = plain_text[16:-pad_len]

        # 提取消息和 corp_id
        msg_len = int.from_bytes(content[:4], byteorder="big")
        msg = content[4:4+msg_len].decode("utf-8")
        from_corp_id = content[4+msg_len:].decode("utf-8")

        # 验证 corp_id
        if from_corp_id == corp_id:
            return msg
        else:
            return "CorpID 验证失败"
    except Exception as e:
        return f"解密失败: {str(e)}"

@router.post("/callback")
async def wechat_callback(request: Request, background_tasks: BackgroundTasks):
    """企业微信消息回调"""
    try:
        # 获取请求体
        body = await request.body()
        xml_data = body.decode("utf-8")

        # 解析消息
        message = parse_file_message(xml_data)

        # 检查是否为文件消息
        if message["msg_type"] != "file":
            return "success"

        # 检查文件名是否为 PDF
        if not message["file_name"].lower().endswith(".pdf"):
            await send_text_message(message["from_user"], "请发送 PDF 文件")
            return "success"

        # 异步处理 PDF
        background_tasks.add_task(
            async_process_pdf,
            message["from_user"],
            message["media_id"],
            message["file_name"]
        )

        return "success"

    except Exception as e:
        print(f"回调处理失败: {e}")
        return "success"
