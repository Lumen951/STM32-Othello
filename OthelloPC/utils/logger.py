#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logger Module for STM32 Othello PC Client
日志模块

@author: STM32 Othello Project Team
@version: 1.0
@date: 2025-11-22
"""

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

class Logger:
    """日志管理器"""

    def __init__(self, name: str = 'STM32_Othello', log_level: int = logging.INFO):
        """
        初始化日志器

        Args:
            name: 日志器名称
            log_level: 日志级别
        """
        self.name = name
        self.log_level = log_level
        self.logger = None

        self._setup_logger()

    def _setup_logger(self):
        """设置日志器"""
        # 创建日志器
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(self.log_level)

        # 防止重复添加处理器
        if self.logger.handlers:
            return

        # 创建logs目录
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # 文件处理器 - 详细日志
        log_filename = os.path.join(log_dir, f'{self.name}_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler = RotatingFileHandler(
            log_filename,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # 错误日志处理器
        error_filename = os.path.join(log_dir, f'{self.name}_error_{datetime.now().strftime("%Y%m%d")}.log')
        error_handler = RotatingFileHandler(
            error_filename,
            maxBytes=5*1024*1024,   # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)

        # ========== 关键修复：配置根logger，使所有子模块的日志都能输出 ==========
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        # 如果根logger还没有handler，添加相同的handler
        if not root_logger.handlers:
            root_logger.addHandler(console_handler)
            root_logger.addHandler(file_handler)
            root_logger.addHandler(error_handler)

    def debug(self, message: str):
        """记录调试信息"""
        self.logger.debug(message)

    def info(self, message: str):
        """记录普通信息"""
        self.logger.info(message)

    def warning(self, message: str):
        """记录警告信息"""
        self.logger.warning(message)

    def error(self, message: str):
        """记录错误信息"""
        self.logger.error(message)

    def critical(self, message: str):
        """记录严重错误信息"""
        self.logger.critical(message)

    def exception(self, message: str):
        """记录异常信息（包含堆栈跟踪）"""
        self.logger.exception(message)

    @staticmethod
    def get_logger(name: str = None) -> logging.Logger:
        """获取日志器实例"""
        if name is None:
            name = 'STM32_Othello'
        return logging.getLogger(name)