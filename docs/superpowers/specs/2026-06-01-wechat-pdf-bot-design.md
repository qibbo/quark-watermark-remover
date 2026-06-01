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
    │  解析消息，验证白名单
    │      │
    │      ▼
    │  立即返回 success（避免超时）
    │      │
    │      ▼
    │  后台异步处理：
    │    ├─ 下载 PDF
    │    ├─ watermark_remover.py
    │    ├─ 上传结果
    │    ├─ 发送文件给用户
    │    └─ 清理临时文件
    │
    └─ 记录运行日志
```

## 组件职责

| 组件 | 职责 |
|------|------|
| `app/main.py` | FastAPI 入口，启动服务，路由注册 |
| `app/wechat.py` | 企业微信接口：验证 URL、解析消息、下载/上传文件、发送回复 |
| `app/pdf_processor.py` | PDF 处理：调用 watermark_remover，处理异常，返回结果 |
| `watermark_remover.py` | 核心逻辑：已有，不修改 |

## 数据流（异步处理）

1. **接收消息**：企业微信 POST 到 `/wechat/callback`
2. **立即返回**：返回 "success"，避免企业微信回调超时
3. **后台处理**：
   - 解析消息，提取文件 MediaID
   - 下载文件：用 MediaID 调用企业微信 API 下载 PDF
   - 处理 PDF：调用 `watermark_remover.remove_watermark()`
   - 上传文件：将处理后的 PDF 上传到企业微信，获取新 MediaID
   - 发送回复：用新 MediaID 发送文件给用户
   - 清理临时文件：删除 input.pdf 和 output.pdf
4. **记录日志**：记录时间、发送人、文件名、处理耗时、处理结果

## 用户白名单

在企业微信管理后台配置"可见范围"，指定哪些用户或部门可以使用该应用。

- 企业微信自动拒绝不可见用户，不会回调到服务
- 管理后台直接配置，更直观安全
- 代码无需维护白名单逻辑

## 错误处理

统一策略：收到文件 → 执行处理 → 返回结果文件

暂不增加 "PDF 中未找到水印" 等业务判断，降低复杂度和误判概率。

| 场景 | 处理方式 |
|------|----------|
| 非白名单用户 | 返回"该应用暂未开放使用" |
| 非 PDF 文件 | 返回"请发送 PDF 文件" |
| 处理失败 | 返回"处理失败，请重试" |

## 运行日志

记录以下信息用于排查问题：

```
时间 | 发送人 | 文件名 | 处理耗时 | 处理结果
```

示例：

```
2026-06-01 21:33 | user=zhangsan | file=test.pdf | cost=3.2s | success
```

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
- 环境变量：CorpID、Secret、Token、EncodingAESKey、ALLOWED_USERS

**可迁移性**：架构保持平台无关（FastAPI + pypdf + requests），后续如需长期运行，可无缝迁移至 Oracle Free Tier，无需修改业务逻辑。

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
