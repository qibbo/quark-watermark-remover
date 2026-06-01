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

    try:
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
    finally:
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
