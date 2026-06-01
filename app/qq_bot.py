import os
import asyncio
import base64
import tempfile
import time
import uuid
import requests
import botpy
from botpy import logging
from botpy.message import C2CMessage
from app.pdf_processor import process_pdf

# 配置
QQ_APPID = os.getenv("QQ_APPID", "")
QQ_SECRET = os.getenv("QQ_SECRET", "")

_log = logging.get_logger()

# 临时文件存储，用于 URL 方式上传
_temp_files = {}


def register_temp_file(file_path: str) -> str:
    """注册临时文件，返回文件 ID"""
    file_id = str(uuid.uuid4())
    _temp_files[file_id] = file_path
    return file_id


def get_temp_file(file_id: str) -> str | None:
    """获取临时文件路径"""
    return _temp_files.get(file_id)


def remove_temp_file(file_id: str):
    """删除临时文件记录"""
    _temp_files.pop(file_id, None)


async def download_file(url: str) -> str:
    """下载文件"""
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("文件下载失败")

    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"qq_{uuid.uuid4().hex[:8]}.pdf")
    with open(temp_path, "wb") as f:
        f.write(response.content)
    return temp_path


async def process_and_send(message: C2CMessage, file_url: str, file_name: str):
    """处理 PDF 并发送"""
    temp_file_id = None
    try:
        # 下载文件
        input_path = await download_file(file_url)

        # 处理 PDF
        output_path = input_path.replace(".pdf", "_processed.pdf")
        result = await process_pdf(input_path, output_path)

        if result["success"]:
            # 注册临时文件，通过 HTTP 端点提供下载
            temp_file_id = register_temp_file(output_path)
            server_url = os.getenv("SERVER_URL", "")
            if not server_url:
                domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")
                if domain:
                    server_url = f"https://{domain}"
                else:
                    raise Exception("未配置 SERVER_URL，请在 Railway 环境变量中设置")
            if not server_url.startswith("http"):
                server_url = f"https://{server_url}"

            download_url = f"{server_url}/temp/{temp_file_id}"
            _log.info(f"文件下载 URL: {download_url}")

            # 上传文件并直接发送（srv_send_msg=True）
            http = message._api._http
            token = http._token
            await token.check_token()

            upload_url = f"https://api.sgroup.qq.com/v2/users/{message.author.user_openid}/files"
            headers = {
                "Authorization": token.get_string(),
                "Content-Type": "application/json",
            }

            payload = {
                "file_type": 4,
                "url": download_url,
                "srv_send_msg": True,
            }
            response = requests.post(upload_url, headers=headers, json=payload)
            if response.status_code != 200:
                raise Exception(f"文件发送失败: {response.text}")

            _log.info(f"处理成功: {file_name}, 耗时: {result['cost']}s")

            # 延迟清理临时文件，等 QQ 服务器下载完成
            async def delayed_cleanup():
                await asyncio.sleep(300)
                remove_temp_file(temp_file_id)
                cleanup_temp_files(input_path, output_path)
            asyncio.create_task(delayed_cleanup())
            return
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
        # 失败时立即清理临时文件
        if temp_file_id:
            remove_temp_file(temp_file_id)


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
