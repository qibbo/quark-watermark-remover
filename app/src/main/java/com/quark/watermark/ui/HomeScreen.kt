package com.quark.watermark.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.quark.watermark.ui.theme.*

data class FileItem(
    val name: String,
    val status: FileStatus
)

enum class FileStatus {
    PENDING, PROCESSING, SUCCESS, FAIL, SKIPPED
}

@Composable
fun HomeScreen(
    files: List<FileItem>,
    isProcessing: Boolean,
    progress: Float,
    onSelectFile: () -> Unit,
    onStartProcess: () -> Unit,
    onClearList: () -> Unit,
    onRemoveFile: (Int) -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Background)
            .padding(16.dp)
    ) {
        // ── 标题 ──
        Text(
            text = "夸克去水印",
            fontSize = 20.sp,
            fontWeight = FontWeight.Bold,
            color = TextPrimary
        )

        Spacer(modifier = Modifier.height(16.dp))

        // ── 选择文件区 ──
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .clickable(enabled = !isProcessing) { onSelectFile() },
            shape = RoundedCornerShape(10.dp),
            colors = CardDefaults.cardColors(containerColor = DropZoneBg),
            border = androidx.compose.foundation.BorderStroke(1.dp, DropBorder)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 20.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text("📄", fontSize = 28.sp)
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    "点击选择 PDF 文件",
                    fontSize = 13.sp,
                    color = TextSecondary
                )
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        // ── 文件列表标题 ──
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = if (files.isEmpty()) "文件列表" else "文件列表（${files.size}）",
                fontSize = 13.sp,
                fontWeight = FontWeight.Bold,
                color = TextPrimary
            )
        }

        Spacer(modifier = Modifier.height(4.dp))

        // ── 文件列表 ──
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f),
            shape = RoundedCornerShape(12.dp),
            colors = CardDefaults.cardColors(containerColor = CardBackground),
            border = androidx.compose.foundation.BorderStroke(1.dp, CardBorder)
        ) {
            if (files.isEmpty()) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        "暂无文件，请点击上方选择 PDF",
                        fontSize = 12.sp,
                        color = TextSecondary
                    )
                }
            } else {
                LazyColumn(
                    modifier = Modifier.padding(4.dp),
                    verticalArrangement = Arrangement.spacedBy(2.dp)
                ) {
                    itemsIndexed(files) { index, file ->
                        FileCard(
                            file = file,
                            onRemove = if (!isProcessing) { { onRemoveFile(index) } } else null
                        )
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        // ── 进度条 ──
        Column {
            LinearProgressIndicator(
                progress = progress,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(8.dp)
                    .clip(RoundedCornerShape(4.dp)),
                color = Primary,
                trackColor = ProgressBg,
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = when {
                    isProcessing -> "处理中 ${(progress * files.size).toInt()}/${files.size}"
                    progress >= 1f -> "完成"
                    else -> "就绪"
                },
                fontSize = 12.sp,
                color = TextSecondary,
                modifier = Modifier.fillMaxWidth(),
                textAlign = androidx.compose.ui.text.style.TextAlign.End
            )
        }

        Spacer(modifier = Modifier.height(12.dp))

        // ── 操作按钮 ──
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Button(
                onClick = onStartProcess,
                modifier = Modifier
                    .weight(1f)
                    .height(44.dp),
                enabled = files.isNotEmpty() && !isProcessing,
                colors = ButtonDefaults.buttonColors(
                    containerColor = Primary,
                    disabledContainerColor = Primary.copy(alpha = 0.5f)
                ),
                shape = RoundedCornerShape(10.dp)
            ) {
                Text("开始去水印", fontWeight = FontWeight.Bold, fontSize = 14.sp)
            }
            OutlinedButton(
                onClick = onClearList,
                modifier = Modifier.height(44.dp),
                enabled = files.isNotEmpty() && !isProcessing,
                shape = RoundedCornerShape(10.dp),
                border = androidx.compose.foundation.BorderStroke(1.dp, CardBorder)
            ) {
                Text("清空列表", fontSize = 13.sp, color = TextPrimary)
            }
        }
    }

}

@Composable
fun FileCard(file: FileItem, onRemove: (() -> Unit)?) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(6.dp),
        colors = CardDefaults.cardColors(containerColor = DropZoneBg),
        border = androidx.compose.foundation.BorderStroke(1.dp, CardBorder)
    ) {
        Row(
            modifier = Modifier
                .padding(horizontal = 8.dp, vertical = 6.dp)
                .fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
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
                    FileStatus.PENDING -> "待处理"
                    FileStatus.PROCESSING -> "处理中"
                    FileStatus.SUCCESS -> "完成"
                    FileStatus.FAIL -> "失败"
                    FileStatus.SKIPPED -> "无水印，跳过"
                },
                fontSize = 11.sp,
                color = when (file.status) {
                    FileStatus.SUCCESS -> Success
                    FileStatus.FAIL -> Fail
                    FileStatus.PROCESSING -> Processing
                    FileStatus.SKIPPED -> TextSecondary
                    else -> TextSecondary
                },
                modifier = Modifier.padding(horizontal = 4.dp)
            )

            if (onRemove != null) {
                Text(
                    text = "✕",
                    fontSize = 11.sp,
                    color = TextSecondary,
                    modifier = Modifier
                        .clickable { onRemove() }
                        .padding(4.dp)
                )
            }
        }
    }
}
