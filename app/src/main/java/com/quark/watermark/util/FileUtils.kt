package com.quark.watermark.util

import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import java.io.File
import java.io.FileOutputStream
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

object FileUtils {

    fun saveToDownloads(context: Context, fileName: String, data: ByteArray): Uri? {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val contentValues = ContentValues().apply {
                put(MediaStore.Downloads.DISPLAY_NAME, fileName)
                put(MediaStore.Downloads.MIME_TYPE, "application/pdf")
                put(MediaStore.Downloads.RELATIVE_PATH, "Download/夸克去水印")
            }
            val resolver = context.contentResolver
            val uri = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, contentValues)
            uri?.let {
                resolver.openOutputStream(it)?.use { stream ->
                    stream.write(data)
                }
            }
            uri
        } else {
            val dir = File(
                Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS),
                "夸克去水印"
            )
            if (!dir.exists()) dir.mkdirs()
            val file = File(dir, fileName)
            file.writeBytes(data)
            Uri.fromFile(file)
        }
    }

    fun getOutputFileName(inputName: String): String {
        val dotIndex = inputName.lastIndexOf('.')
        return if (dotIndex > 0) {
            "${inputName.substring(0, dotIndex)}_去水印${inputName.substring(dotIndex)}"
        } else {
            "${inputName}_去水印"
        }
    }

    fun getFileNameFromUri(context: Context, uri: Uri): String {
        var name = "document.pdf"
        context.contentResolver.query(uri, null, null, null, null)?.use { cursor ->
            val nameIndex = cursor.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME)
            if (cursor.moveToFirst() && nameIndex >= 0) {
                name = cursor.getString(nameIndex)
            }
        }
        return name
    }

    // ── 分享相关 ──────────────────────────────────────────

    /**
     * 智能分享：单文件直接分享 PDF，多文件自动打包 ZIP
     * 微信/QQ 等应用不支持多 PDF 分享，统一用 ZIP 保证兼容性
     */
    fun sharePdf(context: Context, uris: List<Uri>, fileNames: List<String> = emptyList(), count: Int = uris.size) {
        if (uris.isEmpty()) return

        if (uris.size == 1) {
            // 单文件：直接分享 PDF
            val intent = Intent(Intent.ACTION_SEND).apply {
                type = "application/pdf"
                putExtra(Intent.EXTRA_STREAM, uris.first())
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            context.startActivity(Intent.createChooser(intent, "分享 PDF"))
            return
        }

        // 多文件：打包 ZIP 分享，兼容所有应用（包括微信/QQ）
        val zipUri = createZipFromPdfs(context, uris, fileNames, count)
        if (zipUri == null) {
            // ZIP 创建失败，降级为逐个分享
            shareOneByOne(context, uris)
            return
        }

        val intent = Intent(Intent.ACTION_SEND).apply {
            type = "application/zip"
            putExtra(Intent.EXTRA_STREAM, zipUri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        context.startActivity(Intent.createChooser(intent, "分享 ZIP"))
    }

    private fun shareOneByOne(context: Context, uris: List<Uri>) {
        for (uri in uris) {
            val intent = Intent(Intent.ACTION_SEND).apply {
                type = "application/pdf"
                putExtra(Intent.EXTRA_STREAM, uri)
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            context.startActivity(Intent.createChooser(intent, "分享 PDF"))
        }
    }

    private fun createZipFromPdfs(context: Context, uris: List<Uri>, fileNames: List<String>, count: Int): Uri? {
        return try {
            val timestamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())
            val zipFileName = "去水印结果_共${count}个_${timestamp}.zip"
            val zipFile = File(context.cacheDir, zipFileName)

            ZipOutputStream(FileOutputStream(zipFile)).use { zipOut ->
                for (i in uris.indices) {
                    val name = if (i < fileNames.size) fileNames[i] else "file_${i + 1}.pdf"
                    zipOut.putNextEntry(ZipEntry(name))
                    context.contentResolver.openInputStream(uris[i])?.use { input ->
                        input.copyTo(zipOut)
                    }
                    zipOut.closeEntry()
                }
            }

            // 通过 FileProvider 分享缓存文件
            val authority = "${context.packageName}.fileprovider"
            androidx.core.content.FileProvider.getUriForFile(context, authority, zipFile)
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }
}
