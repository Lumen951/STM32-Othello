#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Game History Manager for STM32 Othello PC Client
游戏历史记录管理器

@author: STM32 Othello Project Team
@version: 1.0
@date: 2025-12-09
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import logging


class GameHistoryRecord:
    """游戏历史记录"""

    def __init__(self, game_data: Dict):
        """
        初始化历史记录

        Args:
            game_data: 游戏数据字典
        """
        self.game_id = game_data.get('game_id', '')
        self.timestamp = game_data.get('timestamp', datetime.now().timestamp())
        self.date_str = datetime.fromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M:%S')

        # 游戏结果
        self.black_count = game_data.get('black_count', 0)
        self.white_count = game_data.get('white_count', 0)
        self.winner = game_data.get('winner', 'unknown')
        self.status = game_data.get('status', 0)

        # 游戏信息
        self.move_count = game_data.get('move_count', 0)
        self.duration = game_data.get('duration', 0)
        self.game_mode = game_data.get('game_mode', 'normal')

        # 完整游戏数据
        self.full_data = game_data

    def to_dict(self) -> Dict:
        """转换为字典"""
        return self.full_data

    def get_summary(self) -> str:
        """获取摘要信息"""
        winner_text = {
            'black': '黑方获胜',
            'white': '白方获胜',
            'draw': '平局'
        }.get(self.winner, '未知')

        # 游戏模式标识
        mode_icon = {
            'normal': '🎮',
            'challenge': '🎯',
            'timed': '⏱️'
        }.get(self.game_mode, '🎮')

        return f"{mode_icon} {self.date_str} | {winner_text} | {self.black_count}-{self.white_count} | {self.move_count}手"


class GameHistoryManager:
    """游戏历史记录管理器"""

    def __init__(self, data_file: str = 'data/game_history.json'):
        """
        初始化历史记录管理器

        Args:
            data_file: 数据文件路径
        """
        self.data_file = data_file
        self.logger = logging.getLogger(__name__)
        self.records: List[GameHistoryRecord] = []

        # 加载历史记录
        self._load_history()

    def add_game(self, game_state, game_mode: str = 'normal') -> GameHistoryRecord:
        """
        添加游戏记录

        Args:
            game_state: 游戏状态对象
            game_mode: 游戏模式 ('normal', 'challenge', 'timed')

        Returns:
            GameHistoryRecord: 历史记录对象
        """
        # 生成游戏ID
        game_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 确定获胜方
        if game_state.black_count > game_state.white_count:
            winner = 'black'
        elif game_state.white_count > game_state.black_count:
            winner = 'white'
        else:
            winner = 'draw'

        # 创建游戏数据
        game_data = game_state.to_dict()
        game_data['game_id'] = game_id
        game_data['timestamp'] = datetime.now().timestamp()
        game_data['winner'] = winner
        game_data['duration'] = game_state.get_game_duration()
        game_data['game_mode'] = game_mode  # 使用传入的游戏模式

        # 创建记录
        record = GameHistoryRecord(game_data)
        self.records.insert(0, record)  # 最新的在前面

        # 保存到文件
        self._save_history()

        self.logger.info(f"添加游戏记录: {game_id}")
        return record

    def get_all_records(self) -> List[GameHistoryRecord]:
        """获取所有记录"""
        return self.records

    def get_record_by_id(self, game_id: str) -> Optional[GameHistoryRecord]:
        """
        根据ID获取记录

        Args:
            game_id: 游戏ID

        Returns:
            GameHistoryRecord: 历史记录对象，未找到返回None
        """
        for record in self.records:
            if record.game_id == game_id:
                return record
        return None

    def delete_record(self, game_id: str) -> bool:
        """
        删除记录

        Args:
            game_id: 游戏ID

        Returns:
            bool: 是否删除成功
        """
        for i, record in enumerate(self.records):
            if record.game_id == game_id:
                self.records.pop(i)
                self._save_history()
                self.logger.info(f"删除游戏记录: {game_id}")
                return True
        return False

    def clear_all(self):
        """清空所有记录"""
        self.records.clear()
        self._save_history()
        self.logger.info("清空所有游戏记录")

    def get_statistics(self) -> Dict:
        """
        获取统计信息

        Returns:
            Dict: 统计数据
        """
        total_games = len(self.records)
        black_wins = sum(1 for r in self.records if r.winner == 'black')
        white_wins = sum(1 for r in self.records if r.winner == 'white')
        draws = sum(1 for r in self.records if r.winner == 'draw')

        total_moves = sum(r.move_count for r in self.records)
        avg_moves = total_moves / total_games if total_games > 0 else 0

        total_duration = sum(r.duration for r in self.records)
        avg_duration = total_duration / total_games if total_games > 0 else 0

        return {
            'total_games': total_games,
            'black_wins': black_wins,
            'white_wins': white_wins,
            'draws': draws,
            'avg_moves': avg_moves,
            'avg_duration': avg_duration
        }

    def _load_history(self):
        """加载历史记录"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 加载记录
                records_data = data.get('records', [])
                self.records = [GameHistoryRecord(r) for r in records_data]

                self.logger.info(f"已加载 {len(self.records)} 条游戏记录")
            else:
                # 创建数据目录
                os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
                self.logger.info("游戏历史文件不存在，将创建新文件")

        except Exception as e:
            self.logger.error(f"加载游戏历史失败: {e}")

    def _save_history(self):
        """保存历史记录"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)

            # 准备数据
            data = {
                'version': '1.0',
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_records': len(self.records),
                'records': [r.to_dict() for r in self.records]
            }

            # 保存到文件
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"游戏历史已保存: {len(self.records)} 条记录")

        except Exception as e:
            self.logger.error(f"保存游戏历史失败: {e}")

    def export_to_json(self, filename: str) -> bool:
        """
        导出为JSON文件

        Args:
            filename: 文件名

        Returns:
            bool: 是否成功
        """
        try:
            data = {
                'export_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_records': len(self.records),
                'records': [r.to_dict() for r in self.records]
            }

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"游戏历史已导出到: {filename}")
            return True

        except Exception as e:
            self.logger.error(f"导出游戏历史失败: {e}")
            return False
