import os
import asyncio
import base64
import tempfile
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
    try:
        # 下载文件
        input_path = await download_file(file_url)

        # 处理 PDF
        output_path = input_path.replace(".pdf", "_processed.pdf")
        result = await process_pdf(input_path, output_path)

        if result["success"]:
            # 大文件压缩（QQ API payload 限制约 12MB）
            send_path = output_path
            file_size = os.path.getsize(output_path)
            _log.info(f"处理后文件大小: {file_size} bytes")

            if file_size > 10 * 1024 * 1024:
                _log.info("文件超过 10MB，尝试压缩...")
                compressed_path = output_path.replace(".pdf", "_compressed.pdf")
                try:
                    from pypdf import PdfReader, PdfWriter
                    reader = PdfReader(output_path)
                    writer = PdfWriter()
                    for page in reader.pages:
                        page.compress_content_streams()
                        writer.add_page(page)
                    with open(compressed_path, "wb") as f:
                        writer.write(f)
                    compressed_size = os.path.getsize(compressed_path)
                    _log.info(f"压缩后文件大小: {compressed_size} bytes")
                    if compressed_size < file_size:
                        send_path = compressed_path
                    else:
                        _log.info("压缩效果不明显，使用原文件")
                        os.remove(compressed_path)
                except Exception as e:
                    _log.info(f"压缩失败: {e}")

            # 上传文件并直接发送
            http = message._api._http
            token = http._token
            await token.check_token()

            upload_url = f"https://api.sgroup.qq.com/v2/users/{message.author.user_openid}/files"
            headers = {
                "Authorization": token.get_string(),
                "Content-Type": "application/json",
            }

            with open(send_path, "rb") as f:
                file_data = base64.b64encode(f.read()).decode("utf-8")

            payload = {
                "file_type": 4,
                "file_data": file_data,
                "url": "https://placeholder.example.com/file.pdf",
                "srv_send_msg": True,
            }

            _log.info(f"开始上传文件, payload 大小: {len(file_data)} bytes")
            response = requests.post(upload_url, headers=headers, json=payload, timeout=60)
            if response.status_code != 200:
                raise Exception(f"文件发送失败: {response.text}")

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
        # 清理可能的压缩文件
        if output_path:
            compressed = output_path.replace(".pdf", "_compressed.pdf")
            cleanup_temp_files(compressed)


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
