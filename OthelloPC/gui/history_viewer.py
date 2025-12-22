#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
History Viewer Window for STM32 Othello PC Client
历史回看窗口

@author: STM32 Othello Project Team
@version: 1.0
@date: 2025-12-09
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
import logging

from gui.styles import DieterStyle, DieterWidgets
from gui.game_board import GameBoard
from game.replay_manager import ReplayManager
from data.game_history import GameHistoryManager


class HistoryViewerWindow(tk.Toplevel):
    """历史回看窗口"""

    def __init__(self, parent, history_manager: GameHistoryManager):
        """
        初始化历史回看窗口

        Args:
            parent: 父窗口
            history_manager: 历史记录管理器
        """
        super().__init__(parent)

        self.history_manager = history_manager
        self.replay_manager = ReplayManager()
        self.logger = logging.getLogger(__name__)

        # 窗口设置
        self.title("历史回看")
        self.geometry("900x700")
        self.configure(bg=DieterStyle.COLORS['white'])

        # 当前选中的记录
        self.selected_record = None

        # 棋盘组件
        self.game_board = None

        # 创建UI
        self._create_ui()

        # 加载历史记录列表
        self._load_history_list()

        # 注册回放管理器回调
        self.replay_manager.register_callback(self._on_replay_state_changed)

        # 启动更新循环
        self._update_replay()

    def _create_ui(self):
        """创建用户界面"""
        # === 主容器 ===
        main_container = tk.Frame(self, bg=DieterStyle.COLORS['white'])
        main_container.pack(fill='both', expand=True, padx=10, pady=10)

        # === 左侧：历史记录列表 ===
        left_frame = tk.Frame(main_container, bg=DieterStyle.COLORS['white'])
        left_frame.pack(side='left', fill='both', padx=(0, 10))

        # 标题
        tk.Label(
            left_frame,
            text="📜 历史记录",
            font=('Arial', 12, 'bold'),
            bg=DieterStyle.COLORS['white'],
            fg=DieterStyle.COLORS['gray_dark']
        ).pack(pady=(0, 10))

        # 列表框
        list_frame = tk.Frame(left_frame, bg=DieterStyle.COLORS['white'])
        list_frame.pack(fill='both', expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')

        self.history_listbox = tk.Listbox(
            list_frame,
            width=35,
            height=25,
            font=('Consolas', 9),
            bg=DieterStyle.COLORS['white'],
            fg=DieterStyle.COLORS['black'],
            selectbackground=DieterStyle.COLORS['braun_orange'],
            selectforeground=DieterStyle.COLORS['white'],
            yscrollcommand=scrollbar.set
        )
        self.history_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.history_listbox.yview)

        self.history_listbox.bind('<<ListboxSelect>>', self._on_select_record)

        # 按钮区域
        button_frame = tk.Frame(left_frame, bg=DieterStyle.COLORS['white'])
        button_frame.pack(fill='x', pady=(10, 0))

        load_btn = DieterWidgets.create_button(
            button_frame, "加载", self._load_selected, 'primary'
        )
        load_btn.pack(side='left', padx=(0, 5))

        delete_btn = DieterWidgets.create_button(
            button_frame, "删除", self._delete_selected, 'secondary'
        )
        delete_btn.pack(side='left')

        # === 右侧：回放区域 ===
        right_frame = tk.Frame(main_container, bg=DieterStyle.COLORS['white'])
        right_frame.pack(side='right', fill='both', expand=True)

        # 游戏信息
        info_frame = tk.Frame(right_frame, bg=DieterStyle.COLORS['board_bg'],
                             relief='solid', bd=2)
        info_frame.pack(fill='x', pady=(0, 10))

        self.info_label = tk.Label(
            info_frame,
            text="请选择一个历史记录",
            font=('Arial', 10),
            bg=DieterStyle.COLORS['board_bg'],
            fg=DieterStyle.COLORS['gray_dark'],
            justify='left'
        )
        self.info_label.pack(padx=10, pady=10)

        # 棋盘（使用临时游戏状态）
        from game.game_state import GameState
        temp_state = GameState()
        temp_state.start_new_game()

        self.game_board = GameBoard(
            right_frame,
            temp_state,
            on_move_callback=None
        )
        self.game_board.pack(pady=10)
        self.game_board.set_interactive(False)  # 禁用交互（只读模式）

        # 回放控制面板
        control_frame = tk.Frame(right_frame, bg=DieterStyle.COLORS['board_bg'],
                                relief='solid', bd=2)
        control_frame.pack(fill='x', pady=(10, 0))

        # 进度显示
        progress_frame = tk.Frame(control_frame, bg=DieterStyle.COLORS['board_bg'])
        progress_frame.pack(fill='x', padx=10, pady=(10, 5))

        self.progress_label = tk.Label(
            progress_frame,
            text="0 / 0",
            font=('Arial', 10, 'bold'),
            bg=DieterStyle.COLORS['board_bg'],
            fg=DieterStyle.COLORS['black']
        )
        self.progress_label.pack()

        # 进度条
        self.progress_scale = tk.Scale(
            control_frame,
            from_=0,
            to=100,
            orient='horizontal',
            bg=DieterStyle.COLORS['board_bg'],
            fg=DieterStyle.COLORS['black'],
            highlightthickness=0,
            command=self._on_progress_changed
        )
        self.progress_scale.pack(fill='x', padx=10, pady=(0, 10))

        # 控制按钮
        btn_frame = tk.Frame(control_frame, bg=DieterStyle.COLORS['board_bg'])
        btn_frame.pack(pady=(0, 10))

        # 第一行按钮
        row1 = tk.Frame(btn_frame, bg=DieterStyle.COLORS['board_bg'])
        row1.pack(pady=(0, 5))

        self.start_btn = DieterWidgets.create_button(
            row1, "⏮ 开始", self._jump_to_start, 'secondary'
        )
        self.start_btn.config(width=8)
        self.start_btn.pack(side='left', padx=2)

        self.backward_btn = DieterWidgets.create_button(
            row1, "◀ 后退", self._step_backward, 'secondary'
        )
        self.backward_btn.config(width=8)
        self.backward_btn.pack(side='left', padx=2)

        self.play_btn = DieterWidgets.create_button(
            row1, "▶ 播放", self._toggle_play, 'primary'
        )
        self.play_btn.config(width=8)
        self.play_btn.pack(side='left', padx=2)

        self.forward_btn = DieterWidgets.create_button(
            row1, "▶ 前进", self._step_forward, 'secondary'
        )
        self.forward_btn.config(width=8)
        self.forward_btn.pack(side='left', padx=2)

        self.end_btn = DieterWidgets.create_button(
            row1, "⏭ 结束", self._jump_to_end, 'secondary'
        )
        self.end_btn.config(width=8)
        self.end_btn.pack(side='left', padx=2)

        # 第二行：速度控制
        row2 = tk.Frame(btn_frame, bg=DieterStyle.COLORS['board_bg'])
        row2.pack()

        tk.Label(
            row2,
            text="速度:",
            font=('Arial', 9),
            bg=DieterStyle.COLORS['board_bg'],
            fg=DieterStyle.COLORS['gray_dark']
        ).pack(side='left', padx=(0, 5))

        self.speed_var = tk.StringVar(value="1.0x")
        speed_combo = ttk.Combobox(
            row2,
            textvariable=self.speed_var,
            values=['0.5x', '1.0x', '2.0x', '4.0x'],
            state='readonly',
            width=8,
            font=('Arial', 9)
        )
        speed_combo.pack(side='left')
        speed_combo.bind('<<ComboboxSelected>>', self._on_speed_changed)

    def _load_history_list(self):
        """加载历史记录列表"""
        self.history_listbox.delete(0, tk.END)

        records = self.history_manager.get_all_records()
        for record in records:
            self.history_listbox.insert(tk.END, record.get_summary())

        self.logger.info(f"加载了 {len(records)} 条历史记录")

    def _on_select_record(self, event):
        """选择记录"""
        selection = self.history_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        records = self.history_manager.get_all_records()
        if index < len(records):
            self.selected_record = records[index]
            self._update_info_display()

    def _load_selected(self):
        """加载选中的记录"""
        if not self.selected_record:
            messagebox.showwarning("提示", "请先选择一个历史记录")
            return

        # 加载到回放管理器
        if self.replay_manager.load_game(self.selected_record.full_data):
            self.replay_manager.jump_to_start()
            self._update_board()
            self._update_controls()
            messagebox.showinfo("成功", "历史记录已加载")
        else:
            messagebox.showerror("错误", "加载历史记录失败")

    def _delete_selected(self):
        """删除选中的记录"""
        if not self.selected_record:
            messagebox.showwarning("提示", "请先选择一个历史记录")
            return

        if messagebox.askyesno("确认", "确定要删除这条历史记录吗？"):
            if self.history_manager.delete_record(self.selected_record.game_id):
                self._load_history_list()
                self.selected_record = None


    def _jump_to_start(self):
        """跳转到开始"""
        self.replay_manager.jump_to_start()
        self._update_board()
        self._update_controls()

    def _step_backward(self):
        """后退一步"""
        self.replay_manager.step_backward()
        self._update_board()
        self._update_controls()

    def _toggle_play(self):
        """切换播放/暂停"""
        self.replay_manager.toggle_play_pause()
        self._update_play_button()

    def _step_forward(self):
        """前进一步"""
        self.replay_manager.step_forward()
        self._update_board()
        self._update_controls()

    def _jump_to_end(self):
        """跳转到结束"""
        self.replay_manager.jump_to_end()
        self._update_board()
        self._update_controls()

    def _on_speed_changed(self, event=None):
        """速度变化"""
        speed_str = self.speed_var.get()
        speed = float(speed_str.replace('x', ''))
        self.replay_manager.set_play_speed(speed)

    def _on_progress_changed(self, value):
        """进度条变化"""
        if not self.replay_manager.game_data:
            return

        total_moves = self.replay_manager.get_total_moves()
        if total_moves == 0:
            return

        # 计算目标步骤
        target_move = int((float(value) / 100.0) * total_moves) - 1
        self.replay_manager.jump_to_move(target_move)
        self._update_board()

    def _on_replay_state_changed(self):
        """回放状态变化"""
        self._update_board()
        self._update_controls()

    def _update_board(self):
        """更新棋盘显示"""
        state = self.replay_manager.get_current_state()
        if state and self.game_board:
            self.game_board.game_state = state
            self.game_board.update_board()

    def _update_controls(self):
        """更新控制按钮状态"""
        current, total = self.replay_manager.get_progress()
        self.progress_label.config(text=f"{current} / {total}")

        # 更新进度条（防止触发 command 回调）
        if total > 0:
            progress = (current / total) * 100

            # 【关键修复】暂时移除 command 回调，避免循环触发
            old_command = self.progress_scale.cget('command')
            self.progress_scale.config(command='')
            self.progress_scale.set(progress)
            self.progress_scale.config(command=old_command)

        # 更新按钮状态
        has_data = self.replay_manager.game_data is not None
        at_start = self.replay_manager.is_at_start()
        at_end = self.replay_manager.is_at_end()

        self.start_btn.config(state='normal' if has_data and not at_start else 'disabled')
        self.backward_btn.config(state='normal' if has_data and not at_start else 'disabled')
        self.play_btn.config(state='normal' if has_data else 'disabled')
        self.forward_btn.config(state='normal' if has_data and not at_end else 'disabled')
        self.end_btn.config(state='normal' if has_data and not at_end else 'disabled')

    def _update_play_button(self):
        """更新播放按钮"""
        if self.replay_manager.is_playing:
            self.play_btn.config(text="⏸ 暂停")
        else:
            self.play_btn.config(text="▶ 播放")

    def _update_info_display(self):
        """更新信息显示"""
        if not self.selected_record:
            self.info_label.config(text="请选择一个历史记录")
            return

        info_text = (
            f"日期: {self.selected_record.date_str}\n"
            f"结果: {self.selected_record.winner}\n"
            f"得分: {self.selected_record.black_count} - {self.selected_record.white_count}\n"
            f"步数: {self.selected_record.move_count}\n"
            f"用时: {self.selected_record.duration:.1f}秒"
        )
        self.info_label.config(text=info_text)

    def _update_replay(self):
        """更新回放（定时调用）"""
        self.replay_manager.update()
        if self.replay_manager.is_playing:
            self._update_board()
            self._update_controls()
            self._update_play_button()

        # 继续调用
        self.after(100, self._update_replay)
