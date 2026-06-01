package com.quark.watermark

import android.content.Intent
import android.net.Uri
import android.os.Bundle
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
    private var pendingShareUri: Uri? = null

    private val filePickerLauncher = registerForActivityResult(
        ActivityResultContracts.OpenMultipleDocuments()
    ) { uris ->
        if (uris.isNotEmpty()) {
            processFiles(uris)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // 处理从其他应用分享进来的 PDF
        val shareUri = handleShareIntent(intent)

        setContent {
            QuarkWatermarkTheme {
                var files by remember { mutableStateOf(listOf<FileItem>()) }
                var result by remember { mutableStateOf<ProcessResult?>(null) }
                val scope = rememberCoroutineScope()

                // 如果从分享进入，自动处理
                LaunchedEffect(shareUri) {
                    if (shareUri != null) {
                        processFiles(listOf(shareUri))
                    }
                }

                HomeScreen(
                    files = files,
                    onSelectFile = {
                        filePickerLauncher.launch(arrayOf("application/pdf"))
                    },
                    onSave = { saveFiles() },
                    onShare = { shareFiles() },
                    result = result,
                    onResultDismiss = { result = null }
                )
            }
        }
    }

    private fun handleShareIntent(intent: Intent?): Uri? {
        if (intent?.action == Intent.ACTION_SEND && intent.type == "application/pdf") {
            return intent.getParcelableExtra(Intent.EXTRA_STREAM)
        }
        return null
    }

    private fun processFiles(uris: List<Uri>) {
        val scope = kotlinx.coroutines.CoroutineScope(Dispatchers.Main)
        scope.launch {
            val fileList = mutableListOf<FileItem>()
            val failures = mutableListOf<Pair<String, String>>()
            var successCount = 0

            for (uri in uris) {
                val name = FileUtils.getFileNameFromUri(this@MainActivity, uri)
                fileList.add(FileItem(name, FileStatus.PROCESSING))

                val result = withContext(Dispatchers.IO) {
                    val input = contentResolver.openInputStream(uri) ?: return@withContext
                    val output = ByteArrayOutputStream()
                    val r = remover.removeWatermark(input, output)
                    input.close()
                    r to output.toByteArray()
                }

                val (processResult, data) = result
                if (processResult.success) {
                    val outName = FileUtils.getOutputFileName(name)
                    val savedUri = withContext(Dispatchers.IO) {
                        FileUtils.saveToDownloads(this@MainActivity, outName, data)
                    }
                    if (savedUri != null) {
                        fileList[fileList.lastIndex] = FileItem(name, FileStatus.SUCCESS)
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

            files = fileList
            result = ProcessResult(successCount, failures.size, failures)
        }
    }

    private fun saveFiles() {
        // 文件已保存到 Downloads，提示用户
    }

    private fun shareFiles() {
        // 分享第一个成功的文件
    }
}
