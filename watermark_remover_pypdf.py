# watermark_remover_pypdf.py - 使用 pypdf 的轻量版本
import os
import re
import pypdf


class WatermarkNotFoundError(Exception):
    """PDF 中未找到目标水印"""
    pass


class NotPdfFileError(Exception):
    """文件不是有效的 PDF"""
    pass


# 匹配水印命令模式：q ... /QuarkX2 Do Q
WATERMARK_PATTERN = re.compile(rb'q\s+[\d\s]+cm\s+/QuarkX2\s+Do\s+Q')


def remove_watermark(input_path: str, output_path: str) -> bool:
    """
    去除 PDF 文件中的夸克扫描王水印

    Args:
        input_path: 输入 PDF 文件路径
        output_path: 输出 PDF 文件路径

    Returns:
        True 表示处理成功

    Raises:
        WatermarkNotFoundError: 未找到水印（可能已处理过）
        NotPdfFileError: 文件不是有效的 PDF
    """
    # 检查 PDF 文件头
    with open(input_path, 'rb') as f:
        header = f.read(5)
    if header != b'%PDF-':
        raise NotPdfFileError("文件不是有效的 PDF")

    try:
        reader = pypdf.PdfReader(input_path)
    except Exception as e:
        raise NotPdfFileError(f"文件不是有效的 PDF: {e}")

    found = False

    for page in reader.pages:
        # 获取内容流
        if '/Contents' not in page:
            continue

        contents_ref = page['/Contents']

        # 处理内容流可能是数组的情况
        if isinstance(contents_ref, pypdf.generic.ArrayObject):
            for ref in contents_ref:
                if hasattr(ref, 'get_object'):
                    stream = ref.get_object()
                    if hasattr(stream, 'get_data'):
                        data = stream.get_data()
                        if b'QuarkX2' in data:
                            found = True
                            new_data = WATERMARK_PATTERN.sub(b'', data)
                            new_data = re.sub(rb'\n{3,}', b'\n\n', new_data)
                            stream.set_data(new_data)
        elif hasattr(contents_ref, 'get_object'):
            stream = contents_ref.get_object()
            if hasattr(stream, 'get_data'):
                data = stream.get_data()
                if b'QuarkX2' in data:
                    found = True
                    new_data = WATERMARK_PATTERN.sub(b'', data)
                    new_data = re.sub(rb'\n{3,}', b'\n\n', new_data)
                    stream.set_data(new_data)

    if not found:
        raise WatermarkNotFoundError("PDF 中未找到目标水印，可能已处理过")

    # 处理文件冲突
    final_path = _resolve_conflict(output_path)

    # 保存修改后的 PDF
    writer = pypdf.PdfWriter()
    writer.append_pages_from_reader(reader)

    with open(final_path, 'wb') as f:
        writer.write(f)

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
