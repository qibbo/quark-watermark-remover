# generate_ico.py - 手动构建 ICO 文件（BMP DIB 格式，兼容 Windows）
from PIL import Image
import struct
import os


def image_to_dib(img):
    """将 RGBA 图像转换为 BMP DIB 格式（BITMAPINFOHEADER + 像素数据 + AND mask）"""
    w, h = img.size
    pixels = list(img.getdata())

    # 构建像素行（从下到上，每行 4 字节对齐）
    row_size = w * 4
    padding = (4 - row_size % 4) % 4

    xor_mask = b''
    and_mask = b''

    for y in range(h - 1, -1, -1):  # BMP 从底部开始
        row = b''
        and_row = b''
        for x in range(w):
            r, g, b, a = pixels[y * w + x]
            row += struct.pack('BBBB', b, g, r, a)  # BGRA 格式
            # AND mask: 1 表示透明，0 表示不透明
            and_row_bit = 1 if a < 128 else 0
            # 每行的 AND mask 按 32 位对齐
        xor_mask += row + b'\x00' * padding

        # AND mask: 每像素 1 bit，行按 32 位（4 字节）对齐
        and_row_bits = ''
        for x in range(w):
            r, g, b, a = pixels[y * w + x]
            and_row_bits += '1' if a < 128 else '0'
        # 补齐到 32 的倍数
        while len(and_row_bits) % 32 != 0:
            and_row_bits += '0'
        # 转为字节
        and_row_bytes = b''
        for i in range(0, len(and_row_bits), 8):
            and_row_bytes += struct.pack('B', int(and_row_bits[i:i+8], 2))
        and_mask += and_row_bytes

    # BITMAPINFOHEADER (40 bytes)
    header = struct.pack('<IiiHHIIiiII',
        40,        # biSize
        w,         # biWidth
        h * 2,     # biHeight (icon: 包含 XOR 和 AND mask)
        1,         # biPlanes
        32,        # biBitCount
        0,         # biCompression (BI_RGB)
        len(xor_mask) + len(and_mask),  # biSizeImage
        0,         # biXPelsPerMeter
        0,         # biYPelsPerMeter
        0,         # biClrUsed
        0          # biClrImportant
    )

    return header + xor_mask + and_mask


def generate_ico():
    """从原始 PNG 手动构建 ICO 文件"""
    src_path = 'logo/logo.png'
    ico_path = 'logo/logo_new.ico'

    img = Image.open(src_path).convert('RGBA')
    print(f'原图: {img.size}')

    sizes = [16, 32, 48, 64, 128, 256]

    # 生成各尺寸的 DIB 数据
    dib_data_list = []
    for s in sizes:
        resized = img.resize((s, s), Image.Resampling.LANCZOS)
        dib = image_to_dib(resized)
        dib_data_list.append(dib)
        print(f'  {s}x{s}: {len(dib):,} bytes DIB')

    # ICO header
    ico = struct.pack('<HHH', 0, 1, len(sizes))

    # ICO directory entries (16 bytes each)
    data_offset = 6 + len(sizes) * 16  # header + directory
    for i, (s, dib) in enumerate(zip(sizes, dib_data_list)):
        w = s if s < 256 else 0
        h = s if s < 256 else 0
        ico += struct.pack('<BBBBHHII',
            w, h, 0, 0,      # width, height, color count, reserved
            1, 32,            # planes, bit count
            len(dib),         # size of image data
            data_offset       # offset to image data
        )
        data_offset += len(dib)

    # Append image data
    for dib in dib_data_list:
        ico += dib

    with open(ico_path, 'wb') as f:
        f.write(ico)

    print(f'\nICO 已生成: {ico_path}')
    print(f'文件大小: {os.path.getsize(ico_path):,} bytes')

    # 验证
    with open(ico_path, 'rb') as f:
        data = f.read()
    _, _, count = struct.unpack('<HHH', data[:6])
    print(f'图标数: {count}')
    for i in range(count):
        off = 6 + i * 16
        w, h, _, _, _, bpp, size, img_off = struct.unpack('<BBBBHHII', data[off:off+16])
        w = w if w != 0 else 256
        h = h if h != 0 else 256
        print(f'  [{i}] {w}x{h}, {bpp}bpp, {size:,} bytes @ offset {img_off}')


if __name__ == '__main__':
    generate_ico()
