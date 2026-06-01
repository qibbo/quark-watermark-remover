package com.quark.watermark.util

import android.content.ComponentName
import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.content.pm.ResolveInfo
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

    data class ShareApp(
        val label: String,
        val packageName: String,
        val componentName: ComponentName,
        val supportsMultiple: Boolean
    )

    /**
     * 智能分享：单文件直接分享，多文件优先多文件分享，不支持的自动打包 ZIP
     */
    fun sharePdf(context: Context, uris: List<Uri>, fileNames: List<String> = emptyList()) {
        if (uris.isEmpty()) return

        if (uris.size == 1) {
            // 单文件：直接分享
            val intent = Intent(Intent.ACTION_SEND).apply {
                type = "application/pdf"
                putExtra(Intent.EXTRA_STREAM, uris.first())
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            context.startActivity(Intent.createChooser(intent, "分享 PDF"))
            return
        }

        // 多文件：查询支持情况
        val multiApps = queryApps(context, Intent.ACTION_SEND_MULTIPLE, "application/pdf")
        val singleApps = queryApps(context, Intent.ACTION_SEND, "application/pdf")

        // 仅支持单文件的 App（需要打包 ZIP）
        val singleOnlyApps = singleApps.filter { single ->
            multiApps.none { multi ->
                multi.packageName == single.packageName
            }
        }

        if (singleOnlyApps.isEmpty()) {
            // 所有 App 都支持多文件，直接分享
            shareMultiplePdfs(context, uris)
            return
        }

        // 有不支持多文件的 App，创建 ZIP 用于降级分享
        val zipUri = createZipFromPdfs(context, uris, fileNames)
        if (zipUri == null) {
            // ZIP 创建失败，降级为逐个分享
            shareOneByOne(context, uris)
            return
        }

        // 构建自定义分享面板 Intent
        val targetIntents = mutableListOf<Intent>()

        // 多文件分享的 App
        for (app in multiApps) {
            val intent = Intent(Intent.ACTION_SEND_MULTIPLE).apply {
                type = "application/pdf"
                putParcelableArrayListExtra(Intent.EXTRA_STREAM, ArrayList(uris))
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                component = app.componentName
            }
            targetIntents.add(intent)
        }

        // 仅支持单文件的 App → 分享 ZIP
        for (app in singleOnlyApps) {
            val intent = Intent(Intent.ACTION_SEND).apply {
                type = "application/zip"
                putExtra(Intent.EXTRA_STREAM, zipUri)
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                component = app.componentName
            }
            targetIntents.add(intent)
        }

        if (targetIntents.isEmpty()) {
            // 没有可用 App，用系统默认 chooser
            shareMultiplePdfs(context, uris)
            return
        }

        // 使用第一个 Intent 作为 chooser 基础，其余作为替代
        val chooserIntent = Intent.createChooser(targetIntents.removeAt(0), "分享 PDF")
        chooserIntent.putExtra(Intent.EXTRA_INITIAL_INTENTS, targetIntents.toTypedArray())
        context.startActivity(chooserIntent)
    }

    private fun shareMultiplePdfs(context: Context, uris: List<Uri>) {
        val intent = Intent(Intent.ACTION_SEND_MULTIPLE).apply {
            type = "application/pdf"
            putParcelableArrayListExtra(Intent.EXTRA_STREAM, ArrayList(uris))
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        context.startActivity(Intent.createChooser(intent, "分享 PDF"))
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

    private fun queryApps(context: Context, action: String, mimeType: String): List<ShareApp> {
        val intent = Intent(action).apply { type = mimeType }
        val flags = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            PackageManager.MATCH_ALL
        } else {
            0
        }
        val apps = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            context.packageManager.queryIntentActivities(intent, PackageManager.ResolveInfoFlags.of(flags.toLong()))
        } else {
            @Suppress("DEPRECATION")
            context.packageManager.queryIntentActivities(intent, flags)
        }

        return apps
            .filter { it.activityInfo.packageName != context.packageName }
            .map { info ->
                ShareApp(
                    label = info.loadLabel(context.packageManager).toString(),
                    packageName = info.activityInfo.packageName,
                    componentName = ComponentName(info.activityInfo.packageName, info.activityInfo.name),
                    supportsMultiple = action == Intent.ACTION_SEND_MULTIPLE
                )
            }
    }

    private fun createZipFromPdfs(context: Context, uris: List<Uri>, fileNames: List<String>): Uri? {
        return try {
            val timestamp = SimpleDateFormat("yyyyMMdd_HHmm", Locale.getDefault()).format(Date())
            val zipFileName = "去水印结果_${timestamp}.zip"
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
