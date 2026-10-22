package com.quark.watermark.util

import org.junit.Assert.assertEquals
import org.junit.Test

class FileUtilsTest {

    @Test
    fun `输出文件名追加_Y后缀`() {
        assertEquals("合同_Y.pdf", FileUtils.getOutputFileName("合同.pdf"))
    }

    @Test
    fun `无扩展名时直接追加后缀`() {
        assertEquals("扫描件_Y", FileUtils.getOutputFileName("扫描件"))
    }

    @Test
    fun `多点文件名只处理最后一个点`() {
        assertEquals("a.b_Y.pdf", FileUtils.getOutputFileName("a.b.pdf"))
    }
}
