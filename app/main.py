from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from app.qq_bot import start_qq_bot
import asyncio
import os
import uuid
import threading
import time

app = FastAPI(title="PDF 助手")

# 临时文件目录
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "temp_files")
os.makedirs(TEMP_DIR, exist_ok=True)

# 记录临时文件的创建时间 {filepath: timestamp}
_temp_files: dict[str, float] = {}
_temp_lock = threading.Lock()


def register_temp_file(filepath: str):
    """注册临时文件，用于后续清理"""
    with _temp_lock:
        _temp_files[filepath] = time.time()


def cleanup_expired_files(max_age_seconds: int = 600):
    """清理过期的临时文件（默认 10 分钟）"""
    now = time.time()
    with _temp_lock:
        expired = [f for f, t in _temp_files.items() if now - t > max_age_seconds]
    for f in expired:
        try:
            if os.path.exists(f):
                os.remove(f)
            with _temp_lock:
                _temp_files.pop(f, None)
        except Exception:
            pass


@app.get("/")
async def root():
    return {"status": "ok"}


@app.get("/temp/{filename}")
async def download_temp_file(filename: str):
    """下载临时文件"""
    # 防止路径遍历
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="无效的文件名")

    filepath = os.path.join(TEMP_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在或已过期")

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/pdf"
    )


@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    print("=== 启动服务 ===")
    print(f"临时文件目录: {TEMP_DIR}")

    appid = os.getenv('QQ_APPID', '')
    secret = os.getenv('QQ_SECRET', '')
    print(f"QQ_APPID: '{appid}' (长度: {len(appid)})")
    print(f"QQ_SECRET: '{secret[:10]}...' (长度: {len(secret)})" if secret else "QQ_SECRET: 未设置")

    if not appid or not secret:
        print("警告：QQ_APPID 或 QQ_SECRET 未设置，请在 Railway 环境变量中配置")
        return

    print("正在启动 QQ 机器人...")
    asyncio.create_task(asyncio.to_thread(start_qq_bot))

    # 定期清理过期文件
    async def periodic_cleanup():
        while True:
            await asyncio.sleep(60)  # 每分钟检查一次
            cleanup_expired_files()

    asyncio.create_task(periodic_cleanup())
