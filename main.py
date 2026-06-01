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
