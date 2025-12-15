#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Timed Mode Manager for STM32 Othello PC Client
计时模式管理器（简化版 - 纯tkinter.after实现）

@author: STM32 Othello Project Team
@version: 2.0
@date: 2025-12-15
"""

import logging
from typing import Callable, Optional


class TimedModeManager:
    """计时模式管理器（简化版）

    功能：
    - 倒计时管理（默认180秒）
    - 启动/暂停/继续/停止控制
    - 时间更新回调
    - 时间到自动结束触发

    实现方式：
    - 纯tkinter.after()实现，无threading
    - 单线程，无锁，无死锁风险
    """

    def __init__(self, root, duration: int = 180):
        """初始化计时模式管理器

        Args:
            root: tkinter根窗口（用于after调度）
            duration: 游戏时长（秒），默认180秒（3分钟）
        """
        self.root = root
        self.duration = duration
        self.remaining = duration
        self.running = False
        self.paused = False
        self.after_id = None  # after调度ID

        # 回调函数
        self.on_time_update: Optional[Callable[[int], None]] = None
        self.on_time_up: Optional[Callable[[], None]] = None

        # 日志
        self.logger = logging.getLogger(__name__)

        self.logger.info(f"计时模式管理器初始化完成（简化版），时长：{duration}秒")

    def start(self, duration: Optional[int] = None):
        """启动计时模式

        Args:
            duration: 可选的自定义时长（秒），如果不提供则使用初始化时的时长
        """
        # 如果已在运行，先停止
        if self.running:
            self._stop_timer()

        # 设置时长
        if duration is not None:
            self.duration = duration

        self.remaining = self.duration
        self.running = True
        self.paused = False

        self.logger.info(f"计时模式启动，时长：{self.duration}秒")

        # 立即触发一次更新回调
        if self.on_time_update:
            self.on_time_update(self.remaining)

        # 开始倒计时
        self._countdown()

    def pause(self):
        """暂停计时"""
        if not self.running or self.paused:
            self.logger.warning("计时模式未运行或已暂停，无法暂停")
            return

        self.paused = True
        self._stop_timer()

        self.logger.info(f"计时模式暂停，剩余时间：{self.remaining}秒")

    def resume(self):
        """继续计时"""
        if not self.running or not self.paused:
            self.logger.warning("计时模式未暂停，无法继续")
            return

        self.paused = False

        self.logger.info(f"计时模式继续，剩余时间：{self.remaining}秒")

        # 恢复倒计时
        self._countdown()

    def stop(self):
        """停止计时"""
        if not self.running:
            return

        self.running = False
        self.paused = False
        self._stop_timer()

        self.logger.info("计时模式停止")

    def reset(self):
        """重置计时器（回到初始时长）"""
        self.stop()
        self.remaining = self.duration

        self.logger.info(f"计时模式重置，时长：{self.duration}秒")

        # 触发更新回调
        if self.on_time_update:
            self.on_time_update(self.remaining)

    def _countdown(self):
        """倒计时逻辑（递归调用）

        注意：此方法在主线程中调用（通过root.after）
        """
        # 检查是否应该继续倒计时
        if not self.running or self.paused:
            return

        # 检查是否时间到
        if self.remaining <= 0:
            self.running = False
            self.logger.info("计时结束！")

            # 触发时间到回调
            if self.on_time_up:
                try:
                    self.on_time_up()
                except Exception as e:
                    self.logger.error(f"时间到回调执行失败: {e}")
            return

        # 减1秒
        self.remaining -= 1

        # 触发时间更新回调
        if self.on_time_update:
            try:
                self.on_time_update(self.remaining)
            except Exception as e:
                self.logger.error(f"时间更新回调执行失败: {e}")

        # 调度下一次倒计时（1秒后）
        if self.running:  # 再次检查是否还在运行
            self.after_id = self.root.after(1000, self._countdown)

    def _stop_timer(self):
        """停止当前定时器"""
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def get_remaining_time(self) -> int:
        """获取剩余时间

        Returns:
            剩余时间（秒）
        """
        return self.remaining

    def is_running(self) -> bool:
        """判断是否正在运行

        Returns:
            True如果正在运行
        """
        return self.running

    def is_paused(self) -> bool:
        """判断是否已暂停

        Returns:
            True如果已暂停
        """
        return self.paused

    def set_duration(self, duration: int):
        """设置游戏时长

        Args:
            duration: 时长（秒）

        注意：只有在未运行时才能设置
        """
        if self.running:
            self.logger.warning("计时模式正在运行，无法设置时长")
            return False

        self.duration = duration
        self.remaining = duration

        self.logger.info(f"计时模式时长设置为：{duration}秒")
        return True

    def get_duration(self) -> int:
        """获取游戏时长

        Returns:
            时长（秒）
        """
        return self.duration

    def get_elapsed_time(self) -> int:
        """获取已用时间

        Returns:
            已用时间（秒）
        """
        return self.duration - self.remaining

    def format_time(self, seconds: int) -> str:
        """格式化时间为 MM:SS 格式

        Args:
            seconds: 时间（秒）

        Returns:
            格式化后的字符串（如 "03:25"）
        """
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"

    def get_formatted_remaining_time(self) -> str:
        """获取格式化的剩余时间

        Returns:
            格式化后的剩余时间（如 "03:25"）
        """
        return self.format_time(self.remaining)
