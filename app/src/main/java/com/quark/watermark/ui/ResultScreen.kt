package com.quark.watermark.ui

import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.quark.watermark.ui.theme.*
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.statusBars
import androidx.compose.foundation.layout.windowInsetsPadding
import kotlinx.coroutines.launch

data class ProcessResult(
    val successCount: Int,
    val failCount: Int,
    val skipCount: Int,
    val failures: List<Pair<String, String>>,
    val files: List<FileItem> = emptyList()
)

@Composable
fun ResultScreen(
    result: ProcessResult,
    hasSavedFiles: Boolean,
    onShare: (List<Uri>, List<String>) -> Unit,
    onSave: suspend () -> List<Uri>,
    onOpenDir: () -> Unit,
    onBack: () -> Unit
) {
    var saveMessage by remember { mutableStateOf<String?>(null) }
    var isSaved by remember { mutableStateOf(false) }
    var savedUris by remember { mutableStateOf(listOf<Uri>()) }
    var isSaving by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Background)
            .windowInsetsPadding(WindowInsets.statusBars)
            .padding(start = 16.dp, end = 16.dp, top = 16.dp, bottom = 24.dp)
    ) {
        Text(
            text = "已完成",
            fontSize = 20.sp,
            fontWeight = FontWeight.Bold,
            color = TextPrimary
        )

        Spacer(modifier = Modifier.height(16.dp))

        // ── 统计卡片 ──
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(12.dp),
            colors = CardDefaults.cardColors(containerColor = CardBackground),
            border = androidx.compose.foundation.BorderStroke(1.dp, CardBorder)
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                if (result.successCount > 0) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text("✅", fontSize = 18.sp)
                        Text(
                            "${result.successCount}",
                            fontSize = 18.sp,
                            fontWeight = FontWeight.Bold,
                            color = Success
                        )
                        Text("成功", fontSize = 11.sp, color = TextSecondary)
                    }
                }
                if (result.failCount > 0) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text("❌", fontSize = 18.sp)
                        Text(
                            "${result.failCount}",
                            fontSize = 18.sp,
                            fontWeight = FontWeight.Bold,
                            color = Fail
                        )
                        Text("失败", fontSize = 11.sp, color = TextSecondary)
                    }
                }
                if (result.skipCount > 0) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text("⏭", fontSize = 18.sp)
                        Text(
                            "${result.skipCount}",
                            fontSize = 18.sp,
                            fontWeight = FontWeight.Bold,
                            color = TextSecondary
                        )
                        Text("跳过", fontSize = 11.sp, color = TextSecondary)
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        // ── 文件列表 ──
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(12.dp),
            colors = CardDefaults.cardColors(containerColor = CardBackground),
            border = androidx.compose.foundation.BorderStroke(1.dp, CardBorder)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(8.dp)
            ) {
                if (result.files.isEmpty()) {
                    Text(
                        "暂无文件",
                        fontSize = 13.sp,
                        color = TextSecondary,
                        modifier = Modifier.padding(12.dp)
                    )
                } else {
                    LazyColumn(
                        modifier = Modifier.heightIn(max = 300.dp),
                        verticalArrangement = Arrangement.spacedBy(6.dp)
                    ) {
                        itemsIndexed(result.files) { _, file ->
                            FileResultCard(file)
                        }
                    }
                }
            }
        }

        // ── 失败详情 ──
        if (result.failures.isNotEmpty()) {
            Spacer(modifier = Modifier.height(12.dp))
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(8.dp),
                colors = CardDefaults.cardColors(containerColor = Fail.copy(alpha = 0.05f))
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Text(
                        "失败详情",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        color = Fail
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    result.failures.forEach { (name, error) ->
                        Text(
                            "· $name - $error",
                            fontSize = 11.sp,
                            color = TextSecondary
                        )
                    }
                }
            }
        }

        Spacer(modifier = Modifier.weight(1f))

        // ── 保存提示 ──
        if (saveMessage != null) {
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(8.dp),
                colors = CardDefaults.cardColors(
                    containerColor = if (saveMessage!!.contains("成功") || saveMessage!!.contains("已保存"))
                        Success.copy(alpha = 0.1f)
                    else Fail.copy(alpha = 0.1f)
                )
            ) {
                Text(
                    text = saveMessage!!,
                    modifier = Modifier.padding(12.dp),
                    fontSize = 13.sp,
                    color = if (saveMessage!!.contains("成功") || saveMessage!!.contains("已保存"))
                        Success else Fail
                )
            }
            Spacer(modifier = Modifier.height(8.dp))
        }

        // ── 操作按钮 ──
        if (hasSavedFiles) {
            Button(
                onClick = {
                    if (!isSaving && !isSaved) {
                        isSaving = true
                        scope.launch {
                            val uris = onSave()
                            savedUris = uris
                            isSaved = true
                            isSaving = false
                            saveMessage = "已保存到 Downloads/夸克去水印/"
                        }
                    }
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(44.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (isSaved) Success else Primary
                ),
                shape = RoundedCornerShape(10.dp),
                enabled = !isSaving && !isSaved
            ) {
                Text(
                    when {
                        isSaving -> "保存中..."
                        isSaved -> "已保存"
                        else -> "保存到本地"
                    },
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp
                )
            }

            Spacer(modifier = Modifier.height(8.dp))

            if (isSaved) {
                OutlinedButton(
                    onClick = onOpenDir,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(44.dp),
                    shape = RoundedCornerShape(10.dp),
                    border = androidx.compose.foundation.BorderStroke(1.dp, Primary)
                ) {
                    Text("打开目录", fontSize = 14.sp, color = Primary)
                }

                Spacer(modifier = Modifier.height(8.dp))
            }

            OutlinedButton(
                onClick = {
                    if (!isSaving) {
                        if (savedUris.isEmpty()) {
                            isSaving = true
                            scope.launch {
                                val uris = onSave()
                                savedUris = uris
                                isSaved = true
                                isSaving = false
                                if (uris.isNotEmpty()) {
                                    val names = uris.map { uri ->
                                        uri.lastPathSegment?.substringAfterLast('/') ?: "file.pdf"
                                    }
                                    onShare(uris, names)
                                }
                            }
                        } else {
                            val names = savedUris.map { uri ->
                                uri.lastPathSegment?.substringAfterLast('/') ?: "file.pdf"
                            }
                            onShare(savedUris, names)
                        }
                    }
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(44.dp),
                shape = RoundedCornerShape(10.dp),
                border = androidx.compose.foundation.BorderStroke(1.dp, Primary),
                enabled = !isSaving
            ) {
                Text("分享", fontSize = 14.sp, color = Primary)
            }
        } else {
            Button(
                onClick = { saveMessage = "没有可操作的文件" },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(44.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Primary.copy(alpha = 0.5f)),
                shape = RoundedCornerShape(10.dp)
            ) {
                Text("保存到本地", fontWeight = FontWeight.Bold, fontSize = 14.sp)
            }
        }

        Spacer(modifier = Modifier.height(8.dp))

        TextButton(onClick = onBack) {
            Text("返回", fontSize = 13.sp, color = TextSecondary)
        }
    }
}

@Composable
private fun FileResultCard(file: FileItem) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(8.dp),
        colors = CardDefaults.cardColors(containerColor = CardBackground),
        border = androidx.compose.foundation.BorderStroke(1.dp, CardBorder)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 12.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = when (file.status) {
                    FileStatus.SUCCESS -> "✅"
                    FileStatus.FAIL -> "❌"
                    FileStatus.SKIPPED -> "⏭"
                    FileStatus.PROCESSING -> "⏳"
                    FileStatus.PENDING -> "📄"
                },
                fontSize = 14.sp
            )

            Spacer(modifier = Modifier.width(8.dp))

            Text(
                text = file.name,
                fontSize = 12.sp,
                color = TextPrimary,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                modifier = Modifier.weight(1f)
            )

            Text(
                text = when (file.status) {
                    FileStatus.SUCCESS -> "成功"
                    FileStatus.FAIL -> "失败"
                    FileStatus.SKIPPED -> "跳过"
                    FileStatus.PROCESSING -> "处理中"
                    FileStatus.PENDING -> "等待"
                },
                fontSize = 11.sp,
                color = when (file.status) {
                    FileStatus.SUCCESS -> Success
                    FileStatus.FAIL -> Fail
                    FileStatus.SKIPPED -> TextSecondary
                    FileStatus.PROCESSING -> Processing
                    FileStatus.PENDING -> TextSecondary
                },
                fontWeight = FontWeight.Medium
            )
        }
    }
}
