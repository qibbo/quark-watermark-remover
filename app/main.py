from fastapi import FastAPI
from app.wechat import router as wechat_router

app = FastAPI(title="企业微信 PDF 助手")
app.include_router(wechat_router, prefix="/wechat")

@app.get("/")
async def root():
    return {"status": "ok"}
