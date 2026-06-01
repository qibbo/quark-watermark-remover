import os
import json
import pytest
from config import Config


@pytest.fixture
def config_file(tmp_path):
    """返回临时配置文件路径"""
    return str(tmp_path / "config.json")


def test_config_default_values(config_file):
    """测试默认配置值"""
    config = Config(config_file)
    assert config.output_dir is None
    assert config.window_width == 600
    assert config.window_height == 500


def test_config_save_and_load(config_file):
    """测试配置保存和加载"""
    config = Config(config_file)
    config.output_dir = "/some/path"
    config.window_width = 800
    config.save()

    # 重新加载
    config2 = Config(config_file)
    assert config2.output_dir == "/some/path"
    assert config2.window_width == 800


def test_config_reset_output_dir(config_file):
    """测试重置输出目录"""
    config = Config(config_file)
    config.output_dir = "/some/path"
    config.save()

    config.reset_output_dir()
    assert config.output_dir is None

    # 验证持久化
    config2 = Config(config_file)
    assert config2.output_dir is None


def test_config_save_window_position(config_file):
    """测试保存窗口位置"""
    config = Config(config_file)
    config.window_x = 100
    config.window_y = 200
    config.save()

    config2 = Config(config_file)
    assert config2.window_x == 100
    assert config2.window_y == 200
