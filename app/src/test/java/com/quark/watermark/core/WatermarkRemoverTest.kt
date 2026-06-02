package com.quark.watermark.core

import org.junit.Assert.*
import org.junit.Test
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.File

class WatermarkRemoverTest {

    private val remover = WatermarkRemover()

    // ── 基础测试 ──

    @Test
    fun `non-PDF input returns error`() {
        val input = ByteArrayInputStream("not a pdf".toByteArray())
        val output = ByteArrayOutputStream()

        val result = remover.removeWatermark(input, output)

        assertFalse(result.success)
        assertNotNull(result.error)
    }

    @Test
    fun `watermark pattern matches correctly`() {
        val pattern = WatermarkRemover.WATERMARK_PATTERN
        val sample = "q 1 0 0 1 0 0 cm /QuarkX2 Do Q"
        val matcher = pattern.matcher(sample)
        assertTrue(matcher.find())
    }

    @Test
    fun `watermark pattern does not match normal content`() {
        val pattern = WatermarkRemover.WATERMARK_PATTERN
        val sample = "BT /F1 12 Tf (Hello World) Tj ET"
        val matcher = pattern.matcher(sample)
        assertFalse(matcher.find())
    }

    // ── 测试文件验证 ──

    private fun getTestFile(name: String): File {
        // 从项目根目录查找测试文件
        val projectDir = File(System.getProperty("user.dir")).parentFile
        val file = File(projectDir, "test_pdfs/$name")
        assertTrue("测试文件不存在: ${file.absolutePath ?: "unknown"}", file.exists())
        return file
    }

    private fun processFile(file: File): WatermarkRemover.Result {
        val input = file.inputStream()
        val output = ByteArrayOutputStream()
        val result = remover.removeWatermark(input, output)
        input.close()
        return result
    }

    @Test
    fun `带水印PDF应成功处理`() {
        val result = processFile(getTestFile("正常_带水印.pdf"))
        assertTrue("应该成功", result.success)
        assertTrue("应该检测到水印", result.hasWatermark)
    }

    @Test
    fun `无水印PDF应提示跳过`() {
        val result = processFile(getTestFile("正常_无水印.pdf"))
        assertTrue("应该成功", result.success)
        assertFalse("不应有水印", result.hasWatermark)
    }

    @Test
    fun `损坏PDF应返回错误`() {
        val result = processFile(getTestFile("损坏_截断.pdf"))
        assertFalse("损坏文件应失败", result.success)
        assertNotNull("应有错误信息", result.error)
    }

    @Test
    fun `非PDF文件应返回错误`() {
        val result = processFile(getTestFile("非PDF文件.pdf"))
        assertFalse("非PDF应失败", result.success)
        assertNotNull("应有错误信息", result.error)
    }

    @Test
    fun `空文件应返回错误`() {
        val result = processFile(getTestFile("空文件.pdf"))
        assertFalse("空文件应失败", result.success)
        assertNotNull("应有错误信息", result.error)
    }

    @Test
    fun `加密PDF应返回错误`() {
        val result = processFile(getTestFile("加密_需要密码.pdf"))
        assertFalse("加密文件应失败", result.success)
        assertNotNull("应有错误信息", result.error)
        assertTrue("应提示加密", result.error!!.contains("加密"))
    }

    @Test
    fun `多页PDF应成功处理`() {
        val result = processFile(getTestFile("多页_带水印.pdf"))
        assertTrue("应该成功", result.success)
        assertTrue("应该检测到水印", result.hasWatermark)
    }
}
