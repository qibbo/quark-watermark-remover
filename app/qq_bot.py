import os
import asyncio
import tempfile
import time
import requests
import qqbot
from qqbot import *
from qqbot.model.message import Message
from app.pdf_processor import process_pdf

# 配置
QQ_APPID = os.getenv("QQ_APPID", "")
QQ_SECRET = os.getenv("QQ_SECRET", "")

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

async def process_and_send(openid: str, file_url: str, file_name: str, msg_id: str):
    """处理 PDF 并发送"""
    try:
        # 先回复收到
        await send_text_message(openid, f"收到 {file_name}，正在处理...", msg_id)

        # 下载文件
        input_path = await download_file(file_url)

        # 处理 PDF
        output_path = input_path.replace(".pdf", "_processed.pdf")
        result = await process_pdf(input_path, output_path)

        if result["success"]:
            # 上传文件
            file_info = await upload_file(output_path)

            # 发送文件
            await send_file_message(openid, file_info, msg_id)

            print(f"处理成功: {file_name}, 耗时: {result['cost']}s")
        else:
            await send_text_message(openid, f"处理失败: {result['error']}", msg_id)
            print(f"处理失败: {file_name}, 错误: {result['error']}")

        # 清理临时文件
        cleanup_temp_files(input_path, output_path)

    except Exception as e:
        print(f"处理异常: {file_name}, 错误: {str(e)}")
        try:
            await send_text_message(openid, f"处理异常: {str(e)}", msg_id)
        except:
            pass

def cleanup_temp_files(*file_paths):
    """清理临时文件"""
    for file_path in file_paths:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"清理文件失败 {file_path}: {e}")

def start_qq_bot():
    """启动 QQ 机器人"""
    # 事件订阅
    intents = Intents(
        public_guild_messages=True,
        public_messages=True
    )

    # 创建机器人实例
    bot = Bot(intents=intents)

    @bot.event_handler
    async def on_ready():
        print("QQ 机器人已启动")

    @bot.event_handler
    async def on_message(message: Message):
        # 检查是否有附件
        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type and "pdf" in attachment.content_type.lower():
                    # 异步处理 PDF
                    asyncio.create_task(
                        process_and_send(
                            message.author.id,
                            attachment.url,
                            attachment.filename,
                            message.id
                        )
                    )
                else:
                    await send_text_message(
                        message.author.id,
                        "请发送 PDF 文件",
                        message.id
                    )
        # 检查是否为富媒体消息
        elif message.media:
            if message.media.file_info:
                # 处理富媒体消息
                asyncio.create_task(
                    process_and_send(
                        message.author.id,
                        message.media.url,
                        "file.pdf",
                        message.id
                    )
                )

    # 启动机器人
    bot.run(QQ_APPID, QQ_SECRET)
