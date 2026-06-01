# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

批量去除夸克扫描王非会员版 PDF 水印的桌面工具，打包为独立 EXE 发给同事使用。

## 常用命令

```bash
# 运行程序
python main.py

# 运行全部测试
python -m pytest tests/ -v

# 运行单个测试
python -m pytest tests/test_watermark_remover.py::test_remove_watermark_creates_output -v

# 打包 EXE（必须在虚拟环境中，Anaconda 的 pathlib 包会与 PyInstaller 冲突）
# 首次使用：python -m venv .venv && source .venv/Scripts/activate && pip install -r requirements.txt
pyinstaller --onefile --windowed --name "夸克去水印" main.py
```

## 架构

- `watermark_remover.py` — 核心逻辑：解析 PDF 内容流，删除 `QuarkX2` 水印引用行
- `gui.py` — CustomTkinter 界面，tkinterdnd2 拖拽支持，多线程批量处理
- `config.py` — JSON 持久化配置（输出路径、窗口位置）
- `main.py` — 入口，处理 windowed 模式下 stdout 为 None 的情况
- `build.py` — PyInstaller 打包脚本

## 关键技术细节

- 水印识别：查找 PDF 页面内容流中的 `QuarkX2` 图片引用并删除对应行
- GUI 类根据 tkinterdnd2 可用性动态选择基类（`TkinterDnD.Tk` 或 `ctk.CTk`）
- `self.app_config` 而非 `self.config`，避免与 tkinter 内置 `config` 方法冲突
- 输出文件命名：`原文件名_去水印.pdf`，冲突时自动加数字后缀 `(2)`、`(3)`...
