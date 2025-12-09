#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Game Control Panel for STM32 Othello PC Client
游戏控制面板

@author: STM32 Othello Project Team
@version: 1.0
@date: 2025-12-09
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
import logging

from gui.styles import DieterStyle, DieterWidgets
from communication.serial_handler import SerialProtocol


class ControlPanel(tk.Frame):
    """游戏控制面板"""

    def __init__(self, parent, serial_handler, on_state_change: Optional[Callable] = None,
                 on_mode_change: Optional[Callable] = None):
        """
        初始化控制面板

        Args:
            parent: 父容器
            serial_handler: 串口处理器
            on_state_change: 状态变化回调函数
            on_mode_change: 模式变化回调函数
        """
        super().__init__(parent, bg=DieterStyle.COLORS['white'])

        self.serial_handler = serial_handler
        self.on_state_change = on_state_change
        self.on_mode_change = on_mode_change
        self.logger = logging.getLogger(__name__)

        # 当前游戏状态
        self.game_state = 'idle'  # idle, playing, paused, ended
        self.current_mode = SerialProtocol.GAME_MODE_NORMAL

        # 创建UI
        self._create_ui()

        # 初始化按钮状态
        self._update_button_states()

    def _create_ui(self):
        """创建用户界面"""
        # === 主容器 ===
        main_container = tk.Frame(self, bg=DieterStyle.COLORS['board_bg'],
                                 relief='solid', bd=2)
        main_container.pack(fill='both', expand=True, padx=5, pady=5)

        # === 标题 ===
        title_label = tk.Label(
            main_container,
            text="🎮 游戏控制",
            font=('Arial', 12, 'bold'),
            bg=DieterStyle.COLORS['board_bg'],
            fg=DieterStyle.COLORS['gray_dark']
        )
        title_label.pack(pady=(10, 5))

        # === 游戏控制按钮区域 ===
        control_frame = tk.Frame(main_container, bg=DieterStyle.COLORS['board_bg'])
        control_frame.pack(fill='x', padx=10, pady=5)

        # 第一行：开始、暂停、继续
        row1 = tk.Frame(control_frame, bg=DieterStyle.COLORS['board_bg'])
        row1.pack(fill='x', pady=(0, 5))

        self.start_btn = DieterWidgets.create_button(
            row1, "▶ 开始", self._on_start, 'primary'
        )
        self.start_btn.pack(side='left', padx=(0, 5), fill='x', expand=True)

        self.pause_btn = DieterWidgets.create_button(
            row1, "⏸ 暂停", self._on_pause, 'secondary'
        )
        self.pause_btn.pack(side='left', padx=(0, 5), fill='x', expand=True)

        self.resume_btn = DieterWidgets.create_button(
            row1, "▶ 继续", self._on_resume, 'secondary'
        )
        self.resume_btn.pack(side='left', fill='x', expand=True)

        # 第二行：结束、重置
        row2 = tk.Frame(control_frame, bg=DieterStyle.COLORS['board_bg'])
        row2.pack(fill='x')

        self.end_btn = DieterWidgets.create_button(
            row2, "⏹ 结束", self._on_end, 'secondary'
        )
        self.end_btn.pack(side='left', padx=(0, 5), fill='x', expand=True)

        self.reset_btn = DieterWidgets.create_button(
            row2, "🔄 重置", self._on_reset, 'secondary'
        )
        self.reset_btn.pack(side='left', fill='x', expand=True)

        # === 分隔线 ===
        separator = tk.Frame(main_container, height=2, bg=DieterStyle.COLORS['gray_light'])
        separator.pack(fill='x', padx=10, pady=10)

        # === 游戏模式选择 ===
        mode_frame = tk.Frame(main_container, bg=DieterStyle.COLORS['board_bg'])
        mode_frame.pack(fill='x', padx=10, pady=5)

        mode_label = tk.Label(
            mode_frame,
            text="游戏模式:",
            font=('Arial', 10, 'bold'),
            bg=DieterStyle.COLORS['board_bg'],
            fg=DieterStyle.COLORS['gray_dark']
        )
        mode_label.pack(side='left', padx=(0, 10))

        # 模式下拉框
        self.mode_var = tk.StringVar(value="普通模式")
        self.mode_combo = ttk.Combobox(
            mode_frame,
            textvariable=self.mode_var,
            values=["普通模式", "闯关模式", "计时模式"],
            state='readonly',
            width=12,
            font=('Arial', 10)
        )
        self.mode_combo.pack(side='left', fill='x', expand=True)
        self.mode_combo.bind('<<ComboboxSelected>>', self._on_mode_changed)

        # === 状态显示 ===
        status_frame = tk.Frame(main_container, bg='white', relief='ridge', bd=2)
        status_frame.pack(fill='x', padx=10, pady=(10, 5))

        tk.Label(
            status_frame,
            text="当前状态",
            font=('Arial', 10, 'bold'),
            bg='white',
            fg=DieterStyle.COLORS['gray_dark']
        ).pack(pady=(5, 2))

        self.state_display = tk.Label(
            status_frame,
            text="● 空闲",
            font=('Arial', 12, 'bold'),
            bg='white',
            fg=DieterStyle.COLORS['gray_mid']
        )
        self.state_display.pack(pady=(2, 5))

        # === 按键提示 ===
        hint_frame = tk.Frame(main_container, bg=DieterStyle.COLORS['board_bg'])
        hint_frame.pack(fill='x', padx=10, pady=(5, 10))

        hint_label = tk.Label(
            hint_frame,
            text="💡 下位机按键:\n1=开始 *=暂停 #=继续\nD=结束 0=重置",
            font=('Arial', 9),
            bg=DieterStyle.COLORS['board_bg'],
            fg=DieterStyle.COLORS['gray_mid'],
            justify='left'
        )
        hint_label.pack()

    def _on_start(self):
        """开始游戏"""
        if not self.serial_handler.is_connected():
            self.logger.warning("未连接到STM32，无法发送命令")
            return

        self.logger.info("发送开始游戏命令")
        if self.serial_handler.send_game_start():
            self._set_state('playing')
        else:
            self.logger.error("发送开始命令失败")

    def _on_pause(self):
        """暂停游戏"""
        if not self.serial_handler.is_connected():
            self.logger.warning("未连接到STM32，无法发送命令")
            return

        self.logger.info("发送暂停游戏命令")
        if self.serial_handler.send_game_pause():
            self._set_state('paused')
        else:
            self.logger.error("发送暂停命令失败")

    def _on_resume(self):
        """继续游戏"""
        if not self.serial_handler.is_connected():
            self.logger.warning("未连接到STM32，无法发送命令")
            return

        self.logger.info("发送继续游戏命令")
        if self.serial_handler.send_game_resume():
            self._set_state('playing')
        else:
            self.logger.error("发送继续命令失败")

    def _on_end(self):
        """结束游戏"""
        if not self.serial_handler.is_connected():
            self.logger.warning("未连接到STM32，无法发送命令")
            return

        self.logger.info("发送结束游戏命令")
        if self.serial_handler.send_game_end():
            self._set_state('ended')
        else:
            self.logger.error("发送结束命令失败")

    def _on_reset(self):
        """重置游戏"""
        if not self.serial_handler.is_connected():
            self.logger.warning("未连接到STM32，无法发送命令")
            return

        self.logger.info("发送重置游戏命令")
        if self.serial_handler.send_game_reset():
            self._set_state('idle')
        else:
            self.logger.error("发送重置命令失败")

    def _on_mode_changed(self, event=None):
        """模式选择变化"""
        mode_name = self.mode_var.get()

        # 映射模式名称到协议常量
        mode_map = {
            "普通模式": SerialProtocol.GAME_MODE_NORMAL,
            "闯关模式": SerialProtocol.GAME_MODE_CHALLENGE,
            "计时模式": SerialProtocol.GAME_MODE_TIMED
        }

        self.current_mode = mode_map.get(mode_name, SerialProtocol.GAME_MODE_NORMAL)

        # 调用模式变化回调
        if self.on_mode_change:
            self.on_mode_change(self.current_mode)

        if not self.serial_handler.is_connected():
            self.logger.warning("未连接到STM32，无法发送模式选择命令")
            return

        # 发送模式选择命令
        time_limit = 300 if self.current_mode == SerialProtocol.GAME_MODE_TIMED else 0

        self.logger.info(f"发送模式选择命令: {mode_name} (0x{self.current_mode:02X})")
        if self.serial_handler.send_mode_select(self.current_mode, time_limit):
            self.logger.info(f"模式切换成功: {mode_name}")
        else:
            self.logger.error("发送模式选择命令失败")

    def _set_state(self, new_state: str):
        """设置游戏状态"""
        self.game_state = new_state
        self._update_button_states()
        self._update_state_display()

        # 调用状态变化回调
        if self.on_state_change:
            self.on_state_change(new_state)

    def _update_button_states(self):
        """更新按钮状态"""
        # 根据当前状态启用/禁用按钮
        if self.game_state == 'idle':
            self.start_btn.config(state='normal')
            self.pause_btn.config(state='disabled')
            self.resume_btn.config(state='disabled')
            self.end_btn.config(state='disabled')
            self.reset_btn.config(state='normal')
            self.mode_combo.config(state='readonly')

        elif self.game_state == 'playing':
            self.start_btn.config(state='disabled')
            self.pause_btn.config(state='normal')
            self.resume_btn.config(state='disabled')
            self.end_btn.config(state='normal')
            self.reset_btn.config(state='normal')
            self.mode_combo.config(state='disabled')

        elif self.game_state == 'paused':
            self.start_btn.config(state='disabled')
            self.pause_btn.config(state='disabled')
            self.resume_btn.config(state='normal')
            self.end_btn.config(state='normal')
            self.reset_btn.config(state='normal')
            self.mode_combo.config(state='disabled')

        elif self.game_state == 'ended':
            self.start_btn.config(state='normal')
            self.pause_btn.config(state='disabled')
            self.resume_btn.config(state='disabled')
            self.end_btn.config(state='disabled')
            self.reset_btn.config(state='normal')
            self.mode_combo.config(state='readonly')

    def _update_state_display(self):
        """更新状态显示"""
        state_config = {
            'idle': ('● 空闲', DieterStyle.COLORS['gray_mid']),
            'playing': ('● 进行中', DieterStyle.COLORS['success_green']),
            'paused': ('● 已暂停', DieterStyle.COLORS['braun_orange']),
            'ended': ('● 已结束', DieterStyle.COLORS['error_red'])
        }

        text, color = state_config.get(self.game_state, ('● 未知', DieterStyle.COLORS['gray_mid']))
        self.state_display.config(text=text, fg=color)

    def set_connection_state(self, connected: bool):
        """设置连接状态"""
        if not connected:
            # 断开连接时禁用所有控制按钮
            self.start_btn.config(state='disabled')
            self.pause_btn.config(state='disabled')
            self.resume_btn.config(state='disabled')
            self.end_btn.config(state='disabled')
            self.reset_btn.config(state='disabled')
            self.mode_combo.config(state='disabled')
        else:
            # 连接时根据当前状态更新按钮
            self._update_button_states()

    def get_current_state(self) -> str:
        """获取当前游戏状态"""
        return self.game_state

    def get_current_mode(self) -> int:
        """获取当前游戏模式"""
        return self.current_mode
