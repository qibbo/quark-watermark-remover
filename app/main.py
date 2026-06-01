from fastapi import FastAPI
from app.wechat import router as wechat_router
from app.qq_bot import start_qq_bot
import asyncio

app = FastAPI(title="PDF 助手")
app.include_router(wechat_router, prefix="/wechat")

@app.get("/")
async def root():
    return {"status": "ok"}

@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    # 启动 QQ 机器人
    asyncio.create_task(asyncio.to_thread(start_qq_bot))
