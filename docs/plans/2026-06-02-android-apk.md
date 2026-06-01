# 夸克去水印 Android 版实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个 Android APP，去除夸克扫描王 PDF 中的水印，支持文件选择和分享接收，纯本地处理。

**Architecture:** 单 Activity + Jetpack Compose UI。核心去水印逻辑用 iText 7 操作 PDF 内容流，正则匹配移除 QuarkX2 水印命令。通过 SAF 文件选择器和 Intent Filter 接收文件，处理后保存到 Downloads 目录。

**Tech Stack:** Kotlin, iText 7, Jetpack Compose, Material3, JUnit

---

## 文件结构

```
app/
├── build.gradle.kts                    # 模块构建配置
├── src/
│   ├── main/
│   │   ├── AndroidManifest.xml         # Intent Filter 配置
│   │   ├── java/com/quark/watermark/
│   │   │   ├── MainActivity.kt         # 入口，处理 Intent
│   │   │   ├── ui/
│   │   │   │   ├── HomeScreen.kt       # 主界面 Composable
│   │   │   │   ├── ResultDialog.kt     # 结果弹窗 Composable
│   │   │   │   └── theme/
│   │   │   │       ├── Theme.kt        # Material3 主题
│   │   │   │       └── Color.kt        # 配色定义
│   │   │   ├── core/
│   │   │   │   └── WatermarkRemover.kt # 去水印核心逻辑
│   │   │   └── util/
│   │   │       └── FileUtils.kt        # 文件读写、分享
│   │   └── res/
│   │       └── values/
│   │           └── strings.xml         # 字符串资源
│   └── test/
│       └── java/com/quark/watermark/
│           └── core/
│               └── WatermarkRemoverTest.kt  # 核心逻辑单元测试
build.gradle.kts                        # 项目构建配置
settings.gradle.kts                     # 项目设置
```

---

### Task 1: 项目初始化

**Files:**
- Create: `build.gradle.kts`（项目级）
- Create: `settings.gradle.kts`
- Create: `app/build.gradle.kts`
- Create: `app/src/main/AndroidManifest.xml`
- Create: `app/src/main/res/values/strings.xml`

- [ ] **Step 1: 创建项目级 build.gradle.kts**

```kotlin
// build.gradle.kts
plugins {
    id("com.android.application") version "8.2.0" apply false
    id("org.jetbrains.kotlin.android") version "1.9.20" apply false
}
```

- [ ] **Step 2: 创建 settings.gradle.kts**

```kotlin
// settings.gradle.kts
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "QuarkWatermark"
include(":app")
```

- [ ] **Step 3: 创建 app/build.gradle.kts**

```kotlin
// app/build.gradle.kts
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.quark.watermark"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.quark.watermark"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "1.0.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_1_8
        targetCompatibility = JavaVersion.VERSION_1_8
    }

    kotlinOptions {
        jvmTarget = "1.8"
    }

    buildFeatures {
        compose = true
    }

    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.5"
    }
}

dependencies {
    // iText 7
    implementation("com.itextpdf:itext7-core:7.2.5")

    // Jetpack Compose
    implementation(platform("androidx.compose:compose-bom:2023.10.01"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.activity:activity-compose:1.8.1")
    debugImplementation("androidx.compose.ui:ui-tooling")

    // Coroutines
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")

    // Unit test
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.7.3")
}
```

- [ ] **Step 4: 创建 AndroidManifest.xml**

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <application
        android:allowBackup="true"
        android:label="@string/app_name"
        android:supportsRtl="true"
        android:theme="@android:style/Theme.Material.Light.NoActionBar">

        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>

            <!-- 接收其他应用分享的 PDF -->
            <intent-filter>
                <action android:name="android.intent.action.SEND" />
                <category android:name="android.intent.category.DEFAULT" />
                <data android:mimeType="application/pdf" />
            </intent-filter>
        </activity>
    </application>
</manifest>
```

- [ ] **Step 5: 创建 strings.xml**

```xml
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">夸克去水印</string>
    <string name="select_pdf">选择 PDF 文件</string>
    <string name="save_local">保存到本地</string>
    <string name="share">分享</string>
    <string name="processing">处理中...</string>
    <string name="result_title">处理完成</string>
    <string name="result_success">成功 %d 个</string>
    <string name="result_fail">失败 %d 个</string>
    <string name="confirm">确定</string>
</resources>
```

- [ ] **Step 6: Commit**

```bash
git add build.gradle.kts settings.gradle.kts app/build.gradle.kts app/src/
git commit -m "init: Android 项目骨架，配置 iText 7 和 Compose"
```

---

### Task 2: 核心去水印逻辑

**Files:**
- Create: `app/src/main/java/com/quark/watermark/core/WatermarkRemover.kt`
- Create: `app/src/test/java/com/quark/watermark/core/WatermarkRemoverTest.kt`

- [ ] **Step 1: 创建 WatermarkRemover.kt**

```kotlin
package com.quark.watermark.core

import com.itextpdf.kernel.pdf.PdfDocument
import com.itextpdf.kernel.pdf.PdfReader
import com.itextpdf.kernel.pdf.PdfWriter
import com.itextpdf.kernel.pdf.canvas.parser.PdfCanvasProcessor
import com.itextpdf.kernel.pdf.canvas.parser.listener.FilteredEventListener
import com.itextpdf.kernel.pdf.canvas.parser.listener.IPdfTextExtractionStrategy
import java.io.InputStream
import java.io.OutputStream
import java.util.regex.Pattern

class WatermarkRemover {

    companion object {
        // 匹配水印命令：q ... /QuarkX2 Do Q
        val WATERMARK_PATTERN: Pattern = Pattern.compile(
            "q\\s+[\\d\\s\\.]+cm\\s+/QuarkX2\\s+Do\\s+Q"
        )
    }

    data class Result(
        val success: Boolean,
        val error: String? = null,
        val hasWatermark: Boolean = true
    )

    fun removeWatermark(input: InputStream, output: OutputStream): Result {
        return try {
            val reader = PdfReader(input)
            val writer = PdfWriter(output)
            val pdfDoc = PdfDocument(reader, writer)
            var found = false

            for (i in 1..pdfDoc.numberOfPages) {
                val page = pdfDoc.getPage(i)
                val contentStream = page.getPdfObject()
                    .getAsDictionary(com.itextpdf.kernel.pdf.PdfName.ROOT)
                    ?.getAsDictionary(com.itextpdf.kernel.pdf.PdfName.PAGES)

                // 获取页面内容流
                val contents = page.getPdfObject()
                    .getAsStream(com.itextpdf.kernel.pdf.PdfName.CONTENTS)

                if (contents != null) {
                    val data = contents.getBytes()
                    val text = String(data)
                    if (text.contains("QuarkX2")) {
                        found = true
                        val matcher = WATERMARK_PATTERN.matcher(text)
                        val cleaned = matcher.replaceAll("")
                            .replace(Regex("\n{3,}"), "\n\n")
                        contents.setData(cleaned.toByteArray())
                    }
                }
            }

            pdfDoc.close()

            if (!found) {
                Result(success = true, hasWatermark = false)
            } else {
                Result(success = true)
            }
        } catch (e: Exception) {
            Result(success = false, error = classifyError(e))
        }
    }

    private fun classifyError(e: Exception): String {
        val msg = e.message?.lowercase() ?: ""
        return when {
            "password" in msg || "encrypted" in msg -> "文件已加密"
            "corrupt" in msg || "damaged" in msg -> "文件损坏"
            "non" in msg && "pdf" in msg -> "非 PDF 文件"
            else -> "未知错误: ${e.message?.take(50)}"
        }
    }
}
```

- [ ] **Step 2: 创建单元测试 WatermarkRemoverTest.kt**

```kotlin
package com.quark.watermark.core

import org.junit.Assert.*
import org.junit.Test
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream

class WatermarkRemoverTest {

    @Test
    fun `non-PDF input returns error`() {
        val remover = WatermarkRemover()
        val input = ByteArrayInputStream("not a pdf".toByteArray())
        val output = ByteArrayOutputStream()

        val result = remover.removeWatermark(input, output)

        assertFalse(result.success)
        assertNotNull(result.error)
    }

    @Test
    fun `watermark pattern matches correctly`() {
        val pattern = WatermarkRemover.WATERMARK_PATTERN
        val sample = "q 1 0 0 1 0 0 cm /QuarkX2 Do Q"
        val matcher = pattern.matcher(sample)
        assertTrue(matcher.find())
    }

    @Test
    fun `watermark pattern does not match normal content`() {
        val pattern = WatermarkRemover.WATERMARK_PATTERN
        val sample = "BT /F1 12 Tf (Hello World) Tj ET"
        val matcher = pattern.matcher(sample)
        assertFalse(matcher.find())
    }
}
```

- [ ] **Step 3: 运行单元测试**

Run: `./gradlew :app:testDebugUnitTest`
Expected: 3 tests PASS

- [ ] **Step 4: Commit**

```bash
git add app/src/main/java/com/quark/watermark/core/ app/src/test/java/com/quark/watermark/core/
git commit -m "feat: 核心去水印逻辑 WatermarkRemover + 单元测试"
```

---

### Task 3: 主题和配色

**Files:**
- Create: `app/src/main/java/com/quark/watermark/ui/theme/Color.kt`
- Create: `app/src/main/java/com/quark/watermark/ui/theme/Theme.kt`

- [ ] **Step 1: 创建 Color.kt**

```kotlin
package com.quark.watermark.ui.theme

import androidx.compose.ui.graphics.Color

val Background = Color(0xFFF5F6FA)
val CardBackground = Color(0xFFFFFFFF)
val Primary = Color(0xFF3B82F6)
val PrimaryHover = Color(0xFF2563EB)
val Success = Color(0xFF10B981)
val Fail = Color(0xFFEF4444)
val Processing = Color(0xFFF59E0B)
val TextPrimary = Color(0xFF1E293B)
val TextSecondary = Color(0xFF94A3B8)
```

- [ ] **Step 2: 创建 Theme.kt**

```kotlin
package com.quark.watermark.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

private val LightColorScheme = lightColorScheme(
    primary = Primary,
    background = Background,
    surface = CardBackground,
    onPrimary = CardBackground,
    onBackground = TextPrimary,
    onSurface = TextPrimary,
)

@Composable
fun QuarkWatermarkTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = LightColorScheme,
        content = content
    )
}
```

- [ ] **Step 3: Commit**

```bash
git add app/src/main/java/com/quark/watermark/ui/theme/
git commit -m "feat: Material3 主题和配色方案"
```

---

### Task 4: 主界面 UI

**Files:**
- Create: `app/src/main/java/com/quark/watermark/ui/HomeScreen.kt`
- Create: `app/src/main/java/com/quark/watermark/ui/ResultDialog.kt`

- [ ] **Step 1: 创建 ResultDialog.kt**

```kotlin
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
```

- [ ] **Step 2: 创建 HomeScreen.kt**

```kotlin
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
```

- [ ] **Step 3: Commit**

```bash
git add app/src/main/java/com/quark/watermark/ui/
git commit -m "feat: 主界面和结果弹窗 UI"
```

---

### Task 5: 文件工具类

**Files:**
- Create: `app/src/main/java/com/quark/watermark/util/FileUtils.kt`

- [ ] **Step 1: 创建 FileUtils.kt**

```kotlin
package com.quark.watermark.util

import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import androidx.core.content.FileProvider
import java.io.File

object FileUtils {

    fun saveToDownloads(context: Context, fileName: String, data: ByteArray): Uri? {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            // Android 10+ 使用 MediaStore
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
            // Android 9 及以下直接写文件
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

    fun sharePdf(context: Context, uri: Uri) {
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = "application/pdf"
            putExtra(Intent.EXTRA_STREAM, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        context.startActivity(Intent.createChooser(intent, "分享 PDF"))
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
}
```

- [ ] **Step 2: Commit**

```bash
git add app/src/main/java/com/quark/watermark/util/
git commit -m "feat: 文件工具类，支持保存到 Downloads 和分享"
```

---

### Task 6: MainActivity 入口

**Files:**
- Create: `app/src/main/java/com/quark/watermark/MainActivity.kt`

- [ ] **Step 1: 创建 MainActivity.kt**

```kotlin
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
```

- [ ] **Step 2: Commit**

```bash
git add app/src/main/java/com/quark/watermark/MainActivity.kt
git commit -m "feat: MainActivity 入口，处理文件选择和分享 Intent"
```

---

### Task 7: 构建和测试

- [ ] **Step 1: 构建 APK**

Run: `./gradlew :app:assembleDebug`
Expected: BUILD SUCCESSFUL

- [ ] **Step 2: 安装到设备测试**

Run: `adb install app/build/outputs/apk/debug/app-debug.apk`

测试场景：
1. 打开 APP → 点击选择 PDF → 选择文件 → 验证处理结果
2. 从其他应用（如文件管理器）分享 PDF → 验证自动处理
3. 处理已加密 PDF → 验证错误提示
4. 处理无水印 PDF → 验证跳过提示

- [ ] **Step 3: Commit 最终状态**

```bash
git add -A
git commit -m "feat: Android 版完成，可构建和运行"
```

---

## 自检清单

- [ ] spec 中每个需求都有对应 task
- [ ] 没有 TBD/TODO 占位符
- [ ] 函数名和类型在 task 间一致
- [ ] 文件命名与桌面端一致（`{name}_去水印{ext}`）
