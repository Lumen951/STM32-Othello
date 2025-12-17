#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Game State Manager for STM32 Othello PC Client
游戏状态管理器

@author: STM32 Othello Project Team
@version: 1.0
@date: 2025-11-22
"""

import json
import time
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Tuple
import logging

# 创建模块级logger
logger = logging.getLogger(__name__)

class PieceType(Enum):
    """棋子类型枚举"""
    EMPTY = 0
    BLACK = 1
    WHITE = 2

class GameStatus(Enum):
    """游戏状态枚举"""
    PLAYING = 0
    BLACK_WIN = 1
    WHITE_WIN = 2
    DRAW = 3
    NOT_STARTED = 4

class Move:
    """走法记录"""
    def __init__(self, row: int, col: int, player: PieceType, timestamp: float = None):
        self.row = row
        self.col = col
        self.player = player
        self.timestamp = timestamp if timestamp else time.time()
        self.flipped_count = 0

    def to_notation(self) -> str:
        """转换为棋谱记号"""
        col_char = chr(ord('A') + self.col)
        row_num = self.row + 1
        return f"{col_char}{row_num}"

    def __str__(self):
        return self.to_notation()

class GameState:
    """游戏状态类"""
    def __init__(self):
        self.board = [[PieceType.EMPTY for _ in range(8)] for _ in range(8)]
        self.current_player = PieceType.BLACK
        self.black_count = 0
        self.white_count = 0
        self.status = GameStatus.NOT_STARTED
        self.move_count = 0
        self.game_start_time = None
        self.game_end_time = None
        self.moves_history: List[Move] = []

    def start_new_game(self):
        """开始新游戏"""
        # 清空棋盘
        self.board = [[PieceType.EMPTY for _ in range(8)] for _ in range(8)]

        # 设置初始位置
        self.board[3][3] = PieceType.BLACK  # D4
        self.board[4][4] = PieceType.BLACK  # E5
        self.board[3][4] = PieceType.WHITE  # E4
        self.board[4][3] = PieceType.WHITE  # D5

        self.current_player = PieceType.BLACK
        self.black_count = 2
        self.white_count = 2
        self.status = GameStatus.PLAYING
        self.move_count = 0
        self.game_start_time = time.time()
        self.game_end_time = None
        self.moves_history = []

    def make_move(self, row: int, col: int, player: PieceType) -> bool:
        """执行走法"""
        if not self.is_valid_move(row, col, player):
            return False

        # 记录走法
        move = Move(row, col, player)
        flipped_count = 0

        # 放置棋子
        self.board[row][col] = player

        # 翻转棋子
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for dx, dy in directions:
            flipped_count += self._flip_pieces_in_direction(row, col, dx, dy, player)

        move.flipped_count = flipped_count
        self.moves_history.append(move)

        # 更新游戏状态
        self.move_count += 1
        self._update_piece_counts()
        self._switch_player()
        self._check_game_over()

        return True

    def is_valid_move(self, row: int, col: int, player: PieceType) -> bool:
        """检查走法是否有效"""
        if not (0 <= row < 8 and 0 <= col < 8):
            return False

        if self.board[row][col] != PieceType.EMPTY:
            return False

        if self.status != GameStatus.PLAYING:
            return False

        # 检查是否能翻转对手棋子
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for dx, dy in directions:
            if self._can_flip_in_direction(row, col, dx, dy, player):
                return True

        return False

    def get_valid_moves(self, player: PieceType) -> List[Tuple[int, int]]:
        """获取所有有效走法"""
        valid_moves = []
        for row in range(8):
            for col in range(8):
                if self.is_valid_move(row, col, player):
                    valid_moves.append((row, col))
        return valid_moves

    def _flip_pieces_in_direction(self, row: int, col: int, dx: int, dy: int, player: PieceType) -> int:
        """在指定方向翻转棋子"""
        opponent = PieceType.WHITE if player == PieceType.BLACK else PieceType.BLACK
        flipped = 0
        check_row, check_col = row + dx, col + dy

        # 寻找对手棋子
        to_flip = []
        while (0 <= check_row < 8 and 0 <= check_col < 8 and
               self.board[check_row][check_col] == opponent):
            to_flip.append((check_row, check_col))
            check_row, check_col = check_row + dx, check_col + dy

        # 检查是否以己方棋子结束
        if (0 <= check_row < 8 and 0 <= check_col < 8 and
            self.board[check_row][check_col] == player and len(to_flip) > 0):
            # 执行翻转
            for flip_row, flip_col in to_flip:
                self.board[flip_row][flip_col] = player
                flipped += 1

        return flipped

    def _can_flip_in_direction(self, row: int, col: int, dx: int, dy: int, player: PieceType) -> bool:
        """检查在指定方向是否可以翻转"""
        opponent = PieceType.WHITE if player == PieceType.BLACK else PieceType.BLACK
        check_row, check_col = row + dx, col + dy
        found_opponent = False

        while 0 <= check_row < 8 and 0 <= check_col < 8:
            if self.board[check_row][check_col] == opponent:
                found_opponent = True
            elif self.board[check_row][check_col] == player:
                return found_opponent
            else:
                break
            check_row, check_col = check_row + dx, check_col + dy

        return False

    def _update_piece_counts(self):
        """更新棋子计数"""
        self.black_count = 0
        self.white_count = 0
        for row in range(8):
            for col in range(8):
                if self.board[row][col] == PieceType.BLACK:
                    self.black_count += 1
                elif self.board[row][col] == PieceType.WHITE:
                    self.white_count += 1

    def _switch_player(self):
        """切换当前玩家"""
        next_player = PieceType.WHITE if self.current_player == PieceType.BLACK else PieceType.BLACK

        # 检查下一个玩家是否有有效走法
        if self.get_valid_moves(next_player):
            self.current_player = next_player
        elif self.get_valid_moves(self.current_player):
            # 下一个玩家无法走棋，当前玩家继续
            pass
        else:
            # 双方都无法走棋，游戏结束
            self._end_game()

    def _check_game_over(self):
        """检查游戏是否结束"""
        if self.black_count + self.white_count == 64:
            self._end_game()
        elif not self.get_valid_moves(PieceType.BLACK) and not self.get_valid_moves(PieceType.WHITE):
            self._end_game()

    def _end_game(self):
        """结束游戏"""
        self.game_end_time = time.time()
        if self.black_count > self.white_count:
            self.status = GameStatus.BLACK_WIN
        elif self.white_count > self.black_count:
            self.status = GameStatus.WHITE_WIN
        else:
            self.status = GameStatus.DRAW

    def get_game_duration(self) -> float:
        """获取游戏时长（秒）"""
        if self.game_start_time is None:
            return 0
        end_time = self.game_end_time if self.game_end_time else time.time()
        return end_time - self.game_start_time

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'board': [[piece.value for piece in row] for row in self.board],
            'current_player': self.current_player.value,
            'black_count': self.black_count,
            'white_count': self.white_count,
            'status': self.status.value,
            'move_count': self.move_count,
            'game_start_time': self.game_start_time,
            'game_end_time': self.game_end_time,
            'moves': [{'row': m.row, 'col': m.col, 'player': m.player.value,
                      'timestamp': m.timestamp, 'flipped': m.flipped_count}
                     for m in self.moves_history]
        }

    def from_dict(self, data: Dict):
        """从字典数据恢复状态"""
        self.board = [[PieceType(piece) for piece in row] for row in data['board']]
        self.current_player = PieceType(data['current_player'])
        self.black_count = data['black_count']
        self.white_count = data['white_count']
        self.status = GameStatus(data['status'])
        self.move_count = data['move_count']
        self.game_start_time = data['game_start_time']
        self.game_end_time = data.get('game_end_time')

        # 恢复走法历史
        self.moves_history = []
        for move_data in data.get('moves', []):
            move = Move(move_data['row'], move_data['col'],
                       PieceType(move_data['player']), move_data['timestamp'])
            move.flipped_count = move_data.get('flipped', 0)
            self.moves_history.append(move)

class GameStateManager:
    """游戏状态管理器"""
    def __init__(self):
        self.current_game = GameState()
        self.games_history: List[GameState] = []
        self.observers = []

    def start_new_game(self):
        """开始新游戏"""
        # 保存当前游戏到历史记录
        if self.current_game.move_count > 0:
            self.games_history.append(self.current_game)

        # 创建新游戏
        self.current_game = GameState()
        self.current_game.start_new_game()
        self._notify_observers('game_started')

    def make_move(self, row: int, col: int) -> bool:
        """执行走法"""
        if self.current_game.make_move(row, col, self.current_game.current_player):
            self._notify_observers('move_made', {'row': row, 'col': col})
            if self.current_game.status != GameStatus.PLAYING:
                self._notify_observers('game_ended')
            return True
        return False

    def update_board_state(self, board_data: bytes):
        """从STM32更新完整游戏状态"""
        import struct

        # 检查数据长度（Game_State_Data_t = 72 bytes）
        if len(board_data) < 72:
            logger.error(f"❌ 游戏状态数据不完整: 接收{len(board_data)}字节, 期望72字节")
            return

        try:
            # ========== 1. 解析棋盘数据 (0-63字节) ==========
            for i in range(64):
                row = i // 8
                col = i % 8
                piece_value = board_data[i]
                self.current_game.board[row][col] = PieceType(piece_value)

            # ========== 2. 解析当前玩家 (64字节) ⚠️ 关键修复 ==========
            current_player_value = board_data[64]
            old_player = self.current_game.current_player
            self.current_game.current_player = PieceType(current_player_value)

            # ========== 3. 解析棋子计数 (65-66字节) ==========
            self.current_game.black_count = board_data[65]
            self.current_game.white_count = board_data[66]

            # ========== 4. 解析游戏结束标志 (67字节) ==========
            game_over = board_data[67]
            if game_over == 1:
                # 根据分数判断结果
                if self.current_game.black_count > self.current_game.white_count:
                    self.current_game.status = GameStatus.BLACK_WIN
                elif self.current_game.white_count > self.current_game.black_count:
                    self.current_game.status = GameStatus.WHITE_WIN
                else:
                    self.current_game.status = GameStatus.DRAW
            else:
                self.current_game.status = GameStatus.PLAYING

            # ========== 5. 解析走法计数 (68-71字节, little-endian uint32) ==========
            move_count = struct.unpack('<I', board_data[68:72])[0]
            self.current_game.move_count = move_count

            # ========== 日志输出 ==========
            logger.info(f"✅ 游戏状态同步: 玩家 {old_player.name}→{self.current_game.current_player.name}, "
                       f"黑={self.current_game.black_count}, 白={self.current_game.white_count}, "
                       f"步数={move_count}")

            # ========== 通知观察者 ==========
            self._notify_observers('board_updated')

        except Exception as e:
            logger.error(f"❌ 解析游戏状态失败: {e}")
            import traceback
            traceback.print_exc()

    def get_game_pgn(self) -> str:
        """获取当前游戏的PGN格式棋谱"""
        pgn_lines = []
        pgn_lines.append('[Event "STM32 Othello Game"]')
        pgn_lines.append(f'[Date "{datetime.now().strftime("%Y.%m.%d")}"]')
        pgn_lines.append('[Black "Player/AI"]')
        pgn_lines.append('[White "Player/AI"]')

        if self.current_game.status == GameStatus.BLACK_WIN:
            pgn_lines.append('[Result "1-0"]')
        elif self.current_game.status == GameStatus.WHITE_WIN:
            pgn_lines.append('[Result "0-1"]')
        elif self.current_game.status == GameStatus.DRAW:
            pgn_lines.append('[Result "1/2-1/2"]')
        else:
            pgn_lines.append('[Result "*"]')

        pgn_lines.append('')

        # 添加走法
        moves_line = ""
        for i, move in enumerate(self.current_game.moves_history):
            if i % 2 == 0:  # 黑方走法
                moves_line += f"{i//2 + 1}.{move.to_notation()} "
            else:  # 白方走法
                moves_line += f"{move.to_notation()} "

        pgn_lines.append(moves_line.strip())
        return '\n'.join(pgn_lines)

    def save_game(self, filename: str):
        """保存游戏到文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.current_game.to_dict(), f, indent=2, ensure_ascii=False)

    def load_game(self, filename: str):
        """从文件加载游戏"""
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.current_game.from_dict(data)
            self._notify_observers('game_loaded')

    def add_observer(self, callback):
        """添加状态观察者"""
        self.observers.append(callback)

    def _notify_observers(self, event, data=None):
        """通知观察者"""
        for callback in self.observers:
            try:
                callback(event, data)
            except Exception as e:
                print(f"Observer notification error: {e}")

    def get_statistics(self) -> Dict:
        """获取游戏统计信息"""
        total_games = len(self.games_history)
        if self.current_game.move_count > 0:
            total_games += 1

        black_wins = sum(1 for game in self.games_history if game.status == GameStatus.BLACK_WIN)
        white_wins = sum(1 for game in self.games_history if game.status == GameStatus.WHITE_WIN)
        draws = sum(1 for game in self.games_history if game.status == GameStatus.DRAW)

        return {
            'total_games': total_games,
            'black_wins': black_wins,
            'white_wins': white_wins,
            'draws': draws,
            'current_game_moves': self.current_game.move_count,
            'current_game_duration': self.current_game.get_game_duration()
        }