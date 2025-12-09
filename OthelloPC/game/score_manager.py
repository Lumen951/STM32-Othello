#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Score Manager for STM32 Othello PC Client
分数管理器

@author: STM32 Othello Project Team
@version: 1.0
@date: 2025-12-09
"""

import json
import os
from typing import Dict, Optional
from datetime import datetime
import logging


class ScoreRecord:
    """分数记录"""

    def __init__(self, black_score: int, white_score: int,
                 winner: str, game_mode: str = "normal",
                 timestamp: float = None):
        """
        初始化分数记录

        Args:
            black_score: 黑子分数
            white_score: 白子分数
            winner: 获胜方 ("black", "white", "draw")
            game_mode: 游戏模式
            timestamp: 时间戳
        """
        self.black_score = black_score
        self.white_score = white_score
        self.winner = winner
        self.game_mode = game_mode
        self.timestamp = timestamp if timestamp else datetime.now().timestamp()

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'black_score': self.black_score,
            'white_score': self.white_score,
            'winner': self.winner,
            'game_mode': self.game_mode,
            'timestamp': self.timestamp,
            'date': datetime.fromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M:%S')
        }

    @staticmethod
    def from_dict(data: Dict) -> 'ScoreRecord':
        """从字典创建"""
        return ScoreRecord(
            black_score=data['black_score'],
            white_score=data['white_score'],
            winner=data['winner'],
            game_mode=data.get('game_mode', 'normal'),
            timestamp=data['timestamp']
        )


class ScoreManager:
    """分数管理器"""

    def __init__(self, data_file: str = 'data/scores.json'):
        """
        初始化分数管理器

        Args:
            data_file: 数据文件路径
        """
        self.data_file = data_file
        self.logger = logging.getLogger(__name__)

        # 当前游戏分数
        self.current_black_score = 2
        self.current_white_score = 2

        # 累计分数（闯关模式）
        self.total_score = 0
        self.consecutive_wins = 0
        self.consecutive_losses = 0

        # 历史最高分
        self.highest_score = 0
        self.highest_score_date = None

        # 统计数据
        self.total_games = 0
        self.black_wins = 0
        self.white_wins = 0
        self.draws = 0

        # 加载历史数据
        self._load_data()

    def update_current_score(self, black_score: int, white_score: int):
        """
        更新当前游戏分数

        Args:
            black_score: 黑子分数
            white_score: 白子分数
        """
        self.current_black_score = black_score
        self.current_white_score = white_score

    def record_game_result(self, black_score: int, white_score: int,
                          game_mode: str = "normal") -> ScoreRecord:
        """
        记录游戏结果

        Args:
            black_score: 黑子分数
            white_score: 白子分数
            game_mode: 游戏模式

        Returns:
            ScoreRecord: 分数记录
        """
        # 确定获胜方
        if black_score > white_score:
            winner = "black"
            self.black_wins += 1
            self.consecutive_wins += 1
            self.consecutive_losses = 0
        elif white_score > black_score:
            winner = "white"
            self.white_wins += 1
            self.consecutive_losses += 1
            self.consecutive_wins = 0
        else:
            winner = "draw"
            self.draws += 1
            self.consecutive_wins = 0
            self.consecutive_losses = 0

        self.total_games += 1

        # 更新累计分数（闯关模式）
        if game_mode == "challenge":
            if winner == "black":
                self.total_score += black_score

            # 更新最高分
            if self.total_score > self.highest_score:
                self.highest_score = self.total_score
                self.highest_score_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 创建记录
        record = ScoreRecord(black_score, white_score, winner, game_mode)

        # 保存数据
        self._save_data()

        self.logger.info(f"记录游戏结果: {winner} 获胜 ({black_score}-{white_score})")

        return record

    def reset_challenge_score(self):
        """重置闯关模式累计分数"""
        self.total_score = 0
        self.consecutive_wins = 0
        self.consecutive_losses = 0
        self.logger.info("闯关模式分数已重置")

    def get_statistics(self) -> Dict:
        """
        获取统计数据

        Returns:
            Dict: 统计数据
        """
        win_rate = 0
        if self.total_games > 0:
            win_rate = (self.black_wins / self.total_games) * 100

        return {
            'total_games': self.total_games,
            'black_wins': self.black_wins,
            'white_wins': self.white_wins,
            'draws': self.draws,
            'win_rate': win_rate,
            'consecutive_wins': self.consecutive_wins,
            'consecutive_losses': self.consecutive_losses,
            'total_score': self.total_score,
            'highest_score': self.highest_score,
            'highest_score_date': self.highest_score_date
        }

    def _load_data(self):
        """加载历史数据"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 加载统计数据
                self.total_games = data.get('total_games', 0)
                self.black_wins = data.get('black_wins', 0)
                self.white_wins = data.get('white_wins', 0)
                self.draws = data.get('draws', 0)
                self.highest_score = data.get('highest_score', 0)
                self.highest_score_date = data.get('highest_score_date', None)

                self.logger.info(f"已加载分数数据: {self.total_games}场游戏")
            else:
                # 创建数据目录
                os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
                self.logger.info("分数数据文件不存在，将创建新文件")

        except Exception as e:
            self.logger.error(f"加载分数数据失败: {e}")

    def _save_data(self):
        """保存数据"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)

            data = {
                'total_games': self.total_games,
                'black_wins': self.black_wins,
                'white_wins': self.white_wins,
                'draws': self.draws,
                'highest_score': self.highest_score,
                'highest_score_date': self.highest_score_date,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.logger.info("分数数据已保存")

        except Exception as e:
            self.logger.error(f"保存分数数据失败: {e}")

    def reset_statistics(self):
        """重置所有统计数据"""
        self.total_games = 0
        self.black_wins = 0
        self.white_wins = 0
        self.draws = 0
        self.total_score = 0
        self.consecutive_wins = 0
        self.consecutive_losses = 0
        self.highest_score = 0
        self.highest_score_date = None

        self._save_data()
        self.logger.info("所有统计数据已重置")
