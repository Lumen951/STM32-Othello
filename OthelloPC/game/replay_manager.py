#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Replay Manager for STM32 Othello PC Client
棋局回放管理器

@author: STM32 Othello Project Team
@version: 1.0
@date: 2025-12-09
"""

import time
from typing import Optional, Callable
import logging
from game.game_state import GameState, PieceType, Move


class ReplayManager:
    """棋局回放管理器"""

    def __init__(self):
        """初始化回放管理器"""
        self.logger = logging.getLogger(__name__)

        # 回放数据
        self.game_data: Optional[dict] = None
        self.moves_list: list = []
        self.current_move_index = -1

        # 回放状态
        self.is_playing = False
        self.play_speed = 1.0  # 播放速度倍数
        self.last_step_time = 0

        # 回调函数
        self.on_state_changed: Optional[Callable] = None

    def load_game(self, game_data: dict) -> bool:
        """
        加载游戏数据

        Args:
            game_data: 游戏数据字典

        Returns:
            bool: 是否加载成功
        """
        try:
            self.game_data = game_data
            self.moves_list = game_data.get('moves', [])
            self.current_move_index = -1
            self.is_playing = False

            self.logger.info(f"加载游戏数据: {len(self.moves_list)} 步棋")
            return True

        except Exception as e:
            self.logger.error(f"加载游戏数据失败: {e}")
            return False

    def get_current_state(self) -> Optional[GameState]:
        """
        获取当前回放状态

        Returns:
            GameState: 当前游戏状态
        """
        if not self.game_data:
            return None

        # 创建新的游戏状态
        state = GameState()
        state.start_new_game()

        # 重放到当前步骤
        for i in range(self.current_move_index + 1):
            if i < len(self.moves_list):
                move_data = self.moves_list[i]
                row = move_data['row']
                col = move_data['col']
                player = PieceType(move_data['player'])

                state.make_move(row, col, player)

        return state

    def step_forward(self) -> bool:
        """
        前进一步

        Returns:
            bool: 是否成功
        """
        if not self.game_data:
            return False

        if self.current_move_index < len(self.moves_list) - 1:
            self.current_move_index += 1
            self._notify_state_changed()
            return True

        return False

    def step_backward(self) -> bool:
        """
        后退一步

        Returns:
            bool: 是否成功
        """
        if not self.game_data:
            return False

        if self.current_move_index >= 0:
            self.current_move_index -= 1
            self._notify_state_changed()
            return True

        return False

    def jump_to_move(self, move_index: int) -> bool:
        """
        跳转到指定步骤

        Args:
            move_index: 步骤索引 (-1表示初始状态)

        Returns:
            bool: 是否成功
        """
        if not self.game_data:
            return False

        if -1 <= move_index < len(self.moves_list):
            self.current_move_index = move_index
            self._notify_state_changed()
            return True

        return False

    def jump_to_start(self) -> bool:
        """
        跳转到开始

        Returns:
            bool: 是否成功
        """
        return self.jump_to_move(-1)

    def jump_to_end(self) -> bool:
        """
        跳转到结束

        Returns:
            bool: 是否成功
        """
        if not self.game_data:
            return False

        return self.jump_to_move(len(self.moves_list) - 1)

    def play(self):
        """开始自动播放"""
        if self.game_data and not self.is_playing:
            self.is_playing = True
            self.last_step_time = time.time()
            self.logger.info("开始自动播放")

    def pause(self):
        """暂停自动播放"""
        if self.is_playing:
            self.is_playing = False
            self.logger.info("暂停自动播放")

    def toggle_play_pause(self):
        """切换播放/暂停"""
        if self.is_playing:
            self.pause()
        else:
            self.play()

    def set_play_speed(self, speed: float):
        """
        设置播放速度

        Args:
            speed: 速度倍数 (0.5, 1.0, 2.0, 4.0)
        """
        self.play_speed = max(0.1, min(10.0, speed))
        self.logger.info(f"设置播放速度: {self.play_speed}x")

    def update(self):
        """
        更新回放状态（需要在主循环中调用）
        """
        if not self.is_playing or not self.game_data:
            return

        current_time = time.time()
        step_interval = 1.0 / self.play_speed  # 基础间隔1秒

        if current_time - self.last_step_time >= step_interval:
            if not self.step_forward():
                # 到达结尾，停止播放
                self.pause()
            self.last_step_time = current_time

    def get_progress(self) -> tuple:
        """
        获取回放进度

        Returns:
            tuple: (当前步骤, 总步骤数)
        """
        if not self.game_data:
            return (0, 0)

        return (self.current_move_index + 1, len(self.moves_list))

    def get_current_move_info(self) -> Optional[dict]:
        """
        获取当前步骤信息

        Returns:
            dict: 步骤信息
        """
        if not self.game_data or self.current_move_index < 0:
            return None

        if self.current_move_index < len(self.moves_list):
            return self.moves_list[self.current_move_index]

        return None

    def register_callback(self, callback: Callable):
        """
        注册状态变化回调

        Args:
            callback: 回调函数
        """
        self.on_state_changed = callback

    def _notify_state_changed(self):
        """通知状态变化"""
        if self.on_state_changed:
            try:
                self.on_state_changed()
            except Exception as e:
                self.logger.error(f"回调函数执行失败: {e}")

    def is_at_start(self) -> bool:
        """是否在开始位置"""
        return self.current_move_index == -1

    def is_at_end(self) -> bool:
        """是否在结束位置"""
        if not self.game_data:
            return True
        return self.current_move_index >= len(self.moves_list) - 1

    def get_total_moves(self) -> int:
        """获取总步数"""
        return len(self.moves_list) if self.game_data else 0
