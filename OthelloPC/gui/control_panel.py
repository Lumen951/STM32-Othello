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
from game.player_manager import get_player_manager


class ControlPanel(tk.Frame):
    """游戏控制面板"""

    def __init__(self, parent, serial_handler, on_state_change: Optional[Callable] = None,
                 on_mode_change: Optional[Callable] = None, main_window=None):
        """
        初始化控制面板

        Args:
            parent: 父容器
            serial_handler: 串口处理器
            on_state_change: 状态变化回调函数
            on_mode_change: 模式变化回调函数
            main_window: 主窗口引用（用于登录检查）
        """
        super().__init__(parent, bg=DieterStyle.COLORS['white'])

        self.serial_handler = serial_handler
        self.on_state_change = on_state_change
        self.on_mode_change = on_mode_change
        self.main_window = main_window  # 保存主窗口引用
        self.logger = logging.getLogger(__name__)
        self.player_manager = get_player_manager()

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
            row1, "▶ 开始/重启", self._on_start, 'primary'
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

        # 第二行：结束、重置、刷新同步
        row2 = tk.Frame(control_frame, bg=DieterStyle.COLORS['board_bg'])
        row2.pack(fill='x')

        self.end_btn = DieterWidgets.create_button(
            row2, "⏹ 结束", self._on_end, 'secondary'
        )
        self.end_btn.pack(side='left', padx=(0, 5), fill='x', expand=True)

        self.reset_btn = DieterWidgets.create_button(
            row2, "🔄 重置", self._on_reset, 'secondary'
        )
        self.reset_btn.pack(side='left', padx=(0, 5), fill='x', expand=True)

        # === 新增：刷新同步按钮 ===
        self.sync_btn = DieterWidgets.create_button(
            row2, "🔄 刷新同步", self._on_sync, 'secondary'
        )
        self.sync_btn.pack(side='left', fill='x', expand=True)

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
            values=["普通模式", "闯关模式", "计时模式"],  # 移除"作弊模式"
            state='readonly',
            width=12,
            font=('Arial', 10)
        )
        self.mode_combo.pack(side='left', fill='x', expand=True)
        self.mode_combo.bind('<<ComboboxSelected>>', self._on_mode_changed)

        # === AI难度选择（仅闯关模式可见）===
        self.ai_difficulty_frame = tk.Frame(main_container, bg=DieterStyle.COLORS['board_bg'])
        self.ai_difficulty_frame.pack(fill='x', padx=10, pady=5)
        self.ai_difficulty_frame.pack_forget()  # 初始隐藏

        ai_label = tk.Label(
            self.ai_difficulty_frame,
            text="AI难度:",
            font=('Arial', 10, 'bold'),
            bg=DieterStyle.COLORS['board_bg'],
            fg=DieterStyle.COLORS['gray_dark']
        )
        ai_label.pack(side='left', padx=(0, 10))

        self.ai_difficulty_var = tk.StringVar(value="中等")
        self.ai_difficulty_combo = ttk.Combobox(
            self.ai_difficulty_frame,
            textvariable=self.ai_difficulty_var,
            values=["简单", "中等", "困难"],
            state='readonly',
            width=12,
            font=('Arial', 10)
        )
        self.ai_difficulty_combo.pack(side='left', fill='x', expand=True)

        # === 作弊模式叠加复选框（全局可见）===
        self.cheat_overlay_frame = tk.Frame(main_container, bg=DieterStyle.COLORS['board_bg'])
        self.cheat_overlay_frame.pack(fill='x', padx=10, pady=5)

        # 作弊模式复选框
        self.cheat_enabled_var = tk.BooleanVar(value=False)
        self.cheat_checkbox = ttk.Checkbutton(
            self.cheat_overlay_frame,
            text="开启作弊模式",
            variable=self.cheat_enabled_var,
            command=self._on_cheat_toggle
        )
        self.cheat_checkbox.pack(side='left', padx=(0, 20))

        # 颜色选择（仅作弊启用时可用）
        color_label = tk.Label(
            self.cheat_overlay_frame,
            text="选择颜色:",
            font=('Arial', 10),
            bg=DieterStyle.COLORS['board_bg'],
            fg=DieterStyle.COLORS['gray_dark']
        )
        color_label.pack(side='left', padx=(0, 10))

        self.cheat_color_var = tk.StringVar(value="黑棋")
        self.cheat_black_radio = ttk.Radiobutton(
            self.cheat_overlay_frame,
            text="黑棋",
            variable=self.cheat_color_var,
            value="黑棋",
            command=self._on_cheat_color_changed,
            state='disabled'  # 初始禁用
        )
        self.cheat_black_radio.pack(side='left', padx=(0, 10))

        self.cheat_white_radio = ttk.Radiobutton(
            self.cheat_overlay_frame,
            text="白棋",
            variable=self.cheat_color_var,
            value="白棋",
            command=self._on_cheat_color_changed,
            state='disabled'  # 初始禁用
        )
        self.cheat_white_radio.pack(side='left')

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
            text="💡 提示:\n• 未连接STM32时可在上位机玩游戏\n• 连接后可同步控制下位机\n• 下位机按键: 1=开始 *=暂停 #=继续",
            font=('Arial', 9),
            bg=DieterStyle.COLORS['board_bg'],
            fg=DieterStyle.COLORS['gray_mid'],
            justify='left'
        )
        hint_label.pack()

    def _on_start(self):
        """开始/重启游戏"""
        self.logger.info("开始/重启游戏")

        # 触发新游戏（通过回调通知主窗口）
        if self.on_state_change:
            self.on_state_change('new_game')

        # 如果连接了STM32，发送开始命令
        if self.serial_handler.is_connected():
            # 重要：重新发送当前模式和时间限制到STM32（确保模式不被重置）
            time_limit = 300 if self.current_mode == SerialProtocol.GAME_MODE_TIMED else 0
            self.serial_handler.send_mode_select(self.current_mode, time_limit)

            # 作弊模式通过 send_cheat_toggle() 单独控制，不是游戏模式
            # 已在 _on_cheat_toggle() 中处理，此处无需额外发送

            # 然后发送开始命令
            if self.serial_handler.send_game_start():
                self._set_state('playing')
            else:
                self.logger.error("发送开始命令失败")
        else:
            # 未连接时也可以开始游戏（仅上位机）
            self._set_state('playing')

    def _on_pause(self):
        """暂停游戏"""
        self.logger.info("暂停游戏")

        # 如果连接了STM32，发送暂停命令
        if self.serial_handler.is_connected():
            if self.serial_handler.send_game_pause():
                self._set_state('paused')
            else:
                self.logger.error("发送暂停命令失败")
        else:
            # 未连接时也可以暂停（仅上位机）
            self._set_state('paused')

    def _on_resume(self):
        """继续游戏"""
        self.logger.info("继续游戏")

        # 如果连接了STM32，发送继续命令
        if self.serial_handler.is_connected():
            if self.serial_handler.send_game_resume():
                self._set_state('playing')
            else:
                self.logger.error("发送继续命令失败")
        else:
            # 未连接时也可以继续（仅上位机）
            self._set_state('playing')

    def _on_end(self):
        """结束游戏"""
        self.logger.info("结束游戏")

        # 如果连接了STM32，发送结束命令
        if self.serial_handler.is_connected():
            if self.serial_handler.send_game_end():
                self._set_state('ended')
            else:
                self.logger.error("发送结束命令失败")
        else:
            # 未连接时也可以结束（仅上位机）
            self._set_state('ended')

    def _on_reset(self):
        """重置游戏"""
        self.logger.info("重置游戏")

        # 如果连接了STM32，发送重置命令
        if self.serial_handler.is_connected():
            if self.serial_handler.send_game_reset():
                self._set_state('idle')
            else:
                self.logger.error("发送重置命令失败")
        else:
            # 未连接时也可以重置（仅上位机）
            self._set_state('idle')

    def _on_sync(self):
        """手动同步上位机状态到下位机"""
        self.logger.info("请求手动同步游戏状态到STM32")

        if not self.serial_handler.is_connected():
            from tkinter import messagebox
            messagebox.showwarning(
                "同步失败",
                "未连接到STM32设备\n\n请先连接设备后再尝试同步"
            )
            return

        # 触发主窗口执行同步
        if self.on_state_change:
            self.on_state_change('sync_to_stm32')

    def _on_mode_changed(self, event=None):
        """模式选择变化"""
        mode_name = self.mode_var.get()

        # 映射模式名称到协议常量（移除作弊模式）
        mode_map = {
            "普通模式": SerialProtocol.GAME_MODE_NORMAL,
            "闯关模式": SerialProtocol.GAME_MODE_CHALLENGE,
            "计时模式": SerialProtocol.GAME_MODE_TIMED
        }

        new_mode = mode_map.get(mode_name, SerialProtocol.GAME_MODE_NORMAL)

        # 登录检查：闯关/计时模式需要登录
        if mode_name in ["闯关模式", "计时模式"]:
            if not self.player_manager.is_logged_in:
                self.logger.warning(f"{mode_name}需要登录玩家")

                # 恢复到之前的模式
                old_mode_name = {
                    SerialProtocol.GAME_MODE_NORMAL: "普通模式",
                    SerialProtocol.GAME_MODE_CHALLENGE: "闯关模式",
                    SerialProtocol.GAME_MODE_TIMED: "计时模式"
                }.get(self.current_mode, "普通模式")

                self.mode_var.set(old_mode_name)

                # 弹出登录窗口
                if self.main_window:
                    self.main_window.show_player_select_for_mode(mode_name, new_mode)
                return

        self.current_mode = new_mode

        # 显示/隐藏AI难度选择（仅闯关模式可见）
        if mode_name == "闯关模式":
            self.ai_difficulty_frame.pack(fill='x', padx=10, pady=5, after=self.mode_combo.master)
        else:
            # 普通模式和计时模式
            self.ai_difficulty_frame.pack_forget()

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
        """设置连接状态（不影响按钮可用性）"""
        # 无论是否连接，按钮都保持可用
        # 连接状态仅影响是否向STM32发送命令
        self._update_button_states()

    def get_current_state(self) -> str:
        """获取当前游戏状态"""
        return self.game_state

    def get_current_mode(self) -> int:
        """获取当前游戏模式"""
        return self.current_mode

    def get_ai_difficulty(self) -> int:
        """
        获取AI难度等级

        Returns:
            0=简单, 1=中等, 2=困难
        """
        difficulty_map = {
            "简单": 0,
            "中等": 1,
            "困难": 2
        }
        return difficulty_map.get(self.ai_difficulty_var.get(), 1)

    def _on_cheat_toggle(self):
        """作弊模式复选框切换"""
        is_enabled = self.cheat_enabled_var.get()

        # ========== 新增：防止重复触发 ==========
        if hasattr(self, '_last_cheat_state') and self._last_cheat_state == is_enabled:
            self.logger.debug("Cheat state unchanged, ignoring duplicate toggle")
            return  # 状态未变化，忽略

        self._last_cheat_state = is_enabled
        # ========== 新增结束 ==========

        # 启用/禁用颜色选择单选按钮
        state = 'normal' if is_enabled else 'disabled'
        self.cheat_black_radio.config(state=state)
        self.cheat_white_radio.config(state=state)

        # === 严格参数验证 ===
        color_name = self.cheat_color_var.get()

        # 验证颜色名称
        if color_name not in ["黑棋", "白棋"]:
            self.logger.error(f"❌ Invalid color name: {color_name}")
            self.cheat_enabled_var.set(not is_enabled)
            return

        # 映射颜色：1=黑棋, 2=白棋
        player_color = 1 if color_name == "黑棋" else 2

        # 二次验证：确保颜色值为整数1或2
        if not isinstance(player_color, int) or player_color not in [1, 2]:
            self.logger.error(f"❌ Color mapping failed: {color_name} -> {player_color}")
            self.cheat_enabled_var.set(not is_enabled)
            return

        # === 连接状态检查 ===
        if not self.serial_handler or not self.serial_handler.is_connected():
            self.logger.warning("⚠️ 未连接到STM32，无法发送作弊模式命令")
            # 恢复复选框状态
            self.cheat_enabled_var.set(not is_enabled)

            # 弹出提示框
            from tkinter import messagebox
            messagebox.showwarning(
                "连接错误",
                "未连接到STM32设备\n\n作弊模式需要与下位机通信，请先连接设备。"
            )
            return

        # === 发送作弊叠加命令到STM32 ===
        self.logger.info(f"📤 Sending cheat toggle: enable={is_enabled}, color={color_name} ({player_color})")

        success = self.serial_handler.send_cheat_toggle(is_enabled, player_color)

        if success:
            status = "启用" if is_enabled else "禁用"
            self.logger.info(f"✅ 作弊模式{status}成功: {color_name}")
        else:
            self.logger.error("❌ 发送作弊模式切换命令失败")
            # 恢复复选框状态
            self.cheat_enabled_var.set(not is_enabled)

            # 弹出错误提示
            from tkinter import messagebox
            messagebox.showerror(
                "通信错误",
                f"无法发送作弊模式命令到STM32\n\n请检查：\n1. 设备连接是否正常\n2. 串口通信是否稳定"
            )

        # ========== 通知主窗口作弊模式状态变化 ==========
        if self.main_window:
            self.main_window._cheat_mode_enabled = is_enabled
            self.logger.info(f"通知主窗口: 作弊模式={'启用' if is_enabled else '禁用'}")

    def _on_cheat_color_changed(self):
        """作弊模式颜色选择变化回调"""
        if not self.cheat_enabled_var.get():
            # 作弊模式未启用，忽略颜色变化
            self.logger.debug("Cheat mode not enabled, ignoring color change")
            return

        # === 严格参数验证 ===
        color_name = self.cheat_color_var.get()

        # 验证颜色名称
        if color_name not in ["黑棋", "白棋"]:
            self.logger.error(f"❌ Invalid color name: {color_name}")
            return

        # 映射颜色：1=黑棋, 2=白棋
        player_color = 1 if color_name == "黑棋" else 2

        # 二次验证：确保颜色值为整数1或2
        if not isinstance(player_color, int) or player_color not in [1, 2]:
            self.logger.error(f"❌ Color mapping failed: {color_name} -> {player_color}")
            return

        # ========== 新增：只更新上位机状态，不重复发送到STM32 ==========
        # 触发上位机的颜色选择回调（更新 current_player）
        if hasattr(self, 'on_cheat_color_selected') and self.on_cheat_color_selected:
            self.on_cheat_color_selected(player_color)

        self.logger.info(f"✅ 作弊颜色切换: {color_name} (仅上位机本地)")

        # ========== 移除原有的 STM32 通信代码（避免重复发送）==========
        # 不再调用 send_cheat_toggle()，因为这会导致下位机重新初始化作弊模式
        # 下位机的颜色切换通过按键 A/B 在本地完成

