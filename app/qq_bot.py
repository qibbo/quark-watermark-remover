import os
import asyncio
import tempfile
import uuid
import shutil
import base64
import requests
import botpy
from botpy import logging
from botpy.message import C2CMessage
from app.pdf_processor import process_pdf

# 配置
QQ_APPID = os.getenv("QQ_APPID", "")
QQ_SECRET = os.getenv("QQ_SECRET", "")

# 临时文件目录（与 main.py 一致）
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "temp_files")

# Railway 域名，用于生成下载 URL
# 可通过环境变量配置，或自动检测
SERVER_URL = os.getenv("SERVER_URL", "").rstrip("/")

_log = logging.get_logger()


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
    input_path = None
    output_path = None
    temp_download_path = None
    try:
        # 下载文件
        input_path = await download_file(file_url)

        # 检查文件大小（限制 100MB）
        input_size = os.path.getsize(input_path)
        if input_size > 100 * 1024 * 1024:
            await message._api.post_c2c_message(
                openid=message.author.user_openid,
                msg_type=0,
                content=f"文件太大（{input_size // 1024 // 1024}MB），QQ 限制 15MB 以内",
                msg_id=message.id
            )
            return

        # 处理 PDF
        output_path = input_path.replace(".pdf", "_processed.pdf")
        result = await process_pdf(input_path, output_path)

        if result["success"]:
            # 复制文件到临时目录，提供下载链接
            temp_filename = f"{uuid.uuid4().hex[:12]}.pdf"
            temp_download_path = os.path.join(TEMP_DIR, temp_filename)
            os.makedirs(TEMP_DIR, exist_ok=True)
            shutil.copy2(output_path, temp_download_path)

            # 注册到临时文件管理
            from app.main import register_temp_file
            register_temp_file(temp_download_path)

            # 生成下载 URL
            server_url = SERVER_URL
            if not server_url:
                # 尝试从环境变量获取
                server_url = os.getenv("SERVER_URL", "")
                if not server_url:
                    server_url = os.getenv("RAILWAY_STATIC_URL", "")
                if not server_url:
                    server_url = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")

            if not server_url:
                raise Exception("SERVER_URL 未配置，无法生成下载链接")

            # 确保有 https:// 前缀
            server_url = server_url.rstrip("/")
            if not server_url.startswith("http"):
                server_url = f"https://{server_url}"

            download_url = f"{server_url}/temp/{temp_filename}"
            _log.info(f"生成下载链接: {download_url}")

            # 获取 access token
            http = message._api._http
            token = http._token
            await token.check_token()

            # 第一步：上传文件信息，获取 file_info
            upload_url = f"https://api.sgroup.qq.com/v2/users/{message.author.user_openid}/files"
            headers = {
                "Authorization": token.get_string(),
                "Content-Type": "application/json",
            }

            # 使用 base64 上传（QQ 服务器无法访问我们的 URL）
            with open(output_path, "rb") as f:
                file_data = base64.b64encode(f.read()).decode("utf-8")

            payload = {
                "file_type": 4,
                "url": download_url,  # 仍然需要提供 url，但 QQ 服务器无法访问
                "file_data": file_data,
                "srv_send_msg": False,
            }

            _log.info(f"上传文件 (base64), 大小: {len(file_data)} bytes")
            response = requests.post(upload_url, headers=headers, json=payload, timeout=120)
            if response.status_code != 200:
                raise Exception(f"文件上传失败: {response.text}")

            upload_result = response.json()
            file_info = upload_result.get("file_info")
            if not file_info:
                raise Exception(f"未获取到 file_info: {upload_result}")

            _log.info(f"获取 file_info 成功")

            # 第二步：发送消息
            send_url = f"https://api.sgroup.qq.com/v2/users/{message.author.user_openid}/messages"
            send_payload = {
                "msg_type": 7,  # media 富媒体
                "media": {"file_info": file_info},
                "msg_id": message.id,
            }

            send_response = requests.post(send_url, headers=headers, json=send_payload, timeout=30)
            if send_response.status_code != 200:
                raise Exception(f"消息发送失败: {send_response.text}")

            _log.info(f"处理成功: {file_name}, 耗时: {result['cost']}s")
        else:
            await message._api.post_c2c_message(
                openid=message.author.user_openid,
                msg_type=0,
                content=f"处理失败: {result['error']}",
                msg_id=message.id
            )
            _log.info(f"处理失败: {file_name}, 错误: {result['error']}")

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
    finally:
        cleanup_temp_files(input_path, output_path)


def cleanup_temp_files(*file_paths):
    """清理临时文件"""
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
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
                    asyncio.create_task(
                        process_and_send(message, attachment.url, filename)
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
                asyncio.create_task(
                    process_and_send(message, message.media.url, "file.pdf")
                )


def start_qq_bot():
    """启动 QQ 机器人"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    intents = botpy.Intents(public_messages=True)
    client = MyClient(intents=intents)
    client.run(appid=QQ_APPID, secret=QQ_SECRET)
