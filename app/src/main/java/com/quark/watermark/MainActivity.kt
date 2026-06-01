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
            onFilesSelected(uris)
        }
    }

    private var onFilesSelected: (List<Uri>) -> Unit = {}

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        val shareUri = handleShareIntent(intent)

        setContent {
            QuarkWatermarkTheme {
                var files by remember { mutableStateOf(listOf<FileItem>()) }
                var isProcessing by remember { mutableStateOf(false) }
                var progress by remember { mutableStateOf(0f) }
                var result by remember { mutableStateOf<ProcessResult?>(null) }
                var savedUris by remember { mutableStateOf(listOf<Uri>()) }
                var showResult by remember { mutableStateOf(false) }
                var sortAscending by remember { mutableStateOf(true) }
                val scope = rememberCoroutineScope()

                onFilesSelected = { uris ->
                    val newFiles = uris.map { uri ->
                        val name = FileUtils.getFileNameFromUri(this@MainActivity, uri)
                        FileItem(name, FileStatus.PENDING)
                    }
                    files = files + newFiles
                    // 保存 URI 映射
                    savedUriMap.clear()
                    uris.forEachIndexed { index, uri ->
                        savedUriMap[files.size - uris.size + index] = uri
                    }
                }

                LaunchedEffect(shareUri) {
                    if (shareUri != null) {
                        onFilesSelected(listOf(shareUri))
                    }
                }

                if (showResult && result != null) {
                    ResultScreen(
                        result = result!!,
                        onSave = {
                            Toast.makeText(this@MainActivity, "已保存到 Downloads/夸克去水印/", Toast.LENGTH_SHORT).show()
                        },
                        onShare = {
                            if (savedUris.isNotEmpty()) {
                                shareFilesOneByOne(savedUris)
                            }
                        },
                        onBack = {
                            showResult = false
                            files = emptyList()
                            result = null
                            savedUris = emptyList()
                            progress = 0f
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
                                    savedUris = output.savedUris
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
                        sortAscending = sortAscending
                    )
                }
            }
        }
    }

    private val savedUriMap = mutableMapOf<Int, Uri>()

    private fun shareFilesOneByOne(uris: List<Uri>) {
        // 逐个分享，兼容微信等不支持多文件 PDF 的应用
        for (uri in uris) {
            val intent = Intent(Intent.ACTION_SEND).apply {
                type = "application/pdf"
                putExtra(Intent.EXTRA_STREAM, uri)
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            startActivity(Intent.createChooser(intent, "分享 PDF"))
        }
    }

    private fun handleShareIntent(intent: Intent?): Uri? {
        if (intent?.action == Intent.ACTION_SEND && intent.type == "application/pdf") {
            return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                intent.getParcelableExtra(Intent.EXTRA_STREAM, Uri::class.java)
            } else {
                @Suppress("DEPRECATION")
                intent.getParcelableExtra(Intent.EXTRA_STREAM)
            }
        }
        return null
    }

    private data class ProcessOutput(
        val files: List<FileItem>,
        val result: ProcessResult,
        val savedUris: List<Uri>
    )

    private suspend fun processFiles(
        files: List<FileItem>,
        onProgress: (Int, Int) -> Unit
    ): ProcessOutput {
        val fileList = files.toMutableList()
        val failures = mutableListOf<Pair<String, String>>()
        val savedUriList = mutableListOf<Uri>()
        var successCount = 0
        var failCount = 0
        var skipCount = 0
        val total = files.size

        for (i in files.indices) {
            val uri = savedUriMap[i] ?: continue
            fileList[i] = FileItem(files[i].name, FileStatus.PROCESSING)

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
                        val outName = FileUtils.getOutputFileName(files[i].name)
                        val savedUri = withContext(Dispatchers.IO) {
                            FileUtils.saveToDownloads(this@MainActivity, outName, data)
                        }
                        if (savedUri != null) {
                            fileList[i] = FileItem(files[i].name, FileStatus.SUCCESS)
                            savedUriList.add(savedUri)
                            successCount++
                        } else {
                            fileList[i] = FileItem(files[i].name, FileStatus.FAIL)
                            failures.add(files[i].name to "保存失败")
                            failCount++
                        }
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
            ProcessResult(successCount, failCount, skipCount, failures),
            savedUriList
        )
    }
}
