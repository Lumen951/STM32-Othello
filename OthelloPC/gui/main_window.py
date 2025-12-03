#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main Window for STM32 Othello PC Client
PC上位机主窗口

@author: STM32 Othello Project Team
@version: 1.0
@date: 2025-11-22
"""

import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Optional
import logging

from gui.styles import DieterStyle, DieterWidgets, AppTheme
from gui.game_board import GameBoard
from gui.history_panel import HistoryPanel
from gui.analysis_window import AnalysisReportWindow
from communication.serial_handler import SerialHandler
from game.game_state import GameStateManager
from analysis.deepseek_client import DeepSeekClient

class MainWindow:
    """PC上位机主窗口"""

    def __init__(self, root: tk.Tk, serial_handler: SerialHandler,
                 game_manager: GameStateManager, config=None):
        """
        初始化主窗口

        Args:
            root: Tkinter根窗口
            serial_handler: 串口处理器
            game_manager: 游戏状态管理器
            config: 配置对象
        """
        self.root = root
        self.serial_handler = serial_handler
        self.game_manager = game_manager
        self.config = config

        # 日志 (必须在其他初始化之前)
        self.logger = logging.getLogger(__name__)

        # UI组件
        self.game_board: Optional[GameBoard] = None
        self.history_panel: Optional[HistoryPanel] = None

        # DeepSeek客户端
        self.deepseek_client = None
        self._setup_deepseek_client()

        # 应用主题
        AppTheme.apply_to_window(self.root)

        # 创建界面
        self.setup_ui()

        # 注册游戏状态观察者
        self.game_manager.add_observer(self._on_game_state_changed)

        self.logger.info("主窗口初始化完成")

    def setup_ui(self):
        """设置用户界面"""
        # === 主布局 ===
        main_container = tk.Frame(self.root, bg=DieterStyle.COLORS['white'])
        main_container.pack(fill='both', expand=True)

        # === 左侧游戏区域 ===
        left_frame = tk.Frame(main_container, bg=DieterStyle.COLORS['white'])
        left_frame.pack(side='left', fill='both', expand=True, padx=(10, 5), pady=10)

        # 游戏标题
        title_label = DieterWidgets.create_label(left_frame, "STM32 黑白棋", 'title')
        title_label.pack(anchor='w', pady=(0, 10))

        # 游戏控制按钮
        control_frame = tk.Frame(left_frame, bg=DieterStyle.COLORS['white'])
        control_frame.pack(fill='x', pady=(0, 10))

        self.new_game_btn = DieterWidgets.create_button(
            control_frame, "新游戏", self._new_game, 'primary'
        )
        self.new_game_btn.pack(side='left', padx=(0, 10))

        self.connect_btn = DieterWidgets.create_button(
            control_frame, "连接STM32", self._toggle_connection, 'secondary'
        )
        self.connect_btn.pack(side='left', padx=(0, 10))

        # 连接状态指示
        self.status_label = DieterWidgets.create_label(
            control_frame, "未连接", 'small'
        )
        self.status_label.pack(side='left', padx=(10, 0))

        # 游戏棋盘
        self.game_board = GameBoard(
            left_frame,
            self.game_manager.current_game,
            on_move_callback=self._on_player_move
        )
        self.game_board.pack(pady=10)

        # === 右侧信息面板 ===
        right_frame = tk.Frame(main_container, bg=DieterStyle.COLORS['white'])
        right_frame.pack(side='right', fill='both', padx=(5, 10), pady=10)

        # 历史记录面板
        self.history_panel = HistoryPanel(
            right_frame,
            self.game_manager,
            on_analyze_callback=self._request_analysis
        )
        self.history_panel.pack(fill='both', expand=True)

        # === 菜单栏 ===
        self._create_menu()

        # 初始更新界面
        self._update_ui_state()

    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 游戏菜单
        game_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="游戏", menu=game_menu)
        game_menu.add_command(label="新游戏", command=self._new_game)
        game_menu.add_separator()
        game_menu.add_command(label="保存游戏", command=self._save_game)
        game_menu.add_command(label="加载游戏", command=self._load_game)
        game_menu.add_separator()
        game_menu.add_command(label="退出", command=self.root.quit)

        # 连接菜单
        connection_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="连接", menu=connection_menu)
        connection_menu.add_command(label="连接STM32", command=self._connect_stm32)
        connection_menu.add_command(label="断开连接", command=self._disconnect_stm32)
        connection_menu.add_separator()
        connection_menu.add_command(label="连接设置", command=self._connection_settings)

        # 分析菜单
        analysis_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="分析", menu=analysis_menu)
        analysis_menu.add_command(label="DeepSeek分析", command=self._request_analysis)
        analysis_menu.add_command(label="DeepSeek设置", command=self._deepseek_settings)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self._show_help)
        help_menu.add_command(label="关于", command=self._show_about)

    def _setup_deepseek_client(self):
        """设置DeepSeek客户端"""
        try:
            # 使用config对象初始化DeepSeek客户端
            # config对象会自动从.env和config.json读取所有DeepSeek配置
            self.deepseek_client = DeepSeekClient(config=self.config)

            if self.config and self.config.deepseek_api_key:
                self.logger.info("DeepSeek客户端初始化完成")
            else:
                self.logger.warning("未设置DeepSeek API密钥")

        except Exception as e:
            self.logger.error(f"DeepSeek客户端初始化失败: {e}")
            self.deepseek_client = DeepSeekClient()  # 创建无密钥版本

    def _new_game(self):
        """开始新游戏"""
        try:
            self.game_manager.start_new_game()

            # 更新棋盘显示
            if self.game_board:
                self.game_board.game_state = self.game_manager.current_game
                self.game_board.reset_board()

            # 如果连接了STM32，发送新游戏命令
            if self.serial_handler.is_connected():
                self.serial_handler.send_new_game()

            self.logger.info("开始新游戏")

        except Exception as e:
            self.logger.error(f"开始新游戏失败: {e}")
            messagebox.showerror("错误", f"开始新游戏时发生错误:\\n{e}")

    def _toggle_connection(self):
        """切换STM32连接状态"""
        if self.serial_handler.is_connected():
            self._disconnect_stm32()
        else:
            self._connect_stm32()

    def _connect_stm32(self):
        """连接STM32设备"""
        try:
            # 获取可用端口
            ports = self.serial_handler.get_available_ports()

            if not ports:
                messagebox.showwarning("连接失败", "未找到可用的串口设备")
                return

            # 尝试连接
            success = self.serial_handler.connect()

            if success:
                self.logger.info("STM32连接成功")
                messagebox.showinfo("连接成功", f"已成功连接到STM32设备")
            else:
                messagebox.showerror("连接失败", "无法连接到STM32设备，请检查设备连接")

        except Exception as e:
            self.logger.error(f"STM32连接失败: {e}")
            messagebox.showerror("连接错误", f"连接STM32时发生错误:\\n{e}")

        self._update_ui_state()

    def _disconnect_stm32(self):
        """断开STM32连接"""
        try:
            self.serial_handler.disconnect()
            self.logger.info("STM32连接已断开")

        except Exception as e:
            self.logger.error(f"断开STM32连接失败: {e}")

        self._update_ui_state()

    def _connection_settings(self):
        """连接设置对话框"""
        # 这里可以实现连接设置对话框
        messagebox.showinfo("功能开发中", "连接设置功能正在开发中...")

    def _deepseek_settings(self):
        """DeepSeek设置对话框"""
        # 创建设置对话框
        settings_window = tk.Toplevel(self.root)
        settings_window.title("DeepSeek API 设置")
        settings_window.geometry("500x350")
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()

        # 应用主题
        settings_window.configure(bg=DieterStyle.COLORS['white'])

        # API密钥设置
        main_frame = DieterWidgets.create_panel(settings_window, 'main')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        title_label = DieterWidgets.create_label(main_frame, "DeepSeek API 配置", 'heading')
        title_label.pack(pady=(10, 10))

        # 安全警告
        warning_frame = tk.Frame(main_frame, bg='#FFF9E6', relief='solid', borderwidth=1)
        warning_frame.pack(fill='x', pady=(0, 15))

        warning_text = DieterWidgets.create_label(
            warning_frame,
            "安全提示: 推荐在.env文件中配置API密钥\n"
            "(.env文件不会被Git提交)\n"
            "在此处设置将保存到config.json (会被Git提交)",
            'small'
        )
        warning_text.config(fg='#8B6914', justify='left', wraplength=430)
        warning_text.pack(padx=10, pady=10)

        # API密钥输入
        key_label = DieterWidgets.create_label(main_frame, "API 密钥:", 'body')
        key_label.pack(anchor='w', pady=(0, 5))

        api_key_var = tk.StringVar()
        if self.deepseek_client and self.deepseek_client.api_key:
            api_key_var.set(self.deepseek_client.api_key)

        key_entry = tk.Entry(
            main_frame,
            textvariable=api_key_var,
            width=50,
            font=DieterStyle.get_fonts()['body'],
            show='*'
        )
        key_entry.pack(fill='x', pady=(0, 10))

        # 当前配置来源
        config_source = "未设置"
        if self.config:
            if self.config.deepseek_api_key:
                import os
                env_key = os.getenv('DEEPSEEK_API_KEY')
                if env_key:
                    config_source = ".env 文件"
                else:
                    config_source = "config.json 文件"

        source_label = DieterWidgets.create_label(
            main_frame,
            f"当前密钥来源: {config_source}",
            'small'
        )
        source_label.pack(anchor='w', pady=(0, 10))

        # 按钮区域
        button_frame = tk.Frame(main_frame, bg=DieterStyle.COLORS['panel_bg'])
        button_frame.pack(fill='x', pady=10)

        def save_settings():
            api_key = api_key_var.get().strip()
            if api_key:
                self.deepseek_client.set_api_key(api_key)
                # 保存到配置
                if self.config:
                    self.config.deepseek_api_key = api_key
                    self.config.save()
                messagebox.showinfo("保存成功", "DeepSeek API密钥已保存")
            settings_window.destroy()

        def test_connection():
            api_key = api_key_var.get().strip()
            if not api_key:
                messagebox.showwarning("测试失败", "请先输入API密钥")
                return

            # 临时设置API密钥进行测试
            test_client = DeepSeekClient(api_key=api_key)
            result = test_client.test_connection()

            if result['success']:
                messagebox.showinfo("测试成功", result['message'])
            else:
                messagebox.showerror("测试失败", result['message'])

        save_btn = DieterWidgets.create_button(button_frame, "保存", save_settings, 'primary')
        save_btn.pack(side='right', padx=(5, 0))

        test_btn = DieterWidgets.create_button(button_frame, "测试连接", test_connection, 'secondary')
        test_btn.pack(side='right')

        cancel_btn = DieterWidgets.create_button(button_frame, "取消", settings_window.destroy, 'secondary')
        cancel_btn.pack(side='left')

    def _request_analysis(self):
        """请求DeepSeek分析"""
        try:
            # 检查游戏状态
            if self.game_manager.current_game.move_count == 0:
                messagebox.showwarning("分析失败", "游戏尚未开始，无法进行分析")
                return

            # 检查DeepSeek API密钥
            if not self.deepseek_client or not self.deepseek_client.api_key:
                result = messagebox.askyesno(
                    "API密钥未设置",
                    "DeepSeek API密钥未设置，是否现在配置？"
                )
                if result:
                    self._deepseek_settings()
                return

            # 创建分析报告窗口
            analysis_window = AnalysisReportWindow(
                self.root,
                self.game_manager.current_game,
                self.deepseek_client
            )
            analysis_window.show()

        except Exception as e:
            self.logger.error(f"请求分析失败: {e}")
            messagebox.showerror("分析错误", f"请求分析时发生错误:\\n{e}")

    def _save_game(self):
        """保存游戏"""
        try:
            filename = filedialog.asksaveasfilename(
                title="保存游戏",
                defaultextension=".json",
                filetypes=[
                    ("JSON文件", "*.json"),
                    ("所有文件", "*.*")
                ]
            )

            if filename:
                self.game_manager.save_game(filename)
                messagebox.showinfo("保存成功", f"游戏已保存到:\\n{filename}")

        except Exception as e:
            self.logger.error(f"保存游戏失败: {e}")
            messagebox.showerror("保存失败", f"保存游戏时发生错误:\\n{e}")

    def _load_game(self):
        """加载游戏"""
        try:
            filename = filedialog.askopenfilename(
                title="加载游戏",
                filetypes=[
                    ("JSON文件", "*.json"),
                    ("所有文件", "*.*")
                ]
            )

            if filename:
                self.game_manager.load_game(filename)

                # 更新棋盘显示
                if self.game_board:
                    self.game_board.game_state = self.game_manager.current_game
                    self.game_board.reset_board()

                messagebox.showinfo("加载成功", f"游戏已从以下文件加载:\\n{filename}")

        except Exception as e:
            self.logger.error(f"加载游戏失败: {e}")
            messagebox.showerror("加载失败", f"加载游戏时发生错误:\\n{e}")

    def _show_help(self):
        """显示帮助信息"""
        help_text = """STM32 黑白棋 PC上位机使用说明

基本操作:
• 新游戏: 开始一局新的黑白棋游戏
• 连接STM32: 连接到STM32开发板进行硬件交互
• 点击棋盘: 在有效位置下棋

高级功能:
• DeepSeek分析: 使用AI分析游戏局面和棋谱
• 保存/加载: 保存当前游戏状态或加载历史游戏
• 棋谱导出: 导出PGN格式的棋谱记录

设计理念:
本软件遵循Dieter Rams的"Less but better"设计哲学，
追求简洁、功能性和美观的完美平衡。"""

        messagebox.showinfo("使用说明", help_text)

    def _show_about(self):
        """显示关于信息"""
        about_text = """STM32 黑白棋项目 v1.0

开发团队: STM32 Othello Project Team
开发时间: 2025-11-22

技术栈:
• STM32F103C8T6 微控制器
• Python + tkinter GUI框架
• DeepSeek AI API集成
• Dieter Rams设计理念

特色功能:
• STM32硬件棋盘交互
• 智能AI分析系统
• 简洁优雅的用户界面
• 完整的游戏记录系统

© 2025 STM32 Othello Project Team"""

        messagebox.showinfo("关于", about_text)

    def _on_player_move(self, row: int, col: int):
        """处理玩家走棋"""
        try:
            success = self.game_manager.make_move(row, col)

            if success:
                # 更新棋盘显示
                if self.game_board:
                    self.game_board.update_board()
                    self.game_board.highlight_last_move()

                # 发送走法到STM32
                if self.serial_handler.is_connected():
                    player = self.game_manager.current_game.current_player.value
                    self.serial_handler.send_make_move(row, col, player)

                self.logger.info(f"玩家走棋: {chr(ord('A') + col)}{row + 1}")
            else:
                self.logger.warning("无效走法")

        except Exception as e:
            self.logger.error(f"处理玩家走棋失败: {e}")

    def _on_game_state_changed(self, event, data=None):
        """游戏状态变化回调"""
        try:
            # 更新棋盘显示
            if self.game_board:
                self.game_board.update_board()

            # 检查游戏结束
            if event == 'game_ended':
                self._on_game_ended()

        except Exception as e:
            self.logger.error(f"处理游戏状态变化失败: {e}")

    def _on_game_ended(self):
        """游戏结束处理"""
        game_state = self.game_manager.current_game

        # 确定胜负
        if game_state.status.value == 1:  # BLACK_WIN
            winner = f"黑方获胜 ({game_state.black_count}-{game_state.white_count})"
        elif game_state.status.value == 2:  # WHITE_WIN
            winner = f"白方获胜 ({game_state.white_count}-{game_state.black_count})"
        else:  # DRAW
            winner = f"平局 ({game_state.black_count}-{game_state.white_count})"

        # 显示游戏结果
        result = messagebox.askyesno(
            "游戏结束",
            f"{winner}\\n\\n是否使用DeepSeek分析这局游戏？"
        )

        if result:
            self._request_analysis()

    def update_connection_status(self, is_connected: bool):
        """更新连接状态显示"""
        if is_connected:
            self.status_label.config(
                text="已连接",
                fg=DieterStyle.COLORS['success_green']
            )
            self.connect_btn.config(text="断开连接")
        else:
            self.status_label.config(
                text="未连接",
                fg=DieterStyle.COLORS['error_red']
            )
            self.connect_btn.config(text="连接STM32")

    def update_game_board(self):
        """更新游戏棋盘显示"""
        if self.game_board:
            self.game_board.update_board()

    def handle_key_event(self, key_data: bytes):
        """处理STM32按键事件"""
        try:
            if len(key_data) >= 1:
                key_code = key_data[0]
                self.logger.debug(f"收到按键事件: {key_code}")
                # 这里可以处理特定的按键逻辑

        except Exception as e:
            self.logger.error(f"处理按键事件失败: {e}")

    def update_system_info(self, info_data: bytes):
        """更新系统信息"""
        try:
            # 解析系统信息数据
            self.logger.debug(f"收到系统信息: {len(info_data)} bytes")

        except Exception as e:
            self.logger.error(f"更新系统信息失败: {e}")

    def _update_ui_state(self):
        """更新UI状态"""
        # 更新连接状态
        self.update_connection_status(self.serial_handler.is_connected())

        # 更新历史面板的分析状态
        if self.history_panel:
            self.history_panel.set_analysis_status("", False)