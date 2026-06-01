package com.quark.watermark.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.quark.watermark.ui.theme.Fail
import com.quark.watermark.ui.theme.Success

data class ProcessResult(
    val successCount: Int,
    val failCount: Int,
    val failures: List<Pair<String, String>> // filename to error
)

@Composable
fun ResultDialog(
    result: ProcessResult,
    onDismiss: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("处理完成") },
        text = {
            Column {
                Text(
                    text = "✅ 成功 ${result.successCount} 个",
                    color = Success,
                    style = MaterialTheme.typography.bodyLarge
                )
                if (result.failCount > 0) {
                    Text(
                        text = "❌ 失败 ${result.failCount} 个",
                        color = Fail,
                        style = MaterialTheme.typography.bodyLarge
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text("失败详情：", style = MaterialTheme.typography.bodyMedium)
                    result.failures.forEach { (name, error) ->
                        Text(
                            text = "· $name - $error",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text("确定")
            }
        }
    )
}
