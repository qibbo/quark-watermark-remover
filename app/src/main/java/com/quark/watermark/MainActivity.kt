package com.quark.watermark

import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
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

        val shareUri = handleShareIntent(intent)

        setContent {
            QuarkWatermarkTheme {
                var files by remember { mutableStateOf(listOf<FileItem>()) }
                var result by remember { mutableStateOf<ProcessResult?>(null) }
                var savedUris by remember { mutableStateOf(listOf<Uri>()) }
                val scope = rememberCoroutineScope()

                onFilesSelected = { uris ->
                    scope.launch {
                        val (newFiles, processResult, uris) = processFiles(uris)
                        files = newFiles
                        result = processResult
                        savedUris = uris
                    }
                }

                LaunchedEffect(shareUri) {
                    if (shareUri != null) {
                        onFilesSelected(listOf(shareUri))
                    }
                }

                HomeScreen(
                    files = files,
                    onSelectFile = {
                        filePickerLauncher.launch(arrayOf("application/pdf"))
                    },
                    onSave = {
                        Toast.makeText(this@MainActivity, "文件已保存到 Downloads/夸克去水印/", Toast.LENGTH_SHORT).show()
                    },
                    onShare = {
                        if (savedUris.isNotEmpty()) {
                            FileUtils.sharePdf(this@MainActivity, savedUris.first())
                        }
                    },
                    result = result,
                    onResultDismiss = { result = null }
                )
            }
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

    private suspend fun processFiles(uris: List<Uri>): ProcessOutput {
        val fileList = mutableListOf<FileItem>()
        val failures = mutableListOf<Pair<String, String>>()
        val savedUriList = mutableListOf<Uri>()
        var successCount = 0

        for (uri in uris) {
            val name = FileUtils.getFileNameFromUri(this, uri)
            fileList.add(FileItem(name, FileStatus.PROCESSING))

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
                fileList[fileList.lastIndex] = FileItem(name, FileStatus.FAIL)
                failures.add(name to "无法读取文件")
            } else {
                val (processResult, data) = pair
                if (processResult.success) {
                    val outName = FileUtils.getOutputFileName(name)
                    val savedUri = withContext(Dispatchers.IO) {
                        FileUtils.saveToDownloads(this@MainActivity, outName, data)
                    }
                    if (savedUri != null) {
                        fileList[fileList.lastIndex] = FileItem(name, FileStatus.SUCCESS)
                        savedUriList.add(savedUri)
                        successCount++
                    } else {
                        fileList[fileList.lastIndex] = FileItem(name, FileStatus.FAIL)
                        failures.add(name to "保存失败")
                    }
                } else {
                    fileList[fileList.lastIndex] = FileItem(name, FileStatus.FAIL)
                    failures.add(name to (processResult.error ?: "未知错误"))
                }
            }
        }

        return ProcessOutput(fileList, ProcessResult(successCount, failures.size, failures), savedUriList)
    }
}
