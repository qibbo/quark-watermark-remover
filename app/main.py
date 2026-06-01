from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from app.wechat import router as wechat_router
from app.qq_bot import start_qq_bot, get_temp_file, remove_temp_file
import asyncio
import os

app = FastAPI(title="PDF 助手")
app.include_router(wechat_router, prefix="/wechat")

@app.get("/")
async def root():
    return {"status": "ok"}


@app.get("/temp/{file_id}")
async def serve_temp_file(file_id: str):
    """提供临时文件下载（用于 QQ 文件上传）"""
    file_path = get_temp_file(file_id)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在或已过期")
    return FileResponse(file_path, media_type="application/pdf", filename="processed.pdf")

@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    print("=== 启动服务 ===")
    appid = os.getenv('QQ_APPID', '')
    secret = os.getenv('QQ_SECRET', '')
    print(f"QQ_APPID: '{appid}' (长度: {len(appid)})")
    print(f"QQ_SECRET: '{secret[:10]}...' (长度: {len(secret)})" if secret else "QQ_SECRET: 未设置")

    if not appid or not secret:
        print("警告：QQ_APPID 或 QQ_SECRET 未设置，请在 Railway 环境变量中配置")
        return

    print("正在启动 QQ 机器人...")
    # 启动 QQ 机器人（在线程中运行）
    asyncio.create_task(asyncio.to_thread(start_qq_bot))
