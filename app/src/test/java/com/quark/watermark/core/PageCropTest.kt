package com.quark.watermark.core

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Test

class PageCropTest {

    private val a4Portrait = 595f * PageCrop.A4_RATIO      // 841.45
    private val a4Landscape = 841f / PageCrop.A4_RATIO     // 594.68

    @Test
    fun `竖版超高页面裁到A4高度`() {
        val target = PageCrop.targetHeight(595f, 907f)

        assertNotNull(target)
        assertEquals(a4Portrait, target!!, 0.01f)
    }

    @Test
    fun `横版超高页面按长边算A4短边`() {
        val target = PageCrop.targetHeight(841f, 655f)

        assertNotNull(target)
        assertEquals(a4Landscape, target!!, 0.01f)
    }

    @Test
    fun `竖版A4页面不裁剪`() {
        assertNull(PageCrop.targetHeight(595f, 841f))
    }

    @Test
    fun `横版A4页面不裁剪`() {
        assertNull(PageCrop.targetHeight(841f, 595f))
    }

    @Test
    fun `比A4矮的页面不拉伸`() {
        assertNull(PageCrop.targetHeight(595f, 700f))
    }

    @Test
    fun `容差内的偏差视为A4不裁剪`() {
        // 841.45 * 1.02 = 858.3，858 仍在 2% 容差内
        assertNull(PageCrop.targetHeight(595f, 858f))
        // 860 超出 2%，需要裁剪
        assertNotNull(PageCrop.targetHeight(595f, 860f))
    }

    @Test
    fun `异常尺寸不做处理`() {
        assertNull(PageCrop.targetHeight(0f, 800f))
        assertNull(PageCrop.targetHeight(595f, 0f))
    }
}
