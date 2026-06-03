# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

QuarkPDF 去水印助手 - QQ 机器人，自动去除夸克扫描王 PDF 中的水印。用户通过 QQ 单聊发送 PDF 文件，机器人处理后自动回复。

## 技术栈

- Python 3.11, FastAPI + Uvicorn, pypdf, qq-botpy 1.2.1
- 部署平台：Railway

## 构建和运行

```bash
pip install -r requirements.txt

export QQ_APPID=你的AppID
export QQ_SECRET=你的AppSecret
uvicorn app.main:app --reload

python -m pytest tests/
```

## 环境变量

| 变量 | 说明 |
|------|------|
| `QQ_APPID` | QQ 开放平台 AppID |
| `QQ_SECRET` | QQ 开放平台 AppSecret |
| `SERVER_URL` | 服务公网地址（Railway 自动设置 `RAILWAY_PUBLIC_DOMAIN`） |

## 项目结构

```
├── watermark_remover.py   # 核心去水印逻辑（pypdf）
├── app/
│   ├── main.py            # FastAPI 入口，临时文件下载接口
│   ├── qq_bot.py          # QQ 机器人（消息处理、文件上传）
│   └── pdf_processor.py   # PDF 处理异步封装
├── temp_files/            # 临时文件目录（自动清理）
├── tests/                 # 单元测试
├── Procfile               # Railway 部署配置
└── railway.json           # Railway 构建配置
```

## 文件上传机制

**当前方案：base64 编码上传**（URL 方案失败，QQ 服务器返回 "download file error"）

流程：用户发送 PDF → 下载处理 → base64 编码 → QQ 富媒体 API → 发送 file_info → 回复用户

**已知限制**：
- base64 使体积增加约 33%
- 实际可处理文件约 15-20MB（受 base64 和 QQ API 限制）

**URL 方案（已尝试但失败）**：
- 官方文档说 `url` 必填、`file_data` 可选，但 QQ 服务器无法访问 Railway URL
- 可能需要在 QQ 开放平台配置域名白名单

## 部署到 Railway

1. Fork 本仓库
2. 在 [Railway](https://railway.app) 创建项目，连接 GitHub 仓库
3. 添加环境变量 `QQ_APPID` 和 `QQ_SECRET`
4. 自动生成公网域名，部署完成

## QQ 机器人注册

1. 访问 [QQ 开放平台](https://q.qq.com)
2. 创建机器人应用，获取 AppID 和 AppSecret
3. 消息接收方式选择 **WebSocket**
4. 订阅事件：`C2C_MESSAGE_CREATE`（单聊消息）

## 开发历史

项目最初计划使用企业微信机器人，但因个人项目无法完成企业微信的备案要求，被迫放弃，转而采用 QQ 机器人方案。

QQ 机器人方案经历了多轮调试：
- 文件上传方式：base64 编码 → URL 方式（失败，回退到 base64）
- 临时文件清理：延迟清理等待 QQ 服务器下载完成
- 大文件处理：曾添加压缩逻辑，后因无效移除
- 2026-06-03：尝试 URL 上传方案，但 QQ 服务器无法访问 Railway URL，返回 "download file error"

## 关联分支

- `feature/android-apk` - Android 应用版本（使用 iText 7）
- `master` - 主分支
