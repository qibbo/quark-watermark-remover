# 企业微信 PDF 自动处理助手 - 设计文档

## 概述

将现有的夸克去水印工具（`watermark_remover.py`）封装为企业微信自建应用，用户私聊发送 PDF 文件，应用自动去除水印并返回处理后的文件。

## 架构

```
企业微信用户
    │
    ▼
企业微信服务器
    │
    ▼ (HTTPS 回调)
Railway (FastAPI)
    │
    ├─ /wechat/callback  # 接收消息
    │      │
    │      ▼
    │  解析消息，下载 PDF
    │      │
    │      ▼
    │  watermark_remover.py
    │      │
    │      ▼
    │  上传处理后的 PDF
    │      │
    │      ▼
    └─ 返回文件给用户
```

## 组件职责

| 组件 | 职责 |
|------|------|
| `app/main.py` | FastAPI 入口，启动服务，路由注册 |
| `app/wechat.py` | 企业微信接口：验证 URL、解析消息、下载/上传文件、发送回复 |
| `app/pdf_processor.py` | PDF 处理：调用 watermark_remover，处理异常，返回结果 |
| `watermark_remover.py` | 核心逻辑：已有，不修改 |

## 数据流

1. **接收消息**：企业微信 POST 到 `/wechat/callback`
2. **解析消息**：从 XML 中提取文件 MediaID
3. **下载文件**：用 MediaID 调用企业微信 API 下载 PDF
4. **处理 PDF**：调用 `watermark_remover.remove_watermark()`
5. **上传文件**：将处理后的 PDF 上传到企业微信，获取新 MediaID
6. **发送回复**：用新 MediaID 发送文件给用户

## 错误处理

| 场景 | 处理方式 |
|------|----------|
| 非 PDF 文件 | 返回"请发送 PDF 文件" |
| PDF 无水印 | 返回"PDF 中未找到水印，可能已处理过" |
| PDF 损坏 | 返回"PDF 文件损坏，无法处理" |
| 下载失败 | 返回"文件下载失败，请重试" |
| 上传失败 | 返回"处理完成但上传失败，请重试" |
| 未知错误 | 返回"处理失败，请联系管理员" + 记录日志 |

## 测试策略

| 测试类型 | 内容 |
|----------|------|
| 单元测试 | 测试 watermark_remover.py（已有） |
| 接口测试 | 测试企业微信消息解析、文件下载/上传 |
| 集成测试 | 测试完整流程：接收消息 → 处理 → 回复 |

测试优先级：先写接口测试，确保企业微信对接正确；再写集成测试，确保端到端流程正常。

## 部署

- 平台：Railway（免费额度）
- 触发：连接 GitHub 仓库，自动部署
- 环境变量：CorpID、Secret、Token、EncodingAESKey

## 企业微信配置

需要在企业微信管理后台：
1. 创建自建应用
2. 配置消息接收 URL（Railway 提供的域名）
3. 设置 Token 和 EncodingAESKey
4. 开启消息接收

## 依赖

- FastAPI
- uvicorn
- pypdf
- requests
- cryptography（用于企业微信消息加解密）
