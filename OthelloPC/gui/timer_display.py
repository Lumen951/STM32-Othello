#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Timer Display Component for STM32 Othello PC Client
计时显示组件

@author: STM32 Othello Project Team
@version: 1.0
@date: 2025-12-15
"""

import tkinter as tk
from tkinter import ttk, simpledialog
from typing import Optional
import logging

from gui.styles import DieterStyle, DieterWidgets


class TimerDisplay(tk.Frame):
    """计时显示组件

    功能：
    - 显示倒计时（MM:SS格式）
    - 颜色变化（绿色→黄色→红色）
    - 最后10秒闪烁动画
    - 进度条显示
    - 时长配置
    """

    def __init__(self, parent, timed_mode_manager):
        """初始化计时显示组件

        Args:
            parent: 父容器
            timed_mode_manager: 计时模式管理器
        """
        super().__init__(parent, bg=DieterStyle.COLORS['white'])

        self.timed_mode = timed_mode_manager
        self.logger = logging.getLogger(__name__)

        # 闪烁状态
        self._blink_visible = True
        self._blink_job = None

        # 创建UI
        self._setup_ui()

        self.logger.info("计时显示组件初始化完成")

    def _setup_ui(self):
        """创建用户界面 - 垂直紧凑布局，适合放在棋盘左侧"""
        # === 主容器 ===
        main_container = tk.Frame(self, bg=DieterStyle.COLORS['board_bg'],
                                 relief='solid', bd=2)
        main_container.pack(fill='both', expand=True, padx=5, pady=5)

        # === 垂直布局 ===
        # 标题
        title_label = tk.Label(
            main_container,
            text="⏱️",
            font=('Arial', 20),
            bg=DieterStyle.COLORS['board_bg'],
            fg=DieterStyle.COLORS['gray_dark']
        )
        title_label.pack(pady=(10, 5))

        # 时间显示（大字）
        self.time_label = tk.Label(
            main_container,
            text="03:00",
            font=('Arial', 24, 'bold'),
            bg=DieterStyle.COLORS['board_bg'],
            fg=DieterStyle.COLORS['success_green']
        )
        self.time_label.pack(pady=(0, 10))

        # 进度条（垂直）
        self.progress_var = tk.DoubleVar(value=100.0)
        self.progress_bar = ttk.Progressbar(
            main_container,
            variable=self.progress_var,
            maximum=100.0,
            mode='determinate',
            orient='vertical',
            length=200
        )
        self.progress_bar.pack(pady=(0, 10))

        # 设置按钮
        self.config_btn = tk.Button(
            main_container,
            text="⚙",
            command=self._on_config_duration,
            font=('Arial', 14),
            bg=DieterStyle.COLORS['gray_light'],
            fg=DieterStyle.COLORS['gray_dark'],
            relief='flat',
            bd=0,
            width=3,
            cursor='hand2'
        )
        self.config_btn.pack(pady=(0, 10))

        # 提示文字
        hint_label = tk.Label(
            main_container,
            text="时间到\n自动结束",
            font=('Arial', 8),
            bg=DieterStyle.COLORS['board_bg'],
            fg=DieterStyle.COLORS['gray_mid'],
            justify='center'
        )
        hint_label.pack(pady=(0, 10))

    def update_time(self, remaining: int):
        """更新显示的时间

        Args:
            remaining: 剩余秒数
        """
        # 格式化时间
        minutes = remaining // 60
        seconds = remaining % 60
        time_str = f"{minutes:02d}:{seconds:02d}"

        # 更新标签
        self.time_label.config(text=time_str)

        # 更新进度条（直接访问duration属性）
        duration = self.timed_mode.duration
        if duration > 0:
            progress = (remaining / duration) * 100.0
            self.progress_var.set(progress)

        # 颜色逻辑
        if remaining > 30:
            # 绿色（正常）
            color = DieterStyle.COLORS['success_green']
            self._stop_blink()
            self.time_label.config(fg=color)

        elif remaining > 10:
            # 黄色（警告）
            color = DieterStyle.COLORS['braun_orange']
            self._stop_blink()
            self.time_label.config(fg=color)

        else:
            # 红色（危险）+ 闪烁
            color = DieterStyle.COLORS['error_red']
            if self._blink_job is None:
                self._start_blink(color)

        self.logger.debug(f"计时更新：{time_str} (剩余{remaining}秒)")

    def _start_blink(self, color: str):
        """启动闪烁动画

        Args:
            color: 闪烁颜色
        """
        def blink():
            if self._blink_visible:
                self.time_label.config(fg=color)
            else:
                self.time_label.config(fg=DieterStyle.COLORS['board_bg'])

            self._blink_visible = not self._blink_visible
            self._blink_job = self.after(500, blink)

        blink()

    def _stop_blink(self):
        """停止闪烁动画"""
        if self._blink_job is not None:
            self.after_cancel(self._blink_job)
            self._blink_job = None
            self._blink_visible = True

    def _on_config_duration(self):
        """时长配置回调"""
        # 检查是否正在运行
        if self.timed_mode.is_running():
            tk.messagebox.showwarning(
                "无法设置",
                "计时模式正在运行，请先停止游戏"
            )
            return

        # 弹出输入对话框
        current_duration = self.timed_mode.get_duration()
        current_minutes = current_duration // 60

        duration_str = simpledialog.askstring(
            "设置时长",
            f"请输入游戏时长（分钟）：\n当前：{current_minutes}分钟",
            initialvalue=str(current_minutes)
        )

        if duration_str is None:
            return

        # 验证输入
        try:
            duration_minutes = int(duration_str)
            if duration_minutes <= 0 or duration_minutes > 60:
                tk.messagebox.showerror(
                    "输入错误",
                    "时长必须在1-60分钟之间"
                )
                return

            # 设置时长
            duration_seconds = duration_minutes * 60
            if self.timed_mode.set_duration(duration_seconds):
                # 更新显示
                self.update_time(duration_seconds)
                tk.messagebox.showinfo(
                    "设置成功",
                    f"游戏时长已设置为：{duration_minutes}分钟"
                )
                self.logger.info(f"时长设置为：{duration_minutes}分钟")

        except ValueError:
            tk.messagebox.showerror(
                "输入错误",
                "请输入有效的数字"
            )

    def reset_display(self):
        """重置显示（回到初始状态）"""
        duration = self.timed_mode.get_duration()
        self.update_time(duration)
        self._stop_blink()
        self.logger.debug("计时显示已重置")

    def show(self):
        """显示组件"""
        # 使用pack显示，放在棋盘左侧
        self.pack(side='left', padx=(0, 10))
        self.logger.debug("计时显示组件已显示")

    def hide(self):
        """隐藏组件"""
        self.pack_forget()
        self._stop_blink()
        self.logger.debug("计时显示组件已隐藏")


class TimerConfigDialog(tk.Toplevel):
    """时长配置对话框（可选的高级版本）

    提供更友好的时长配置界面
    """

    def __init__(self, parent, current_duration: int):
        """初始化对话框

        Args:
            parent: 父窗口
            current_duration: 当前时长（秒）
        """
        super().__init__(parent)

        self.result = None
        self.current_duration = current_duration

        self.title("计时模式 - 时长设置")
        self.geometry("320x200")
        self.resizable(False, False)

        # 居中显示
        self.transient(parent)
        self.grab_set()

        self._setup_ui()

        # 等待用户操作
        self.wait_window()

    def _setup_ui(self):
        """创建UI"""
        # === 主容器 ===
        main_frame = tk.Frame(self, bg=DieterStyle.COLORS['white'], padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)

        # === 标题 ===
        title_label = tk.Label(
            main_frame,
            text="设置游戏时长",
            font=('Arial', 14, 'bold'),
            bg=DieterStyle.COLORS['white'],
            fg=DieterStyle.COLORS['gray_dark']
        )
        title_label.pack(pady=(0, 20))

        # === 时长输入 ===
        input_frame = tk.Frame(main_frame, bg=DieterStyle.COLORS['white'])
        input_frame.pack(pady=(0, 20))

        tk.Label(
            input_frame,
            text="时长（分钟）：",
            font=('Arial', 11),
            bg=DieterStyle.COLORS['white']
        ).pack(side='left', padx=(0, 10))

        self.duration_var = tk.StringVar(value=str(self.current_duration // 60))
        duration_entry = tk.Entry(
            input_frame,
            textvariable=self.duration_var,
            font=('Arial', 11),
            width=10,
            justify='center'
        )
        duration_entry.pack(side='left')
        duration_entry.focus()

        # === 按钮区域 ===
        button_frame = tk.Frame(main_frame, bg=DieterStyle.COLORS['white'])
        button_frame.pack()

        ok_btn = DieterWidgets.create_button(
            button_frame, "确定", self._on_ok, 'primary'
        )
        ok_btn.pack(side='left', padx=(0, 10))

        cancel_btn = DieterWidgets.create_button(
            button_frame, "取消", self._on_cancel, 'secondary'
        )
        cancel_btn.pack(side='left')

    def _on_ok(self):
        """确定回调"""
        try:
            duration_minutes = int(self.duration_var.get())
            if duration_minutes <= 0 or duration_minutes > 60:
                tk.messagebox.showerror(
                    "输入错误",
                    "时长必须在1-60分钟之间"
                )
                return

            self.result = duration_minutes * 60
            self.destroy()

        except ValueError:
            tk.messagebox.showerror(
                "输入错误",
                "请输入有效的数字"
            )

    def _on_cancel(self):
        """取消回调"""
        self.result = None
        self.destroy()

    def get_result(self) -> Optional[int]:
        """获取结果

        Returns:
            时长（秒），如果取消则返回None
        """
        return self.result
