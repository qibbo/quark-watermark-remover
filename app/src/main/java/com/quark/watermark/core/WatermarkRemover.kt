package com.quark.watermark.core

import com.itextpdf.kernel.geom.Rectangle
import com.itextpdf.kernel.pdf.PdfDocument
import com.itextpdf.kernel.pdf.PdfName
import com.itextpdf.kernel.pdf.PdfPage
import com.itextpdf.kernel.pdf.PdfReader
import com.itextpdf.kernel.pdf.PdfStream
import com.itextpdf.kernel.pdf.PdfWriter
import java.io.InputStream
import java.io.OutputStream
import java.util.regex.Pattern

class WatermarkRemover {

    companion object {
        const val WATERMARK_NAME = "QuarkX2"

        // 匹配水印绘制指令：q ... cm /QuarkX2 Do Q
        val WATERMARK_PATTERN: Pattern = Pattern.compile(
            "q\\s+[-\\d.\\s]+cm\\s+/$WATERMARK_NAME\\s+Do\\s+Q"
        )
    }

    data class Result(
        val success: Boolean,
        val error: String? = null,
        val hasWatermark: Boolean = true,
        /** 被裁掉的页面总高度（pt），0 表示页面尺寸未变 */
        val croppedHeight: Float = 0f
    )

    fun removeWatermark(input: InputStream, output: OutputStream): Result {
        return try {
            val reader = PdfReader(input)
            val writer = PdfWriter(output)
            val pdfDoc = PdfDocument(reader, writer)
            var found = false
            var croppedTotal = 0f

            for (i in 1..pdfDoc.numberOfPages) {
                val page = pdfDoc.getPage(i)
                val streams = contentStreams(page)
                if (streams.isEmpty()) continue

                // 用原始内容流判断是否为夸克水印页
                val texts = streams.map { String(it.getBytes()) }
                if (texts.none { it.contains(WATERMARK_NAME) }) continue
                found = true

                // 1. 删除水印绘制指令
                for (stream in streams) {
                    val text = String(stream.getBytes())
                    if (!text.contains(WATERMARK_NAME)) continue
                    val cleaned = WATERMARK_PATTERN.matcher(text)
                        .replaceAll("")
                        .replace(Regex("\n{3,}"), "\n\n")
                    stream.setData(cleaned.toByteArray())
                }

                // 2. 新版夸克会在文档下方追加白条放水印，导致页面比 A4 高，
                //    这里以页面顶边为锚点保留 A4 高度，裁掉底部多余部分
                val box = page.getMediaBox()
                val targetHeight = PageCrop.targetHeight(box.width, box.height)
                if (targetHeight != null) {
                    val newBox = Rectangle(
                        box.left,
                        box.bottom + (box.height - targetHeight),
                        box.width,
                        targetHeight
                    )
                    page.setMediaBox(newBox)
                    page.setCropBox(newBox)
                    croppedTotal += box.height - targetHeight
                }
            }

            pdfDoc.close()

            if (!found) {
                Result(success = true, hasWatermark = false)
            } else {
                Result(success = true, croppedHeight = croppedTotal)
            }
        } catch (e: Exception) {
            Result(success = false, error = classifyError(e))
        }
    }

    /**
     * 取页面的内容流。Contents 可能是单个流，也可能是流数组
     * （被多次追加写入过的 PDF 常见），两种都要处理。
     */
    private fun contentStreams(page: PdfPage): List<PdfStream> {
        val pageDict = page.getPdfObject()
        val array = pageDict.getAsArray(PdfName.Contents)
        if (array != null) {
            return (0 until array.size()).mapNotNull { array.getAsStream(it) }
        }
        val single = pageDict.getAsStream(PdfName.Contents)
        return if (single != null) listOf(single) else emptyList()
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

/**
 * 页面尺寸裁剪计算，与 PDF 解析解耦，便于单测。
 *
 * 夸克新版导出的页面：宽度固定为 A4 宽（竖版 595 / 横版 841），
 * 下方追加一条白条放置水印，因此页面高度可能大于标准 A4。
 * 规则：以页面顶边为锚点，保留 A4 高度，裁掉底部多余部分。
 */
internal object PageCrop {

    /** A4 长边与短边之比 */
    const val A4_RATIO = 1.4142f

    /** 与 A4 高度偏差在此比例内视为"A4 页面"，不做裁剪 */
    const val TOLERANCE = 0.02f

    /**
     * 目标页面高度。横版（宽 > 高）用长边算短边，竖版用宽算长边。
     * @return null 表示不需要裁剪（已是 A4，或页面比 A4 矮）
     */
    fun targetHeight(width: Float, height: Float): Float? {
        if (width <= 0f || height <= 0f) return null

        val a4 = if (width > height) width / A4_RATIO else width * A4_RATIO
        val diff = height - a4

        // 本来就是 A4，不裁
        if (Math.abs(diff) / a4 <= TOLERANCE) return null
        // 比 A4 矮，不拉伸
        if (diff <= 0f) return null

        return a4
    }
}
