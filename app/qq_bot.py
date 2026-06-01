import os
import asyncio
import tempfile
from qqbot import *
from qqbot.core.util.yaml_util import YamlUtil
from qqbot.model.message import MessageEmbed, MessageEmbedField, MessageEmbedThumbnail
from app.pdf_processor import process_pdf

# 配置
qq_config = {
    "appid": os.getenv("QQ_APPID", ""),
    "secret": os.getenv("QQ_SECRET", ""),
    "token": os.getenv("QQ_TOKEN", ""),
    "sandbox": False
}

async def download_file(url: str) -> str:
    """下载文件"""
    import requests
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
    # QQ 机器人 API 上传文件
    import requests
    url = "https://api.sgroup.qq.com/v2/users/me/files"
    headers = {
        "Authorization": f"Bot {qq_config['appid']}.{qq_config['token']}"
    }
    with open(file_path, "rb") as f:
        files = {"file": f}
        response = requests.post(url, headers=headers, files=files)

    if response.status_code != 200:
        raise Exception("文件上传失败")

    result = response.json()
    return result.get("file_info", "")

async def send_file_message(channel_id: str, file_info: str):
    """发送文件消息"""
    import requests
    url = f"https://api.sgroup.qq.com/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {qq_config['appid']}.{qq_config['token']}",
        "Content-Type": "application/json"
    }
    data = {
        "msg_type": 7,
        "media": {
            "file_info": file_info
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        raise Exception("消息发送失败")

async def process_and_send(channel_id: str, file_url: str, file_name: str):
    """处理 PDF 并发送"""
    try:
        # 下载文件
        input_path = await download_file(file_url)

        # 处理 PDF
        output_path = input_path.replace(".pdf", "_processed.pdf")
        result = await process_pdf(input_path, output_path)

        if result["success"]:
            # 上传文件
            file_info = await upload_file(output_path)

            # 发送文件
            await send_file_message(channel_id, file_info)

            print(f"处理成功: {file_name}, 耗时: {result['cost']}s")
        else:
            print(f"处理失败: {file_name}, 错误: {result['error']}")

        # 清理临时文件
        cleanup_temp_files(input_path, output_path)

    except Exception as e:
        print(f"处理异常: {file_name}, 错误: {str(e)}")

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
    # 创建机器人实例
    bot = Bot(qq_config)

    @bot.event_handler
    async def on_ready():
        print("QQ 机器人已启动")

    @bot.event_handler
    async def on_message(message):
        # 检查是否为文件消息
        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type == "application/pdf":
                    # 异步处理 PDF
                    asyncio.create_task(
                        process_and_send(
                            message.channel_id,
                            attachment.url,
                            attachment.filename
                        )
                    )
                    await message.reply("收到 PDF，正在处理...")
                else:
                    await message.reply("请发送 PDF 文件")

    # 启动机器人
    bot.run(qq_config["appid"], qq_config["token"])
