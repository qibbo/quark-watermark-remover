package com.quark.watermark.core

import com.itextpdf.kernel.pdf.PdfDocument
import com.itextpdf.kernel.pdf.PdfName
import com.itextpdf.kernel.pdf.PdfReader
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Assume.assumeTrue
import org.junit.Test
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.File

/**
 * 新版夸克水印（文档下方追加白条）的端到端用例。
 * 样本含个人文档，放在 test_pdfs/ 且不入版本控制，缺失时自动跳过。
 */
class NewWatermarkPdfTest {

    private val remover = WatermarkRemover()

    private fun sample(name: String): File {
        val root = File(System.getProperty("user.dir") ?: ".").parentFile
        val file = File(root, "test_pdfs/$name")
        assumeTrue("缺少样本: $name，跳过", file.exists())
        return file
    }

    private data class Output(
        val result: WatermarkRemover.Result,
        val width: Float,
        val height: Float,
        val content: String
    )

    private fun process(name: String): Output {
        val file = sample(name)
        val out = ByteArrayOutputStream()
        val result = file.inputStream().use { remover.removeWatermark(it, out) }
        val bytes = out.toByteArray()

        val doc = PdfDocument(PdfReader(ByteArrayInputStream(bytes)))
        val page = doc.getPage(1)
        val box = page.getMediaBox()
        val content = page.getPdfObject().getAsStream(PdfName.Contents)
            ?.let { String(it.getBytes()) } ?: ""
        val width = box.width
        val height = box.height
        doc.close()

        return Output(result, width, height, content)
    }

    private fun assertA4Portrait(o: Output) {
        assertEquals("宽度不变", 595f, o.width, 0.5f)
        assertEquals("裁到 A4 高度", 595f * PageCrop.A4_RATIO, o.height, 0.5f)
        assertEquals("比例接近 A4", 1.4142f, o.height / o.width, 0.005f)
    }

    private fun assertA4Landscape(o: Output) {
        assertEquals("宽度不变", 841f, o.width, 0.5f)
        assertEquals("裁到 A4 短边", 841f / PageCrop.A4_RATIO, o.height, 0.5f)
        assertEquals("比例接近 A4", 1.4142f, o.width / o.height, 0.005f)
    }

    @Test
    fun `竖版超高样本裁到A4`() {
        val o = process("新版_竖版超高.pdf")

        assertTrue(o.result.success)
        assertTrue(o.result.hasWatermark)
        assertA4Portrait(o)
        assertFalse("水印指令应已删除", o.content.contains("QuarkX2"))
        assertTrue("文档图应保留", o.content.contains("QuarkX1"))
        assertEquals(65.55f, o.result.croppedHeight, 0.5f)
    }

    @Test
    fun `竖版超高样本2裁到A4`() {
        val o = process("新版_竖版超高2.pdf")

        assertA4Portrait(o)
        assertFalse(o.content.contains("QuarkX2"))
        assertTrue(o.content.contains("QuarkX1"))
        assertEquals(63.55f, o.result.croppedHeight, 0.5f)
    }

    @Test
    fun `竖版A4样本只删水印不改尺寸`() {
        val o = process("新版_竖版A4.pdf")

        assertTrue(o.result.success)
        assertEquals("宽度不变", 595f, o.width, 0.5f)
        assertEquals("高度不变", 841f, o.height, 0.5f)
        assertEquals("不应裁剪", 0f, o.result.croppedHeight, 0.01f)
        assertFalse("水印指令应已删除", o.content.contains("QuarkX2"))
    }

    @Test
    fun `横版超高样本按长边裁到A4`() {
        val o = process("新版_横版超高.pdf")

        assertTrue(o.result.success)
        assertA4Landscape(o)
        assertFalse(o.content.contains("QuarkX2"))
        assertEquals(60.32f, o.result.croppedHeight, 0.5f)
    }

    @Test
    fun `横版A4样本只删水印不改尺寸`() {
        val o = process("新版_横版A4.pdf")

        assertEquals("宽度不变", 841f, o.width, 0.5f)
        assertEquals("高度不变", 595f, o.height, 0.5f)
        assertEquals("不应裁剪", 0f, o.result.croppedHeight, 0.01f)
        assertFalse("水印指令应已删除", o.content.contains("QuarkX2"))
    }
}
