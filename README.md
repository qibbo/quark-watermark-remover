# QuarkPDF 去水印 - Android 版

去除夸克扫描王 PDF 中的水印，纯本地处理，无需联网。

## 功能

- 选择 PDF 文件，一键去除水印
- 纯本地处理，不上传任何文件
- 处理后可保存或分享给其他应用

## 技术方案

- 语言：Kotlin
- PDF 库：Apache PDFBox for Android
- 核心逻辑：解析 PDF 内容流，正则匹配并移除 `QuarkX2` 水印指令

## 核心逻辑参考

`watermark_remover.py` 中的 Python 实现：

```python
# 水印命令模式：q ... /QuarkX2 Do Q
WATERMARK_PATTERN = re.compile(rb'q\s+[\d\s]+cm\s+/QuarkX2\s+Do\s+Q')

# 遍历每页的内容流，移除水印命令
for page in reader.pages:
    data = stream.get_data()
    if b'QuarkX2' in data:
        new_data = WATERMARK_PATTERN.sub(b'', data)
        stream.set_data(new_data)
```

Kotlin 实现需要：
1. 用 PDFBox 读取 PDF
2. 遍历每页的 ContentStream
3. 正则匹配 `q\s+[\d\s]+cm\s+/QuarkX2\s+Do\s+Q`
4. 移除匹配内容
5. 保存新 PDF

## 状态

规划中...
