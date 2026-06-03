package com.quark.watermark

import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.*
import com.quark.watermark.core.WatermarkRemover
import com.quark.watermark.ui.*
import com.quark.watermark.ui.theme.QuarkWatermarkTheme
import com.quark.watermark.util.FileUtils
import com.quark.watermark.util.ImageToPdfUtil
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.ByteArrayOutputStream

class MainActivity : ComponentActivity() {

    private val remover = WatermarkRemover()

    private val filePickerLauncher = registerForActivityResult(
        ActivityResultContracts.OpenMultipleDocuments()
    ) { uris ->
        if (uris.isNotEmpty()) {
            onFilesSelected(uris, false, null)
        }
    }

    private var onFilesSelected: (List<Uri>, Boolean, List<String>?) -> Unit = { _, _, _ -> }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        setContent {
            QuarkWatermarkTheme {
                var files by remember { mutableStateOf(listOf<FileItem>()) }
                var isProcessing by remember { mutableStateOf(false) }
                var progress by remember { mutableStateOf(0f) }
                var result by remember { mutableStateOf<ProcessResult?>(null) }
                var processedData by remember { mutableStateOf(listOf<Pair<String, ByteArray>>()) }
                var showResult by remember { mutableStateOf(false) }
                var sortAscending by remember { mutableStateOf(true) }
                var isImageMode by remember { mutableStateOf(false) }
                val scope = rememberCoroutineScope()

                // 使用 rememberUpdatedState 保持回调的最新引用
                val currentOnFilesSelected by rememberUpdatedState<(List<Uri>, Boolean, List<String>?) -> Unit> { uris, fromImage, originalNames ->
                    val startIdx = files.size
                    val newFiles = uris.mapIndexed { index, uri ->
                        val name = if (originalNames != null && index < originalNames.size) {
                            originalNames[index]
                        } else {
                            FileUtils.getFileNameFromUri(this@MainActivity, uri)
                        }
                        FileItem(name, FileStatus.PENDING)
                    }
                    files = files + newFiles
                    // 保存 URI 映射
                    uris.forEachIndexed { index, uri ->
                        savedUriMap[startIdx + index] = uri
                    }
                    // 标记图片转换的文件
                    if (fromImage) {
                        isImageMode = true
                        uris.forEachIndexed { index, _ ->
                            skipWatermarkSet.add(startIdx + index)
                        }
                    }
                }

                onFilesSelected = currentOnFilesSelected

                val shareResult = remember { handleShareIntent(intent) }

                LaunchedEffect(Unit) {
                    if (shareResult != null) {
                        val isImage = shareResult.originalFileName != null
                        val names = if (isImage) listOf(shareResult.originalFileName!!) else null
                        currentOnFilesSelected(listOf(shareResult.uri), isImage, names)
                    }
                }

                if (showResult && result != null) {
                    val hasSavedFiles = processedData.isNotEmpty()
                    ResultScreen(
                        result = result!!,
                        hasSavedFiles = hasSavedFiles,
                        onShare = { uris, names ->
                            FileUtils.sharePdf(this@MainActivity, uris, names, result!!.successCount)
                        },
                        onSave = {
                            val uris = mutableListOf<Uri>()
                            for ((name, data) in processedData) {
                                // 图片转换的文件已经是 ID_Copy 格式，不需要再添加 _去水印 后缀
                                val outName = if (isImageMode && name.startsWith("ID_Copy_")) {
                                    name
                                } else {
                                    FileUtils.getOutputFileName(name)
                                }
                                val uri = withContext(Dispatchers.IO) {
                                    FileUtils.saveToDownloads(this@MainActivity, outName, data)
                                }
                                if (uri != null) uris.add(uri)
                            }
                            uris
                        },
                        onOpenDir = {
                            openDownloadsFolder()
                        },
                        onBack = {
                            showResult = false
                            files = emptyList()
                            result = null
                            processedData = emptyList()
                            progress = 0f
                            skipWatermarkSet.clear()
                            isImageMode = false
                        }
                    )
                } else {
                    HomeScreen(
                        files = files,
                        isProcessing = isProcessing,
                        progress = progress,
                        onSelectFile = {
                            filePickerLauncher.launch(arrayOf("application/pdf"))
                        },
                        onStartProcess = {
                            if (files.isNotEmpty() && !isProcessing) {
                                scope.launch {
                                    isProcessing = true
                                    val output = processFiles(files) { current, total ->
                                        progress = current.toFloat() / total
                                    }
                                    files = output.files
                                    result = output.result
                                    processedData = output.processedData
                                    isProcessing = false
                                    showResult = true
                                }
                            }
                        },
                        onClearList = {
                            if (!isProcessing) {
                                files = emptyList()
                                progress = 0f
                                savedUriMap.clear()
                                skipWatermarkSet.clear()
                                isImageMode = false
                            }
                        },
                        onRemoveFile = { index ->
                            if (!isProcessing) {
                                files = files.toMutableList().also { it.removeAt(index) }
                            }
                        },
                        onSortFiles = {
                            if (!isProcessing) {
                                val indices = files.indices.toList()
                                val sorted = if (sortAscending) {
                                    indices.sortedBy { files[it].name.lowercase() }
                                } else {
                                    indices.sortedByDescending { files[it].name.lowercase() }
                                }
                                files = sorted.map { files[it] }
                                // 同步 URI 映射
                                val newMap = mutableMapOf<Int, Uri>()
                                sorted.forEachIndexed { newIndex, oldIndex ->
                                    savedUriMap[oldIndex]?.let { newMap[newIndex] = it }
                                }
                                savedUriMap.clear()
                                savedUriMap.putAll(newMap)
                                sortAscending = !sortAscending
                            }
                        },
                        sortAscending = sortAscending,
                        isImageMode = isImageMode,
                        deviceModel = Build.MODEL ?: ""
                    )
                }
            }
        }
    }

    private val savedUriMap = mutableMapOf<Int, Uri>()
    private val skipWatermarkSet = mutableSetOf<Int>() // 图片转换的 PDF 跳过去水印

    private data class ShareResult(val uri: Uri, val originalFileName: String?)

    private fun handleShareIntent(intent: Intent?): ShareResult? {
        if (intent?.action != Intent.ACTION_SEND) return null

        val uri: Uri = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            intent.getParcelableExtra(Intent.EXTRA_STREAM, Uri::class.java)
        } else {
            @Suppress("DEPRECATION")
            intent.getParcelableExtra(Intent.EXTRA_STREAM)
        } ?: return null

        // PDF 直接返回
        if (intent.type == "application/pdf") {
            return ShareResult(uri, null)
        }

        // 图片：裁切 A4 区域 → 转 PDF → 写入临时文件
        if (intent.type?.startsWith("image/") == true) {
            val originalName = FileUtils.getFileNameFromUri(this, uri)
            val pdfUri = convertImageToPdf(uri) ?: return null
            return ShareResult(pdfUri, originalName)
        }

        return null
    }

    private fun convertImageToPdf(imageUri: Uri): Uri? {
        return try {
            val pdfData = ImageToPdfUtil.processImage(this, imageUri) ?: return null
            val timestamp = java.text.SimpleDateFormat("yyyyMMdd-HHmmss", java.util.Locale.getDefault()).format(java.util.Date())
            val tempFile = java.io.File(cacheDir, "ID_Copy_$timestamp.pdf")
            tempFile.writeBytes(pdfData)
            androidx.core.content.FileProvider.getUriForFile(
                this,
                "${packageName}.fileprovider",
                tempFile
            )
        } catch (e: Exception) {
            Toast.makeText(this, "图片转换失败: ${e.message}", Toast.LENGTH_SHORT).show()
            null
        }
    }

    private fun openDownloadsFolder() {
        try {
            // 尝试打开 Downloads/夸克去水印/ 目录
            val uri = Uri.parse("content://com.android.externalstorage.documents/document/primary%3ADownload%2F%E5%A4%B8%E5%85%8B%E5%8E%BB%E6%B0%B4%E5%8D%B0")
            val intent = Intent(Intent.ACTION_VIEW).apply {
                setDataAndType(uri, "vnd.android.document/directory")
                addCategory(Intent.CATEGORY_DEFAULT)
            }
            startActivity(intent)
        } catch (e: Exception) {
            try {
                // 备选方案：打开 Downloads 根目录
                val uri = Uri.parse("content://com.android.externalstorage.documents/document/primary%3ADownload")
                val intent = Intent(Intent.ACTION_VIEW).apply {
                    setDataAndType(uri, "vnd.android.document/directory")
                    addCategory(Intent.CATEGORY_DEFAULT)
                }
                startActivity(intent)
            } catch (e2: Exception) {
                Toast.makeText(this, "已保存到 Downloads/夸克去水印/", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private data class ProcessOutput(
        val files: List<FileItem>,
        val result: ProcessResult,
        val processedData: List<Pair<String, ByteArray>>
    )

    private suspend fun processFiles(
        files: List<FileItem>,
        onProgress: (Int, Int) -> Unit
    ): ProcessOutput {
        val fileList = files.toMutableList()
        val failures = mutableListOf<Pair<String, String>>()
        val processedDataList = mutableListOf<Pair<String, ByteArray>>()
        var successCount = 0
        var failCount = 0
        var skipCount = 0
        val total = files.size

        for (i in files.indices) {
            val uri = savedUriMap[i] ?: continue
            fileList[i] = FileItem(files[i].name, FileStatus.PROCESSING)

            // 图片转换的 PDF 跳过去水印，直接读取数据
            if (i in skipWatermarkSet) {
                val data = withContext(Dispatchers.IO) {
                    contentResolver.openInputStream(uri)?.use { it.readBytes() }
                }
                if (data != null) {
                    // 图片转换的文件使用 ID_Copy 时间戳格式作为输出文件名
                    val timestamp = java.text.SimpleDateFormat("yyyyMMdd-HHmmss", java.util.Locale.getDefault()).format(java.util.Date())
                    val pdfName = "ID_Copy_$timestamp.pdf"
                    fileList[i] = FileItem(pdfName, FileStatus.SUCCESS)
                    processedDataList.add(pdfName to data)
                    successCount++
                } else {
                    fileList[i] = FileItem(files[i].name, FileStatus.FAIL)
                    failures.add(files[i].name to "无法读取文件")
                    failCount++
                }
                onProgress(i + 1, total)
                continue
            }

            val pair = withContext(Dispatchers.IO) {
                val input = contentResolver.openInputStream(uri)
                if (input == null) {
                    null
                } else {
                    val output = ByteArrayOutputStream()
                    val r = remover.removeWatermark(input, output)
                    input.close()
                    r to output.toByteArray()
                }
            }

            if (pair == null) {
                fileList[i] = FileItem(files[i].name, FileStatus.FAIL)
                failures.add(files[i].name to "无法读取文件")
                failCount++
            } else {
                val (processResult, data) = pair
                if (processResult.success) {
                    if (!processResult.hasWatermark) {
                        fileList[i] = FileItem(files[i].name, FileStatus.SKIPPED)
                        skipCount++
                    } else {
                        fileList[i] = FileItem(files[i].name, FileStatus.SUCCESS)
                        processedDataList.add(files[i].name to data)
                        successCount++
                    }
                } else {
                    fileList[i] = FileItem(files[i].name, FileStatus.FAIL)
                    failures.add(files[i].name to (processResult.error ?: "未知错误"))
                    failCount++
                }
            }

            onProgress(i + 1, total)
        }

        return ProcessOutput(
            fileList,
            ProcessResult(successCount, failCount, skipCount, failures, fileList),
            processedDataList
        )
    }
}
