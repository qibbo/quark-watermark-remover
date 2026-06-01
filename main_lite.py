# main_lite.py - 使用 pypdf 的轻量版本
import sys
import os

# 确保 UTF-8 输出（windowed 模式下 stdout 为 None）
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8")

# 打包后切到 exe 所在目录，配置文件使用用户目录避免权限问题
if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(sys.executable))

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".quark-watermark-remover")
os.makedirs(CONFIG_DIR, exist_ok=True)
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

import customtkinter as ctk
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

from gui_lite import App


def main():
    app = App(config_path=CONFIG_PATH)
    app.mainloop()


if __name__ == "__main__":
    main()
