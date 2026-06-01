# build_lite.py - 使用 pypdf 的轻量打包脚本
import subprocess
import sys
import os

VERSION = "1.3.0-lite"


def build_lite():
    """打包为独立 EXE（轻量版本，使用 pypdf 替代 PyMuPDF）"""
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", f"夸克去水印_v{VERSION}",
        "--hidden-import", "tkinter",
        "--hidden-import", "_tkinter",
        "--hidden-import", "tkinter.constants",
        # 优化选项
        "--clean",  # 清理临时文件
        # 排除 PyMuPDF（用 pypdf 替代）
        "--exclude-module", "pymupdf",
        "--exclude-module", "fitz",
        "--exclude-module", "mupdf",
        # 排除不需要的模块
        "--exclude-module", "matplotlib",
        "--exclude-module", "numpy",
        "--exclude-module", "pandas",
        "--exclude-module", "scipy",
        "--exclude-module", "PIL",
        "--exclude-module", "pillow",
        "--exclude-module", "cv2",
        "--exclude-module", "torch",
        "--exclude-module", "tensorflow",
        # 排除测试模块
        "--exclude-module", "pytest",
        "--exclude-module", "unittest",
        "--exclude-module", "doctest",
        "--exclude-module", "test",
        # 排除开发工具
        "--exclude-module", "pdb",
        "--exclude-module", "profile",
        "--exclude-module", "cProfile",
        "--exclude-module", "timeit",
    ]

    if os.path.exists("logo/logo.ico"):
        cmd.extend(["--icon", "logo/logo.ico"])

    # 打包 logo 目录作为数据文件
    if os.path.isdir("logo"):
        cmd.extend(["--add-data", "logo;logo"])

    cmd.append("main_lite.py")

    print("开始打包（轻量版本，使用 pypdf）...")
    print(f"命令: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        exe_path = f"dist/夸克去水印_v{VERSION}.exe"
        if os.path.exists(exe_path):
            size = os.path.getsize(exe_path)
            print(f"打包成功！")
            print(f"EXE 位置: {exe_path}")
            print(f"文件大小: {size:,} bytes ({size/1024/1024:.1f} MB)")
        else:
            print("打包成功，但找不到 EXE 文件")
    else:
        print("打包失败:")
        print(result.stderr)


if __name__ == "__main__":
    build_lite()
