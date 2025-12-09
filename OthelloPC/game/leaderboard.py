#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Leaderboard Manager for STM32 Othello PC Client
排行榜管理器

@author: STM32 Othello Project Team
@version: 1.0
@date: 2025-12-09
"""

import json
import os
import csv
from datetime import datetime
from typing import List, Dict, Optional
import logging


class LeaderboardEntry:
    """排行榜条目"""

    def __init__(self, player_name: str, score: int, game_mode: str,
                 duration: float, timestamp: float = None):
        """
        初始化排行榜条目

        Args:
            player_name: 玩家名称
            score: 得分
            game_mode: 游戏模式
            duration: 用时（秒）
            timestamp: 时间戳
        """
        self.player_name = player_name
        self.score = score
        self.game_mode = game_mode
        self.duration = duration
        self.timestamp = timestamp if timestamp else datetime.now().timestamp()
        self.date_str = datetime.fromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M')

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'player_name': self.player_name,
            'score': self.score,
            'game_mode': self.game_mode,
            'duration': self.duration,
            'timestamp': self.timestamp,
            'date': self.date_str
        }

    @staticmethod
    def from_dict(data: Dict) -> 'LeaderboardEntry':
        """从字典创建"""
        return LeaderboardEntry(
            player_name=data['player_name'],
            score=data['score'],
            game_mode=data['game_mode'],
            duration=data['duration'],
            timestamp=data['timestamp']
        )

    def get_summary(self) -> str:
        """获取摘要信息"""
        return f"{self.player_name:12s} | {self.score:3d}分 | {self.duration:5.1f}秒 | {self.date_str}"


class Leaderboard:
    """排行榜管理器"""

    def __init__(self, data_file: str = 'data/leaderboard.json', max_entries: int = 10):
        """
        初始化排行榜

        Args:
            data_file: 数据文件路径
            max_entries: 最大保存条目数
        """
        self.data_file = data_file
        self.max_entries = max_entries
        self.logger = logging.getLogger(__name__)

        # 分模式的排行榜
        self.normal_board: List[LeaderboardEntry] = []
        self.challenge_board: List[LeaderboardEntry] = []
        self.timed_board: List[LeaderboardEntry] = []

        # 加载数据
        self._load_data()

    def add_entry(self, player_name: str, score: int, game_mode: str, duration: float) -> bool:
        """
        添加排行榜条目

        Args:
            player_name: 玩家名称
            score: 得分
            game_mode: 游戏模式 (normal/challenge/timed)
            duration: 用时（秒）

        Returns:
            bool: 是否成功添加（是否进入排行榜）
        """
        entry = LeaderboardEntry(player_name, score, game_mode, duration)

        # 选择对应的排行榜
        board = self._get_board(game_mode)
        if board is None:
            return False

        # 添加条目
        board.append(entry)

        # 排序（按分数降序，分数相同按用时升序）
        board.sort(key=lambda x: (-x.score, x.duration))

        # 保留前N名
        if len(board) > self.max_entries:
            board[:] = board[:self.max_entries]

        # 保存数据
        self._save_data()

        self.logger.info(f"添加排行榜条目: {player_name} - {score}分 ({game_mode})")
        return True

    def get_board(self, game_mode: str) -> List[LeaderboardEntry]:
        """
        获取指定模式的排行榜

        Args:
            game_mode: 游戏模式

        Returns:
            List[LeaderboardEntry]: 排行榜列表
        """
        board = self._get_board(game_mode)
        return board if board is not None else []

    def get_rank(self, score: int, game_mode: str) -> int:
        """
        获取指定分数的排名

        Args:
            score: 分数
            game_mode: 游戏模式

        Returns:
            int: 排名（1-based），0表示未上榜
        """
        board = self._get_board(game_mode)
        if board is None:
            return 0

        for i, entry in enumerate(board):
            if score > entry.score:
                return i + 1

        # 如果排行榜未满，可以上榜
        if len(board) < self.max_entries:
            return len(board) + 1

        return 0  # 未上榜

    def is_high_score(self, score: int, game_mode: str) -> bool:
        """
        判断是否是高分（能否进入排行榜）

        Args:
            score: 分数
            game_mode: 游戏模式

        Returns:
            bool: 是否是高分
        """
        board = self._get_board(game_mode)
        if board is None:
            return False

        # 排行榜未满，直接上榜
        if len(board) < self.max_entries:
            return True

        # 比最后一名高
        return score > board[-1].score

    def clear_board(self, game_mode: str = None):
        """
        清空排行榜

        Args:
            game_mode: 游戏模式，None表示清空所有
        """
        if game_mode is None:
            self.normal_board.clear()
            self.challenge_board.clear()
            self.timed_board.clear()
            self.logger.info("清空所有排行榜")
        else:
            board = self._get_board(game_mode)
            if board is not None:
                board.clear()
                self.logger.info(f"清空{game_mode}模式排行榜")

        self._save_data()

    def export_to_csv(self, filename: str, game_mode: str = None) -> bool:
        """
        导出排行榜到CSV文件

        Args:
            filename: 文件名
            game_mode: 游戏模式，None表示导出所有

        Returns:
            bool: 是否成功
        """
        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['排名', '玩家', '得分', '模式', '用时(秒)', '日期'])

                if game_mode is None:
                    # 导出所有模式
                    for mode in ['normal', 'challenge', 'timed']:
                        board = self._get_board(mode)
                        if board:
                            for i, entry in enumerate(board):
                                writer.writerow([
                                    i + 1,
                                    entry.player_name,
                                    entry.score,
                                    mode,
                                    f"{entry.duration:.1f}",
                                    entry.date_str
                                ])
                else:
                    # 导出指定模式
                    board = self._get_board(game_mode)
                    if board:
                        for i, entry in enumerate(board):
                            writer.writerow([
                                i + 1,
                                entry.player_name,
                                entry.score,
                                entry.game_mode,
                                f"{entry.duration:.1f}",
                                entry.date_str
                            ])

            self.logger.info(f"排行榜已导出到: {filename}")
            return True

        except Exception as e:
            self.logger.error(f"导出排行榜失败: {e}")
            return False

    def _get_board(self, game_mode: str) -> Optional[List[LeaderboardEntry]]:
        """获取对应模式的排行榜"""
        mode_map = {
            'normal': self.normal_board,
            'challenge': self.challenge_board,
            'timed': self.timed_board
        }
        return mode_map.get(game_mode)

    def _load_data(self):
        """加载数据"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 加载各模式排行榜
                self.normal_board = [LeaderboardEntry.from_dict(e)
                                    for e in data.get('normal', [])]
                self.challenge_board = [LeaderboardEntry.from_dict(e)
                                       for e in data.get('challenge', [])]
                self.timed_board = [LeaderboardEntry.from_dict(e)
                                   for e in data.get('timed', [])]

                total = len(self.normal_board) + len(self.challenge_board) + len(self.timed_board)
                self.logger.info(f"已加载排行榜数据: {total} 条记录")
            else:
                # 创建数据目录
                os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
                self.logger.info("排行榜数据文件不存在，将创建新文件")

        except Exception as e:
            self.logger.error(f"加载排行榜数据失败: {e}")

    def _save_data(self):
        """保存数据"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)

            data = {
                'version': '1.0',
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'max_entries': self.max_entries,
                'normal': [e.to_dict() for e in self.normal_board],
                'challenge': [e.to_dict() for e in self.challenge_board],
                'timed': [e.to_dict() for e in self.timed_board]
            }

            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.logger.info("排行榜数据已保存")

        except Exception as e:
            self.logger.error(f"保存排行榜数据失败: {e}")

    def get_statistics(self, game_mode: str) -> Dict:
        """
        获取统计信息

        Args:
            game_mode: 游戏模式

        Returns:
            Dict: 统计数据
        """
        board = self._get_board(game_mode)
        if not board:
            return {
                'total_entries': 0,
                'highest_score': 0,
                'average_score': 0,
                'fastest_time': 0
            }

        scores = [e.score for e in board]
        durations = [e.duration for e in board]

        return {
            'total_entries': len(board),
            'highest_score': max(scores) if scores else 0,
            'average_score': sum(scores) / len(scores) if scores else 0,
            'fastest_time': min(durations) if durations else 0
        }
