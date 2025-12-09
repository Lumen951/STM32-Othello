#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Leaderboard Window for STM32 Othello PC Client
排行榜窗口

@author: STM32 Othello Project Team
@version: 1.0
@date: 2025-12-09
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from typing import Optional
import logging

from gui.styles import DieterStyle, DieterWidgets
from game.leaderboard import Leaderboard


class LeaderboardWindow(tk.Toplevel):
    """排行榜窗口"""

    def __init__(self, parent, leaderboard: Leaderboard):
        """
        初始化排行榜窗口

        Args:
            parent: 父窗口
            leaderboard: 排行榜管理器
        """
        super().__init__(parent)

        self.leaderboard = leaderboard
        self.logger = logging.getLogger(__name__)

        # 窗口设置
        self.title("排行榜")
        self.geometry("700x600")
        self.configure(bg=DieterStyle.COLORS['white'])

        # 当前选择的模式
        self.current_mode = 'normal'

        # 创建UI
        self._create_ui()

        # 加载排行榜
        self._load_leaderboard()

    def _create_ui(self):
        """创建用户界面"""
        # === 主容器 ===
        main_container = tk.Frame(self, bg=DieterStyle.COLORS['white'])
        main_container.pack(fill='both', expand=True, padx=20, pady=20)

        # === 标题 ===
        title_label = tk.Label(
            main_container,
            text="🏆 排行榜",
            font=('Arial', 18, 'bold'),
            bg=DieterStyle.COLORS['white'],
            fg=DieterStyle.COLORS['black']
        )
        title_label.pack(pady=(0, 20))

        # === 模式选择 ===
        mode_frame = tk.Frame(main_container, bg=DieterStyle.COLORS['white'])
        mode_frame.pack(fill='x', pady=(0, 15))

        tk.Label(
            mode_frame,
            text="游戏模式:",
            font=('Arial', 11, 'bold'),
            bg=DieterStyle.COLORS['white'],
            fg=DieterStyle.COLORS['gray_dark']
        ).pack(side='left', padx=(0, 10))

        self.mode_var = tk.StringVar(value="普通模式")
        mode_combo = ttk.Combobox(
            mode_frame,
            textvariable=self.mode_var,
            values=["普通模式", "闯关模式", "计时模式"],
            state='readonly',
            width=15,
            font=('Arial', 10)
        )
        mode_combo.pack(side='left')
        mode_combo.bind('<<ComboboxSelected>>', self._on_mode_changed)

        # === 排行榜表格 ===
        table_frame = tk.Frame(main_container, bg=DieterStyle.COLORS['white'])
        table_frame.pack(fill='both', expand=True, pady=(0, 15))

        # 创建Treeview
        columns = ('rank', 'player', 'score', 'time', 'date')
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            height=15
        )

        # 定义列
        self.tree.heading('rank', text='排名')
        self.tree.heading('player', text='玩家')
        self.tree.heading('score', text='得分')
        self.tree.heading('time', text='用时')
        self.tree.heading('date', text='日期')

        # 设置列宽
        self.tree.column('rank', width=60, anchor='center')
        self.tree.column('player', width=150, anchor='w')
        self.tree.column('score', width=80, anchor='center')
        self.tree.column('time', width=100, anchor='center')
        self.tree.column('date', width=150, anchor='center')

        # 滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # === 统计信息 ===
        stats_frame = tk.Frame(main_container, bg=DieterStyle.COLORS['gray_light'],
                              relief='solid', bd=1)
        stats_frame.pack(fill='x', pady=(0, 15))

        self.stats_label = tk.Label(
            stats_frame,
            text="",
            font=('Arial', 9),
            bg=DieterStyle.COLORS['gray_light'],
            fg=DieterStyle.COLORS['gray_dark'],
            justify='left'
        )
        self.stats_label.pack(padx=10, pady=8)

        # === 按钮区域 ===
        button_frame = tk.Frame(main_container, bg=DieterStyle.COLORS['white'])
        button_frame.pack(fill='x')

        add_btn = DieterWidgets.create_button(
            button_frame, "添加记录", self._add_entry, 'primary'
        )
        add_btn.pack(side='left', padx=(0, 10))

        export_btn = DieterWidgets.create_button(
            button_frame, "导出CSV", self._export_csv, 'secondary'
        )
        export_btn.pack(side='left', padx=(0, 10))

        clear_btn = DieterWidgets.create_button(
            button_frame, "清空", self._clear_board, 'secondary'
        )
        clear_btn.pack(side='left')

    def _load_leaderboard(self):
        """加载排行榜"""
        # 清空表格
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 获取当前模式的排行榜
        board = self.leaderboard.get_board(self.current_mode)

        # 填充数据
        for i, entry in enumerate(board):
            rank = i + 1
            medal = ""
            if rank == 1:
                medal = "🥇"
            elif rank == 2:
                medal = "🥈"
            elif rank == 3:
                medal = "🥉"

            self.tree.insert('', 'end', values=(
                f"{medal} {rank}" if medal else str(rank),
                entry.player_name,
                f"{entry.score}分",
                f"{entry.duration:.1f}秒",
                entry.date_str
            ))

        # 更新统计信息
        self._update_statistics()

    def _on_mode_changed(self, event=None):
        """模式变化"""
        mode_name = self.mode_var.get()
        mode_map = {
            "普通模式": "normal",
            "闯关模式": "challenge",
            "计时模式": "timed"
        }
        self.current_mode = mode_map.get(mode_name, "normal")
        self._load_leaderboard()

    def _add_entry(self):
        """添加记录"""
        # 输入玩家名称
        player_name = simpledialog.askstring(
            "添加记录",
            "请输入玩家名称:",
            parent=self
        )
        if not player_name:
            return

        # 输入得分
        score_str = simpledialog.askstring(
            "添加记录",
            "请输入得分:",
            parent=self
        )
        if not score_str:
            return

        try:
            score = int(score_str)
        except ValueError:
            messagebox.showerror("错误", "得分必须是整数")
            return

        # 输入用时
        time_str = simpledialog.askstring(
            "添加记录",
            "请输入用时（秒）:",
            parent=self
        )
        if not time_str:
            return

        try:
            duration = float(time_str)
        except ValueError:
            messagebox.showerror("错误", "用时必须是数字")
            return

        # 添加到排行榜
        if self.leaderboard.add_entry(player_name, score, self.current_mode, duration):
            messagebox.showinfo("成功", "记录已添加到排行榜")
            self._load_leaderboard()
        else:
            messagebox.showerror("错误", "添加记录失败")

    def _export_csv(self):
        """导出CSV"""
        filename = filedialog.asksaveasfilename(
            title="导出排行榜",
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )

        if filename:
            if self.leaderboard.export_to_csv(filename, self.current_mode):
                messagebox.showinfo("成功", f"排行榜已导出到:\n{filename}")
            else:
                messagebox.showerror("错误", "导出失败")

    def _clear_board(self):
        """清空排行榜"""
        mode_name = self.mode_var.get()
        if messagebox.askyesno("确认", f"确定要清空{mode_name}的排行榜吗？"):
            self.leaderboard.clear_board(self.current_mode)
            self._load_leaderboard()
            messagebox.showinfo("成功", "排行榜已清空")

    def _update_statistics(self):
        """更新统计信息"""
        stats = self.leaderboard.get_statistics(self.current_mode)

        stats_text = (
            f"总记录数: {stats['total_entries']}  |  "
            f"最高分: {stats['highest_score']}  |  "
            f"平均分: {stats['average_score']:.1f}  |  "
            f"最快用时: {stats['fastest_time']:.1f}秒"
        )
        self.stats_label.config(text=stats_text)
