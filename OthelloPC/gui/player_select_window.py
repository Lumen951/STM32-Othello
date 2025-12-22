#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Player Select Window for STM32 Othello PC Client
玩家选择窗口 - 无密码轻量级版本

@author: STM32 Othello Project Team
@version: 1.0
@date: 2025-12-22
"""

import tkinter as tk
from tkinter import messagebox
from typing import Callable, Optional
import logging

from gui.styles import DieterStyle, DieterWidgets
from game.player_manager import get_player_manager


class PlayerSelectWindow(tk.Toplevel):
    """玩家选择窗口 - Dieter Rams极简风格"""

    def __init__(self, parent, title: str = None, on_confirm: Callable = None, allow_skip: bool = False):
        """
        初始化玩家选择窗口

        Args:
            parent: 父窗口
            title: 窗口标题/提示文本
            on_confirm: 确认回调函数
            allow_skip: 是否允许跳过（普通模式允许，闯关/计时模式不允许）
        """
        super().__init__(parent)

        self.player_manager = get_player_manager()
        self.on_confirm = on_confirm
        self.allow_skip = allow_skip
        self.logger = logging.getLogger(__name__)

        # 窗口设置
        self.title("选择玩家")
        self.geometry("450x380")
        self.configure(bg=DieterStyle.COLORS['white'])
        self.resizable(False, False)

        # 居中显示
        self._center_window()

        # 阻塞其他窗口
        self.transient(parent)
        self.grab_set()

        # 保存选择的用户名
        self.selected_username = None

        # 创建UI
        self._create_ui(title)

        # 焦点到输入框
        self.username_entry.focus_set()

    def _center_window(self):
        """窗口居中显示"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def _create_ui(self, custom_title: str = None):
        """创建用户界面"""
        # === 主容器 ===
        main_container = tk.Frame(self, bg=DieterStyle.COLORS['white'])
        main_container.pack(fill='both', expand=True, padx=30, pady=30)

        # === 标题 ===
        title_text = custom_title if custom_title else "选择玩家"
        title_label = tk.Label(
            main_container,
            text=title_text,
            font=('Arial', 16, 'bold'),
            bg=DieterStyle.COLORS['white'],
            fg=DieterStyle.COLORS['black']
        )
        title_label.pack(pady=(0, 25))

        # === 最近使用的玩家 ===
        recent_players = self.player_manager.get_recent_players()
        if recent_players:
            recent_label = tk.Label(
                main_container,
                text="最近使用：",
                font=('Arial', 11, 'bold'),
                bg=DieterStyle.COLORS['white'],
                fg=DieterStyle.COLORS['gray_dark']
            )
            recent_label.pack(anchor='w', pady=(0, 10))

            # 最近玩家按钮容器
            recent_frame = tk.Frame(main_container, bg=DieterStyle.COLORS['white'])
            recent_frame.pack(fill='x', pady=(0, 20))

            # 显示最多6个最近玩家
            for i, player_name in enumerate(recent_players[:6]):
                btn = tk.Button(
                    recent_frame,
                    text=player_name,
                    font=('Arial', 10),
                    bg=DieterStyle.COLORS['gray_light'],
                    fg=DieterStyle.COLORS['black'],
                    relief='flat',
                    padx=15,
                    pady=8,
                    cursor='hand2',
                    command=lambda name=player_name: self._on_select_recent_player(name)
                )
                btn.pack(side='left', padx=(0, 8) if i < 5 else 0)

                # 悬停效果
                btn.bind('<Enter>', lambda e, b=btn: b.config(bg=DieterStyle.COLORS['braun_orange'], fg=DieterStyle.COLORS['white']))
                btn.bind('<Leave>', lambda e, b=btn: b.config(bg=DieterStyle.COLORS['gray_light'], fg=DieterStyle.COLORS['black']))

        # === 或者输入新用户名 ===
        input_label = tk.Label(
            main_container,
            text="或输入新用户名：",
            font=('Arial', 11, 'bold'),
            bg=DieterStyle.COLORS['white'],
            fg=DieterStyle.COLORS['gray_dark']
        )
        input_label.pack(anchor='w', pady=(0, 10))

        # 输入框容器
        entry_frame = tk.Frame(main_container, bg=DieterStyle.COLORS['white'])
        entry_frame.pack(fill='x', pady=(0, 25))

        # 用户名输入框
        self.username_entry = tk.Entry(
            entry_frame,
            font=('Arial', 12),
            bg=DieterStyle.COLORS['white'],
            fg=DieterStyle.COLORS['black'],
            relief='solid',
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=DieterStyle.COLORS['gray_mid'],
            highlightcolor=DieterStyle.COLORS['braun_orange']
        )
        self.username_entry.pack(fill='x', ipady=8)
        self.username_entry.bind('<Return>', lambda e: self._on_confirm_clicked())

        # 字符计数器
        self.char_count_label = tk.Label(
            main_container,
            text="0/20",
            font=('Arial', 9),
            bg=DieterStyle.COLORS['white'],
            fg=DieterStyle.COLORS['gray_mid']
        )
        self.char_count_label.pack(anchor='e', pady=(0, 20))
        self.username_entry.bind('<KeyRelease>', self._update_char_count)

        # === 按钮区域 ===
        button_frame = tk.Frame(main_container, bg=DieterStyle.COLORS['white'])
        button_frame.pack(fill='x')

        # 确认按钮
        confirm_btn = tk.Button(
            button_frame,
            text="确认",
            font=('Arial', 11, 'bold'),
            bg=DieterStyle.COLORS['braun_orange'],
            fg=DieterStyle.COLORS['white'],
            relief='flat',
            padx=30,
            pady=10,
            cursor='hand2',
            command=self._on_confirm_clicked
        )
        confirm_btn.pack(side='left', expand=True, fill='x', padx=(0, 10 if self.allow_skip else 0))

        # 悬停效果
        confirm_btn.bind('<Enter>', lambda e: confirm_btn.config(bg='#FF7722'))
        confirm_btn.bind('<Leave>', lambda e: confirm_btn.config(bg=DieterStyle.COLORS['braun_orange']))

        # 跳过按钮（仅在允许时显示）
        if self.allow_skip:
            skip_btn = tk.Button(
                button_frame,
                text="跳过",
                font=('Arial', 11),
                bg=DieterStyle.COLORS['gray_light'],
                fg=DieterStyle.COLORS['gray_dark'],
                relief='flat',
                padx=30,
                pady=10,
                cursor='hand2',
                command=self._on_skip_clicked
            )
            skip_btn.pack(side='left', expand=True, fill='x')

            # 悬停效果
            skip_btn.bind('<Enter>', lambda e: skip_btn.config(bg=DieterStyle.COLORS['gray_mid'], fg=DieterStyle.COLORS['white']))
            skip_btn.bind('<Leave>', lambda e: skip_btn.config(bg=DieterStyle.COLORS['gray_light'], fg=DieterStyle.COLORS['gray_dark']))

    def _update_char_count(self, event=None):
        """更新字符计数器"""
        text = self.username_entry.get()
        count = len(text)
        self.char_count_label.config(text=f"{count}/20")

        # 超过限制时变红
        if count > 20:
            self.char_count_label.config(fg=DieterStyle.COLORS['error_red'])
        else:
            self.char_count_label.config(fg=DieterStyle.COLORS['gray_mid'])

    def _on_select_recent_player(self, player_name: str):
        """选择最近使用的玩家"""
        self.username_entry.delete(0, tk.END)
        self.username_entry.insert(0, player_name)
        self._update_char_count()

    def _on_confirm_clicked(self):
        """确认按钮点击"""
        username = self.username_entry.get().strip()

        # 验证用户名
        if not username:
            messagebox.showwarning("提示", "请输入用户名或选择最近使用的玩家", parent=self)
            return

        if len(username) > 20:
            messagebox.showwarning("提示", "用户名不能超过20个字符", parent=self)
            return

        # 不允许使用保留名称
        reserved_names = ["玩家1", "玩家2", "平局", "未登录", "未知"]
        if username in reserved_names:
            messagebox.showwarning("提示", f"不能使用保留名称：{username}", parent=self)
            return

        # 选择玩家
        success = self.player_manager.select_player(username)
        if not success:
            messagebox.showerror("错误", "选择玩家失败，请重试", parent=self)
            return

        self.logger.info(f"玩家已选择: {username}")

        # 保存选择的用户名
        self.selected_username = username

        # 调用确认回调
        if self.on_confirm:
            self.on_confirm()

        # 关闭窗口
        self.destroy()

    def _on_skip_clicked(self):
        """跳过按钮点击"""
        self.logger.info("用户跳过登录")
        self.destroy()


def show_player_select(parent, title: str = None, on_confirm: Callable = None, allow_skip: bool = False) -> Optional[str]:
    """
    显示玩家选择对话框（便捷函数）

    Args:
        parent: 父窗口
        title: 窗口标题
        on_confirm: 确认回调
        allow_skip: 是否允许跳过

    Returns:
        str: 选择的用户名，如果取消则返回None
    """
    window = PlayerSelectWindow(parent, title, on_confirm, allow_skip)
    parent.wait_window(window)
    return window.selected_username
