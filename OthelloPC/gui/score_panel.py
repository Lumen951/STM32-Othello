#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Score Panel for STM32 Othello PC Client
分数显示面板

@author: STM32 Othello Project Team
@version: 1.0
@date: 2025-12-09
"""

import tkinter as tk
from typing import Optional
import logging

from gui.styles import DieterStyle


class ScorePanel(tk.Frame):
    """分数显示面板"""

    def __init__(self, parent, score_manager):
        """
        初始化分数面板

        Args:
            parent: 父容器
            score_manager: 分数管理器
        """
        super().__init__(parent, bg=DieterStyle.COLORS['white'])

        self.score_manager = score_manager
        self.logger = logging.getLogger(__name__)

        # 动画相关
        self.animation_running = False
        self.target_black_score = 2
        self.target_white_score = 2

        # 创建UI
        self._create_ui()

        # 初始化显示
        self._update_display()

    def _create_ui(self):
        """创建用户界面"""
        # === 主容器 ===
        main_container = tk.Frame(self, bg=DieterStyle.COLORS['board_bg'],
                                 relief='solid', bd=2)
        main_container.pack(fill='both', expand=True, padx=5, pady=5)

        # === 标题 ===
        title_label = tk.Label(
            main_container,
            text="📊 分数统计",
            font=('Arial', 12, 'bold'),
            bg=DieterStyle.COLORS['board_bg'],
            fg=DieterStyle.COLORS['gray_dark']
        )
        title_label.pack(pady=(10, 5))

        # === 本局得分 ===
        current_frame = tk.Frame(main_container, bg='white', relief='ridge', bd=2)
        current_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(
            current_frame,
            text="本局得分",
            font=('Arial', 10, 'bold'),
            bg='white',
            fg=DieterStyle.COLORS['gray_dark']
        ).pack(pady=(5, 2))

        # 分数显示
        score_display_frame = tk.Frame(current_frame, bg='white')
        score_display_frame.pack(pady=(2, 5))

        # 黑子分数
        self.black_score_label = tk.Label(
            score_display_frame,
            text="2",
            font=('Arial', 24, 'bold'),
            bg='white',
            fg=DieterStyle.COLORS['braun_orange']
        )
        self.black_score_label.pack(side='left', padx=5)

        # VS
        tk.Label(
            score_display_frame,
            text=":",
            font=('Arial', 20, 'bold'),
            bg='white',
            fg=DieterStyle.COLORS['gray_mid']
        ).pack(side='left', padx=5)

        # 白子分数
        self.white_score_label = tk.Label(
            score_display_frame,
            text="2",
            font=('Arial', 24, 'bold'),
            bg='white',
            fg=DieterStyle.COLORS['gray_dark']
        )
        self.white_score_label.pack(side='left', padx=5)

        # 标签
        label_frame = tk.Frame(current_frame, bg='white')
        label_frame.pack(pady=(0, 5))

        tk.Label(
            label_frame,
            text="橙色",
            font=('Arial', 9),
            bg='white',
            fg=DieterStyle.COLORS['braun_orange']
        ).pack(side='left', padx=(0, 40))

        tk.Label(
            label_frame,
            text="白色",
            font=('Arial', 9),
            bg='white',
            fg=DieterStyle.COLORS['gray_dark']
        ).pack(side='left')

        # === 闯关模式统计（初始隐藏）===
        self.challenge_frame = tk.Frame(main_container, bg='white', relief='ridge', bd=2)
        # 初始不显示，等闯关模式启动时再显示

        # 闯关标题
        challenge_title = tk.Label(
            self.challenge_frame,
            text="🎯 闯关模式",
            font=('Arial', 11, 'bold'),
            bg='white',
            fg=DieterStyle.COLORS['braun_orange']
        )
        challenge_title.pack(pady=(8, 5))

        # 总分显示
        total_score_frame = tk.Frame(self.challenge_frame, bg='white')
        total_score_frame.pack(pady=5)

        tk.Label(
            total_score_frame,
            text="总分:",
            font=('Arial', 10),
            bg='white',
            fg=DieterStyle.COLORS['gray_dark']
        ).pack(side='left', padx=(0, 5))

        self.challenge_total_label = tk.Label(
            total_score_frame,
            text="0 / 188",
            font=('Arial', 16, 'bold'),
            bg='white',
            fg=DieterStyle.COLORS['data_blue']
        )
        self.challenge_total_label.pack(side='left')

        # 进度条
        progress_frame = tk.Frame(self.challenge_frame, bg='white')
        progress_frame.pack(fill='x', padx=15, pady=5)

        self.progress_canvas = tk.Canvas(
            progress_frame,
            width=200,
            height=20,
            bg='white',
            highlightthickness=0
        )
        self.progress_canvas.pack()

        # 绘制进度条背景
        self.progress_bg = self.progress_canvas.create_rectangle(
            0, 0, 200, 20,
            fill=DieterStyle.COLORS['gray_light'],
            outline=DieterStyle.COLORS['gray_mid']
        )
        self.progress_bar = self.progress_canvas.create_rectangle(
            0, 0, 0, 20,
            fill=DieterStyle.COLORS['success_green'],
            outline=''
        )
        self.progress_text = self.progress_canvas.create_text(
            100, 10,
            text="0%",
            font=('Arial', 9, 'bold'),
            fill=DieterStyle.COLORS['gray_dark']
        )

        # 闯关统计
        challenge_stats_frame = tk.Frame(self.challenge_frame, bg=DieterStyle.COLORS['gray_light'])
        challenge_stats_frame.pack(fill='x', padx=10, pady=5)

        # 局数
        stats_row1 = tk.Frame(challenge_stats_frame, bg=DieterStyle.COLORS['gray_light'])
        stats_row1.pack(fill='x', padx=5, pady=2)

        tk.Label(
            stats_row1,
            text="已玩局数:",
            font=('Arial', 9),
            bg=DieterStyle.COLORS['gray_light'],
            fg=DieterStyle.COLORS['gray_dark']
        ).pack(side='left')

        self.challenge_games_label = tk.Label(
            stats_row1,
            text="0",
            font=('Arial', 9, 'bold'),
            bg=DieterStyle.COLORS['gray_light'],
            fg=DieterStyle.COLORS['black']
        )
        self.challenge_games_label.pack(side='right')

        # 胜负统计
        stats_row2 = tk.Frame(challenge_stats_frame, bg=DieterStyle.COLORS['gray_light'])
        stats_row2.pack(fill='x', padx=5, pady=2)

        tk.Label(
            stats_row2,
            text="胜/负/平:",
            font=('Arial', 9),
            bg=DieterStyle.COLORS['gray_light'],
            fg=DieterStyle.COLORS['gray_dark']
        ).pack(side='left')

        self.challenge_record_label = tk.Label(
            stats_row2,
            text="0 / 0 / 0",
            font=('Arial', 9, 'bold'),
            bg=DieterStyle.COLORS['gray_light'],
            fg=DieterStyle.COLORS['black']
        )
        self.challenge_record_label.pack(side='right')

        # 连败警告
        stats_row3 = tk.Frame(challenge_stats_frame, bg=DieterStyle.COLORS['gray_light'])
        stats_row3.pack(fill='x', padx=5, pady=2)

        tk.Label(
            stats_row3,
            text="连败:",
            font=('Arial', 9),
            bg=DieterStyle.COLORS['gray_light'],
            fg=DieterStyle.COLORS['gray_dark']
        ).pack(side='left')

        self.challenge_losses_label = tk.Label(
            stats_row3,
            text="0 / 2",
            font=('Arial', 9, 'bold'),
            bg=DieterStyle.COLORS['gray_light'],
            fg=DieterStyle.COLORS['success_green']
        )
        self.challenge_losses_label.pack(side='right')

        # === 累计分数（普通模式） ===
        total_frame = tk.Frame(main_container, bg='white', relief='ridge', bd=2)
        total_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(
            total_frame,
            text="累计总分",
            font=('Arial', 10, 'bold'),
            bg='white',
            fg=DieterStyle.COLORS['gray_dark']
        ).pack(pady=(5, 2))

        self.total_score_label = tk.Label(
            total_frame,
            text="0",
            font=('Arial', 20, 'bold'),
            bg='white',
            fg=DieterStyle.COLORS['data_blue']
        )
        self.total_score_label.pack(pady=(2, 5))

        # === 最高分记录 ===
        record_frame = tk.Frame(main_container, bg='white', relief='ridge', bd=2)
        record_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(
            record_frame,
            text="最高分记录",
            font=('Arial', 10, 'bold'),
            bg='white',
            fg=DieterStyle.COLORS['gray_dark']
        ).pack(pady=(5, 2))

        self.highest_score_label = tk.Label(
            record_frame,
            text="0",
            font=('Arial', 18, 'bold'),
            bg='white',
            fg=DieterStyle.COLORS['success_green']
        )
        self.highest_score_label.pack(pady=(2, 2))

        self.highest_date_label = tk.Label(
            record_frame,
            text="暂无记录",
            font=('Arial', 8),
            bg='white',
            fg=DieterStyle.COLORS['gray_mid']
        )
        self.highest_date_label.pack(pady=(0, 5))

        # === 统计信息 ===
        stats_frame = tk.Frame(main_container, bg=DieterStyle.COLORS['gray_light'],
                              relief='solid', bd=1)
        stats_frame.pack(fill='x', padx=10, pady=(5, 10))

        # 总局数
        stats_row1 = tk.Frame(stats_frame, bg=DieterStyle.COLORS['gray_light'])
        stats_row1.pack(fill='x', padx=5, pady=2)

        tk.Label(
            stats_row1,
            text="总局数:",
            font=('Arial', 9),
            bg=DieterStyle.COLORS['gray_light'],
            fg=DieterStyle.COLORS['gray_dark']
        ).pack(side='left')

        self.total_games_label = tk.Label(
            stats_row1,
            text="0",
            font=('Arial', 9, 'bold'),
            bg=DieterStyle.COLORS['gray_light'],
            fg=DieterStyle.COLORS['black']
        )
        self.total_games_label.pack(side='right')

        # 胜率
        stats_row2 = tk.Frame(stats_frame, bg=DieterStyle.COLORS['gray_light'])
        stats_row2.pack(fill='x', padx=5, pady=2)

        tk.Label(
            stats_row2,
            text="胜率:",
            font=('Arial', 9),
            bg=DieterStyle.COLORS['gray_light'],
            fg=DieterStyle.COLORS['gray_dark']
        ).pack(side='left')

        self.win_rate_label = tk.Label(
            stats_row2,
            text="0.0%",
            font=('Arial', 9, 'bold'),
            bg=DieterStyle.COLORS['gray_light'],
            fg=DieterStyle.COLORS['black']
        )
        self.win_rate_label.pack(side='right')

        # 连胜
        stats_row3 = tk.Frame(stats_frame, bg=DieterStyle.COLORS['gray_light'])
        stats_row3.pack(fill='x', padx=5, pady=2)

        tk.Label(
            stats_row3,
            text="连胜:",
            font=('Arial', 9),
            bg=DieterStyle.COLORS['gray_light'],
            fg=DieterStyle.COLORS['gray_dark']
        ).pack(side='left')

        self.consecutive_wins_label = tk.Label(
            stats_row3,
            text="0",
            font=('Arial', 9, 'bold'),
            bg=DieterStyle.COLORS['gray_light'],
            fg=DieterStyle.COLORS['success_green']
        )
        self.consecutive_wins_label.pack(side='right')

    def update_current_score(self, black_score: int, white_score: int, animate: bool = True):
        """
        更新当前分数

        Args:
            black_score: 黑子分数
            white_score: 白子分数
            animate: 是否使用动画
        """
        self.score_manager.update_current_score(black_score, white_score)

        if animate and not self.animation_running:
            self.target_black_score = black_score
            self.target_white_score = white_score
            self._animate_score_change()
        else:
            self.black_score_label.config(text=str(black_score))
            self.white_score_label.config(text=str(white_score))

    def update_total_score(self, total_score: int):
        """
        更新累计分数

        Args:
            total_score: 累计分数
        """
        self.score_manager.total_score = total_score
        self.total_score_label.config(text=str(total_score))

    def update_statistics(self):
        """更新统计信息"""
        stats = self.score_manager.get_statistics()

        self.total_games_label.config(text=str(stats['total_games']))
        self.win_rate_label.config(text=f"{stats['win_rate']:.1f}%")
        self.consecutive_wins_label.config(text=str(stats['consecutive_wins']))
        self.total_score_label.config(text=str(stats['total_score']))
        self.highest_score_label.config(text=str(stats['highest_score']))

        if stats['highest_score_date']:
            self.highest_date_label.config(text=stats['highest_score_date'])
        else:
            self.highest_date_label.config(text="暂无记录")

    def _update_display(self):
        """更新显示"""
        self.black_score_label.config(text=str(self.score_manager.current_black_score))
        self.white_score_label.config(text=str(self.score_manager.current_white_score))
        self.update_statistics()

    def _animate_score_change(self):
        """分数变化动画"""
        if self.animation_running:
            return

        self.animation_running = True
        current_black = int(self.black_score_label.cget('text'))
        current_white = int(self.white_score_label.cget('text'))

        # 简单的数字递增动画
        if current_black < self.target_black_score:
            current_black += 1
            self.black_score_label.config(text=str(current_black))

        if current_white < self.target_white_score:
            current_white += 1
            self.white_score_label.config(text=str(current_white))

        # 检查是否完成
        if (current_black >= self.target_black_score and
            current_white >= self.target_white_score):
            self.animation_running = False
        else:
            self.after(50, self._animate_score_change)

    def reset_display(self):
        """重置显示"""
        self.black_score_label.config(text="2")
        self.white_score_label.config(text="2")
        self.update_statistics()

    def show_challenge_mode(self, show: bool = True):
        """
        显示/隐藏闯关模式统计

        Args:
            show: True=显示，False=隐藏
        """
        if show:
            self.challenge_frame.pack(fill='x', padx=10, pady=5, before=self.total_score_label.master)
        else:
            self.challenge_frame.pack_forget()

    def update_challenge_stats(self, stats):
        """
        更新闯关模式统计

        Args:
            stats: ChallengeStats对象
        """
        # 更新总分
        self.challenge_total_label.config(text=f"{stats.total_score} / 188")

        # 更新进度条
        progress = min(100, (stats.total_score / 188) * 100)
        bar_width = int(200 * progress / 100)
        self.progress_canvas.coords(self.progress_bar, 0, 0, bar_width, 20)
        self.progress_canvas.itemconfig(self.progress_text, text=f"{progress:.0f}%")

        # 根据进度改变进度条颜色
        if progress >= 80:
            color = DieterStyle.COLORS['success_green']
        elif progress >= 50:
            color = DieterStyle.COLORS['braun_orange']
        else:
            color = DieterStyle.COLORS['data_blue']
        self.progress_canvas.itemconfig(self.progress_bar, fill=color)

        # 更新局数
        self.challenge_games_label.config(text=str(stats.games_played))

        # 更新胜负统计
        self.challenge_record_label.config(
            text=f"{stats.games_won} / {stats.games_lost} / {stats.games_drawn}"
        )

        # 更新连败（带颜色警告）
        self.challenge_losses_label.config(text=f"{stats.consecutive_losses} / 2")
        if stats.consecutive_losses >= 1:
            self.challenge_losses_label.config(fg=DieterStyle.COLORS['error_red'])
        else:
            self.challenge_losses_label.config(fg=DieterStyle.COLORS['success_green'])
