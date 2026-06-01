# gui_lite.py - 使用 pypdf 的轻量版本
import os
import threading
import customtkinter as ctk
from tkinter import filedialog
from watermark_remover_pypdf import remove_watermark, get_output_path, WatermarkNotFoundError, NotPdfFileError
from config import Config

# 拖拽支持（可选依赖）
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_DND = True
except ImportError:
    HAS_DND = False

# 根据是否有拖拽支持选择基类
if HAS_DND:
    BaseClass = TkinterDnD.Tk
else:
    BaseClass = ctk.CTk

# ── 配色方案（浅色精致风） ──────────────────────────────
COLORS = {
    "bg":           "#F5F6FA",   # 窗口背景
    "card":         "#FFFFFF",   # 卡片背景
    "card_border":  "#E2E5EC",   # 卡片边框
    "card_hover":   "#EEF0F5",   # 卡片悬停
    "accent":       "#3B82F6",   # 主色调（蓝）
    "accent_hover": "#2563EB",   # 主色调悬停
    "secondary":    "#64748B",   # 次要色（灰蓝）
    "success":      "#10B981",   # 成功
    "fail":         "#EF4444",   # 失败
    "processing":   "#F59E0B",   # 进行中
    "text":         "#1E293B",   # 文字主色
    "text_sub":     "#94A3B8",   # 文字次色
    "text_light":   "#FFFFFF",   # 浅色文字
    "drop_zone":    "#FAFBFE",   # 拖拽区背景
    "drop_border":  "#CBD5E1",   # 拖拽区边框
    "drop_hover":   "#EFF6FF",   # 拖拽区悬停
    "progress_bg":  "#E2E5EC",   # 进度条背景
    "btn_secondary":"#F1F5F9",   # 次按钮背景
    "btn_sec_hover":"#E2E8F0",   # 次按钮悬停
}

# ── 字体（Win7 兼容，使用微软雅黑） ──────────────────
FONT_FAMILY = "Microsoft YaHei UI"
FONT_FAMILY_FALLBACK = "Microsoft YaHei"


def _get_font(size=13, weight="normal"):
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


def _classify_error(e: Exception) -> str:
    """将异常转换为简短的友好提示"""
    msg = str(e).lower()
    if "password" in msg or "encrypted" in msg or "加密" in msg:
        return "失败-文件已加密"
    if "space" in msg or "disk" in msg or "空间" in msg:
        return "失败-磁盘空间不足"
    if "corrupt" in msg or "broken" in msg or "damaged" in msg or "损坏" in msg or "cannot open" in msg:
        return "失败-文件损坏"
    if "no pages" in msg or "page_count" in msg or "无内容" in msg:
        return "失败-PDF无内容"
    if "permission" in msg or "denied" in msg or "占用" in msg or "另一个程序" in msg:
        return "失败-文件被占用或无权限"
    if "name too long" in msg or "filename too long" in msg or "文件名过长" in msg or "errno 36" in msg:
        return "失败-路径过长"
    # 兜底：未知错误
    raw = str(e)[:50]
    return f"未知错误：{raw}"


class App(BaseClass):
    def __init__(self, config_path: str = "config.json"):
        super().__init__()

        self.app_config = Config(config_path)
        self.files = []  # [(path, status_label, card_frame)]
        self.processing = False
        self._closing = False

        self.title("夸克扫描王 PDF 去水印工具")
        self.geometry(f"{self.app_config.window_width}x{self.app_config.window_height}")
        self.minsize(560, 560)
        if self.app_config.window_x is not None and self.app_config.window_y is not None:
            self.geometry(f"+{self.app_config.window_x}+{self.app_config.window_y}")

        # 设置窗口图标（兼容开发模式和打包模式）
        import sys
        if getattr(sys, "frozen", False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_dir, "logo", "logo.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # 设置窗口背景色（TkinterDnD.Tk 不支持 fg_color）
        try:
            self.configure(fg_color=COLORS["bg"])
        except Exception:
            self.configure(bg=COLORS["bg"])

        self._setup_ui()
        if HAS_DND:
            self._setup_dnd()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_ui(self):
        """构建界面"""
        # ── 主内容区 ────────────────────────────────────
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=(16, 20))

        # ── 拖拽区 ──────────────────────────────────────
        self.drop_frame = ctk.CTkFrame(
            content,
            fg_color=COLORS["drop_zone"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["drop_border"],
            height=90,
        )
        self.drop_frame.pack(fill="x", pady=(0, 12))
        self.drop_frame.pack_propagate(False)

        drop_inner = ctk.CTkFrame(self.drop_frame, fg_color="transparent")
        drop_inner.place(relx=0.5, rely=0.5, anchor="center")

        self.drop_icon = ctk.CTkLabel(
            drop_inner,
            text="📄",
            font=("", 28),
            text_color=COLORS["text_sub"],
        )
        self.drop_icon.pack()

        self.drop_label = ctk.CTkLabel(
            drop_inner,
            text="拖拽 PDF 文件到此处，或点击选择",
            font=_get_font(13),
            text_color=COLORS["text_sub"],
        )
        self.drop_label.pack()

        # 拖拽区交互
        self.drop_frame.bind("<Button-1>", lambda e: self._select_files())
        self.drop_icon.bind("<Button-1>", lambda e: self._select_files())
        self.drop_label.bind("<Button-1>", lambda e: self._select_files())
        for w in [self.drop_frame, self.drop_icon, self.drop_label]:
            w.bind("<Enter>", self._drop_hover_enter)
            w.bind("<Leave>", self._drop_hover_leave)

        # ── 文件列表 ────────────────────────────────────
        list_header = ctk.CTkFrame(content, fg_color="transparent")
        list_header.pack(fill="x", pady=(0, 4))

        self.file_count_label = ctk.CTkLabel(
            list_header,
            text="文件列表",
            font=_get_font(13, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        )
        self.file_count_label.pack(side="left")

        self.sort_ascending = True
        self.sort_btn = ctk.CTkButton(
            list_header,
            text="↕ A→Z",
            font=_get_font(11),
            width=70,
            height=26,
            corner_radius=6,
            fg_color="transparent",
            hover_color=COLORS["card_hover"],
            text_color=COLORS["text_sub"],
            command=self._sort_files,
        )
        self.sort_btn.pack(side="right")

        self.file_frame = ctk.CTkScrollableFrame(
            content,
            fg_color=COLORS["card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["card_border"],
            height=180,
            scrollbar_button_color=COLORS["progress_bg"],
            scrollbar_button_hover_color=COLORS["drop_border"],
        )
        self.file_frame.pack(fill="both", expand=True, pady=(0, 12))

        # 空列表占位
        self.empty_label = ctk.CTkLabel(
            self.file_frame,
            text="暂无文件，请拖拽或选择 PDF 文件",
            font=_get_font(12),
            text_color=COLORS["text_sub"],
        )
        self.empty_label.pack(pady=40)

        # ── 输出路径 ────────────────────────────────────
        path_frame = ctk.CTkFrame(
            content,
            fg_color=COLORS["card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["card_border"],
        )
        path_frame.pack(fill="x", pady=(0, 12))

        path_inner = ctk.CTkFrame(path_frame, fg_color="transparent")
        path_inner.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(
            path_inner,
            text="输出路径",
            font=_get_font(12, "bold"),
            text_color=COLORS["text"],
        ).pack(side="left", padx=(0, 8))

        self.path_var = ctk.StringVar(value=self.app_config.output_dir or "（原文件目录）")
        self.path_entry = ctk.CTkEntry(
            path_inner,
            textvariable=self.path_var,
            font=_get_font(12),
            fg_color=COLORS["drop_zone"],
            border_color=COLORS["card_border"],
            text_color=COLORS["text"],
            placeholder_text_color=COLORS["text_sub"],
            border_width=1,
            corner_radius=8,
            height=34,
            state="disabled",
        )
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            path_inner,
            text="选择",
            font=_get_font(12),
            width=60,
            height=34,
            corner_radius=8,
            fg_color=COLORS["btn_secondary"],
            hover_color=COLORS["btn_sec_hover"],
            text_color=COLORS["text"],
            border_width=1,
            border_color=COLORS["card_border"],
            command=self._select_output_dir,
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            path_inner,
            text="默认",
            font=_get_font(12),
            width=54,
            height=34,
            corner_radius=8,
            fg_color=COLORS["btn_secondary"],
            hover_color=COLORS["btn_sec_hover"],
            text_color=COLORS["text_sub"],
            border_width=1,
            border_color=COLORS["card_border"],
            command=self._reset_output_dir,
        ).pack(side="left")

        # ── 进度区 ──────────────────────────────────────
        progress_frame = ctk.CTkFrame(content, fg_color="transparent")
        progress_frame.pack(fill="x", pady=(0, 12))

        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            height=8,
            corner_radius=4,
            fg_color=COLORS["progress_bg"],
            progress_color=COLORS["accent"],
        )
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(
            progress_frame,
            text="就绪",
            font=_get_font(12),
            text_color=COLORS["text_sub"],
            anchor="e",
        )
        self.status_label.pack(fill="x", pady=(4, 0))


        # ── 操作按钮 ────────────────────────────────────
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x")

        self.start_btn = ctk.CTkButton(
            btn_frame,
            text="开始去水印",
            font=_get_font(14, "bold"),
            height=44,
            corner_radius=10,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["text_light"],
            command=self._start_process,
        )
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.clear_btn = ctk.CTkButton(
            btn_frame,
            text="清空列表",
            font=_get_font(13),
            height=44,
            corner_radius=10,
            fg_color=COLORS["btn_secondary"],
            hover_color=COLORS["btn_sec_hover"],
            text_color=COLORS["text"],
            border_width=1,
            border_color=COLORS["card_border"],
            command=self._clear_list,
        )
        self.clear_btn.pack(side="left")

    # ── 拖拽区悬停效果 ──────────────────────────────────
    def _drop_hover_enter(self, event):
        self.drop_frame.configure(border_color=COLORS["accent"], fg_color=COLORS["drop_hover"])

    def _drop_hover_leave(self, event):
        self.drop_frame.configure(border_color=COLORS["drop_border"], fg_color=COLORS["drop_zone"])

    # ── 拖拽支持 ────────────────────────────────────────
    def _setup_dnd(self):
        if not HAS_DND:
            return
        try:
            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<Drop>>", self._on_drop)
        except Exception:
            pass

    def _on_drop(self, event):
        files = self.tk.splitlist(event.data)
        for f in files:
            if f.lower().endswith(".pdf") and f not in [p for p, _, _ in self.files]:
                self._add_file(f)

    def _select_files(self):
        files = filedialog.askopenfilenames(
            title="选择 PDF 文件",
            filetypes=[("PDF 文件", "*.pdf")],
        )
        for f in files:
            if f.lower().endswith(".pdf") and f not in [p for p, _, _ in self.files]:
                self._add_file(f)

    # ── 文件卡片 ────────────────────────────────────────
    def _add_file(self, path: str):
        # 隐藏空列表占位
        if self.empty_label is not None:
            self.empty_label.pack_forget()

        card = ctk.CTkFrame(
            self.file_frame,
            fg_color=COLORS["drop_zone"],
            corner_radius=6,
            border_width=1,
            border_color=COLORS["card_border"],
            height=32,
        )
        card.pack(fill="x", padx=4, pady=2)
        card.pack_propagate(False)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=8, pady=0)

        # 删除按钮（先放右侧）
        del_btn = ctk.CTkButton(
            inner,
            text="✕",
            font=_get_font(11),
            width=24,
            height=24,
            corner_radius=4,
            fg_color="transparent",
            hover_color=COLORS["fail"],
            text_color=COLORS["text_sub"],
            command=lambda: self._remove_file(path, card),
        )
        del_btn.pack(side="right")

        status_label = ctk.CTkLabel(
            inner,
            text="待处理",
            font=_get_font(11),
            text_color=COLORS["text_sub"],
            width=120,
            anchor="e",
        )
        status_label.pack(side="right", padx=(0, 4))

        name_label = ctk.CTkLabel(
            inner,
            text=os.path.basename(path),
            font=_get_font(12),
            text_color=COLORS["text"],
            anchor="w",
        )
        name_label.pack(side="left", fill="x", expand=True)

        self.files.append((path, status_label, card))
        self._update_file_count()

    def _remove_file(self, path: str, card):
        """从列表中删除单个文件"""
        if self.processing:
            return
        card.destroy()
        self.files = [(p, s, c) for p, s, c in self.files if p != path]
        self._update_file_count()
        if not self.files:
            self.empty_label.pack(pady=40)

    def _update_file_count(self):
        count = len(self.files)
        self.file_count_label.configure(text=f"文件列表（{count}）" if count else "文件列表")

    def _sort_files(self):
        """按文件名排序，切换升序/降序"""
        if not self.files or self.processing:
            return

        self.sort_ascending = not self.sort_ascending
        self.sort_btn.configure(
            text="↕ A→Z" if self.sort_ascending else "↕ Z→A"
        )

        # 排序（reverse=True 时为降序）
        self.files.sort(key=lambda x: os.path.basename(x[0]).lower(), reverse=not self.sort_ascending)

        # 重新排列卡片
        for _, _, card in self.files:
            card.pack_forget()
        for _, _, card in self.files:
            card.pack(fill="x", padx=4, pady=2)

    # ── 输出路径 ────────────────────────────────────────
    def _select_output_dir(self):
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.app_config.output_dir = directory
            self.path_var.set(directory)

    def _reset_output_dir(self):
        self.app_config.reset_output_dir()
        self.path_var.set("（原文件目录）")

    # ── 清空列表 ────────────────────────────────────────
    def _clear_list(self):
        if self.processing:
            return
        self.empty_label = None
        for widget in self.file_frame.winfo_children():
            widget.destroy()
        self.files.clear()
        self.progress_bar.set(0)
        self.status_label.configure(text="就绪")
        self.empty_label = ctk.CTkLabel(
            self.file_frame,
            text="暂无文件，请拖拽或选择 PDF 文件",
            font=_get_font(12),
            text_color=COLORS["text_sub"],
        )
        self.empty_label.pack(pady=40)
        self._update_file_count()

    # ── 处理逻辑 ────────────────────────────────────────
    def _start_process(self):
        if not self.files or self.processing:
            return

        self.processing = True
        self.start_btn.configure(state="disabled")
        self.clear_btn.configure(state="disabled")
        threading.Thread(target=self._process_files, daemon=True).start()

    def _process_files(self):
        files_snapshot = list(self.files)
        output_dir = self.app_config.output_dir
        total = len(files_snapshot)
        success = 0
        fail = 0

        skip = 0
        for i, (path, status_label, card) in enumerate(files_snapshot):
            if self._closing:
                return

            self.after(0, lambda sl=status_label: sl.configure(text="处理中", text_color=COLORS["processing"]))

            try:
                output_path = get_output_path(path, output_dir)
                # 自动创建输出目录
                out_dir = os.path.dirname(output_path)
                if out_dir and not os.path.exists(out_dir):
                    os.makedirs(out_dir, exist_ok=True)
                remove_watermark(path, output_path)
                success += 1
                self.after(0, lambda sl=status_label: sl.configure(text="完成", text_color=COLORS["success"]))
            except WatermarkNotFoundError:
                skip += 1
                self.after(0, lambda sl=status_label: sl.configure(text="无水印，跳过", text_color=COLORS["text_sub"]))
            except NotPdfFileError:
                fail += 1
                self.after(0, lambda sl=status_label: sl.configure(text="失败-非PDF文件", text_color=COLORS["fail"]))
            except Exception as e:
                fail += 1
                msg = _classify_error(e)
                self.after(0, lambda sl=status_label, m=msg: sl.configure(text=m, text_color=COLORS["fail"]))

            progress = (i + 1) / total
            self.after(0, lambda p=progress: self.progress_bar.set(p))
            self.after(0, lambda i=i: self.status_label.configure(text=f"处理中 {i + 1}/{total}"))

        if self._closing:
            return

        def _finish():
            parts = [f"成功 {success}"]
            if skip:
                parts.append(f"跳过 {skip}")
            if fail:
                parts.append(f"失败 {fail}")
            self.status_label.configure(text=f"完成 · {'，'.join(parts)}")

            self.processing = False
            self.start_btn.configure(state="normal")
            self.clear_btn.configure(state="normal")

        self.after(0, _finish)

    # ── 关闭窗口 ────────────────────────────────────────
    def _on_close(self):
        self._closing = True
        self.app_config.window_width = self.winfo_width()
        self.app_config.window_height = self.winfo_height()
        self.app_config.window_x = self.winfo_x()
        self.app_config.window_y = self.winfo_y()
        self.app_config.save()
        self.destroy()
