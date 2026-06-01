import time
from watermark_remover import remove_watermark, WatermarkNotFoundError, NotPdfFileError

async def process_pdf(input_path: str, output_path: str) -> dict:
    """处理 PDF 文件"""
    start_time = time.time()

    try:
        remove_watermark(input_path, output_path)
        cost = time.time() - start_time
        return {
            "success": True,
            "cost": round(cost, 2),
            "error": None
        }
    except WatermarkNotFoundError:
        cost = time.time() - start_time
        return {
            "success": True,  # 即使没有水印也返回成功
            "cost": round(cost, 2),
            "error": None
        }
    except NotPdfFileError:
        return {
            "success": False,
            "cost": 0,
            "error": "请发送 PDF 文件"
        }
    except Exception as e:
        return {
            "success": False,
            "cost": 0,
            "error": f"处理失败: {str(e)}"
        }
