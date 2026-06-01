# gui.py
import os
import threading
import customtkinter as ctk
from tkinter import filedialog
from watermark_remover import remove_watermark, get_output_path
from config import Config

# 拖拽支持（可选依赖）
try:
    from tkinterdnd2 import DND_FILES
    HAS_DND = True
except ImportError:
    HAS_DND = False


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
        if not HAS_DND:
            return
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
