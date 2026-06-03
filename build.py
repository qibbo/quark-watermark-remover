#!/usr/bin/env python3
"""
夸克去水印 Android 打包脚本
功能：检查代码变化，自动更新版本号，打包 Release APK
"""

import os
import re
import subprocess
import sys

# 项目根目录
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_FILE = os.path.join(PROJECT_DIR, "app", "build.gradle.kts")


def run_cmd(cmd, cwd=None):
    """执行命令并返回结果"""
    result = subprocess.run(
        cmd,
        cwd=cwd or PROJECT_DIR,
        capture_output=True,
        text=True,
        shell=True
    )
    return result.returncode == 0, result.stdout.strip()


def check_git_changes():
    """检查代码是否有变化"""
    # 检查未提交的修改
    ok, _ = run_cmd("git diff --quiet HEAD")
    if not ok:
        return True

    # 检查暂存区
    ok, _ = run_cmd("git diff --cached --quiet")
    if not ok:
        return True

    # 检查未跟踪的文件（排除 build 和 .gradle）
    ok, output = run_cmd("git ls-files --others --exclude-standard")
    if ok and output:
        lines = [l for l in output.split("\n") if l and "build/" not in l and ".gradle/" not in l]
        if lines:
            return True

    return False


def get_current_version():
    """获取当前版本号"""
    with open(BUILD_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # 提取 versionName
    match = re.search(r'val appVersionName = "(\d+\.\d+\.\d+)"', content)
    version = match.group(1) if match else "1.0.0"

    # 提取 versionCode
    match = re.search(r'versionCode = (\d+)', content)
    code = int(match.group(1)) if match else 1

    return version, code


def update_version(version, code):
    """更新版本号"""
    major, minor, patch = map(int, version.split("."))

    # 递增修订版本
    patch += 1
    if patch > 9:
        patch = 0
        minor += 1
    if minor > 9:
        minor = 0
        major += 1

    new_version = f"{major}.{minor}.{patch}"
    new_code = code + 1

    # 更新 build.gradle.kts
    with open(BUILD_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace(
        f'val appVersionName = "{version}"',
        f'val appVersionName = "{new_version}"'
    )
    content = content.replace(
        f"versionCode = {code}",
        f"versionCode = {new_code}"
    )

    with open(BUILD_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    return new_version, new_code


def gradle_build():
    """执行 Gradle 打包"""
    # 设置代理环境变量
    env = os.environ.copy()
    env["https_proxy"] = "http://127.0.0.1:7890"
    env["http_proxy"] = "http://127.0.0.1:7890"

    # 执行打包命令
    cmd = os.path.join(PROJECT_DIR, "gradlew.bat" if sys.platform == "win32" else "./gradlew")
    result = subprocess.run(
        [cmd, "assembleRelease"],
        cwd=PROJECT_DIR,
        env=env
    )
    return result.returncode == 0


def find_apk():
    """查找生成的 APK 文件"""
    apk_dir = os.path.join(PROJECT_DIR, "app", "build", "outputs", "apk", "release")
    if not os.path.exists(apk_dir):
        return None, 0

    for f in os.listdir(apk_dir):
        if f.endswith(".apk"):
            path = os.path.join(apk_dir, f)
            size = os.path.getsize(path)
            return path, size

    return None, 0


def format_size(size_bytes):
    """格式化文件大小"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def main():
    print("=== 夸克去水印打包脚本 ===\n")

    # 获取当前版本
    version, code = get_current_version()
    print(f"当前版本：{version} ({code})")

    # 检查代码变化
    has_changes = check_git_changes()

    if has_changes:
        print("检测到代码变化，更新版本号...")
        new_version, new_code = update_version(version, code)
        print(f"版本号已更新：{version} ({code}) -> {new_version} ({new_code})")
    else:
        print("代码无变化，保持当前版本号")

    # 执行打包
    print("\n开始打包...")
    success = gradle_build()

    if not success:
        print("\n打包失败")
        sys.exit(1)

    # 获取打包结果
    apk_path, apk_size = find_apk()

    if apk_path:
        print(f"\n打包完成！")
        print(f"APK 文件：{apk_path}")
        print(f"文件大小：{format_size(apk_size)}")
    else:
        print("\n打包失败：未找到 APK 文件")
        sys.exit(1)


if __name__ == "__main__":
    main()
