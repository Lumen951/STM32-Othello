#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive Game Board Component for STM32 Othello PC Client
交互式游戏棋盘组件

@author: STM32 Othello Project Team
@version: 1.0
@date: 2025-11-22
"""

import tkinter as tk
from tkinter import Canvas
import math
from typing import Optional, Callable, Tuple, List

from game.game_state import PieceType, GameState
from gui.styles import DieterStyle, AppTheme

class GameBoard(tk.Frame):
    """交互式游戏棋盘组件"""

    def __init__(self, parent, game_state: GameState, on_move_callback: Optional[Callable] = None,
                 check_cheat_mode: Optional[Callable] = None,
                 get_cheat_color: Optional[Callable] = None):
        super().__init__(parent, bg=DieterStyle.COLORS['white'])

        self.game_state = game_state
        self.on_move_callback = on_move_callback
        self.check_cheat_mode = check_cheat_mode  # 新增：检查作弊模式的回调
        self.get_cheat_color = get_cheat_color  # 新增：获取作弊模式选中颜色的回调

        # 棋盘配置
        self.board_size = DieterStyle.SIZES['board_size']
        self.cell_size = DieterStyle.SIZES['cell_size']
        self.piece_radius = DieterStyle.SIZES['piece_radius']

        # 颜色配置
        self.colors = AppTheme.get_board_colors()

        # 鼠标交互状态
        self.hover_position: Optional[Tuple[int, int]] = None
        self.show_valid_moves = True
        self.is_interactive = True  # 棋盘是否可交互

        # 创建棋盘画布
        self.canvas = Canvas(
            self,
            width=self.board_size,
            height=self.board_size,
            bg=self.colors['background'],
            highlightthickness=0
        )
        self.canvas.pack(padx=DieterStyle.SIZES['padding_medium'],
                        pady=DieterStyle.SIZES['padding_medium'])

        # 绑定鼠标事件
        self.canvas.bind('<Button-1>', self._on_click)
        self.canvas.bind('<Motion>', self._on_mouse_move)
        self.canvas.bind('<Leave>', self._on_mouse_leave)

        # 初始化棋盘
        self._setup_board()
        self.update_board()

    def _setup_board(self):
        """设置棋盘基本结构"""
        # 绘制棋盘网格
        for i in range(9):  # 9条线画出8×8网格
            x = i * self.cell_size
            y = i * self.cell_size

            # 垂直线
            self.canvas.create_line(
                x, 0, x, self.board_size,
                fill=self.colors['grid'],
                width=1,
                tags='grid'
            )

            # 水平线
            self.canvas.create_line(
                0, y, self.board_size, y,
                fill=self.colors['grid'],
                width=1,
                tags='grid'
            )

        # 绘制坐标标签
        self._draw_coordinates()

        # 绘制中心点标记
        self._draw_center_dots()

    def _draw_coordinates(self):
        """绘制坐标标签"""
        font_config = DieterStyle.get_fonts()['small']

        # 列标签 (A-H)
        for col in range(8):
            x = col * self.cell_size + self.cell_size // 2
            label = chr(ord('A') + col)
            self.canvas.create_text(
                x, -15,
                text=label,
                font=font_config,
                fill=DieterStyle.COLORS['gray_dark'],
                tags='coordinates'
            )
            self.canvas.create_text(
                x, self.board_size + 15,
                text=label,
                font=font_config,
                fill=DieterStyle.COLORS['gray_dark'],
                tags='coordinates'
            )

        # 行标签 (1-8)
        for row in range(8):
            y = row * self.cell_size + self.cell_size // 2
            label = str(row + 1)
            self.canvas.create_text(
                -15, y,
                text=label,
                font=font_config,
                fill=DieterStyle.COLORS['gray_dark'],
                tags='coordinates'
            )
            self.canvas.create_text(
                self.board_size + 15, y,
                text=label,
                font=font_config,
                fill=DieterStyle.COLORS['gray_dark'],
                tags='coordinates'
            )

    def _draw_center_dots(self):
        """绘制中心点标记"""
        # 在 D4, E4, D5, E5 位置绘制小点
        center_positions = [(3, 3), (3, 4), (4, 3), (4, 4)]
        for row, col in center_positions:
            x = col * self.cell_size + self.cell_size // 2
            y = row * self.cell_size + self.cell_size // 2
            self.canvas.create_oval(
                x - 2, y - 2, x + 2, y + 2,
                fill=DieterStyle.COLORS['gray_mid'],
                outline=DieterStyle.COLORS['gray_mid'],
                tags='center_dots'
            )

    def update_board(self):
        """更新棋盘显示"""
        # 清除旧的棋子和提示
        self.canvas.delete('pieces')
        self.canvas.delete('valid_moves')
        self.canvas.delete('hover')

        # 绘制棋子
        for row in range(8):
            for col in range(8):
                piece = self.game_state.board[row][col]
                if piece != PieceType.EMPTY:
                    self._draw_piece(row, col, piece)

        # 绘制有效走法提示
        if self.show_valid_moves and self.game_state.current_player:
            self._draw_valid_moves()

        # 绘制鼠标悬停效果
        if self.hover_position:
            self._draw_hover_highlight(*self.hover_position)

    def _draw_piece(self, row: int, col: int, piece: PieceType):
        """绘制棋子"""
        x = col * self.cell_size + self.cell_size // 2
        y = row * self.cell_size + self.cell_size // 2

        if piece == PieceType.BLACK:
            fill_color = self.colors['black_piece']
            outline_color = self.colors['piece_border']
        else:  # PieceType.WHITE
            fill_color = self.colors['white_piece']
            outline_color = self.colors['piece_border']

        # 绘制棋子
        self.canvas.create_oval(
            x - self.piece_radius, y - self.piece_radius,
            x + self.piece_radius, y + self.piece_radius,
            fill=fill_color,
            outline=outline_color,
            width=2,
            tags='pieces'
        )

    def _draw_valid_moves(self):
        """绘制有效走法提示"""
        valid_moves = self.game_state.get_valid_moves(self.game_state.current_player)

        for row, col in valid_moves:
            x = col * self.cell_size + self.cell_size // 2
            y = row * self.cell_size + self.cell_size // 2

            # 绘制小圆点提示
            self.canvas.create_oval(
                x - 6, y - 6, x + 6, y + 6,
                fill=self.colors['valid_move'],
                outline=self.colors['valid_move'],
                tags='valid_moves'
            )

    def _draw_hover_highlight(self, row: int, col: int):
        """绘制鼠标悬停高亮"""
        x1 = col * self.cell_size + 2
        y1 = row * self.cell_size + 2
        x2 = x1 + self.cell_size - 4
        y2 = y1 + self.cell_size - 4

        # ========== 新增：作弊模式下显示不同的悬停效果 ==========
        is_cheat_mode = self.check_cheat_mode() if self.check_cheat_mode else False

        if is_cheat_mode:
            # 作弊模式：所有位置都显示为可下棋
            color = self.colors['hover_highlight']
            width = 3
            is_valid = True
        else:
            # 正常模式：检查是否是有效走法
            is_valid = self.game_state.is_valid_move(row, col, self.game_state.current_player)
            if is_valid:
                color = self.colors['hover_highlight']
                width = 3
            else:
                color = self.colors['invalid_move']
                width = 2

        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline=color,
            width=width,
            fill='',
            tags='hover'
        )

        # 如果是有效走法（或作弊模式），绘制预览棋子
        if is_valid:
            x = col * self.cell_size + self.cell_size // 2
            y = row * self.cell_size + self.cell_size // 2

            # 在作弊模式下使用选中的颜色，否则使用当前玩家颜色
            if is_cheat_mode and self.get_cheat_color:
                cheat_color = self.get_cheat_color()  # 获取作弊模式选中的颜色 (1=BLACK, 2=WHITE)
                if cheat_color == 1:  # BLACK
                    fill_color = self.colors['black_piece']
                else:  # WHITE
                    fill_color = self.colors['white_piece']
            else:
                # 正常模式：使用当前玩家颜色
                if self.game_state.current_player == PieceType.BLACK:
                    fill_color = self.colors['black_piece']
                else:
                    fill_color = self.colors['white_piece']

            # 半透明预览效果
            self.canvas.create_oval(
                x - self.piece_radius + 5, y - self.piece_radius + 5,
                x + self.piece_radius - 5, y + self.piece_radius - 5,
                fill=fill_color,
                outline=color,
                width=2,
                stipple='gray25',  # 半透明效果
                tags='hover'
            )

    def _on_click(self, event):
        """处理鼠标点击事件"""
        # 检查棋盘是否可交互
        if not self.is_interactive:
            return

        col = event.x // self.cell_size
        row = event.y // self.cell_size

        # 检查坐标有效性
        if 0 <= row < 8 and 0 <= col < 8:
            # ========== 新增：作弊模式下跳过合法性检查 ==========
            is_cheat_mode = self.check_cheat_mode() if self.check_cheat_mode else False

            if is_cheat_mode:
                # 作弊模式：允许点击任意位置
                if self.on_move_callback:
                    self.on_move_callback(row, col)
            else:
                # 正常模式：检查是否是有效走法
                if self.game_state.is_valid_move(row, col, self.game_state.current_player):
                    if self.on_move_callback:
                        self.on_move_callback(row, col)

    def _on_mouse_move(self, event):
        """处理鼠标移动事件"""
        col = event.x // self.cell_size
        row = event.y // self.cell_size

        # 检查坐标有效性
        if 0 <= row < 8 and 0 <= col < 8:
            new_position = (row, col)
            if new_position != self.hover_position:
                self.hover_position = new_position
                self.update_board()
        else:
            if self.hover_position:
                self.hover_position = None
                self.update_board()

    def _on_mouse_leave(self, event):
        """处理鼠标离开事件"""
        if self.hover_position:
            self.hover_position = None
            self.update_board()

    def set_show_valid_moves(self, show: bool):
        """设置是否显示有效走法"""
        self.show_valid_moves = show
        self.update_board()

    def highlight_last_move(self):
        """高亮显示最后一步走法"""
        if self.game_state.moves_history:
            last_move = self.game_state.moves_history[-1]
            row, col = last_move.row, last_move.col

            x1 = col * self.cell_size + 1
            y1 = row * self.cell_size + 1
            x2 = x1 + self.cell_size - 2
            y2 = y1 + self.cell_size - 2

            self.canvas.delete('last_move')
            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline=DieterStyle.COLORS['braun_orange'],
                width=2,
                fill='',
                tags='last_move'
            )

    def animate_piece_flip(self, flipped_positions: List[Tuple[int, int]]):
        """动画显示翻转的棋子"""
        # 简单的闪烁效果
        for row, col in flipped_positions:
            x = col * self.cell_size + self.cell_size // 2
            y = row * self.cell_size + self.cell_size // 2

            # 创建闪烁效果
            highlight = self.canvas.create_oval(
                x - self.piece_radius - 3, y - self.piece_radius - 3,
                x + self.piece_radius + 3, y + self.piece_radius + 3,
                outline=DieterStyle.COLORS['braun_orange'],
                width=3,
                fill='',
                tags='animation'
            )

            # 500ms后移除动画
            self.after(500, lambda: self.canvas.delete('animation'))

    def reset_board(self):
        """重置棋盘显示"""
        self.hover_position = None
        self.canvas.delete('pieces')
        self.canvas.delete('valid_moves')
        self.canvas.delete('hover')
        self.canvas.delete('last_move')
        self.canvas.delete('animation')
        self.update_board()

    def get_cell_at_position(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        """根据像素坐标获取格子位置"""
        col = x // self.cell_size
        row = y // self.cell_size

        if 0 <= row < 8 and 0 <= col < 8:
            return (row, col)
        return None

    def set_interactive(self, enabled: bool):
        """
        设置棋盘是否可交互

        Args:
            enabled: True=可交互，False=禁用交互
        """
        self.is_interactive = enabled

        # 更新视觉反馈
        if not enabled:
            # 禁用时清除悬停效果
            self.hover_position = None
            self.update_board()
            # 可选：添加半透明遮罩效果
            self.canvas.config(cursor="arrow")
        else:
            self.canvas.config(cursor="hand2")