# QuarkPDF 去水印助手

QQ 机器人，自动去除夸克扫描王 PDF 中的水印。

## 工作原理

1. 用户通过 QQ 向机器人发送 PDF 文件
2. 机器人使用 pypdf 解析 PDF 内容流，移除水印指令
3. 处理后的 PDF 自动回复给用户

## 项目结构

```
├── watermark_remover.py   # 核心去水印逻辑
├── app/
│   ├── main.py            # FastAPI 入口
│   ├── qq_bot.py          # QQ 机器人实现
│   └── pdf_processor.py   # PDF 处理封装
├── tests/                 # 测试
├── requirements.txt       # 依赖
├── Procfile               # Railway 部署配置
└── railway.json           # Railway 构建配置
```

## 环境变量

在 Railway 或 `.env` 中配置：

| 变量 | 说明 |
|------|------|
| `QQ_APPID` | QQ 开放平台 AppID |
| `QQ_SECRET` | QQ 开放平台 AppSecret |

## 本地运行

```bash
pip install -r requirements.txt
export QQ_APPID=你的AppID
export QQ_SECRET=你的AppSecret
uvicorn app.main:app --reload
```

## 部署到 Railway

1. Fork 本仓库
2. 在 [Railway](https://railway.app) 创建项目，连接 GitHub 仓库
3. 添加环境变量 `QQ_APPID` 和 `QQ_SECRET`
4. 自动生成公网域名，部署完成

## 限制

- 仅支持 PDF 文件
- 文件大小限制约 15MB（QQ API 限制）
- 仅支持 QQ 单聊

## QQ 机器人注册

1. 访问 [QQ 开放平台](https://q.qq.com)
2. 创建机器人应用，获取 AppID 和 AppSecret
3. 消息接收方式选择 **WebSocket**
4. 订阅事件：`C2C_MESSAGE_CREATE`（单聊消息）
