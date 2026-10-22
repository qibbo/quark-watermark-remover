# CLAUDE.md

本文件为在此仓库中工作的 AI 编程助手（Claude Code / WorkBuddy 等）提供项目约定、架构说明与操作流程。

## 项目概述

夸克去水印 (Quark Watermark Remover) — Android 应用，用于移除夸克扫描王 PDF 中的水印，并把分享进来的截图裁切成 A4 生成复印件 PDF。纯本地处理，无需联网。

**唯一的交付形态是 Android 应用。** 仓库中的 Python 桌面版只是最初的技术验证，已冻结、不再维护，改动不要回灌到桌面版。

## 分支策略

| 分支 | 用途 |
|---|---|
| `feature/android-apk` | **活跃开发分支**，Android 版全部代码在此 |
| `master` | 默认分支，与 `feature/android-apk` 保持同一提交 |
| `legacy/pymupdf` | 更早的桌面版实验（PyMuPDF / pypdf 两套引擎），冻结 |
| `feature/wechat-pdf-bot` | 已中止的微信机器人方案，不再推进 |

`master` 是 Android 分支的祖先，早期提交里是 Python 桌面版代码。两条线的版本号各自独立：桌面版停在 v1.4.1（`v1.0.0`～`v1.4.1` 这批 tag 全部属于桌面版），**Android 线自 `2.0.0` 起号**，当前 v2.0.1，不要用 tag 跨线对照。

## 环境要求

| 项 | 要求 |
|---|---|
| JDK | **17**（AGP 8.2.0 的硬性要求；`compileOptions` 里的 `VERSION_1_8` 是 Java 语言级别，不是 JDK 版本） |
| Android SDK | 路径写入 `local.properties` 的 `sdk.dir`，需含 `platforms;android-34`、`build-tools;34.0.0`、`platform-tools` |
| 环境变量 | `JAVA_HOME` 必须指向 JDK 17，否则 `./gradlew` 直接报 "JAVA_HOME is not set" |

本机（Windows）当前安装位置：

- JDK 17：`D:/Development/jdk-17`（Temurin 17.0.20.1）
- Android SDK：`D:/Development/Android/sdk`

两者已写入用户级环境变量（`JAVA_HOME` / `ANDROID_HOME` / `ANDROID_SDK_ROOT`，PATH 追加 `%JAVA_HOME%\bin`），新开终端即可生效。

### 代理

访问中国大陆以外的服务时使用 FlClash HTTP 代理：

```bash
https_proxy=http://127.0.0.1:7890 http_proxy=http://127.0.0.1:7890
```

适用于 GitHub、Maven Central、npm、pip 等境外源；中国大陆服务（如 Gitee）不走代理。Gradle 走代理需额外传 JVM 参数：

```bash
export GRADLE_OPTS="-Dhttps.proxyHost=127.0.0.1 -Dhttps.proxyPort=7890 -Dhttp.proxyHost=127.0.0.1 -Dhttp.proxyPort=7890"
```

注意：FlClash 未开启时不要带代理参数，否则所有请求会因连不上代理而超时。实测 dl.google.com 经代理约 7 MB/s，GitHub Releases 仅约 0.2 MB/s，依赖下载的瓶颈通常在 GitHub。

## 构建与打包

```bash
./gradlew assembleDebug      # Debug
./gradlew assembleRelease    # Release（需 keystore 签名）
./gradlew test               # 单元测试，纯 JVM，无需设备
./gradlew clean              # 清理
```

**打包脚本（推荐）：**

```bash
python build.py
```

脚本行为：检测代码变化 → 有变化则递增版本号 → 执行 `assembleRelease` → 打印 APK 路径与大小。首次全量构建（含依赖下载）约 15 分钟，之后增量构建约 1 分钟。

产物：`app/build/outputs/apk/release/夸克去水印_v{version}-release.apk`

## 版本管理

**规则：代码有变更必须递增版本号；仅重新打包则版本号不变。**

1. 修改 `app/build.gradle.kts` 的 `appVersionName`（如 2.0.0 → 2.0.1）
2. 同步 `versionCode` 加 1
3. 再执行 `assembleRelease`

Android 线编号从 `2.0.0` 起，`1.x` 属于桌面版历史。

**注意**：`build.py` 的变更检测把**未跟踪文件**也算作代码变更。仓库里存在 `草稿纸_勿删.md`、`.workbuddy/` 这类本地文件时会误判并递增版本号，需要精确控制版本号时直接跑 `./gradlew assembleRelease`。

### 发布约定

- tag 用 `v{version}`，指向 `master` 当前提交
- Release 资产必须用**纯 ASCII 文件名**：`quark-watermark-v{version}-release.apk`
- 用中文文件名（`夸克去水印_v2.0.0-release.apk`）上传，GitHub 会把中文吞掉，资产名变成 `_v2.0.0-release.apk`
- 发布后同步更新 README 的「版本与发布」表

### 发布记录

| 版本 | 内容 |
|---|---|
| v2.0.1 | 新增小米15（`24129PN74C`）裁切适配；红米K60 数据标记存疑 |
| v2.0.0 | Android 线起号；新增 realme X7 Pro 适配；图片模式按钮文案通用化为「生成复印件PDF」 |

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

页面切换没有用 Navigation 库，由 `MainActivity` 里的 `showResult` 布尔状态控制。处理流程：选文件 / 接收分享 → `processFiles()` 逐文件处理 → 结果暂存在 `processedData` → 结果页点「保存」才落盘。

## 截图转 PDF

**流程：** 截图分享到 app → 按机型裁切 A4 区域 → 转 PDF（595×842pt）→ 保存 / 分享

**配置文件：** `app/src/main/assets/crop_config.json`

- `default`：未匹配机型时的兜底坐标（采用一加 Ace5 至尊版数据）
- `devices`：按 `Build.MODEL` 精确匹配（忽略大小写），key 为型号代码
- 单位：像素（px），坐标系为截图原图像素
- 以 `_` 开头的字段仅为说明，代码自动忽略
- 内置校验：`width ÷ height` 应约等于 0.707（A4 宽高比）

**已适配机型：**

| 机型 | 型号代码 | 屏幕分辨率 | left | top | width | height | 状态 |
|---|---|---|---|---|---|---|---|
| 一加 Ace5 至尊版 | `PLC110` | 1264×2780 | 54 | 494 | 1160 | 1641 | 已验证，同时作为 default |
| realme X7 Pro | `RMX2121` | 1080×2400 | 48 | 426 | 984 | 1391 | 已验证 |
| 小米15 | `24129PN74C` | 1200×2670 | 53 | 524 | 1095 | 1548 | 已验证，v2.0.1 起支持 |
| 红米 K60 | `23013RK75C` | 1220×2712 | 42 | 431 | 1002 | 1408 | **数据存疑，待重测** |

红米 K60 的左右边距为 42/176，明显不对称（居中应约 109/109），高度占屏比 51.9% 也低于其他机型的 58%~59%，疑 `left` 偏小约 67px。数据保留未删，`_备注` 字段内有记录，等该机在手时重测。

**新增机型流程：**

1. `adb shell getprop ro.product.model` 取型号代码（必须用设备上报值，不能按市场名推测）
2. `adb shell wm size` 记录物理分辨率，确认系统「屏幕分辨率」设置与之一致
3. 在目标机打开 WPS 复印件预览并截图，用 `adb exec-out screencap -p > 机型.png` 取原图（不接受聊天软件转发过的压缩图）
4. 在 Photoshop 等工具中量出 A4 白纸区域的左上角与右下角，相减得 `width` / `height`
5. 校验 `width ÷ height ≈ 0.707`，偏差超过 2% 说明取点错误
6. 写入 `devices` 并升级版本号

注意：「显示大小」「字体大小」「导航方式」都会改变 WPS 顶部工具栏高度，进而影响 `top`。测量时保持日常使用的设置。

**生成的 PDF 文件名格式：** `ID_Copy_yyyymmdd-hhmmss.pdf`

## 水印移除原理

正则匹配 PDF 页面内容流中的夸克水印命令并移除：

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
- 多文件：自动打包 ZIP 分享（兼容微信/QQ 等不支持多 PDF 分享的应用），ZIP 名形如 `去水印结果_共N个_时间戳.zip`
- 通过 FileProvider 分享缓存文件

## 签名配置

Release 签名使用项目根目录的 keystore：

- 文件: `quark-watermark.keystore`
- 别名: `quark`
- 密码: 见 `app/build.gradle.kts` 中的 `signingConfigs`

**注意**: keystore 已加入 `.gitignore`，不应提交到版本控制。

## 测试

```bash
./gradlew test
```

用例覆盖：正常 PDF、无水印、损坏文件、非 PDF、空文件、加密 PDF、多页 PDF。

**注意**：其中 6 个用例依赖项目根目录的 `test_pdfs/` 样本（如 `正常_带水印.pdf`），该目录未纳入版本控制。样本缺失时这 6 个用例会失败，只有 3 个纯正则用例能通过。

## 已知问题

- `WatermarkRemover` 只读取 `page.getPdfObject().getAsStream(Contents)`；若页面内容流是数组（被多次追加写过的 PDF 常见），会取到 null 从而跳过该页，水印漏删。
- `MainActivity` 的 `savedUriMap` / `skipWatermarkSet` 是 Activity 级可变 Map，Compose 状态也未用 `rememberSaveable`。屏幕旋转或进程被回收后 URI 映射丢失，处理会中断。
- 图片模式标志 `isImageMode` 是全局单一值，图片与 PDF 混选时首页按钮文案会误判（处理逻辑按索引判断，不受影响）。
