# build.py
import subprocess
import sys
import os

VERSION = "1.2.0"


def build():
    """打包为独立 EXE"""
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", f"夸克去水印_v{VERSION}",
        "--hidden-import", "tkinter",
        "--hidden-import", "_tkinter",
        "--hidden-import", "tkinter.constants",
    ]

    if os.path.exists("logo/logo.ico"):
        cmd.extend(["--icon", "logo/logo.ico"])

    # 打包 logo 目录作为数据文件
    if os.path.isdir("logo"):
        cmd.extend(["--add-data", "logo;logo"])

    cmd.append("main.py")

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
