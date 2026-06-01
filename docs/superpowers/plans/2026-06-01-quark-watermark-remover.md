# 夸克扫描王 PDF 去水印工具 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个批量去除夸克扫描王 PDF 水印的桌面工具，打包为独立 EXE

**Architecture:** 使用 CustomTkinter 构建 GUI，PyMuPDF 处理 PDF，模块化设计分离界面、逻辑和配置

**Tech Stack:** Python 3.11, CustomTkinter, PyMuPDF (fitz), PyInstaller

---

## 文件结构

```
quark-watermark-remover/
├── main.py              # 程序入口，启动 GUI
├── gui.py               # GUI 界面（CustomTkinter）
├── watermark_remover.py # 水印删除核心逻辑
├── config.py            # 配置管理（JSON 持久化）
├── build.py             # PyInstaller 打包脚本
└── tests/
    ├── __init__.py
    ├── test_watermark_remover.py  # 水印删除逻辑测试
    └── test_config.py             # 配置管理测试
```

---

### Task 1: 项目初始化与依赖安装

**Files:**
- Create: `requirements.txt`

- [ ] **Step 1: 创建 requirements.txt**

```txt
customtkinter>=5.2.0
PyMuPDF>=1.23.0
pyinstaller>=6.0.0
```

- [ ] **Step 2: 安装依赖**

Run: `pip install -r requirements.txt`

Expected: 成功安装 customtkinter, PyMuPDF, pyinstaller

- [ ] **Step 3: 验证安装**

Run: `python -c "import customtkinter; import fitz; print('OK')"`

Expected: `OK`

- [ ] **Step 4: 初始化 git 仓库**

```bash
cd D:/AI/quark-watermark-remover
git init
echo "__pycache__/" > .gitignore
echo "*.pyc" >> .gitignore
echo "dist/" >> .gitignore
echo "build/" >> .gitignore
echo "*.spec" >> .gitignore
echo "config.json" >> .gitignore
git add .
git commit -m "chore: initialize project with requirements"
```

---

### Task 2: 水印删除核心逻辑（watermark_remover.py）

**Files:**
- Create: `watermark_remover.py`
- Create: `tests/__init__.py`
- Create: `tests/test_watermark_remover.py`

- [ ] **Step 1: 编写水印删除函数的测试**

```python
# tests/test_watermark_remover.py
import os
import pytest
import fitz
from watermark_remover import remove_watermark


@pytest.fixture
def sample_pdf(tmp_path):
    """创建一个带水印的测试 PDF"""
    pdf_path = tmp_path / "test.pdf"
    doc = fitz.open()

    # 添加两页
    for _ in range(2):
        page = doc.new_page(width=595, height=907)
        # 模拟水印内容流
        content = b"q\n0 0 0 RG\n/QuarkE1 gs q 535 0 0 841 29 66 cm /QuarkX1 Do Q\nq 162 0 0 50 389 8 cm /QuarkX2 Do Q\nQ\n"
        page._clean_contents()
        xref = doc.get_new_xref()
        doc.update_stream(xref, content)
        page.set_contents([xref])

    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


def test_remove_watermark_creates_output(sample_pdf):
    """测试去水印后生成新文件"""
    output_path = sample_pdf.parent / "test_去水印.pdf"
    result = remove_watermark(str(sample_pdf), str(output_path))
    assert result is True
    assert output_path.exists()


def test_remove_watermark_removes_quarkx2(sample_pdf):
    """测试水印引用被删除"""
    output_path = sample_pdf.parent / "test_去水印.pdf"
    remove_watermark(str(sample_pdf), str(output_path))

    doc = fitz.open(str(output_path))
    for page in doc:
        for xref in page.get_contents():
            stream = doc.xref_stream(xref)
            if stream:
                assert b"QuarkX2" not in stream
    doc.close()


def test_remove_watermark_preserves_content(sample_pdf):
    """测试主要内容保留"""
    output_path = sample_pdf.parent / "test_去水印.pdf"
    remove_watermark(str(sample_pdf), str(output_path))

    doc = fitz.open(str(output_path))
    assert doc.page_count == 2
    for page in doc:
        for xref in page.get_contents():
            stream = doc.xref_stream(xref)
            if stream:
                assert b"QuarkX1" in stream
    doc.close()


def test_remove_watermark_no_watermark(tmp_path):
    """测试无水印文件"""
    pdf_path = tmp_path / "no_watermark.pdf"
    doc = fitz.open()
    page = doc.new_page()
    content = b"q\n0 0 0 RG\n/QuarkE1 gs q 535 0 0 841 29 66 cm /QuarkX1 Do Q\nQ\n"
    xref = doc.get_new_xref()
    doc.update_stream(xref, content)
    page.set_contents([xref])
    doc.save(str(pdf_path))
    doc.close()

    output_path = tmp_path / "no_watermark_去水印.pdf"
    result = remove_watermark(str(pdf_path), str(output_path))
    assert result is True  # 无水印也返回 True，标记为无需处理


def test_output_naming_conflict(tmp_path):
    """测试文件冲突时自动重命名"""
    pdf_path = tmp_path / "test.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(str(pdf_path))
    doc.close()

    # 创建已存在的输出文件
    output_path = tmp_path / "test_去水印.pdf"
    output_path.write_text("existing")

    result = remove_watermark(str(pdf_path), str(output_path))
    assert result is True

    # 应该创建 test_去水印(2).pdf
    conflict_path = tmp_path / "test_去水印(2).pdf"
    assert conflict_path.exists()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_watermark_remover.py -v`

Expected: FAIL (模块不存在)

- [ ] **Step 3: 实现 watermark_remover.py**

```python
# watermark_remover.py
import os
import fitz


def remove_watermark(input_path: str, output_path: str) -> bool:
    """
    去除 PDF 文件中的夸克扫描王水印

    Args:
        input_path: 输入 PDF 文件路径
        output_path: 输出 PDF 文件路径

    Returns:
        True 表示处理成功（无论是否有水印）
    """
    doc = fitz.open(input_path)

    for page in doc:
        contents = page.get_contents()
        for xref in contents:
            stream = doc.xref_stream(xref)
            if stream and b"QuarkX2" in stream:
                lines = stream.split(b"\n")
                new_lines = [line for line in lines if b"QuarkX2" not in line]
                new_stream = b"\n".join(new_lines)
                doc.update_stream(xref, new_stream)

    # 处理文件冲突
    final_path = _resolve_conflict(output_path)

    doc.save(final_path)
    doc.close()
    return True


def _resolve_conflict(output_path: str) -> str:
    """处理文件名冲突，自动添加数字后缀"""
    if not os.path.exists(output_path):
        return output_path

    base, ext = os.path.splitext(output_path)
    counter = 2
    while os.path.exists(f"{base}({counter}){ext}"):
        counter += 1
    return f"{base}({counter}){ext}"


def get_output_path(input_path: str, output_dir: str = None) -> str:
    """
    生成输出文件路径

    Args:
        input_path: 输入文件路径
        output_dir: 输出目录（None 则使用原文件目录）

    Returns:
        输出文件完整路径
    """
    filename = os.path.basename(input_path)
    name, ext = os.path.splitext(filename)
    output_name = f"{name}_去水印{ext}"

    if output_dir:
        return os.path.join(output_dir, output_name)
    return os.path.join(os.path.dirname(input_path), output_name)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_watermark_remover.py -v`

Expected: 全部 PASS

- [ ] **Step 5: 提交**

```bash
git add watermark_remover.py tests/
git commit -m "feat: implement watermark removal logic with tests"
```

---

### Task 3: 配置管理（config.py）

**Files:**
- Create: `config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: 编写配置管理的测试**

```python
# tests/test_config.py
import os
import json
import pytest
from config import Config


@pytest.fixture
def config_file(tmp_path):
    """返回临时配置文件路径"""
    return str(tmp_path / "config.json")


def test_config_default_values(config_file):
    """测试默认配置值"""
    config = Config(config_file)
    assert config.output_dir is None
    assert config.window_width == 600
    assert config.window_height == 500


def test_config_save_and_load(config_file):
    """测试配置保存和加载"""
    config = Config(config_file)
    config.output_dir = "/some/path"
    config.window_width = 800
    config.save()

    # 重新加载
    config2 = Config(config_file)
    assert config2.output_dir == "/some/path"
    assert config2.window_width == 800


def test_config_reset_output_dir(config_file):
    """测试重置输出目录"""
    config = Config(config_file)
    config.output_dir = "/some/path"
    config.save()

    config.reset_output_dir()
    assert config.output_dir is None

    # 验证持久化
    config2 = Config(config_file)
    assert config2.output_dir is None


def test_config_save_window_position(config_file):
    """测试保存窗口位置"""
    config = Config(config_file)
    config.window_x = 100
    config.window_y = 200
    config.save()

    config2 = Config(config_file)
    assert config2.window_x == 100
    assert config2.window_y == 200
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_config.py -v`

Expected: FAIL (模块不存在)

- [ ] **Step 3: 实现 config.py**

```python
# config.py
import json
import os


class Config:
    """配置管理类，支持 JSON 持久化"""

    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.output_dir: str = None
        self.window_width: int = 600
        self.window_height: int = 500
        self.window_x: int = None
        self.window_y: int = None
        self._load()

    def _load(self):
        """从文件加载配置"""
        if not os.path.exists(self.config_path):
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.output_dir = data.get("output_dir")
                self.window_width = data.get("window_width", self.window_width)
                self.window_height = data.get("window_height", self.window_height)
                self.window_x = data.get("window_x")
                self.window_y = data.get("window_y")
        except (json.JSONDecodeError, IOError):
            pass

    def save(self):
        """保存配置到文件"""
        data = {
            "output_dir": self.output_dir,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "window_x": self.window_x,
            "window_y": self.window_y,
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def reset_output_dir(self):
        """重置输出目录为默认值"""
        self.output_dir = None
        self.save()
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_config.py -v`

Expected: 全部 PASS

- [ ] **Step 5: 提交**

```bash
git add config.py tests/test_config.py
git commit -m "feat: implement config management with persistence"
```

---

### Task 4: GUI 界面（gui.py）

**Files:**
- Create: `gui.py`

- [ ] **Step 1: 实现 GUI 主框架**

```python
# gui.py
import os
import threading
import customtkinter as ctk
from tkinter import filedialog, DND_FILES
from watermark_remover import remove_watermark, get_output_path
from config import Config


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.config = Config()
        self.files = []  # [(path, status_label)]

        self.title("夸克扫描王 PDF 去水印工具")
        self.geometry(f"{self.config.window_width}x{self.config.window_height}")
        if self.config.window_x and self.config.window_y:
            self.geometry(f"+{self.config.window_x}+{self.config.window_y}")

        self._setup_ui()
        self._setup_dnd()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_ui(self):
        """构建界面"""
        # 拖拽提示
        self.drop_label = ctk.CTkLabel(
            self,
            text="拖拽 PDF 文件到此处，或点击下方按钮选择",
            height=60,
            fg_color=("gray85", "gray25"),
            corner_radius=10,
        )
        self.drop_label.pack(fill="x", padx=10, pady=(10, 5))
        self.drop_label.bind("<Button-1>", lambda e: self._select_files())

        # 文件列表
        self.file_frame = ctk.CTkScrollableFrame(self, height=200)
        self.file_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # 输出路径
        path_frame = ctk.CTkFrame(self)
        path_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(path_frame, text="输出路径:").pack(side="left", padx=(5, 0))

        self.path_var = ctk.StringVar(value=self.config.output_dir or "（原文件目录）")
        self.path_entry = ctk.CTkEntry(path_frame, textvariable=self.path_var)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=5)

        ctk.CTkButton(path_frame, text="选择", width=60, command=self._select_output_dir).pack(side="left", padx=2)
        ctk.CTkButton(path_frame, text="恢复默认", width=80, command=self._reset_output_dir).pack(side="left", padx=(2, 5))

        # 进度条
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(self, text="就绪")
        self.status_label.pack(pady=(0, 5))

        # 按钮
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkButton(btn_frame, text="开始去水印", command=self._start_process).pack(side="left", padx=5, fill="x", expand=True)
        ctk.CTkButton(btn_frame, text="清空列表", fg_color="gray", command=self._clear_list).pack(side="left", padx=5)

    def _setup_dnd(self):
        """设置拖拽支持"""
        try:
            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<Drop>>", self._on_drop)
        except Exception:
            # 拖拽不可用时降级
            pass

    def _on_drop(self, event):
        """处理拖拽文件"""
        files = self.tk.splitlist(event.data)
        for f in files:
            if f.lower().endswith(".pdf") and f not in [p for p, _ in self.files]:
                self._add_file(f)

    def _select_files(self):
        """选择文件对话框"""
        files = filedialog.askopenfilenames(
            title="选择 PDF 文件",
            filetypes=[("PDF 文件", "*.pdf")],
        )
        for f in files:
            if f not in [p for p, _ in self.files]:
                self._add_file(f)

    def _add_file(self, path: str):
        """添加文件到列表"""
        frame = ctk.CTkFrame(self.file_frame)
        frame.pack(fill="x", padx=2, pady=2)

        name_label = ctk.CTkLabel(frame, text=os.path.basename(path), anchor="w")
        name_label.pack(side="left", fill="x", expand=True, padx=5)

        status_label = ctk.CTkLabel(frame, text="待完成", text_color="gray", width=80)
        status_label.pack(side="right", padx=5)

        self.files.append((path, status_label))

    def _select_output_dir(self):
        """选择输出目录"""
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.config.output_dir = directory
            self.path_var.set(directory)

    def _reset_output_dir(self):
        """重置输出目录"""
        self.config.reset_output_dir()
        self.path_var.set("（原文件目录）")

    def _clear_list(self):
        """清空文件列表"""
        for widget in self.file_frame.winfo_children():
            widget.destroy()
        self.files.clear()
        self.progress_bar.set(0)
        self.status_label.configure(text="就绪")

    def _start_process(self):
        """开始处理（在新线程中运行）"""
        if not self.files:
            return

        threading.Thread(target=self._process_files, daemon=True).start()

    def _process_files(self):
        """处理所有文件"""
        total = len(self.files)
        success = 0
        fail = 0

        for i, (path, status_label) in enumerate(self.files):
            # 更新状态为"转换中"
            self.after(0, lambda sl=status_label: sl.configure(text="转换中", text_color="blue"))

            try:
                output_path = get_output_path(path, self.config.output_dir)
                remove_watermark(path, output_path)
                success += 1
                self.after(0, lambda sl=status_label: sl.configure(text="已完成", text_color="green"))
            except Exception as e:
                fail += 1
                error_msg = str(e)[:20]
                self.after(0, lambda sl=status_label, msg=error_msg: sl.configure(text=f"失败:{msg}", text_color="red"))

            # 更新进度
            progress = (i + 1) / total
            self.after(0, lambda p=progress: self.progress_bar.set(p))
            self.after(0, lambda i=i: self.status_label.configure(text=f"处理中 {i+1}/{total}..."))

        # 完成
        self.after(0, lambda: self.status_label.configure(text=f"完成！成功 {success} 个，失败 {fail} 个"))

    def _on_close(self):
        """关闭窗口时保存配置"""
        self.config.window_width = self.winfo_width()
        self.config.window_height = self.winfo_height()
        self.config.window_x = self.winfo_x()
        self.config.window_y = self.winfo_y()
        self.config.save()
        self.destroy()
```

- [ ] **Step 2: 测试 GUI 启动**

Run: `python -c "from gui import App; app = App(); app.mainloop()"`

Expected: 窗口正常显示，可关闭

- [ ] **Step 3: 提交**

```bash
git add gui.py
git commit -m "feat: implement GUI with drag-drop and progress"
```

---

### Task 5: 程序入口（main.py）

**Files:**
- Create: `main.py`

- [ ] **Step 1: 实现 main.py**

```python
# main.py
import sys
import os

# 确保 UTF-8 输出
sys.stdout.reconfigure(encoding="utf-8")

# 设置工作目录为脚本所在目录（打包后兼容）
if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(sys.executable))

from gui import App


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 测试完整程序**

Run: `python main.py`

Expected: 程序启动，可拖拽文件，点击去水印后生成 `原文件名_去水印.pdf`

- [ ] **Step 3: 使用测试文件验证**

1. 拖拽 `测试文件/单店合同.pdf` 到窗口
2. 点击「开始去水印」
3. 验证生成 `测试文件/单店合同_去水印.pdf`
4. 验证新文件无水印

- [ ] **Step 4: 提交**

```bash
git add main.py
git commit -m "feat: add main entry point"
```

---

### Task 6: 打包脚本（build.py）

**Files:**
- Create: `build.py`

- [ ] **Step 1: 实现打包脚本**

```python
# build.py
import subprocess
import sys
import os


def build():
    """打包为独立 EXE"""
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "夸克去水印",
        "--add-data", f"config.json;." if os.path.exists("config.json") else "",
        "main.py",
    ]

    # 移除空的 add-data 参数
    cmd = [c for c in cmd if c]

    print("开始打包...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("打包成功！")
        print(f"EXE 位置: dist/夸克去水印.exe")
    else:
        print("打包失败:")
        print(result.stderr)


if __name__ == "__main__":
    build()
```

- [ ] **Step 2: 执行打包**

Run: `python build.py`

Expected: 生成 `dist/夸克去水印.exe`

- [ ] **Step 3: 测试 EXE**

1. 运行 `dist/夸克去水印.exe`
2. 拖拽测试文件
3. 验证去水印功能正常

- [ ] **Step 4: 提交**

```bash
git add build.py
git commit -m "feat: add build script for PyInstaller packaging"
```

---

### Task 7: 最终验证与清理

- [ ] **Step 1: 运行所有测试**

Run: `python -m pytest tests/ -v`

Expected: 全部 PASS

- [ ] **Step 2: 完整功能测试**

1. 运行 `python main.py`
2. 拖拽多个 PDF 文件
3. 设置自定义输出路径
4. 点击「开始去水印」
5. 验证所有文件处理完成
6. 验证配置持久化（重启后路径保留）

- [ ] **Step 3: 测试错误场景**

1. 添加被占用的文件 → 应显示「失败:文件被占用」
2. 添加无水印文件 → 应显示「已完成」
3. 验证单个失败不影响其他文件

- [ ] **Step 4: 最终提交**

```bash
git add .
git commit -m "chore: final verification and cleanup"
```

---

## 自审清单

- ✅ 所有设计需求均有对应任务
- ✅ 无 TBD/TODO 占位符
- ✅ 类型/函数名一致
- ✅ 每步包含完整代码
- ✅ 测试覆盖核心逻辑
