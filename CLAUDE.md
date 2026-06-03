# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

QuarkPDF 去水印助手 - QQ 机器人，自动去除夸克扫描王 PDF 中的水印。用户通过 QQ 单聊发送 PDF 文件，机器人处理后自动回复。

## 项目状态

**当前状态：可用，已解决大文件上传问题**

- 核心去水印逻辑正常工作
- QQ 机器人消息收发正常
- 文件上传采用 URL 方式，避免 base64 膨胀

## 技术栈

- **语言**: Python 3.11
- **Web 框架**: FastAPI + Uvicorn
- **PDF 处理**: pypdf 3.17.1
- **QQ 机器人**: qq-botpy 1.2.1（QQ 开放平台 SDK）
- **部署平台**: Railway

## 项目结构

```
├── watermark_remover.py   # 核心去水印逻辑（pypdf）
├── app/
│   ├── main.py            # FastAPI 入口，临时文件下载接口，启动 QQ 机器人
│   ├── qq_bot.py          # QQ 机器人实现（消息处理、文件上传）
│   └── pdf_processor.py   # PDF 处理异步封装
├── temp_files/            # 临时文件目录（自动创建，自动清理）
├── tests/                 # 单元测试
├── requirements.txt       # Python 依赖
├── Procfile               # Railway 部署配置
└── railway.json           # Railway 构建配置
```

## 文件上传机制

采用 **URL 方式**上传文件，避免 base64 编码的 33% 体积膨胀：

```
1. 用户发送 PDF → 机器人下载并处理
2. 处理后的 PDF 复制到 temp_files/ 目录
3. 生成临时下载链接：https://{domain}/temp/{uuid}.pdf
4. 调用 QQ 富媒体 API（url 参数），QQ 服务器主动拉取文件
5. 获取 file_info 后发送消息
```

**关键点**：
- `url` 参数是 QQ API 的必填项，`file_data` 是可选的
- QQ 服务器会主动拉取 URL，所以 Railway 必须有公网可访问的域名
- 临时文件 10 分钟后自动清理

## 环境变量

| 变量 | 说明 |
|------|------|
| `QQ_APPID` | QQ 开放平台 AppID |
| `QQ_SECRET` | QQ 开放平台 AppSecret |
| `SERVER_URL` | 服务公网地址（如 `https://xxx.up.railway.app`），Railway 会自动设置 `RAILWAY_PUBLIC_DOMAIN` |

## 构建和运行

```bash
# 安装依赖
pip install -r requirements.txt

# 本地运行
export QQ_APPID=你的AppID
export QQ_SECRET=你的AppSecret
uvicorn app.main:app --reload

# 运行测试
python -m pytest tests/
```

## 部署到 Railway

1. Fork 本仓库
2. 在 [Railway](https://railway.app) 创建项目，连接 GitHub 仓库
3. 添加环境变量 `QQ_APPID` 和 `QQ_SECRET`
4. 自动生成公网域名，部署完成

## 开发历史

项目最初计划使用企业微信机器人，但因个人项目无法完成企业微信的备案要求，被迫放弃，转而采用 QQ 机器人方案。

QQ 机器人方案经历了多轮调试：
- 文件上传方式：base64 编码 → URL 方式（解决大文件问题）
- 临时文件清理：延迟清理等待 QQ 服务器下载完成
- 大文件处理：曾添加压缩逻辑，后因无效移除
- 2026-06-03：实现 URL 上传方案，QQ 服务器主动拉取文件

## 关联分支

- `feature/android-apk` - Android 应用版本（使用 iText 7）
- `master` - 主分支
