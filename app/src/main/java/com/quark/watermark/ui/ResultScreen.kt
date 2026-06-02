package com.quark.watermark.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.quark.watermark.ui.theme.*
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.statusBars
import androidx.compose.foundation.layout.windowInsetsPadding

data class ProcessResult(
    val successCount: Int,
    val failCount: Int,
    val skipCount: Int,
    val failures: List<Pair<String, String>>
)

@Composable
fun ResultScreen(
    result: ProcessResult,
    hasSavedFiles: Boolean,
    onShare: () -> Unit,
    onOpenDir: () -> Unit,
    onBack: () -> Unit
) {
    var saveMessage by remember { mutableStateOf<String?>(null) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Background)
            .windowInsetsPadding(WindowInsets.statusBars)
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Spacer(modifier = Modifier.height(24.dp))

        Text(
            text = "已完成",
            fontSize = 20.sp,
            fontWeight = FontWeight.Bold,
            color = TextPrimary
        )

        Spacer(modifier = Modifier.height(24.dp))

        // ── 统计卡片 ──
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(12.dp),
            colors = CardDefaults.cardColors(containerColor = CardBackground),
            border = androidx.compose.foundation.BorderStroke(1.dp, CardBorder)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                if (result.successCount > 0) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("✅", fontSize = 18.sp)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            "成功 ${result.successCount} 个",
                            fontSize = 15.sp,
                            color = Success,
                            fontWeight = FontWeight.Medium
                        )
                    }
                }
                if (result.failCount > 0) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("❌", fontSize = 18.sp)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            "失败 ${result.failCount} 个",
                            fontSize = 15.sp,
                            color = Fail,
                            fontWeight = FontWeight.Medium
                        )
                    }
                }
                if (result.skipCount > 0) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("⏭", fontSize = 18.sp)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            "跳过 ${result.skipCount} 个",
                            fontSize = 15.sp,
                            color = TextSecondary,
                            fontWeight = FontWeight.Medium
                        )
                    }
                }
            }
        }

        // ── 失败详情 ──
        if (result.failures.isNotEmpty()) {
            Spacer(modifier = Modifier.height(12.dp))
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = CardBackground),
                border = androidx.compose.foundation.BorderStroke(1.dp, CardBorder)
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp)
                ) {
                    Text(
                        "失败详情",
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Bold,
                        color = TextPrimary
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    result.failures.forEach { (name, error) ->
                        Text(
                            "· $name - $error",
                            fontSize = 12.sp,
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
                    containerColor = if (saveMessage!!.contains("成功")) Success.copy(alpha = 0.1f)
                    else Fail.copy(alpha = 0.1f)
                )
            ) {
                Text(
                    text = saveMessage!!,
                    modifier = Modifier.padding(12.dp),
                    fontSize = 13.sp,
                    color = if (saveMessage!!.contains("成功")) Success else Fail
                )
            }
            Spacer(modifier = Modifier.height(8.dp))
        }

        // ── 操作按钮 ──
        Button(
            onClick = {
                if (hasSavedFiles) {
                    onShare()
                } else {
                    saveMessage = "没有可分享的文件"
                }
            },
            modifier = Modifier
                .fillMaxWidth()
                .height(44.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = if (hasSavedFiles) Primary else Primary.copy(alpha = 0.5f)
            ),
            shape = RoundedCornerShape(10.dp)
        ) {
            Text("分享", fontWeight = FontWeight.Bold, fontSize = 14.sp)
        }

        Spacer(modifier = Modifier.height(8.dp))

        OutlinedButton(
            onClick = {
                onOpenDir()
                if (hasSavedFiles) {
                    saveMessage = "已保存到 Downloads/夸克去水印/"
                }
            },
            modifier = Modifier
                .fillMaxWidth()
                .height(44.dp),
            shape = RoundedCornerShape(10.dp),
            border = androidx.compose.foundation.BorderStroke(1.dp, if (hasSavedFiles) Primary else CardBorder)
        ) {
            Text("打开目录", fontSize = 14.sp, color = if (hasSavedFiles) Primary else TextSecondary)
        }

        Spacer(modifier = Modifier.height(8.dp))

        TextButton(onClick = onBack) {
            Text("返回", fontSize = 13.sp, color = TextSecondary)
        }

        Spacer(modifier = Modifier.height(8.dp))
    }
}
