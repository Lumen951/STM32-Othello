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
from gui.control_panel import ControlPanel
from gui.score_panel import ScorePanel
from gui.timer_display import TimerDisplay
from gui.serial_settings_dialog import SerialSettingsDialog
from gui.history_viewer import HistoryViewerWindow
from gui.leaderboard_window import LeaderboardWindow
from gui.analysis_window import AnalysisReportWindow
from communication.serial_handler import SerialHandler
from game.game_state import GameStateManager, PieceType
from game.score_manager import ScoreManager
from game.leaderboard import Leaderboard
from game.challenge_mode import ChallengeMode
from game.timed_mode import TimedModeManager
from game.simple_ai import AIPlayer
from data.game_history import GameHistoryManager
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
        self.control_panel: Optional[ControlPanel] = None
        self.score_panel: Optional[ScorePanel] = None
        self.timer_display: Optional[TimerDisplay] = None

        # 分数管理器
        self.score_manager = ScoreManager()

        # 历史记录管理器
        self.history_manager = GameHistoryManager()

        # 排行榜管理器
        self.leaderboard = Leaderboard()

        # 闯关模式管理器
        self.challenge_mode = ChallengeMode()

        # 计时模式管理器（传递root用于after调度）
        self.timed_mode = TimedModeManager(self.root, duration=180)  # 默认3分钟
        self.timed_mode.on_time_update = self._on_timer_update
        self.timed_mode.on_time_up = self._on_time_up

        # AI玩家（对抗模式）
        self.ai_player = None
        self.is_vs_ai_mode = False

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

        # 创建棋盘容器（水平布局：计时器在左，棋盘在右）
        board_container = tk.Frame(left_frame, bg=DieterStyle.COLORS['white'])
        board_container.pack(pady=10)

        # 游戏棋盘（先放入，side='right'，在右侧）
        self.game_board = GameBoard(
            board_container,
            self.game_manager.current_game,
            on_move_callback=self._on_player_move
        )
        self.game_board.pack(side='right')

        # 计时显示组件（后放入，side='left'，在左侧，初始隐藏）
        self.timer_display = TimerDisplay(board_container, self.timed_mode)
        # 初始不pack，通过show()/hide()控制显示

        # === 右侧信息面板 ===
        right_frame = tk.Frame(main_container, bg=DieterStyle.COLORS['white'])
        right_frame.pack(side='right', fill='both', padx=(5, 10), pady=10)

        # 游戏控制面板
        self.control_panel = ControlPanel(
            right_frame,
            self.serial_handler,
            on_state_change=self._on_game_control_state_changed,
            on_mode_change=self._on_game_mode_changed
        )
        self.control_panel.pack(fill='x', pady=(0, 10))

        # 分数显示面板
        self.score_panel = ScorePanel(
            right_frame,
            self.score_manager
        )
        self.score_panel.pack(fill='x', pady=(0, 10))

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
        game_menu.add_command(label="历史回看", command=self._open_history_viewer)
        game_menu.add_command(label="排行榜", command=self._open_leaderboard)
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
        connection_menu.add_command(label="串口设置", command=self._serial_settings)

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

            # 显示"连接中"状态
            self.update_connection_status('connecting')

            # 重置连接验证标志和计数器（确保每次连接都是全新状态）
            if hasattr(self, '_reset_connection_verification'):
                self._reset_connection_verification()
            self._connection_timeout_count = 0

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
                # 连接失败，恢复未连接状态
                self.update_connection_status('disconnected')
                messagebox.showerror("连接失败",
                    f"无法打开 {port_to_use} 端口\n\n请检查：\n"
                    f"1. 设备是否连接\n"
                    f"2. 端口是否被占用\n"
                    f"3. 驱动是否正常\n"
                    f"4. 是否有权限访问串口\n\n"
                    f"可用端口列表：\n" + "\n".join([f"  {p['device']}: {p['description']}" for p in ports]))

        except Exception as e:
            self.logger.error(f"STM32连接失败: {e}")
            self.update_connection_status('disconnected')
            messagebox.showerror("连接错误", f"连接STM32时发生错误:\n{e}")

    def _verify_connection_timer(self):
        """验证连接的定时器（非阻塞）"""
        # 检查是否收到系统信息响应
        # 该标志在 OthelloPC.on_serial_data_received 中设置
        if hasattr(self, '_connection_verified_flag'):
            if self._connection_verified_flag():
                self.logger.info("STM32连接验证成功")
                port_info = self.serial_handler.port_name or "未知端口"

                # 更新为已连接状态
                self.update_connection_status('connected')

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

            # 重置连接验证标志（重要！避免下次连接时误判）
            if hasattr(self, '_reset_connection_verification'):
                self._reset_connection_verification()

            # 断开串口连接
            self.serial_handler.disconnect()

            # 更新为未连接状态
            self.update_connection_status('disconnected')

            messagebox.showwarning("连接失败",
                "未收到STM32响应，连接已断开\n\n"
                "可能的原因：\n"
                "1. STM32未正常运行或未上电\n"
                "2. 固件未更新或Protocol未启用\n"
                "3. 波特率不匹配（应为115200）\n"
                "4. 接线错误（TX-RX交叉连接）\n\n"
                "建议：\n"
                "• 检查STM32是否运行（观察LED）\n"
                "• 重新烧录固件\n"
                "• 使用串口助手测试硬件连接\n\n"
                "提示：未连接STM32时也可以在上位机玩游戏")
            return

        # 继续等待，500ms后再次检查
        self.root.after(500, self._verify_connection_timer)

    def _disconnect_stm32(self):
        """断开STM32连接"""
        try:
            self.serial_handler.disconnect()
            self.logger.info("STM32连接已断开")

            # 重置连接验证标志
            if hasattr(self, '_reset_connection_verification'):
                self._reset_connection_verification()

            # 更新为未连接状态
            self.update_connection_status('disconnected')

        except Exception as e:
            self.logger.error(f"断开STM32连接失败: {e}")

    def _serial_settings(self):
        """串口设置对话框"""
        try:
            dialog = SerialSettingsDialog(self.root, self.serial_handler, self.config)
            self.root.wait_window(dialog)
        except Exception as e:
            self.logger.error(f"打开串口设置对话框失败: {e}")
            messagebox.showerror("错误", f"打开串口设置对话框失败:\n{e}")

    def _open_history_viewer(self):
        """打开历史回看窗口"""
        try:
            viewer = HistoryViewerWindow(self.root, self.history_manager)
        except Exception as e:
            self.logger.error(f"打开历史回看窗口失败: {e}")
            messagebox.showerror("错误", f"打开历史回看窗口失败:\n{e}")

    def _open_leaderboard(self):
        """打开排行榜窗口"""
        try:
            leaderboard_window = LeaderboardWindow(self.root, self.leaderboard)
        except Exception as e:
            self.logger.error(f"打开排行榜窗口失败: {e}")
            messagebox.showerror("错误", f"打开排行榜窗口失败:\n{e}")

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
            # 在走棋前保存当前玩家（走棋后会切换）
            current_player = self.game_manager.current_game.current_player.value

            # 验证走法是否有效（与STM32端逻辑一致）
            game_state = self.game_manager.current_game
            if not game_state.is_valid_move(row, col, game_state.current_player):
                self.logger.warning(f"无效走法: ({row},{col}) 玩家={current_player}, 不发送到STM32")
                return

            success = self.game_manager.make_move(row, col)

            if success:
                # 更新棋盘显示
                if self.game_board:
                    self.game_board.update_board()
                    self.game_board.highlight_last_move()

                # 发送走法到STM32（使用走棋前的玩家）
                if self.serial_handler.is_connected():
                    self.serial_handler.send_make_move(row, col, current_player)
                    self.logger.info(f"玩家走棋: {chr(ord('A') + col)}{row + 1}, 已发送到STM32")
                else:
                    self.logger.info(f"玩家走棋: {chr(ord('A') + col)}{row + 1}, STM32未连接")

                # 对抗模式：玩家走棋后，AI自动走棋
                if self.is_vs_ai_mode and self.ai_player:
                    # 延迟500ms后AI走棋（让玩家看到自己的走法）
                    self.root.after(500, self._ai_make_move)
            else:
                self.logger.warning("无效走法")

        except Exception as e:
            self.logger.error(f"处理玩家走棋失败: {e}")

    def _ai_make_move(self):
        """AI自动走棋"""
        try:
            # 检查游戏是否结束
            game_state = self.game_manager.current_game
            if game_state.status.value != 0:  # 游戏已结束
                return

            # 检查是否轮到AI
            if game_state.current_player != self.ai_player.player_type:
                return

            # AI计算走法
            move = self.ai_player.make_move(game_state)

            if move:
                row, col = move
                self.logger.info(f"AI走棋: {chr(ord('A') + col)}{row + 1}")

                # 保存AI的玩家类型（在make_move前）
                ai_player_value = self.ai_player.player_type.value

                # 执行走法
                success = self.game_manager.make_move(row, col)

                if success:
                    # 更新棋盘显示
                    if self.game_board:
                        self.game_board.update_board()
                        self.game_board.highlight_last_move()

                    # 发送走法到STM32（使用AI的玩家类型）
                    if self.serial_handler.is_connected():
                        self.serial_handler.send_make_move(row, col, ai_player_value)
            else:
                # AI无可用走法，跳过
                self.logger.info("AI无可用走法，跳过")
                # 切换到玩家
                game_state.current_player = PieceType.BLACK

        except Exception as e:
            self.logger.error(f"AI走棋失败: {e}")

    def _on_game_state_changed(self, event, data=None):
        """游戏状态变化回调"""
        try:
            # 更新棋盘显示
            if self.game_board:
                self.game_board.update_board()

            # 更新状态显示面板
            self._update_status_display()

            # 更新分数面板
            if self.score_panel:
                game_state = self.game_manager.current_game
                self.score_panel.update_current_score(
                    game_state.black_count,
                    game_state.white_count,
                    animate=True
                )

            # 检查游戏结束
            if event == 'game_ended':
                # 如果是闯关模式，先处理闯关逻辑
                if self.challenge_mode.is_active:
                    self._handle_challenge_game_end()
                else:
                    # 普通模式：调用原有的游戏结束处理
                    self._on_game_ended()

        except Exception as e:
            self.logger.error(f"处理游戏状态变化失败: {e}")

    def _on_game_control_state_changed(self, new_state: str):
        """游戏控制状态变化回调"""
        self.logger.info(f"游戏控制状态变化: {new_state}")

        # 处理新游戏请求
        if new_state == 'new_game':
            self._new_game()
            # 启用棋盘
            if self.game_board:
                self.game_board.set_interactive(True)

            # 重置计时器（如果是计时模式）
            if self.timer_display and self.timer_display.winfo_ismapped():
                self.timed_mode.reset()
                self.timer_display.reset_display()

        # 根据状态控制棋盘交互性
        elif new_state == 'idle':
            # 空闲状态：禁用棋盘
            if self.game_board:
                self.game_board.set_interactive(False)

            # 停止并重置计时器
            if self.timed_mode.is_running():
                self.timed_mode.stop()
            self.timed_mode.reset()
            if self.timer_display:
                self.timer_display.reset_display()

        elif new_state == 'playing':
            # 游戏进行中：启用棋盘
            if self.game_board:
                self.game_board.set_interactive(True)

            # 如果计时器可见（计时模式），启动计时
            if self.timer_display and self.timer_display.winfo_ismapped():
                self.timed_mode.start()

        elif new_state == 'paused':
            # 暂停状态：禁用棋盘
            if self.game_board:
                self.game_board.set_interactive(False)

            # 暂停计时器
            if self.timed_mode.is_running():
                self.timed_mode.pause()

        elif new_state == 'resumed':
            # 继续状态：启用棋盘
            if self.game_board:
                self.game_board.set_interactive(True)

            # 继续计时器
            if self.timed_mode.is_paused():
                self.timed_mode.resume()

        elif new_state == 'ended':
            # 结束状态：禁用棋盘
            if self.game_board:
                self.game_board.set_interactive(False)

            # 停止计时器
            if self.timed_mode.is_running():
                self.timed_mode.stop()

            # 弹出DeepSeek分析提示
            game_state = self.game_manager.current_game

            # 确定胜负
            if game_state.status.value == 1:  # BLACK_WIN
                winner = f"黑方（橙色）获胜 ({game_state.black_count}-{game_state.white_count})"
            elif game_state.status.value == 2:  # WHITE_WIN
                winner = f"白方获胜 ({game_state.white_count}-{game_state.black_count})"
            else:  # DRAW
                winner = f"平局 ({game_state.black_count}-{game_state.white_count})"

            # 显示游戏结果并询问是否分析
            result = messagebox.askyesno(
                "游戏结束",
                f"{winner}\n\n是否使用DeepSeek AI分析这局游戏？"
            )

            if result:
                self._request_analysis()

    def _on_game_mode_changed(self, mode: int):
        """游戏模式变化回调"""
        from communication.serial_handler import SerialProtocol

        self.logger.info(f"游戏模式变化: 0x{mode:02X}")

        if mode == 0x04:  # 对抗模式（双人对战）
            # 结束AI模式
            self.is_vs_ai_mode = False
            self.ai_player = None

            # 隐藏计时器
            if self.timer_display:
                self.timer_display.hide()

            # 停止计时
            if self.timed_mode.is_running():
                self.timed_mode.stop()

            self.logger.info("对抗模式已启动（双人对战）")
            messagebox.showinfo(
                "对抗模式",
                f"对抗模式已启动！\n\n"
                f"双人对战模式\n"
                f"玩家1执黑（橙色）\n"
                f"玩家2执白\n\n"
                f"轮流在棋盘上下棋，祝你们玩得愉快！"
            )

        elif mode == SerialProtocol.GAME_MODE_CHALLENGE:
            # 启动闯关模式（人机对抗）
            self.is_vs_ai_mode = True

            # 隐藏计时器
            if self.timer_display:
                self.timer_display.hide()

            # 停止计时
            if self.timed_mode.is_running():
                self.timed_mode.stop()

            # 获取AI难度
            difficulty = self.control_panel.get_ai_difficulty()

            # 创建AI玩家（AI执白）
            self.ai_player = AIPlayer(PieceType.WHITE, difficulty)

            # 启动闯关模式
            self.challenge_mode.start_challenge()

            # 显示闯关模式统计
            if self.score_panel:
                self.score_panel.show_challenge_mode(True)
                self.score_panel.update_challenge_stats(self.challenge_mode.get_stats())

            self.logger.info(f"闯关模式已启动，AI难度: {self.ai_player.get_difficulty_name()}")
            messagebox.showinfo(
                "闯关模式",
                f"闯关模式已启动！\n\n"
                f"与AI对战，累计分数\n"
                f"您执黑（橙色），AI执白\n"
                f"AI难度: {self.ai_player.get_difficulty_name()}\n\n"
                f"目标: 累计获得 {self.challenge_mode.WIN_SCORE} 分\n"
                f"规则: 连续输 {self.challenge_mode.MAX_LOSSES} 局即失败\n\n"
                f"祝你好运！"
            )

        elif mode == SerialProtocol.GAME_MODE_NORMAL:
            # 结束AI模式
            self.is_vs_ai_mode = False
            self.ai_player = None

            # 隐藏计时器
            if self.timer_display:
                self.timer_display.hide()

            # 停止计时
            if self.timed_mode.is_running():
                self.timed_mode.stop()

            # 结束闯关模式（如果正在进行）
            if self.challenge_mode.is_active:
                self.challenge_mode.end_challenge()
                self.logger.info("闯关模式已结束")

            # 隐藏闯关模式统计
            if self.score_panel:
                self.score_panel.show_challenge_mode(False)

        elif mode == SerialProtocol.GAME_MODE_TIMED:
            # 结束AI模式和闯关模式
            self.is_vs_ai_mode = False
            self.ai_player = None

            if self.challenge_mode.is_active:
                self.challenge_mode.end_challenge()
                if self.score_panel:
                    self.score_panel.show_challenge_mode(False)

            # 启动计时模式
            self.logger.info("计时模式已启动")

            # 显示计时器
            if self.timer_display:
                self.timer_display.show()
                self.timer_display.reset_display()

            # 显示提示
            messagebox.showinfo(
                "计时模式",
                f"计时模式已启动！\n\n"
                f"时长：{self.timed_mode.get_duration() // 60} 分钟\n"
                f"目标：在规定时间内尽可能多得分\n\n"
                f"时间到将自动结束游戏！"
            )

        else:
            # 其他模式：隐藏计时器
            if self.timer_display:
                self.timer_display.hide()

            # 停止计时
            if self.timed_mode.is_running():
                self.timed_mode.stop()

    def _on_game_ended(self):
        """游戏结束处理（普通模式）"""
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

    def _handle_challenge_game_end(self):
        """处理闯关模式游戏结束"""
        game_state = self.game_manager.current_game

        # 处理闯关结果
        result = self.challenge_mode.process_game_result(
            game_state.black_count,
            game_state.white_count
        )

        # 显示本局结果
        self._show_challenge_result(game_state, result)

        # 更新闯关进度显示
        if self.score_panel:
            self.score_panel.update_challenge_stats(self.challenge_mode.get_stats())

        # 根据结果决定下一步
        if result == 'win':
            # 闯关成功
            self._show_challenge_victory()
            self.challenge_mode.end_challenge()
            self.is_vs_ai_mode = False
            self.ai_player = None

            # 隐藏闯关模式统计
            if self.score_panel:
                self.score_panel.show_challenge_mode(False)

        elif result == 'game_over':
            # 闯关失败
            self._show_challenge_failure()
            self.challenge_mode.end_challenge()
            self.is_vs_ai_mode = False
            self.ai_player = None

            # 隐藏闯关模式统计
            if self.score_panel:
                self.score_panel.show_challenge_mode(False)

        else:
            # 继续闯关：自动开始下一局
            self._start_next_challenge_game()

    def _show_challenge_result(self, game_state, challenge_result):
        """显示闯关本局结果"""
        stats = self.challenge_mode.get_stats()

        # 确定本局胜负
        if game_state.black_count > game_state.white_count:
            game_result = "🎉 胜利"
            result_color = "green"
        elif game_state.black_count < game_state.white_count:
            game_result = "😢 失败"
            result_color = "red"
        else:
            game_result = "🤝 平局"
            result_color = "gray"

        # 构建消息
        message = f"本局结果: {game_result}\n"
        message += f"本局得分: {game_state.black_count} - {game_state.white_count}\n\n"
        message += f"━━━━━━━━━━━━━━━━\n"
        message += f"📊 闯关进度\n"
        message += f"━━━━━━━━━━━━━━━━\n"
        message += f"总分: {stats.total_score} / {self.challenge_mode.WIN_SCORE}\n"
        message += f"已玩局数: {stats.games_played}\n"
        message += f"胜: {stats.games_won}  负: {stats.games_lost}  平: {stats.games_drawn}\n"
        message += f"连败: {stats.consecutive_losses} / {self.challenge_mode.MAX_LOSSES}\n"

        # 进度条
        progress = self.challenge_mode.get_progress_percentage()
        bar_length = 20
        filled = int(bar_length * progress / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        message += f"\n进度: [{bar}] {progress:.1f}%\n"

        # 显示提示
        if challenge_result == 'ongoing':
            if stats.consecutive_losses == 1:
                message += f"\n⚠️ 警告：已连败1局，再输1局将失败！"
            elif progress >= 80:
                message += f"\n🔥 加油！距离胜利只差 {self.challenge_mode.WIN_SCORE - stats.total_score} 分！"

        # 创建自定义对话框
        self._show_challenge_dialog("闯关模式 - 本局结束", message)

    def _show_challenge_dialog(self, title, message):
        """显示闯关模式对话框（带动画效果）"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x450")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # 应用主题
        from gui.styles import DieterStyle
        dialog.configure(bg=DieterStyle.COLORS['white'])

        # 消息内容
        message_frame = tk.Frame(dialog, bg=DieterStyle.COLORS['white'])
        message_frame.pack(fill='both', expand=True, padx=20, pady=20)

        message_label = tk.Label(
            message_frame,
            text=message,
            font=('Arial', 11),
            bg=DieterStyle.COLORS['white'],
            fg=DieterStyle.COLORS['gray_dark'],
            justify='left'
        )
        message_label.pack()

        # 倒计时标签
        countdown_label = tk.Label(
            dialog,
            text="",
            font=('Arial', 14, 'bold'),
            bg=DieterStyle.COLORS['white'],
            fg=DieterStyle.COLORS['braun_orange']
        )
        countdown_label.pack(pady=10)

        # 按钮
        button_frame = tk.Frame(dialog, bg=DieterStyle.COLORS['white'])
        button_frame.pack(pady=10)

        from gui.styles import DieterWidgets
        ok_btn = DieterWidgets.create_button(
            button_frame, "确定", dialog.destroy, 'primary'
        )
        ok_btn.pack()

        # 倒计时动画（3秒后自动关闭）
        countdown = [3]

        def update_countdown():
            if countdown[0] > 0:
                countdown_label.config(text=f"⏱️ {countdown[0]}秒后自动开始下一局...")
                countdown[0] -= 1
                dialog.after(1000, update_countdown)
            else:
                dialog.destroy()

        update_countdown()

    def _show_challenge_victory(self):
        """显示闯关成功"""
        stats = self.challenge_mode.get_stats()
        duration = self.challenge_mode.get_duration()

        message = "🎊🎊🎊 恭喜闯关成功！🎊🎊🎊\n\n"
        message += f"您已累计获得 {stats.total_score} 分！\n\n"
        message += f"━━━━━━━━━━━━━━━━\n"
        message += f"📈 最终统计\n"
        message += f"━━━━━━━━━━━━━━━━\n"
        message += f"总局数: {stats.games_played}\n"
        message += f"胜: {stats.games_won}  负: {stats.games_lost}  平: {stats.games_drawn}\n"
        message += f"胜率: {stats.games_won / stats.games_played * 100:.1f}%\n"

        if duration:
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            message += f"用时: {minutes}分{seconds}秒\n"

        messagebox.showinfo("🏆 闯关成功", message)

    def _show_challenge_failure(self):
        """显示闯关失败"""
        stats = self.challenge_mode.get_stats()

        message = "😢 闯关失败\n\n"
        message += f"连续输了 {self.challenge_mode.MAX_LOSSES} 局，挑战结束！\n\n"
        message += f"━━━━━━━━━━━━━━━━\n"
        message += f"📊 最终统计\n"
        message += f"━━━━━━━━━━━━━━━━\n"
        message += f"总分: {stats.total_score} / {self.challenge_mode.WIN_SCORE}\n"
        message += f"总局数: {stats.games_played}\n"
        message += f"胜: {stats.games_won}  负: {stats.games_lost}  平: {stats.games_drawn}\n\n"
        message += f"💪 不要气馁，再接再厉！"

        messagebox.showwarning("闯关失败", message)

    def _start_next_challenge_game(self):
        """开始下一局闯关游戏"""
        # 延迟3秒后自动开始（倒计时在对话框中显示）
        self.root.after(3000, self._new_game)

    def update_connection_status(self, status: str):
        """
        更新连接状态显示

        Args:
            status: 连接状态 ('disconnected', 'connecting', 'connected')
        """
        # 调试日志：记录状态变化和调用栈
        import traceback
        caller_info = traceback.extract_stack(limit=3)[-2]
        self.logger.info(f"🔄 连接状态变化: {getattr(self, '_current_connection_status', 'unknown')} → {status}")
        self.logger.debug(f"   调用者: {caller_info.filename}:{caller_info.lineno} in {caller_info.name}")

        # 保存当前状态到缓存
        self._current_connection_status = status

        if status == 'connected':
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
            self.logger.info("✅ UI已更新为【已连接】状态")
        elif status == 'connecting':
            self.status_label.config(
                text="连接中...",
                fg=DieterStyle.COLORS['braun_orange']
            )
            self.connect_btn.config(text="连接中...")
            # 更新状态面板中的连接状态
            self.conn_display.config(
                text="● 连接中...",
                fg=DieterStyle.COLORS['braun_orange']
            )
        else:  # disconnected
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
            self.logger.info("❌ UI已更新为【未连接】状态")

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
        """更新UI状态（仅在初始化时调用）

        注意：此方法只应在初始化时调用一次，不应在运行时调用
        运行时的状态更新应通过 update_connection_status() 显式调用
        """
        # 更新连接状态（初始化时使用）
        connected = self.serial_handler.is_connected()
        status = 'connected' if connected else 'disconnected'
        self.update_connection_status(status)

        # 更新控制面板连接状态
        if self.control_panel:
            self.control_panel.set_connection_state(connected)

        # 更新历史面板的分析状态
        if self.history_panel:
            self.history_panel.set_analysis_status("", False)

        self.logger.debug(f"_update_ui_state调用（初始化）: connected={connected}")

    def _on_timer_update(self, remaining: int):
        """计时器更新回调

        Args:
            remaining: 剩余时间（秒）
        """
        # 更新UI显示
        if self.timer_display:
            self.timer_display.update_time(remaining)

        # 注意：不在倒计时过程中同步STM32，仅在时间结束时同步

    def _on_time_up(self):
        """时间到回调"""
        self.logger.info("计时结束，游戏自动结束")

        # 获取游戏状态
        game_state = self.game_manager.current_game

        # 显示提示并询问是否分析
        result = messagebox.askyesno(
            "⏰ 计时模式 - 时间到",
            f"时间到！游戏自动结束\n\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📊 最终得分\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"黑方（橙色）: {game_state.black_count}\n"
            f"白方: {game_state.white_count}\n\n"
            f"是否使用DeepSeek AI分析这局游戏？"
        )

        # 自动结束游戏
        try:
            from communication.serial_handler import SerialProtocol
            self.serial_handler.send_game_control(SerialProtocol.GAME_CTRL_ACTION_END)
        except Exception as e:
            self.logger.error(f"自动结束游戏失败: {e}")

        # 如果用户选择分析
        if result:
            self._request_analysis()