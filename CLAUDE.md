# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 代理配置

访问中国大陆以外的服务时，必须使用 FlClash HTTP 代理：

```bash
https_proxy=http://127.0.0.1:7890 http_proxy=http://127.0.0.1:7890
```

适用于：GitHub、Railway、npm registry、pip source 等境外服务。不要默认改用 SSH 方式绕过。中国大陆服务（如 Gitee）不走代理。

## 项目概述

夸克去水印 (Quark Watermark Remover) - Android 应用，用于移除夸克扫描王 PDF 中的水印，并把分享进来的截图裁切成 A4 生成复印件 PDF。纯本地处理，无需联网。

**唯一的交付形态是 Android 应用。** 仓库中的 Python 桌面版只是最初的技术验证，已冻结、不再维护，改动不要回灌到桌面版。

## 分支策略

| 分支 | 用途 |
|---|---|
| `feature/android-apk` | **活跃开发分支**，Android 版全部代码在此 |
| `master` | 早期 Python + PyQt 桌面版（技术验证存档），冻结 |
| `legacy/pymupdf` | 更早的桌面版实验（PyMuPDF / pypdf 两套引擎），冻结 |
| `feature/wechat-pdf-bot` | 已中止的微信机器人方案，不再推进 |

注意：`master` 是 Android 分支的祖先，两条线的版本号各自独立。桌面版停在 v1.4.1（`v1.0.0`～`v1.4.1` 这批 tag 全部属于桌面版技术验证），**Android 线自 `2.0.0` 起号**，当前 v2.0.0，不要用 tag 跨线对照。

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

**打包脚本（推荐）：**

```bash
python build.py
```

脚本功能：
- 检查代码是否有变化（git diff）
- 有变化 → 自动更新版本号（1.2.0 → 1.2.1）
- 无变化 → 保持当前版本号
- 执行 `gradlew assembleRelease`
- 显示 APK 文件路径和大小

## 版本管理

**代码有变更时必须更新版本号，仅重新打包则不变：**

1. 修改 `app/build.gradle.kts` 中的 `appVersionName`（如 "1.0.7" → "1.0.8"）
2. 同步修改 `versionCode`（整数，每次 +1）
3. 然后执行 `./gradlew assembleRelease`
4. APK 文件名自动包含版本号：`夸克去水印_v{version}-release.apk`

**规则：**
- 有代码变更 → 必须更新版本号 → 再打包
- 仅重新打包（无代码变更）→ 版本号不变
- Android 线编号从 `2.0.0` 起（`1.x` 属于桌面版历史），发布时打 `v{version}` tag 并把 APK 上传到 Releases

**注意**：`build.py` 的变更检测把**未跟踪文件**也算作代码变更，项目里存在 `草稿纸_勿删.md`、`.workbuddy/` 这类本地文件时，会误判并递增版本号。需要精确控制版本号时直接跑 `./gradlew assembleRelease`。

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
│   ├── FileUtils.kt           # 文件操作：保存、分享、ZIP 打包
│   └── ImageToPdfUtil.kt      # 截图转 PDF：裁切 A4 区域、图片转 PDF
└── MainActivity.kt            # 入口：页面导航、文件处理流程

app/src/main/assets/
└── crop_config.json           # 截图裁切坐标配置（按设备型号）
```

## 截图转 PDF 功能

接收其他应用分享的截图，自动裁切 A4 区域并生成 PDF。

**流程：** 截图分享到 app → 裁切 A4 区域 → 生成 PDF → 保存/分享

**配置文件：** `app/src/main/assets/crop_config.json`
- `default`: 默认裁切坐标（采用一加Ace5至尊版数据）
- `devices`: 按设备型号（`Build.MODEL`）匹配的裁切坐标
- 单位：像素（px）
- 以 `_` 开头的字段是说明，代码会自动忽略
- 已适配机型：红米K60、一加Ace5至尊版、realme X7 Pro

**生成的 PDF 文件名格式：** `ID_Copy_yyyymmdd-hhmmss.pdf`

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
- **构建**: Gradle 8.3, AGP 8.2.0
- **最低 SDK**: 26 (Android 8.0)
- **目标 SDK**: 34 (Android 14)

## 错误分类

`WatermarkRemover.classifyError()` 将异常转为友好提示：

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

**注意**：其中 6 个用例依赖项目根目录的 `test_pdfs/` 样本（如 `正常_带水印.pdf`），该目录未纳入版本控制。样本缺失时这 6 个用例会失败，只有 3 个纯正则用例能通过。

## 已知问题

- `WatermarkRemover` 只读取 `page.getPdfObject().getAsStream(Contents)`；若页面内容流是数组（被多次追加写过的 PDF 常见），会取到 null 从而跳过该页，水印漏删。
- `MainActivity` 的 `savedUriMap` / `skipWatermarkSet` 是 Activity 级可变 Map，Compose 状态也未用 `rememberSaveable`。屏幕旋转或进程被回收后 URI 映射丢失，处理会中断。

## 环境要求

- Android SDK: 路径写入 `local.properties` 的 `sdk.dir`（本机曾用 `D:/Development/Android/sdk`）
- JDK: **17**（AGP 8.2.0 的硬性要求；`compileOptions` 里的 `VERSION_1_8` 是 Java 语言级别，不是 JDK 版本）
- 打包前需确保 `JAVA_HOME` 指向 JDK 17，否则 `./gradlew` 会直接报 "JAVA_HOME is not set"
