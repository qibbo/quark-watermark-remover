# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

夸克去水印 (Quark Watermark Remover) - Android 应用，用于移除夸克扫描王 PDF 中的水印。纯本地处理，无需联网。

## 构建命令

```bash
# Debug 版本
./gradlew assembleDebug

# Release 版本（需要 keystore 签名）
./gradlew assembleRelease

# 运行测试（纯 JVM，无需模拟器或设备）
./gradlew test

# 清理构建
./gradlew clean
```

## 代理配置

访问中国大陆以外的服务（GitHub、Maven Central 等）必须使用代理：

```bash
https_proxy=http://127.0.0.1:7890 http_proxy=http://127.0.0.1:7890 ./gradlew <task>
```

## 版本管理

**代码有变更时必须更新版本号，仅重新打包则不变：**

1. 修改 `app/build.gradle.kts` 中的 `appVersionName`（如 "1.0.7" → "1.0.8"）
2. 同步修改 `versionCode`（整数，每次 +1）
3. 然后执行 `./gradlew assembleRelease`
4. APK 文件名自动包含版本号：`夸克去水印_v{version}-release.apk`

**规则：**
- 有代码变更 → 必须更新版本号 → 再打包
- 仅重新打包（无代码变更）→ 版本号不变

## 核心架构

```
app/src/main/java/com/quark/watermark/
├── core/
│   └── WatermarkRemover.kt    # 水印移除核心逻辑（iText 7）
├── ui/
│   ├── HomeScreen.kt          # 首页：文件选择、进度、操作按钮
│   ├── ResultScreen.kt        # 结果页：统计、分享、打开目录
│   └── theme/
│       ├── Color.kt           # 颜色定义
│       └── Theme.kt           # Material3 主题
├── util/
│   └── FileUtils.kt           # 文件操作：保存、分享、ZIP 打包
└── MainActivity.kt            # 入口：页面导航、文件处理流程
```

## 水印移除原理

正则匹配 PDF 内容流中的夸克水印命令并移除：

```kotlin
// 水印命令模式：q ... /QuarkX2 Do Q
Pattern.compile("q\\s+[\\d\\s\\.]+cm\\s+/QuarkX2\\s+Do\\s+Q")
```

流程：读取 PDF → 遍历页面 → 检查内容流 → 正则替换 → 保存

## 关键技术栈

- **语言**: Kotlin 1.9.20
- **UI**: Jetpack Compose + Material3 (BOM 2023.10.01)
- **PDF 处理**: iText 7.2.5
- **构建**: Gradle 8.5, AGP 8.2.0
- **最低 SDK**: 26 (Android 8.0)
- **目标 SDK**: 34 (Android 14)

## 错误分类

`WatermarkRemover.classifyError()` 将异常转为友好提示，与桌面版保持一致：

| 关键词 | 提示 |
|--------|------|
| password/encrypted/加密 | 文件已加密 |
| space/disk/空间 | 磁盘空间不足 |
| corrupt/broken/damaged/损坏/cannot open | 文件损坏 |
| no pages/page_count/无内容 | PDF无内容 |
| path/name too long/路径过长 | 路径过长 |
| 其他 | 未知错误: {前50字符} |

## 分享机制

- 单文件：直接分享 PDF
- 多文件：自动打包 ZIP 分享（兼容微信/QQ 等不支持多 PDF 分享的应用）
- 通过 FileProvider 分享缓存的 ZIP 文件

## 签名配置

Release 签名使用项目根目录的 keystore：

- 文件: `quark-watermark.keystore`
- 别名: `quark`
- 密码: 见 `app/build.gradle.kts` 中的 `signingConfigs`

**注意**: keystore 文件已加入 .gitignore，不应提交到版本控制。

## 测试

单元测试位于 `app/src/test/`，可在纯 JVM 上运行（无需 Android 设备）：

```bash
./gradlew test
```

测试用例覆盖：正常PDF、无水印、损坏文件、非PDF、空文件、加密PDF、多页PDF。

## 环境要求

- Android SDK: `C:/Android/Sdk`（配置在 `local.properties`）
- JDK: 1.8
- 代理: FlClash HTTP 代理 127.0.0.1:7890
