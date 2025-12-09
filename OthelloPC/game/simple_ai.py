#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple AI for STM32 Othello PC Client
简单AI算法实现（不使用深度学习）

@author: STM32 Othello Project Team
@version: 1.0
@date: 2025-12-09
"""

import random
from typing import List, Tuple, Optional
from game.game_state import GameState, PieceType


class SimpleAI:
    """简单AI算法实现"""

    # 难度等级
    DIFFICULTY_EASY = 0      # 简单：随机走法
    DIFFICULTY_MEDIUM = 1    # 中等：贪心算法
    DIFFICULTY_HARD = 2      # 困难：贪心+位置评分

    # 位置权重表（8x8棋盘）
    POSITION_WEIGHTS = [
        [100, -20,  10,   5,   5,  10, -20, 100],
        [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
        [ 10,  -2,   5,   1,   1,   5,  -2,  10],
        [  5,  -2,   1,   0,   0,   1,  -2,   5],
        [  5,  -2,   1,   0,   0,   1,  -2,   5],
        [ 10,  -2,   5,   1,   1,   5,  -2,  10],
        [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
        [100, -20,  10,   5,   5,  10, -20, 100]
    ]

    def __init__(self, difficulty: int = DIFFICULTY_MEDIUM):
        """
        初始化AI

        Args:
            difficulty: 难度等级 (DIFFICULTY_EASY/MEDIUM/HARD)
        """
        self.difficulty = difficulty

    def get_best_move(self, game_state: GameState, player: PieceType) -> Optional[Tuple[int, int]]:
        """
        获取最佳走法

        Args:
            game_state: 游戏状态
            player: 当前玩家

        Returns:
            (row, col) 或 None（无可用走法）
        """
        try:
            valid_moves = self._get_valid_moves(game_state, player)

            if not valid_moves:
                return None

            if self.difficulty == self.DIFFICULTY_EASY:
                # 简单难度：随机选择
                move = random.choice(valid_moves)
                return move

            elif self.difficulty == self.DIFFICULTY_MEDIUM:
                # 中等难度：选择翻转最多棋子的位置
                move = self._get_max_flip_move(game_state, valid_moves, player)
                return move

            else:  # DIFFICULTY_HARD
                # 困难难度：综合考虑位置权重和翻转数量
                move = self._get_best_scored_move(game_state, valid_moves, player)
                return move

        except Exception as e:
            # 发生异常时，返回第一个有效走法作为后备
            print(f"AI算法异常: {e}")
            valid_moves = self._get_valid_moves(game_state, player)
            if valid_moves:
                return valid_moves[0]
            return None

    def _get_valid_moves(self, game_state: GameState, player: PieceType) -> List[Tuple[int, int]]:
        """
        获取所有有效走法

        Args:
            game_state: 游戏状态
            player: 当前玩家

        Returns:
            有效走法列表 [(row, col), ...]
        """
        valid_moves = []

        for row in range(8):
            for col in range(8):
                if game_state.is_valid_move(row, col, player):
                    valid_moves.append((row, col))

        return valid_moves

    def _count_flips(self, game_state: GameState, row: int, col: int, player: PieceType) -> int:
        """
        计算某个位置可以翻转的棋子数量

        Args:
            game_state: 游戏状态
            row: 行
            col: 列
            player: 当前玩家

        Returns:
            可翻转的棋子数量
        """
        if game_state.board[row][col] != PieceType.EMPTY:
            return 0

        total_flips = 0
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

        for dx, dy in directions:
            flips = self._count_flips_in_direction(game_state, row, col, dx, dy, player)
            total_flips += flips

        return total_flips

    def _count_flips_in_direction(self, game_state: GameState, row: int, col: int,
                                   dx: int, dy: int, player: PieceType) -> int:
        """
        计算某个方向上可以翻转的棋子数量

        Args:
            game_state: 游戏状态
            row: 起始行
            col: 起始列
            dx: 行方向增量
            dy: 列方向增量
            player: 当前玩家

        Returns:
            该方向上可翻转的棋子数量
        """
        opponent = PieceType.WHITE if player == PieceType.BLACK else PieceType.BLACK
        flips = 0
        x, y = row + dx, col + dy

        # 沿着方向查找对手的棋子
        while 0 <= x < 8 and 0 <= y < 8 and game_state.board[x][y] == opponent:
            flips += 1
            x += dx
            y += dy

        # 检查是否以己方棋子结束
        if 0 <= x < 8 and 0 <= y < 8 and game_state.board[x][y] == player and flips > 0:
            return flips

        return 0

    def _get_max_flip_move(self, game_state: GameState, valid_moves: List[Tuple[int, int]],
                           player: PieceType) -> Tuple[int, int]:
        """
        获取翻转最多棋子的走法（多个相同时随机选择）

        Args:
            game_state: 游戏状态
            valid_moves: 有效走法列表
            player: 当前玩家

        Returns:
            最佳走法 (row, col)
        """
        # 收集所有走法及其翻转数
        moves_with_flips = []
        for row, col in valid_moves:
            flips = self._count_flips(game_state, row, col, player)
            moves_with_flips.append(((row, col), flips))

        # 找出最大翻转数
        max_flips = max(flips for _, flips in moves_with_flips)

        # 收集所有最大翻转数的走法
        best_moves = [move for move, flips in moves_with_flips if flips == max_flips]

        # 随机选择一个（增加不可预测性）
        return random.choice(best_moves)

    def _get_best_scored_move(self, game_state: GameState, valid_moves: List[Tuple[int, int]],
                              player: PieceType) -> Tuple[int, int]:
        """
        获取综合评分最高的走法（位置权重 + 翻转数量，多个相同时随机选择）

        Args:
            game_state: 游戏状态
            valid_moves: 有效走法列表
            player: 当前玩家

        Returns:
            最佳走法 (row, col)
        """
        # 收集所有走法及其评分
        moves_with_scores = []
        for row, col in valid_moves:
            # 计算翻转数量
            flips = self._count_flips(game_state, row, col, player)

            # 获取位置权重
            position_weight = self.POSITION_WEIGHTS[row][col]

            # 综合评分：位置权重 * 2 + 翻转数量 * 3
            # 位置权重更重要，但翻转数量也有影响
            score = position_weight * 2 + flips * 3

            moves_with_scores.append(((row, col), score))

        # 找出最高分
        best_score = max(score for _, score in moves_with_scores)

        # 收集所有最高分的走法
        best_moves = [move for move, score in moves_with_scores if score == best_score]

        # 随机选择一个（增加不可预测性）
        return random.choice(best_moves)

    def set_difficulty(self, difficulty: int):
        """
        设置难度等级

        Args:
            difficulty: 难度等级 (DIFFICULTY_EASY/MEDIUM/HARD)
        """
        if difficulty in [self.DIFFICULTY_EASY, self.DIFFICULTY_MEDIUM, self.DIFFICULTY_HARD]:
            self.difficulty = difficulty

    def get_difficulty_name(self) -> str:
        """
        获取当前难度名称

        Returns:
            难度名称字符串
        """
        if self.difficulty == self.DIFFICULTY_EASY:
            return "简单"
        elif self.difficulty == self.DIFFICULTY_MEDIUM:
            return "中等"
        else:
            return "困难"


class AIPlayer:
    """AI玩家类（用于对抗模式）"""

    def __init__(self, player_type: PieceType, difficulty: int = SimpleAI.DIFFICULTY_MEDIUM):
        """
        初始化AI玩家

        Args:
            player_type: 玩家类型（BLACK或WHITE）
            difficulty: 难度等级
        """
        self.player_type = player_type
        self.ai = SimpleAI(difficulty)

    def make_move(self, game_state: GameState) -> Optional[Tuple[int, int]]:
        """
        AI走棋

        Args:
            game_state: 游戏状态

        Returns:
            走法 (row, col) 或 None
        """
        return self.ai.get_best_move(game_state, self.player_type)

    def set_difficulty(self, difficulty: int):
        """设置难度"""
        self.ai.set_difficulty(difficulty)

    def get_difficulty_name(self) -> str:
        """获取难度名称"""
        return self.ai.get_difficulty_name()
