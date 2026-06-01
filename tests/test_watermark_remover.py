import os
import pytest
import pypdf
from pypdf.generic import ArrayObject, DecodedStreamObject, NameObject, NumberObject, DictionaryObject
from watermark_remover import remove_watermark, WatermarkNotFoundError


def create_test_pdf(tmp_path, filename="test.pdf", include_watermark=True):
    """创建测试 PDF 文件"""
    pdf_path = tmp_path / filename
    writer = pypdf.PdfWriter()

    # 添加两页
    for _ in range(2):
        page = writer.add_blank_page(width=595, height=842)

        # 创建内容流
        stream = DecodedStreamObject()
        if include_watermark:
            content = b"q\n0 0 0 RG\n/QuarkE1 gs q 535 0 0 841 29 66 cm /QuarkX1 Do Q\nq 162 0 0 50 389 8 cm /QuarkX2 Do Q\nQ\n"
        else:
            content = b"q\n0 0 0 RG\n/QuarkE1 gs q 535 0 0 841 29 66 cm /QuarkX1 Do Q\nQ\n"
        stream.set_data(content)

        # 设置页面内容
        page[NameObject("/Contents")] = stream
        page[NameObject("/Resources")] = DictionaryObject()

    with open(pdf_path, "wb") as f:
        writer.write(f)

    return pdf_path


@pytest.fixture
def sample_pdf(tmp_path):
    """创建带水印的测试 PDF"""
    return create_test_pdf(tmp_path, include_watermark=True)


def test_remove_watermark_creates_output(sample_pdf):
    """测试去水印后生成新文件"""
    output_path = sample_pdf.parent / "test_去水印.pdf"
    result = remove_watermark(str(sample_pdf), str(output_path))
    assert result is True
    assert output_path.exists()


def test_remove_watermark_removes_quarkx2(sample_pdf):
    """测试水印引用被删除"""
    output_path = sample_pdf.parent / "test_去水印.pdf"
    remove_watermark(str(sample_pdf), str(output_path))

    reader = pypdf.PdfReader(str(output_path))
    for page in reader.pages:
        if "/Contents" in page:
            contents = page["/Contents"]
            if hasattr(contents, "get_object"):
                stream = contents.get_object()
                if hasattr(stream, "get_data"):
                    data = stream.get_data()
                    assert b"QuarkX2" not in data


def test_remove_watermark_preserves_content(sample_pdf):
    """测试主要内容保留"""
    output_path = sample_pdf.parent / "test_去水印.pdf"
    remove_watermark(str(sample_pdf), str(output_path))

    reader = pypdf.PdfReader(str(output_path))
    assert len(reader.pages) == 2
    for page in reader.pages:
        if "/Contents" in page:
            contents = page["/Contents"]
            if hasattr(contents, "get_object"):
                stream = contents.get_object()
                if hasattr(stream, "get_data"):
                    data = stream.get_data()
                    assert b"QuarkX1" in data


def test_remove_watermark_no_watermark(tmp_path):
    """测试无水印文件应抛出 WatermarkNotFoundError"""
    pdf_path = create_test_pdf(tmp_path, "no_watermark.pdf", include_watermark=False)

    output_path = tmp_path / "no_watermark_去水印.pdf"
    with pytest.raises(WatermarkNotFoundError):
        remove_watermark(str(pdf_path), str(output_path))


def test_output_naming_conflict(tmp_path):
    """测试文件冲突时自动重命名"""
    pdf_path = create_test_pdf(tmp_path, include_watermark=True)

    # 创建已存在的输出文件
    output_path = tmp_path / "test_去水印.pdf"
    output_path.write_text("existing")

    result = remove_watermark(str(pdf_path), str(output_path))
    assert result is True

    # 应该创建 test_去水印(2).pdf
    conflict_path = tmp_path / "test_去水印(2).pdf"
    assert conflict_path.exists()
