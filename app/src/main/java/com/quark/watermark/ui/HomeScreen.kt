package com.quark.watermark.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.unit.dp
import com.quark.watermark.ui.theme.*

data class FileItem(
    val name: String,
    val status: FileStatus
)

enum class FileStatus {
    PENDING, PROCESSING, SUCCESS, FAIL
}

@Composable
fun HomeScreen(
    files: List<FileItem>,
    onSelectFile: () -> Unit,
    onSave: () -> Unit,
    onShare: () -> Unit,
    result: ProcessResult?,
    onResultDismiss: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Background)
            .padding(16.dp)
    ) {
        // 标题
        Text(
            text = "夸克去水印",
            style = MaterialTheme.typography.headlineMedium,
            color = TextPrimary
        )

        Spacer(modifier = Modifier.height(24.dp))

        // 选择文件按钮
        Button(
            onClick = onSelectFile,
            modifier = Modifier.fillMaxWidth(),
            colors = ButtonDefaults.buttonColors(containerColor = Primary),
            shape = RoundedCornerShape(12.dp)
        ) {
            Text("📄 选择 PDF 文件", modifier = Modifier.padding(vertical = 8.dp))
        }

        Spacer(modifier = Modifier.height(16.dp))

        // 文件列表
        if (files.isNotEmpty()) {
            LazyColumn(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(files) { file ->
                    FileCard(file)
                }
            }
        } else {
            Box(
                modifier = Modifier.weight(1f).fillMaxWidth(),
                contentAlignment = Alignment.Center
            ) {
                Text("暂无文件", color = TextSecondary)
            }
        }

        // 底部按钮
        if (files.any { it.status == FileStatus.SUCCESS }) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                OutlinedButton(
                    onClick = onSave,
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Text("保存到本地")
                }
                Button(
                    onClick = onShare,
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.buttonColors(containerColor = Primary),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Text("分享")
                }
            }
        }
    }

    // 结果弹窗
    if (result != null) {
        ResultDialog(result = result, onDismiss = onResultDismiss)
    }
}

@Composable
fun FileCard(file: FileItem) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = CardBackground)
    ) {
        Row(
            modifier = Modifier.padding(16.dp).fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = file.name,
                style = MaterialTheme.typography.bodyMedium,
                color = TextPrimary,
                modifier = Modifier.weight(1f)
            )
            Text(
                text = when (file.status) {
                    FileStatus.PENDING -> "⏳ 等待"
                    FileStatus.PROCESSING -> "⏳ 处理中"
                    FileStatus.SUCCESS -> "✅ 完成"
                    FileStatus.FAIL -> "❌ 失败"
                },
                color = when (file.status) {
                    FileStatus.SUCCESS -> Success
                    FileStatus.FAIL -> Fail
                    FileStatus.PROCESSING -> Processing
                    else -> TextSecondary
                }
            )
        }
    }
}
