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
