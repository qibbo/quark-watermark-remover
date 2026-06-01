import os
import pytest
import fitz
from watermark_remover import remove_watermark


@pytest.fixture
def sample_pdf(tmp_path):
    """创建一个带水印的测试 PDF"""
    pdf_path = tmp_path / "test.pdf"
    doc = fitz.open()

    # 添加两页
    for _ in range(2):
        page = doc.new_page(width=595, height=907)
        # 先画点东西创建内容流
        shape = page.new_shape()
        shape.draw_rect(fitz.Rect(0, 0, 10, 10))
        shape.finish(color=(0, 0, 0))
        shape.commit()
        # 替换为模拟水印内容流
        content = b"q\n0 0 0 RG\n/QuarkE1 gs q 535 0 0 841 29 66 cm /QuarkX1 Do Q\nq 162 0 0 50 389 8 cm /QuarkX2 Do Q\nQ\n"
        for xref in page.get_contents():
            doc.update_stream(xref, content)

    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


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

    doc = fitz.open(str(output_path))
    for page in doc:
        for xref in page.get_contents():
            stream = doc.xref_stream(xref)
            if stream:
                assert b"QuarkX2" not in stream
    doc.close()


def test_remove_watermark_preserves_content(sample_pdf):
    """测试主要内容保留"""
    output_path = sample_pdf.parent / "test_去水印.pdf"
    remove_watermark(str(sample_pdf), str(output_path))

    doc = fitz.open(str(output_path))
    assert doc.page_count == 2
    for page in doc:
        for xref in page.get_contents():
            stream = doc.xref_stream(xref)
            if stream:
                assert b"QuarkX1" in stream
    doc.close()


def test_remove_watermark_no_watermark(tmp_path):
    """测试无水印文件"""
    pdf_path = tmp_path / "no_watermark.pdf"
    doc = fitz.open()
    page = doc.new_page()
    # 先画点东西创建内容流
    shape = page.new_shape()
    shape.draw_rect(fitz.Rect(0, 0, 10, 10))
    shape.finish(color=(0, 0, 0))
    shape.commit()
    # 替换为不含水印的内容流
    content = b"q\n0 0 0 RG\n/QuarkE1 gs q 535 0 0 841 29 66 cm /QuarkX1 Do Q\nQ\n"
    for xref in page.get_contents():
        doc.update_stream(xref, content)
    doc.save(str(pdf_path))
    doc.close()

    output_path = tmp_path / "no_watermark_去水印.pdf"
    result = remove_watermark(str(pdf_path), str(output_path))
    assert result is True  # 无水印也返回 True，标记为无需处理


def test_output_naming_conflict(tmp_path):
    """测试文件冲突时自动重命名"""
    pdf_path = tmp_path / "test.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(str(pdf_path))
    doc.close()

    # 创建已存在的输出文件
    output_path = tmp_path / "test_去水印.pdf"
    output_path.write_text("existing")

    result = remove_watermark(str(pdf_path), str(output_path))
    assert result is True

    # 应该创建 test_去水印(2).pdf
    conflict_path = tmp_path / "test_去水印(2).pdf"
    assert conflict_path.exists()
