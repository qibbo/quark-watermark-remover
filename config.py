import json
import os


class Config:
    """配置管理类，支持 JSON 持久化"""

    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.output_dir: str = None
        self.window_width: int = 480
        self.window_height: int = 600
        self.window_x: int = None
        self.window_y: int = None
        self._load()

    def _load(self):
        """从文件加载配置"""
        if not os.path.exists(self.config_path):
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.output_dir = data.get("output_dir")
                self.window_width = data.get("window_width", self.window_width)
                self.window_height = data.get("window_height", self.window_height)
                self.window_x = data.get("window_x")
                self.window_y = data.get("window_y")
                # 确保窗口尺寸不小于最小值
                self.window_width = max(self.window_width, 480)
                self.window_height = max(self.window_height, 560)
        except (json.JSONDecodeError, IOError):
            pass

    def save(self):
        """保存配置到文件（原子写入，先写临时文件再 rename）"""
        data = {
            "output_dir": self.output_dir,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "window_x": self.window_x,
            "window_y": self.window_y,
        }
        tmp_path = self.config_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, self.config_path)

    def reset_output_dir(self):
        """重置输出目录为默认值"""
        self.output_dir = None
        self.save()
