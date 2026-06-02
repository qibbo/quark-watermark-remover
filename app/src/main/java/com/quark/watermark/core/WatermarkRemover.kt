package com.quark.watermark.core

import com.itextpdf.kernel.pdf.PdfDocument
import com.itextpdf.kernel.pdf.PdfReader
import com.itextpdf.kernel.pdf.PdfWriter
import com.itextpdf.kernel.pdf.PdfName
import java.io.InputStream
import java.io.OutputStream
import java.util.regex.Pattern

class WatermarkRemover {

    companion object {
        // 匹配水印命令：q ... /QuarkX2 Do Q
        val WATERMARK_PATTERN: Pattern = Pattern.compile(
            "q\\s+[\\d\\s\\.]+cm\\s+/QuarkX2\\s+Do\\s+Q"
        )
    }

    data class Result(
        val success: Boolean,
        val error: String? = null,
        val hasWatermark: Boolean = true
    )

    fun removeWatermark(input: InputStream, output: OutputStream): Result {
        return try {
            val reader = PdfReader(input)
            val writer = PdfWriter(output)
            val pdfDoc = PdfDocument(reader, writer)
            var found = false

            for (i in 1..pdfDoc.numberOfPages) {
                val page = pdfDoc.getPage(i)

                // 获取页面内容流
                val contents = page.getPdfObject()
                    .getAsStream(PdfName("Contents"))

                if (contents != null) {
                    val data = contents.getBytes()
                    val text = String(data)
                    if (text.contains("QuarkX2")) {
                        found = true
                        val matcher = WATERMARK_PATTERN.matcher(text)
                        val cleaned = matcher.replaceAll("")
                            .replace(Regex("\n{3,}"), "\n\n")
                        contents.setData(cleaned.toByteArray())
                    }
                }
            }

            pdfDoc.close()

            if (!found) {
                Result(success = true, hasWatermark = false)
            } else {
                Result(success = true)
            }
        } catch (e: Exception) {
            Result(success = false, error = classifyError(e))
        }
    }

    private fun classifyError(e: Exception): String {
        val msg = e.message?.lowercase() ?: ""
        return when {
            "password" in msg || "encrypted" in msg || "加密" in msg -> "文件已加密"
            "space" in msg || "disk" in msg || "空间" in msg -> "磁盘空间不足"
            "corrupt" in msg || "broken" in msg || "damaged" in msg || "损坏" in msg || "cannot open" in msg -> "文件损坏"
            "no pages" in msg || "page_count" in msg || "无内容" in msg -> "PDF无内容"
            "path" in msg || "name too long" in msg || "路径过长" in msg -> "路径过长"
            else -> "未知错误: ${e.message?.take(50)}"
        }
    }
}
