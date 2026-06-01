# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

批量去除夸克扫描王非会员版 PDF 水印的桌面工具，打包为独立 EXE 发给同事使用。

当前版本：v1.4.0（EXE 文件名包含版本号：`夸克去水印_v1.4.0.exe`，使用 pypdf 轻量引擎）

## 常用命令

```bash
# 运行程序
python main.py

# 运行全部测试
python -m pytest tests/ -v

# 运行单个测试
python -m pytest tests/test_watermark_remover.py::test_remove_watermark_creates_output -v

# 打包 EXE（必须在虚拟环境中，Anaconda 的 pathlib 包会与 PyInstaller 冲突）
# 首次使用：创建虚拟环境并安装依赖
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt pyinstaller

# 打包（虚拟环境 .venv/ 已保留，后续直接运行）
.venv/Scripts/python build.py
```

## 架构

- `watermark_remover.py` — 核心逻辑：使用 pypdf 解析 PDF 内容流，通过正则表达式删除 `QuarkX2` 水印命令；定义 `WatermarkNotFoundError`、`NotPdfFileError` 异常
- `gui.py` — CustomTkinter 浅色精致界面，tkinterdnd2 拖拽支持，多线程批量处理，支持删除单个文件和排序
- `config.py` — JSON 持久化配置（输出路径、窗口位置），存储在 `~/.quark-watermark-remover/config.json`
- `main.py` — 入口，设置浅色模式，处理 windowed 模式下 stdout 为 None
- `build.py` — PyInstaller 打包脚本，打包 logo 目录作为数据文件，`VERSION` 变量控制 EXE 文件名中的版本号

## 关键技术细节

- UI 设计：浅色精致风，配色方案定义在 `gui.py` 的 `COLORS` 字典中，使用微软雅黑字体
- PDF 引擎：使用 pypdf（纯 Python），打包体积约 13MB，无二进制依赖
- 错误处理：`watermark_remover.py` 先检查 PDF 文件头（`%PDF-`），再调用 pypdf；`gui.py` 分类捕获异常显示友好中文提示
- 水印识别：通过正则表达式 `rb'q\s+[\d\s]+cm\s+/QuarkX2\s+Do\s+Q'` 匹配并删除水印命令
- GUI 类根据 tkinterdnd2 可用性动态选择基类（`TkinterDnD.Tk` 或 `ctk.CTk`）
- `self.app_config` 而非 `self.config`，避免与 tkinter 内置 `config` 方法冲突
- 输出文件命名：`原文件名_去水印.pdf`，冲突时自动加数字后缀 `(2)`、`(3)`...
- 配置文件存储在用户目录 `~/.quark-watermark-remover/`，避免权限问题

## 分支策略

- `master` — 主分支，当前使用 pypdf 引擎（v1.4.0，EXE 约 13MB）
- `legacy/pymupdf` — 归档分支，保留 PyMuPDF 引擎版本（v1.3.0，EXE 约 31MB）

两个分支代码完全独立，互不干扰。需要查看或使用 PyMuPDF 版本时切换到 `legacy/pymupdf` 分支。

## ICO 图标生成注意事项

- **不要使用 Pillow 的 `Image.save(format='ICO', append_images=...)`**，它只会保存第一个尺寸
- **必须手动构建 ICO 文件**：使用 `generate_ico.py`，将每个尺寸编码为 BMP DIB 格式后拼接
- **不要使用 `rcedit` 或 `UpdateResource` 修改 PyInstaller onefile EXE**，会丢失 overlay 数据导致 EXE 损坏
