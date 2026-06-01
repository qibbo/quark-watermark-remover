import os
import asyncio
import tempfile
import time
import requests
import botpy
from botpy import logging
from botpy.message import C2CMessage
from app.pdf_processor import process_pdf

# 配置
QQ_APPID = os.getenv("QQ_APPID", "")
QQ_SECRET = os.getenv("QQ_SECRET", "")

_log = logging.get_logger()

# access_token 缓存
_token_cache = {
    "token": None,
    "expires_at": 0
}

def get_access_token() -> str:
    """获取 QQ 机器人 access_token"""
    if _token_cache["token"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["token"]

    url = "https://bots.qq.com/app/getAppAccessToken"
    data = {
        "appId": QQ_APPID,
        "clientSecret": QQ_SECRET
    }
    response = requests.post(url, json=data)
    result = response.json()

    if "access_token" not in result:
        raise Exception(f"获取 access_token 失败: {result}")

    _token_cache["token"] = result["access_token"]
    _token_cache["expires_at"] = time.time() + int(result["expires_in"]) - 200

    return result["access_token"]

async def download_file(url: str) -> str:
    """下载文件"""
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("文件下载失败")

    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, "qq_file.pdf")
    with open(temp_path, "wb") as f:
        f.write(response.content)
    return temp_path

async def upload_file(file_path: str) -> str:
    """上传文件到 QQ"""
    token = get_access_token()
    url = "https://api.sgroup.qq.com/v2/users/me/files"
    headers = {
        "Authorization": f"Bot {QQ_APPID}.{token}"
    }
    with open(file_path, "rb") as f:
        files = {"file": f}
        response = requests.post(url, headers=headers, files=files)

    if response.status_code != 200:
        raise Exception(f"文件上传失败: {response.text}")

    result = response.json()
    return result.get("file_info", "")

async def send_file_message(openid: str, file_info: str, msg_id: str):
    """发送文件消息（单聊）"""
    token = get_access_token()
    url = f"https://api.sgroup.qq.com/v2/users/{openid}/messages"
    headers = {
        "Authorization": f"Bot {QQ_APPID}.{token}",
        "Content-Type": "application/json"
    }
    data = {
        "msg_type": 7,
        "media": {
            "file_info": file_info
        },
        "msg_id": msg_id
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        raise Exception(f"消息发送失败: {response.text}")

async def send_text_message(openid: str, content: str, msg_id: str):
    """发送文本消息（单聊）"""
    token = get_access_token()
    url = f"https://api.sgroup.qq.com/v2/users/{openid}/messages"
    headers = {
        "Authorization": f"Bot {QQ_APPID}.{token}",
        "Content-Type": "application/json"
    }
    data = {
        "msg_type": 0,
        "content": content,
        "msg_id": msg_id
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        raise Exception(f"消息发送失败: {response.text}")

async def process_and_send(message: C2CMessage, file_url: str, file_name: str):
    """处理 PDF 并发送"""
    try:
        # 先回复收到
        await message._api.post_c2c_message(
            openid=message.author.user_openid,
            msg_type=0,
            content=f"收到 {file_name}，正在处理...",
            msg_id=message.id
        )

        # 下载文件
        input_path = await download_file(file_url)

        # 处理 PDF
        output_path = input_path.replace(".pdf", "_processed.pdf")
        result = await process_pdf(input_path, output_path)

        if result["success"]:
            # 上传文件
            file_info = await upload_file(output_path)

            # 发送文件
            await message._api.post_c2c_file(
                openid=message.author.user_openid,
                file_type=1,
                url=file_info
            )

            _log.info(f"处理成功: {file_name}, 耗时: {result['cost']}s")
        else:
            await message._api.post_c2c_message(
                openid=message.author.user_openid,
                msg_type=0,
                content=f"处理失败: {result['error']}",
                msg_id=message.id
            )
            _log.info(f"处理失败: {file_name}, 错误: {result['error']}")

        # 清理临时文件
        cleanup_temp_files(input_path, output_path)

    except Exception as e:
        _log.info(f"处理异常: {file_name}, 错误: {str(e)}")
        try:
            await message._api.post_c2c_message(
                openid=message.author.user_openid,
                msg_type=0,
                content=f"处理异常: {str(e)}",
                msg_id=message.id
            )
        except:
            pass

def cleanup_temp_files(*file_paths):
    """清理临时文件"""
    for file_path in file_paths:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                _log.info(f"清理文件失败 {file_path}: {e}")

class MyClient(botpy.Client):
    async def on_ready(self):
        _log.info(f"robot 「{self.robot.name}」 on_ready!")

    async def on_c2c_message_create(self, message: C2CMessage):
        """处理单聊消息"""
        _log.info(f"收到消息: {message}")

        # 检查是否有附件
        if hasattr(message, 'attachments') and message.attachments:
            for attachment in message.attachments:
                filename = getattr(attachment, 'filename', '') or ''
                if filename.lower().endswith('.pdf'):
                    # 异步处理 PDF
                    asyncio.create_task(
                        process_and_send(
                            message,
                            attachment.url,
                            filename
                        )
                    )
                else:
                    await message._api.post_c2c_message(
                        openid=message.author.user_openid,
                        msg_type=0,
                        content="请发送 PDF 文件",
                        msg_id=message.id
                    )
        # 检查是否为富媒体消息
        elif hasattr(message, 'media') and message.media:
            if hasattr(message.media, 'file_info') and message.media.file_info:
                # 处理富媒体消息
                asyncio.create_task(
                    process_and_send(
                        message,
                        message.media.url,
                        "file.pdf"
                    )
                )

def start_qq_bot():
    """启动 QQ 机器人"""
    # 在线程中创建新的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # 事件订阅
    intents = botpy.Intents(public_messages=True)

    # 创建机器人实例
    client = MyClient(intents=intents)

    # 启动机器人
    client.run(appid=QQ_APPID, secret=QQ_SECRET)
