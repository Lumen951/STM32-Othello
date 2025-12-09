#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
History Panel Component for STM32 Othello PC Client
历史记录面板组件

@author: STM32 Othello Project Team
@version: 1.0
@date: 2025-11-22
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Optional, Callable
import time
from datetime import datetime

from game.game_state import GameState, GameStateManager, PieceType, GameStatus
from gui.styles import DieterStyle, DieterWidgets

class HistoryPanel(tk.Frame):
    """历史记录面板"""

    def __init__(self, parent, game_manager: GameStateManager,
                 on_analyze_callback: Optional[Callable] = None):
        super().__init__(parent, bg=DieterStyle.COLORS['white'])

        self.game_manager = game_manager
        self.on_analyze_callback = on_analyze_callback

        self.setup_ui()
        self.update_display()

        # 注册游戏状态观察者
        self.game_manager.add_observer(self._on_game_state_changed)

    def setup_ui(self):
        """设置用户界面"""
        # === 游戏状态区域 ===
        status_frame = DieterWidgets.create_panel(self, 'main')
        status_frame.pack(fill='x', padx=10, pady=(10, 5))

        # 标题
        title_label = DieterWidgets.create_label(status_frame, "游戏状态", 'heading')
        title_label.pack(anchor='w', padx=10, pady=(10, 5))

        # 状态信息容器
        self.status_info_frame = tk.Frame(status_frame, bg=DieterStyle.COLORS['panel_bg'])
        self.status_info_frame.pack(fill='x', padx=10, pady=(0, 10))

        # 创建状态标签
        self.current_player_label = DieterWidgets.create_label(
            self.status_info_frame, "当前回合: 黑方", 'body'
        )
        self.current_player_label.pack(anchor='w', pady=2)

        self.score_label = DieterWidgets.create_label(
            self.status_info_frame, "黑子: 2  白子: 2", 'body'
        )
        self.score_label.pack(anchor='w', pady=2)

        self.move_count_label = DieterWidgets.create_label(
            self.status_info_frame, "回合数: 第1手", 'body'
        )
        self.move_count_label.pack(anchor='w', pady=2)

        self.duration_label = DieterWidgets.create_label(
            self.status_info_frame, "游戏时长: 00:00", 'body'
        )
        self.duration_label.pack(anchor='w', pady=2)

        # === 棋谱记录区域 ===
        moves_frame = DieterWidgets.create_panel(self, 'main')
        moves_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # 标题和控制按钮
        moves_header_frame = tk.Frame(moves_frame, bg=DieterStyle.COLORS['panel_bg'])
        moves_header_frame.pack(fill='x', padx=10, pady=(10, 5))

        moves_title = DieterWidgets.create_label(moves_header_frame, "棋谱记录", 'heading')
        moves_title.pack(side='left')

        # 棋谱控制按钮
        self.export_btn = DieterWidgets.create_button(
            moves_header_frame, "导出", self._export_moves, 'secondary'
        )
        self.export_btn.pack(side='right', padx=(5, 0))

        self.clear_btn = DieterWidgets.create_button(
            moves_header_frame, "清空", self._clear_moves, 'secondary'
        )
        self.clear_btn.pack(side='right')

        # 棋谱显示区域
        self.moves_text = scrolledtext.ScrolledText(
            moves_frame,
            width=30,
            height=8,
            font=DieterStyle.get_fonts()['data'],
            bg=DieterStyle.COLORS['white'],
            fg=DieterStyle.COLORS['black'],
            relief='flat',
            bd=1,
            wrap='word',
            state='disabled'
        )
        self.moves_text.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # === 游戏历史区域 ===
        history_frame = DieterWidgets.create_panel(self, 'main')
        history_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # 标题
        history_title = DieterWidgets.create_label(history_frame, "游戏历史", 'heading')
        history_title.pack(anchor='w', padx=10, pady=(10, 5))

        # 历史列表
        history_list_frame = tk.Frame(history_frame, bg=DieterStyle.COLORS['panel_bg'])
        history_list_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # 创建表格
        columns = ('局次', '胜方', '比分', '用时')
        self.history_tree = ttk.Treeview(
            history_list_frame,
            columns=columns,
            show='headings',
            height=6
        )

        # 设置列
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=60, anchor='center')

        # 滚动条
        history_scrollbar = ttk.Scrollbar(
            history_list_frame,
            orient='vertical',
            command=self.history_tree.yview
        )
        self.history_tree.configure(yscrollcommand=history_scrollbar.set)

        self.history_tree.pack(side='left', fill='both', expand=True)
        history_scrollbar.pack(side='right', fill='y')

        # === 分析功能区域 ===
        analysis_frame = DieterWidgets.create_panel(self, 'main')
        analysis_frame.pack(fill='x', padx=10, pady=(5, 10))

        # 分析按钮
        analysis_btn_frame = tk.Frame(analysis_frame, bg=DieterStyle.COLORS['panel_bg'])
        analysis_btn_frame.pack(fill='x', padx=10, pady=10)

        self.analyze_btn = DieterWidgets.create_button(
            analysis_btn_frame, "DeepSeek分析", self._request_analysis, 'primary'
        )
        self.analyze_btn.pack(side='left')

        self.view_last_analysis_btn = DieterWidgets.create_button(
            analysis_btn_frame, "查看上次分析", self._view_last_analysis, 'secondary'
        )
        self.view_last_analysis_btn.pack(side='left', padx=(10, 0))

        # 分析状态显示
        self.analysis_status_label = DieterWidgets.create_label(
            analysis_btn_frame, "", 'small'
        )
        self.analysis_status_label.pack(side='right')

    def update_display(self):
        """更新显示内容"""
        game_state = self.game_manager.current_game

        # 更新游戏状态
        if game_state.current_player == PieceType.BLACK:
            player_text = "当前回合: 黑方"
        elif game_state.current_player == PieceType.WHITE:
            player_text = "当前回合: 白方"
        else:
            player_text = "游戏未开始"

        self.current_player_label.config(text=player_text)

        # 更新分数
        score_text = f"黑子: {game_state.black_count}  白子: {game_state.white_count}"
        self.score_label.config(text=score_text)

        # 更新回合数
        if game_state.move_count == 0:
            move_text = "回合数: 游戏开始"
        else:
            move_text = f"回合数: 第{game_state.move_count}手"
        self.move_count_label.config(text=move_text)

        # 更新游戏时长
        duration = game_state.get_game_duration()
        duration_text = f"游戏时长: {self._format_duration(duration)}"
        self.duration_label.config(text=duration_text)

        # 更新棋谱显示
        self._update_moves_display()

        # 更新游戏历史
        self._update_history_display()

        # 更新按钮状态
        self._update_button_states()

    def _update_moves_display(self):
        """更新棋谱显示"""
        game_state = self.game_manager.current_game

        self.moves_text.config(state='normal')
        self.moves_text.delete(1.0, tk.END)

        if game_state.moves_history:
            moves_lines = []
            current_line = ""

            for i, move in enumerate(game_state.moves_history):
                if i % 2 == 0:  # 黑方走法
                    move_num = i // 2 + 1
                    current_line = f"{move_num:2d}. {move.to_notation():<3}"
                else:  # 白方走法
                    current_line += f" {move.to_notation():<3}"
                    moves_lines.append(current_line)

            # 如果最后是黑方走法（奇数步数），添加未完成的行
            if len(game_state.moves_history) % 2 == 1:
                moves_lines.append(current_line)

            self.moves_text.insert(tk.END, "\n".join(moves_lines))

        # 显示游戏结果
        if game_state.status != GameStatus.PLAYING and game_state.status != GameStatus.NOT_STARTED:
            result_text = "\n\n游戏结束\n"
            if game_state.status == GameStatus.BLACK_WIN:
                result_text += f"黑方获胜 ({game_state.black_count}-{game_state.white_count})"
            elif game_state.status == GameStatus.WHITE_WIN:
                result_text += f"白方获胜 ({game_state.white_count}-{game_state.black_count})"
            else:
                result_text += f"平局 ({game_state.black_count}-{game_state.white_count})"

            self.moves_text.insert(tk.END, result_text)

        self.moves_text.config(state='disabled')

        # 自动滚动到底部
        self.moves_text.see(tk.END)

    def _update_history_display(self):
        """更新游戏历史显示"""
        # 清空现有项目
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        # 添加历史游戏
        for i, game in enumerate(self.game_manager.games_history):
            game_num = i + 1

            # 确定胜方
            if game.status == GameStatus.BLACK_WIN:
                winner = "黑方"
                score = f"{game.black_count}-{game.white_count}"
            elif game.status == GameStatus.WHITE_WIN:
                winner = "白方"
                score = f"{game.white_count}-{game.black_count}"
            else:
                winner = "平局"
                score = f"{game.black_count}-{game.white_count}"

            # 计算用时
            duration = self._format_duration(game.get_game_duration())

            self.history_tree.insert('', 'end', values=(game_num, winner, score, duration))

        # 如果当前游戏已开始，也添加到列表
        current_game = self.game_manager.current_game
        if current_game.move_count > 0:
            game_num = len(self.game_manager.games_history) + 1

            if current_game.status == GameStatus.PLAYING:
                winner = "进行中"
                score = f"{current_game.black_count}-{current_game.white_count}"
            elif current_game.status == GameStatus.BLACK_WIN:
                winner = "黑方"
                score = f"{current_game.black_count}-{current_game.white_count}"
            elif current_game.status == GameStatus.WHITE_WIN:
                winner = "白方"
                score = f"{current_game.white_count}-{current_game.black_count}"
            else:
                winner = "平局"
                score = f"{current_game.black_count}-{current_game.white_count}"

            duration = self._format_duration(current_game.get_game_duration())
            self.history_tree.insert('', 'end', values=(game_num, winner, score, duration))

    def _update_button_states(self):
        """更新按钮状态"""
        game_state = self.game_manager.current_game

        # 分析按钮 - 只要有走法记录就能分析（允许游戏进行中分析）
        if game_state.move_count > 0:
            self.analyze_btn.config(state='normal')
        else:
            self.analyze_btn.config(state='disabled')

        # 导出按钮 - 有走法记录时才能导出
        if game_state.moves_history:
            self.export_btn.config(state='normal')
        else:
            self.export_btn.config(state='disabled')

    def _format_duration(self, duration: float) -> str:
        """格式化时长显示"""
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def _on_game_state_changed(self, event, data=None):
        """游戏状态变化回调"""
        self.after(100, self.update_display)  # 延迟更新避免界面冲突

    def _export_moves(self):
        """导出棋谱"""
        from tkinter import filedialog, messagebox

        try:
            # 生成PGN格式棋谱
            pgn_content = self.game_manager.get_game_pgn()

            # 选择保存文件
            filename = filedialog.asksaveasfilename(
                title="导出棋谱",
                defaultextension=".pgn",
                filetypes=[
                    ("PGN棋谱文件", "*.pgn"),
                    ("文本文件", "*.txt"),
                    ("所有文件", "*.*")
                ]
            )

            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(pgn_content)
                messagebox.showinfo("导出成功", f"棋谱已保存到:\n{filename}")

        except Exception as e:
            messagebox.showerror("导出失败", f"导出棋谱时发生错误:\n{e}")

    def _clear_moves(self):
        """清空走法记录"""
        from tkinter import messagebox

        result = messagebox.askyesno("确认清空", "是否确定要清空当前游戏的走法记录？")
        if result:
            self.game_manager.current_game.moves_history.clear()
            self.game_manager.current_game.move_count = 0
            self.update_display()

    def _request_analysis(self):
        """请求DeepSeek分析"""
        if self.on_analyze_callback:
            # 显示分析状态
            self.analysis_status_label.config(
                text="正在分析...",
                fg=DieterStyle.COLORS['data_blue']
            )
            self.analyze_btn.config(state='disabled')

            # 调用分析回调
            self.on_analyze_callback()

    def _view_last_analysis(self):
        """查看上次分析结果"""
        # TODO: 实现查看上次分析的功能
        from tkinter import messagebox
        messagebox.showinfo("功能开发中", "查看上次分析功能正在开发中...")

    def set_analysis_status(self, status: str, is_error: bool = False):
        """设置分析状态显示"""
        color = DieterStyle.COLORS['error_red'] if is_error else DieterStyle.COLORS['success_green']
        self.analysis_status_label.config(text=status, fg=color)

        if not is_error:
            # 3秒后清除状态
            self.after(3000, lambda: self.analysis_status_label.config(text=""))

        # 重新启用分析按钮
        self._update_button_states()

    def refresh_display(self):
        """刷新显示"""
        self.update_display()