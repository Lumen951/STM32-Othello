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

        # Connection verification
        self._connection_verified = False
        self._connection_timeout_count = 0

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

        # === 状态显示面板（棋盘格样式）===
        self._create_status_grid(left_frame)

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

    def _create_status_grid(self, parent):
        """创建棋盘格样式的状态展示面板"""
        # 状态面板容器
        status_container = tk.Frame(parent, bg=DieterStyle.COLORS['board_bg'],
                                   relief='solid', bd=2)
        status_container.pack(fill='x', pady=(10, 5))

        # 创建2x2网格布局
        # 行0: 当前回合 | 连接状态
        # 行1: 棋子计数 | 按键提示

        # === 第一行 ===
        row1_frame = tk.Frame(status_container, bg=DieterStyle.COLORS['board_bg'])
        row1_frame.pack(fill='x', padx=5, pady=5)

        # 当前回合（左侧）
        turn_cell = tk.Frame(row1_frame, bg='white', relief='ridge', bd=2)
        turn_cell.pack(side='left', fill='both', expand=True, padx=(0, 5))

        tk.Label(turn_cell, text="当前回合",
                font=('Arial', 10, 'bold'),
                bg='white', fg=DieterStyle.COLORS['gray_dark']).pack(pady=(5, 2))

        self.turn_display = tk.Label(turn_cell, text="黑方（橙色）",
                                     font=('Arial', 14, 'bold'),
                                     bg='white', fg=DieterStyle.COLORS['braun_orange'])
        self.turn_display.pack(pady=(2, 5))

        # STM32连接状态（右侧）
        conn_cell = tk.Frame(row1_frame, bg='white', relief='ridge', bd=2)
        conn_cell.pack(side='right', fill='both', expand=True, padx=(5, 0))

        tk.Label(conn_cell, text="STM32状态",
                font=('Arial', 10, 'bold'),
                bg='white', fg=DieterStyle.COLORS['gray_dark']).pack(pady=(5, 2))

        self.conn_display = tk.Label(conn_cell, text="● 未连接",
                                     font=('Arial', 12, 'normal'),
                                     bg='white', fg=DieterStyle.COLORS['error_red'])
        self.conn_display.pack(pady=(2, 5))

        # === 第二行 ===
        row2_frame = tk.Frame(status_container, bg=DieterStyle.COLORS['board_bg'])
        row2_frame.pack(fill='x', padx=5, pady=(0, 5))

        # 棋子计数（左侧）
        score_cell = tk.Frame(row2_frame, bg='white', relief='ridge', bd=2)
        score_cell.pack(side='left', fill='both', expand=True, padx=(0, 5))

        tk.Label(score_cell, text="棋子统计",
                font=('Arial', 10, 'bold'),
                bg='white', fg=DieterStyle.COLORS['gray_dark']).pack(pady=(5, 2))

        self.score_display = tk.Label(score_cell,
                                      text="橙: 2  vs  白: 2",
                                      font=('Arial', 12, 'bold'),
                                      bg='white', fg=DieterStyle.COLORS['black'])
        self.score_display.pack(pady=(2, 5))

        # 按键提示（右侧）
        key_cell = tk.Frame(row2_frame, bg='white', relief='ridge', bd=2)
        key_cell.pack(side='right', fill='both', expand=True, padx=(5, 0))

        tk.Label(key_cell, text="⌨️ 下位机按键",
                font=('Arial', 10, 'bold'),
                bg='white', fg=DieterStyle.COLORS['gray_dark']).pack(pady=(5, 2))

        key_guide = tk.Label(key_cell,
                            text="2↑ 4← 5● 6→ 8↓\n1=新游戏 0=重置 9=发送",
                            font=('Consolas', 9, 'normal'),
                            bg='white', fg=DieterStyle.COLORS['data_blue'],
                            justify='center')
        key_guide.pack(pady=(2, 5))

    def _update_status_display(self):
        """更新状态显示面板"""
        try:
            game_state = self.game_manager.current_game

            # 更新当前回合
            if game_state.current_player.value == 1:  # BLACK
                self.turn_display.config(
                    text="黑方（橙色）▶",
                    fg=DieterStyle.COLORS['braun_orange']
                )
            else:  # WHITE
                self.turn_display.config(
                    text="白方 ▶",
                    fg=DieterStyle.COLORS['black']
                )

            # 更新棋子计数
            self.score_display.config(
                text=f"橙: {game_state.black_count}  vs  白: {game_state.white_count}"
            )

            # 游戏状态特殊显示
            if game_state.status.value != 0:  # Not PLAYING
                winner = ""
                if game_state.status.value == 1:  # BLACK_WIN
                    winner = "🏆 黑方（橙色）获胜！"
                    color = DieterStyle.COLORS['braun_orange']
                elif game_state.status.value == 2:  # WHITE_WIN
                    winner = "🏆 白方获胜！"
                    color = DieterStyle.COLORS['black']
                else:  # DRAW
                    winner = "🤝 平局！"
                    color = DieterStyle.COLORS['gray_dark']

                self.turn_display.config(text=winner, fg=color)

        except Exception as e:
            self.logger.error(f"更新状态显示失败: {e}")

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
                messagebox.showwarning("连接失败", "未找到可用的串口设备\n请检查：\n1. USB-TTL模块是否连接\n2. 驱动是否已安装")
                return

            # 优先尝试连接COM7，如果失败则尝试其他端口
            port_to_use = 'COM7'
            if self.config and hasattr(self.config, 'serial_port'):
                port_to_use = self.config.serial_port

            success = self.serial_handler.connect(port=port_to_use)

            if success:
                self.logger.info(f"串口 {port_to_use} 已打开，正在验证连接...")

                # 发送系统信息请求验证连接
                self.serial_handler.send_system_info_request()

                # 等待响应（使用定时器检查，避免阻塞UI）
                self._connection_timeout_count = 0
                self._verify_connection_timer()
            else:
                messagebox.showerror("连接失败",
                    f"无法打开 {port_to_use} 端口\n\n请检查：\n"
                    f"1. 设备是否连接\n"
                    f"2. 端口是否被占用\n"
                    f"3. 驱动是否正常\n"
                    f"4. 是否有权限访问串口\n\n"
                    f"可用端口列表：\n" + "\n".join([f"  {p['device']}: {p['description']}" for p in ports]))

        except Exception as e:
            self.logger.error(f"STM32连接失败: {e}")
            messagebox.showerror("连接错误", f"连接STM32时发生错误:\n{e}")

        self._update_ui_state()

    def _verify_connection_timer(self):
        """验证连接的定时器（非阻塞）"""
        # 检查是否收到系统信息响应
        # 该标志在 OthelloPC.on_serial_data_received 中设置
        app = self.root.nametowidget(".")  # 获取主应用实例的引用

        # 通过共享变量检查连接状态（从main.py传递）
        if hasattr(self, '_connection_verified_flag'):
            if self._connection_verified_flag():
                self.logger.info("STM32连接验证成功")
                port_info = self.serial_handler.port_name or "未知端口"
                messagebox.showinfo("连接成功",
                    f"已成功连接到STM32设备\n\n"
                    f"端口: {port_info}\n"
                    f"波特率: 115200\n"
                    f"状态: 通信正常")
                return

        # 超时检查（3秒，检查6次，每次500ms）
        self._connection_timeout_count += 1
        if self._connection_timeout_count > 6:
            self.logger.warning("STM32连接验证超时")
            messagebox.showwarning("连接警告",
                "已打开串口，但未收到STM32响应\n\n"
                "可能的原因：\n"
                "1. STM32未正常运行或未上电\n"
                "2. 固件未更新或Protocol未启用\n"
                "3. 波特率不匹配（应为115200）\n"
                "4. 接线错误（TX-RX交叉连接）\n\n"
                "建议：\n"
                "• 检查STM32是否运行（观察LED）\n"
                "• 重新烧录固件\n"
                "• 使用串口助手测试硬件连接")
            return

        # 继续等待，500ms后再次检查
        self.root.after(500, self._verify_connection_timer)

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

            # 创建分析报告窗口（窗口会自动显示，无需调用show()）
            analysis_window = AnalysisReportWindow(
                self.root,
                self.game_manager.current_game,
                self.deepseek_client
            )
            # 注意：窗口在__init__中已经显示并置顶，无需额外调用

        except Exception as e:
            self.logger.error(f"请求分析失败: {e}")
            messagebox.showerror("分析错误", f"请求分析时发生错误:\n{e}")

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

            # 更新状态显示面板
            self._update_status_display()

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
            winner = f"黑方（橙色）获胜 ({game_state.black_count}-{game_state.white_count})"
        elif game_state.status.value == 2:  # WHITE_WIN
            winner = f"白方获胜 ({game_state.white_count}-{game_state.black_count})"
        else:  # DRAW
            winner = f"平局 ({game_state.black_count}-{game_state.white_count})"

        # 显示游戏结果
        result = messagebox.askyesno(
            "游戏结束",
            f"{winner}\n\n是否使用DeepSeek AI分析这局游戏？"
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
            # 更新状态面板中的连接状态
            self.conn_display.config(
                text="● 已连接",
                fg=DieterStyle.COLORS['success_green']
            )
        else:
            self.status_label.config(
                text="未连接",
                fg=DieterStyle.COLORS['error_red']
            )
            self.connect_btn.config(text="连接STM32")
            # 更新状态面板中的连接状态
            self.conn_display.config(
                text="● 未连接",
                fg=DieterStyle.COLORS['error_red']
            )

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