# 夸克扫描王 PDF 去水印工具

批量去除夸克扫描王非会员版导出 PDF 中的水印，支持拖拽文件、批量处理。

## 功能

- 批量去除 PDF 中的 `QuarkX2` 水印
- 支持拖拽文件添加（需 tkinterdnd2）
- 支持删除单个文件、按文件名排序
- 自定义输出目录，文件名冲突自动加数字后缀
- 智能错误提示（无水印跳过、文件损坏、加密等）
- 窗口位置和大小自动记忆
- 浅色精致界面，Win7 及以上兼容

## 使用方式

### 直接运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

### 打包为 EXE

```bash
# 必须在虚拟环境中打包（Anaconda 的 pathlib 与 PyInstaller 冲突）
# 首次使用：创建虚拟环境并安装依赖
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt pyinstaller

# 打包
.venv/Scripts/python build.py
```

打包完成后，EXE 文件位于 `dist/夸克去水印_v{版本号}.exe`。

## 项目结构

```
├── main.py              # 程序入口
├── gui.py               # GUI 界面（CustomTkinter + 拖拽支持）
├── watermark_remover.py # 核心去水印逻辑（PyMuPDF）
├── config.py            # 配置管理（JSON 持久化）
├── build.py             # PyInstaller 打包脚本
├── generate_ico.py      # ICO 图标生成脚本
├── requirements.txt     # 依赖列表
├── logo/
│   ├── logo.png         # 原始图标
│   └── logo.ico         # 生成的 ICO
└── tests/
    ├── test_watermark_remover.py
    └── test_config.py
```

## 错误处理

| 场景 | 显示 |
|------|------|
| 处理成功 | 绿色「完成」 |
| 无水印（已处理过） | 灰色「无水印，跳过」 |
| 文件已加密 | 红色「失败-文件已加密」 |
| 文件损坏 | 红色「失败-文件损坏」 |
| 非 PDF 文件 | 红色「失败-非PDF文件」 |
| 磁盘空间不足 | 红色「失败-磁盘空间不足」 |
| 其他错误 | 红色「未知错误：{信息摘要}」 |

## 依赖

- `customtkinter` — 现代化 tkinter 主题
- `PyMuPDF` — PDF 解析与修改
- `pyinstaller` — 打包为独立 EXE
- `tkinterdnd2` — 文件拖拽支持（可选）
