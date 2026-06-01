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
