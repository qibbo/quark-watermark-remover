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
