package com.quark.watermark.util

import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import java.io.File

object FileUtils {

    fun saveToDownloads(context: Context, fileName: String, data: ByteArray): Uri? {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            // Android 10+ 使用 MediaStore
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
            // Android 9 及以下直接写文件
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

    fun sharePdf(context: Context, uri: Uri) {
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = "application/pdf"
            putExtra(Intent.EXTRA_STREAM, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        context.startActivity(Intent.createChooser(intent, "分享 PDF"))
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
}
