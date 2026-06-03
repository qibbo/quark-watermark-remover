# 夸克去水印 - Android 版

去除夸克扫描王 PDF 中的水印，纯本地处理，无需联网。

## 功能

- 选择 PDF 文件，一键去除水印
- 批量处理多个文件
- 纯本地处理，不上传任何文件
- 处理后可保存到本地或分享给其他应用
- 单文件直接分享 PDF，多文件自动打包 ZIP（兼容微信/QQ）
- **截图转 PDF**：从 WPS 等应用分享截图，自动裁切 A4 区域生成 PDF

## 技术方案

- 语言：Kotlin
- UI：Jetpack Compose + Material3
- PDF 库：iText 7.2.5
- 核心逻辑：解析 PDF 内容流，正则匹配并移除 `QuarkX2` 水印指令

## 截图转 PDF

从 WPS 等应用分享截图，自动裁切 A4 区域生成 PDF。

**使用方法：**
1. 在 WPS 中打开身份证复印件预览
2. 截图
3. 分享到本 app
4. 自动生成 PDF，可保存或分享

**配置文件：** `app/src/main/assets/crop_config.json`
- 按设备型号配置裁切坐标（单位：像素）
- 添加新机型只需在 `devices` 中加一行
- 设备型号获取：`adb shell getprop ro.product.model`

**生成的 PDF 文件名格式：** `ID_Copy_yyyymmdd-hhmmss.pdf`

## 构建

```bash
# Debug 版本
./gradlew assembleDebug

# Release 版本
./gradlew assembleRelease
```

## 下载

从 [Releases](../../releases) 页面下载最新 APK。

## 截图

<p align="center">
  <img src="logo/logo.png" width="100" alt="Logo">
</p>
