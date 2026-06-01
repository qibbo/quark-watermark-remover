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
    print(f"QQ_APPID: {os.getenv('QQ_APPID', '未设置')}")
    print(f"QQ_SECRET: {os.getenv('QQ_SECRET', '未设置')[:10]}...")
    print("正在启动 QQ 机器人...")
    # 启动 QQ 机器人
    asyncio.create_task(asyncio.to_thread(start_qq_bot))
