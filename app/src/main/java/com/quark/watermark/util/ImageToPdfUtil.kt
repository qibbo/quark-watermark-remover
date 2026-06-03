package com.quark.watermark.util

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.pdf.PdfDocument
import android.net.Uri
import android.os.Build
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import kotlin.math.sqrt

object ImageToPdfUtil {

    private const val CONFIG_FILE = "crop_config.json"
    private val A4_RATIO = sqrt(2.0).toFloat()

    data class CropConfig(val left: Int, val top: Int, val width: Int, val height: Int)

    private var cachedConfig: CropConfig? = null

    /**
     * 从 assets/crop_config.json 读取裁切配置
     * 优先匹配设备型号，找不到则用默认值
     */
    private fun loadConfig(context: Context): CropConfig {
        cachedConfig?.let { return it }

        return try {
            val json = context.assets.open(CONFIG_FILE).bufferedReader().use { it.readText() }
            val obj = JSONObject(json)
            val model = Build.MODEL ?: "unknown"

            // 尝试匹配设备型号
            val devices = obj.optJSONObject("devices")
            var deviceConfig: JSONObject? = null
            if (devices != null) {
                val keys = devices.keys()
                while (keys.hasNext()) {
                    val key = keys.next()
                    if (!key.startsWith("_") && key.equals(model, ignoreCase = true)) {
                        deviceConfig = devices.getJSONObject(key)
                        break
                    }
                }
            }

            val config = if (deviceConfig != null) {
                CropConfig(
                    left = deviceConfig.getInt("left"),
                    top = deviceConfig.getInt("top"),
                    width = deviceConfig.getInt("width"),
                    height = deviceConfig.getInt("height")
                )
            } else {
                // 使用默认值
                val default = obj.getJSONObject("default")
                CropConfig(
                    left = default.getInt("left"),
                    top = default.getInt("top"),
                    width = default.getInt("width"),
                    height = default.getInt("height")
                )
            }

            cachedConfig = config
            config
        } catch (e: Exception) {
            // 配置文件读取失败，使用硬编码默认值
            CropConfig(60, 300, 960, (960 * A4_RATIO).toInt())
        }
    }

    fun loadBitmap(context: Context, uri: Uri): Bitmap? {
        return try {
            context.contentResolver.openInputStream(uri)?.use {
                BitmapFactory.decodeStream(it)
            }
        } catch (e: Exception) {
            null
        }
    }

    fun cropA4Region(bitmap: Bitmap, context: Context): Bitmap {
        val config = loadConfig(context)

        val safeLeft = config.left.coerceAtMost(bitmap.width - 1)
        val safeTop = config.top.coerceAtMost(bitmap.height - 1)
        val safeWidth = config.width.coerceAtMost(bitmap.width - safeLeft)
        val safeHeight = config.height.coerceAtMost(bitmap.height - safeTop)

        return Bitmap.createBitmap(bitmap, safeLeft, safeTop, safeWidth, safeHeight)
    }

    fun bitmapToPdf(bitmap: Bitmap): ByteArray {
        val document = PdfDocument()

        val pageWidth = 595
        val pageHeight = 842
        val pageInfo = PdfDocument.PageInfo.Builder(pageWidth, pageHeight, 1).create()
        val page = document.startPage(pageInfo)

        val canvas = page.canvas
        val scaleX = pageWidth.toFloat() / bitmap.width
        val scaleY = pageHeight.toFloat() / bitmap.height
        val scale = minOf(scaleX, scaleY)

        val left = (pageWidth - bitmap.width * scale) / 2
        val top = (pageHeight - bitmap.height * scale) / 2

        canvas.save()
        canvas.translate(left, top)
        canvas.scale(scale, scale)
        canvas.drawBitmap(bitmap, 0f, 0f, null)
        canvas.restore()

        document.finishPage(page)

        val output = ByteArrayOutputStream()
        document.writeTo(output)
        document.close()

        return output.toByteArray()
    }

    fun processImage(context: Context, uri: Uri): ByteArray? {
        val bitmap = loadBitmap(context, uri) ?: return null
        val cropped = cropA4Region(bitmap, context)
        val pdfData = bitmapToPdf(cropped)

        if (cropped !== bitmap) bitmap.recycle()
        cropped.recycle()

        return pdfData
    }
}
