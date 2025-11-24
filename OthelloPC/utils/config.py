#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Module for STM32 Othello PC Client
配置模块

@author: STM32 Othello Project Team
@version: 1.0
@date: 2025-11-22
"""

import json
import os
from typing import Any, Dict
import logging

class Config:
    """配置管理器"""

    def __init__(self, config_file: str = 'config.json'):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config_data: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)

        # 默认配置
        self.default_config = {
            # 串口设置
            'serial': {
                'baud_rate': 115200,
                'timeout': 1.0,
                'auto_connect': True,
                'preferred_port': None
            },

            # DeepSeek API设置
            'deepseek': {
                'api_key': '',
                'base_url': 'https://api.deepseek.com',
                'model': 'deepseek-chat',
                'temperature': 0.1,
                'max_tokens': 2000
            },

            # 界面设置
            'ui': {
                'window_width': 1200,
                'window_height': 800,
                'auto_save': True,
                'language': 'zh',
                'theme': 'dieter_rams'
            },

            # 游戏设置
            'game': {
                'show_valid_moves': True,
                'enable_sound': False,
                'auto_analysis': False,
                'save_pgn': True
            },

            # 日志设置
            'logging': {
                'level': 'INFO',
                'max_files': 5,
                'max_file_size': 10485760  # 10MB
            }
        }

        self.load()

    def load(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)

                # 合并默认配置和加载的配置
                self.config_data = self._merge_configs(self.default_config, loaded_config)
                self.logger.info(f"配置已从 {self.config_file} 加载")
            else:
                self.config_data = self.default_config.copy()
                self.save()  # 创建默认配置文件
                self.logger.info("使用默认配置并创建配置文件")

        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            self.config_data = self.default_config.copy()

    def save(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"配置已保存到 {self.config_file}")
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持点分隔的嵌套键如 'serial.baud_rate'
            default: 默认值

        Returns:
            配置值
        """
        try:
            keys = key.split('.')
            value = self.config_data

            for k in keys:
                value = value[k]

            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any):
        """
        设置配置值

        Args:
            key: 配置键，支持点分隔的嵌套键
            value: 配置值
        """
        try:
            keys = key.split('.')
            config = self.config_data

            # 导航到嵌套字典
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]

            # 设置值
            config[keys[-1]] = value

        except Exception as e:
            self.logger.error(f"设置配置失败: {e}")

    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """
        合并配置字典

        Args:
            default: 默认配置
            loaded: 加载的配置

        Returns:
            合并后的配置
        """
        merged = default.copy()

        for key, value in loaded.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value

        return merged

    # 便捷属性访问
    @property
    def serial_baud_rate(self) -> int:
        return self.get('serial.baud_rate', 115200)

    @serial_baud_rate.setter
    def serial_baud_rate(self, value: int):
        self.set('serial.baud_rate', value)

    @property
    def serial_auto_connect(self) -> bool:
        return self.get('serial.auto_connect', True)

    @serial_auto_connect.setter
    def serial_auto_connect(self, value: bool):
        self.set('serial.auto_connect', value)

    @property
    def serial_preferred_port(self) -> str:
        return self.get('serial.preferred_port', '')

    @serial_preferred_port.setter
    def serial_preferred_port(self, value: str):
        self.set('serial.preferred_port', value)

    @property
    def deepseek_api_key(self) -> str:
        return self.get('deepseek.api_key', '')

    @deepseek_api_key.setter
    def deepseek_api_key(self, value: str):
        self.set('deepseek.api_key', value)

    @property
    def deepseek_base_url(self) -> str:
        return self.get('deepseek.base_url', 'https://api.deepseek.com')

    @deepseek_base_url.setter
    def deepseek_base_url(self, value: str):
        self.set('deepseek.base_url', value)

    @property
    def ui_window_width(self) -> int:
        return self.get('ui.window_width', 1200)

    @ui_window_width.setter
    def ui_window_width(self, value: int):
        self.set('ui.window_width', value)

    @property
    def ui_window_height(self) -> int:
        return self.get('ui.window_height', 800)

    @ui_window_height.setter
    def ui_window_height(self, value: int):
        self.set('ui.window_height', value)

    @property
    def game_show_valid_moves(self) -> bool:
        return self.get('game.show_valid_moves', True)

    @game_show_valid_moves.setter
    def game_show_valid_moves(self, value: bool):
        self.set('game.show_valid_moves', value)

    @property
    def game_auto_analysis(self) -> bool:
        return self.get('game.auto_analysis', False)

    @game_auto_analysis.setter
    def game_auto_analysis(self, value: bool):
        self.set('game.auto_analysis', value)

    @property
    def language(self) -> str:
        return self.get('ui.language', 'zh')

    @language.setter
    def language(self, value: str):
        self.set('ui.language', value)

    def reset_to_default(self):
        """重置为默认配置"""
        self.config_data = self.default_config.copy()
        self.logger.info("配置已重置为默认值")

    def export_config(self, filename: str):
        """导出配置到指定文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"配置已导出到 {filename}")
        except Exception as e:
            self.logger.error(f"导出配置失败: {e}")

    def import_config(self, filename: str):
        """从指定文件导入配置"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)

            self.config_data = self._merge_configs(self.default_config, imported_config)
            self.save()
            self.logger.info(f"配置已从 {filename} 导入")
        except Exception as e:
            self.logger.error(f"导入配置失败: {e}")

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self.config_data.copy()

    def validate_config(self) -> bool:
        """验证配置的有效性"""
        try:
            # 验证串口配置
            if not isinstance(self.serial_baud_rate, int) or self.serial_baud_rate <= 0:
                return False

            # 验证UI配置
            if (not isinstance(self.ui_window_width, int) or
                not isinstance(self.ui_window_height, int) or
                self.ui_window_width < 800 or self.ui_window_height < 600):
                return False

            # 验证语言设置
            if self.language not in ['zh', 'en']:
                return False

            return True

        except Exception as e:
            self.logger.error(f"配置验证失败: {e}")
            return False