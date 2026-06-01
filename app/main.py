from fastapi import FastAPI
from app.wechat import router as wechat_router
from app.qq_bot import start_qq_bot
import asyncio
import os

app = FastAPI(title="PDF 助手")
app.include_router(wechat_router, prefix="/wechat")

@app.get("/")
async def root():
    return {"status": "ok"}

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
    asyncio.create_task(asyncio.to_thread(start_qq_bot))
