#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analysis Report Window for STM32 Othello PC Client
分析报告窗口组件

@author: STM32 Othello Project Team
@version: 1.0
@date: 2025-11-22
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
from datetime import datetime
from typing import Dict, Optional

from gui.styles import DieterStyle, DieterWidgets
from analysis.deepseek_client import DeepSeekClient
from game.game_state import GameState

class AnalysisReportWindow:
    """分析报告窗口"""

    def __init__(self, parent, game_state: GameState, deepseek_client: DeepSeekClient):
        """
        初始化分析报告窗口

        Args:
            parent: 父窗口
            game_state: 游戏状态对象
            deepseek_client: DeepSeek客户端
        """
        self.parent = parent
        self.game_state = game_state
        self.deepseek_client = deepseek_client

        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("DeepSeek 游戏分析报告")
        self.window.geometry("800x600")
        self.window.resizable(True, True)

        # 应用主题
        self.window.configure(bg=DieterStyle.COLORS['white'])

        # 分析结果数据
        self.analysis_result: Optional[Dict] = None
        self.analysis_thread: Optional[threading.Thread] = None

        self.setup_ui()
        self.start_analysis()

        # 设置窗口关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        """设置用户界面"""
        # === 标题区域 ===
        header_frame = DieterWidgets.create_panel(self.window, 'main')
        header_frame.pack(fill='x', padx=10, pady=10)

        title_label = DieterWidgets.create_label(
            header_frame,
            "DeepSeek AI 游戏分析报告",
            'title'
        )
        title_label.pack(pady=10)

        # 游戏信息
        info_frame = tk.Frame(header_frame, bg=DieterStyle.COLORS['panel_bg'])
        info_frame.pack(fill='x', padx=10, pady=(0, 10))

        # 游戏基本信息
        game_info_text = self._generate_game_info_text()
        info_label = DieterWidgets.create_label(info_frame, game_info_text, 'body')
        info_label.pack(anchor='w', padx=10, pady=5)

        # === 控制按钮区域 ===
        control_frame = tk.Frame(self.window, bg=DieterStyle.COLORS['white'])
        control_frame.pack(fill='x', padx=10, pady=(0, 10))

        # 左侧按钮
        left_buttons = tk.Frame(control_frame, bg=DieterStyle.COLORS['white'])
        left_buttons.pack(side='left')

        self.save_btn = DieterWidgets.create_button(\n            left_buttons, \"保存报告\", self._save_report, 'secondary'\n        )\n        self.save_btn.pack(side='left', padx=(0, 5))\n        self.save_btn.config(state='disabled')\n\n        self.export_btn = DieterWidgets.create_button(\n            left_buttons, \"导出PDF\", self._export_pdf, 'secondary'\n        )\n        self.export_btn.pack(side='left', padx=5)\n        self.export_btn.config(state='disabled')\n\n        # 右侧状态和刷新按钮\n        right_buttons = tk.Frame(control_frame, bg=DieterStyle.COLORS['white'])\n        right_buttons.pack(side='right')\n\n        self.refresh_btn = DieterWidgets.create_button(\n            right_buttons, \"重新分析\", self._refresh_analysis, 'secondary'\n        )\n        self.refresh_btn.pack(side='right', padx=(5, 0))\n\n        # 分析状态标签\n        self.status_label = DieterWidgets.create_label(\n            right_buttons, \"正在分析...\", 'small'\n        )\n        self.status_label.pack(side='right', padx=(0, 10))\n        self.status_label.config(fg=DieterStyle.COLORS['data_blue'])\n\n        # === 分析内容区域 ===\n        content_frame = DieterWidgets.create_panel(self.window, 'main')\n        content_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))\n\n        # 创建标签页\n        self.notebook = ttk.Notebook(content_frame)\n        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)\n\n        # 分析报告标签页\n        self.analysis_frame = tk.Frame(self.notebook, bg=DieterStyle.COLORS['white'])\n        self.notebook.add(self.analysis_frame, text='分析报告')\n\n        self.analysis_text = scrolledtext.ScrolledText(\n            self.analysis_frame,\n            font=DieterStyle.get_fonts()['body'],\n            bg=DieterStyle.COLORS['white'],\n            fg=DieterStyle.COLORS['black'],\n            relief='flat',\n            bd=0,\n            wrap='word',\n            state='disabled'\n        )\n        self.analysis_text.pack(fill='both', expand=True, padx=5, pady=5)\n\n        # 棋谱记录标签页\n        self.pgn_frame = tk.Frame(self.notebook, bg=DieterStyle.COLORS['white'])\n        self.notebook.add(self.pgn_frame, text='棋谱记录')\n\n        self.pgn_text = scrolledtext.ScrolledText(\n            self.pgn_frame,\n            font=DieterStyle.get_fonts()['data'],\n            bg=DieterStyle.COLORS['gray_light'],\n            fg=DieterStyle.COLORS['black'],\n            relief='flat',\n            bd=0,\n            wrap='word',\n            state='disabled'\n        )\n        self.pgn_text.pack(fill='both', expand=True, padx=5, pady=5)\n\n        # 技术信息标签页\n        self.tech_frame = tk.Frame(self.notebook, bg=DieterStyle.COLORS['white'])\n        self.notebook.add(self.tech_frame, text='技术信息')\n\n        self.tech_text = scrolledtext.ScrolledText(\n            self.tech_frame,\n            font=DieterStyle.get_fonts()['small'],\n            bg=DieterStyle.COLORS['gray_light'],\n            fg=DieterStyle.COLORS['gray_dark'],\n            relief='flat',\n            bd=0,\n            wrap='word',\n            state='disabled'\n        )\n        self.tech_text.pack(fill='both', expand=True, padx=5, pady=5)\n\n        # 预加载棋谱内容\n        self._update_pgn_display()\n        self._update_tech_display()\n\n    def _generate_game_info_text(self) -> str:\n        \"\"\"生成游戏信息文本\"\"\"\n        status_map = {\n            0: \"进行中\",\n            1: \"黑方获胜\", \n            2: \"白方获胜\",\n            3: \"平局\",\n            4: \"未开始\"\n        }\n\n        duration = self.game_state.get_game_duration()\n        minutes = int(duration // 60)\n        seconds = int(duration % 60)\n\n        info_text = (\n            f\"游戏状态: {status_map.get(self.game_state.status.value, '未知')}  |  \"\n            f\"最终比分: {self.game_state.black_count}-{self.game_state.white_count}  |  \"\n            f\"总手数: {self.game_state.move_count}手  |  \"\n            f\"用时: {minutes:02d}:{seconds:02d}\"\n        )\n        return info_text\n\n    def start_analysis(self):\n        \"\"\"开始分析\"\"\"\n        self.analysis_thread = threading.Thread(target=self._perform_analysis, daemon=True)\n        self.analysis_thread.start()\n\n    def _perform_analysis(self):\n        \"\"\"执行分析（在后台线程中）\"\"\"\n        try:\n            # 更新状态\n            self.window.after(0, lambda: self.status_label.config(\n                text=\"正在连接DeepSeek...\", \n                fg=DieterStyle.COLORS['data_blue']\n            ))\n\n            # 执行分析\n            result = self.deepseek_client.analyze_game(self.game_state)\n\n            # 在主线程中更新UI\n            self.window.after(0, lambda: self._on_analysis_complete(result))\n\n        except Exception as e:\n            error_result = {\n                'success': False,\n                'error': f'分析过程中发生异常: {str(e)}'\n            }\n            self.window.after(0, lambda: self._on_analysis_complete(error_result))\n\n    def _on_analysis_complete(self, result: Dict):\n        \"\"\"分析完成回调\"\"\"\n        self.analysis_result = result\n\n        if result['success']:\n            # 显示分析结果\n            self._display_analysis_result(result)\n            \n            # 更新状态\n            self.status_label.config(\n                text=\"分析完成\", \n                fg=DieterStyle.COLORS['success_green']\n            )\n\n            # 启用按钮\n            self.save_btn.config(state='normal')\n            self.export_btn.config(state='normal')\n\n        else:\n            # 显示错误信息\n            error_text = f\"分析失败: {result.get('error', '未知错误')}\"\n            \n            self.analysis_text.config(state='normal')\n            self.analysis_text.delete(1.0, tk.END)\n            self.analysis_text.insert(tk.END, error_text)\n            self.analysis_text.config(state='disabled')\n\n            # 更新状态\n            self.status_label.config(\n                text=\"分析失败\", \n                fg=DieterStyle.COLORS['error_red']\n            )\n\n    def _display_analysis_result(self, result: Dict):\n        \"\"\"显示分析结果\"\"\"\n        analysis_content = result['analysis']\n        \n        # 添加分析时间戳\n        timestamp = datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")\n        full_content = f\"分析时间: {timestamp}\\n{'='*50}\\n\\n{analysis_content}\"\n\n        # 更新分析文本\n        self.analysis_text.config(state='normal')\n        self.analysis_text.delete(1.0, tk.END)\n        self.analysis_text.insert(tk.END, full_content)\n        self.analysis_text.config(state='disabled')\n\n    def _update_pgn_display(self):\n        \"\"\"更新棋谱显示\"\"\"\n        # 这里可以集成游戏管理器的PGN生成功能\n        pgn_content = self._generate_pgn_content()\n        \n        self.pgn_text.config(state='normal')\n        self.pgn_text.delete(1.0, tk.END)\n        self.pgn_text.insert(tk.END, pgn_content)\n        self.pgn_text.config(state='disabled')\n\n    def _generate_pgn_content(self) -> str:\n        \"\"\"生成PGN格式内容\"\"\"\n        pgn_lines = []\n        pgn_lines.append('[Event \"STM32 Othello Game\"]')\n        pgn_lines.append(f'[Date \"{datetime.now().strftime(\"%Y.%m.%d\")}\"]')\n        pgn_lines.append('[Black \"Player/AI\"]')\n        pgn_lines.append('[White \"Player/AI\"]')\n        \n        # 结果\n        if self.game_state.status.value == 1:  # BLACK_WIN\n            pgn_lines.append('[Result \"1-0\"]')\n        elif self.game_state.status.value == 2:  # WHITE_WIN\n            pgn_lines.append('[Result \"0-1\"]')\n        elif self.game_state.status.value == 3:  # DRAW\n            pgn_lines.append('[Result \"1/2-1/2\"]')\n        else:\n            pgn_lines.append('[Result \"*\"]')\n        \n        pgn_lines.append('')\n        \n        # 走法记录\n        moves_line = \"\"\n        for i, move in enumerate(self.game_state.moves_history):\n            if i % 2 == 0:  # 黑方走法\n                moves_line += f\"{i//2 + 1}.{move.to_notation()} \"\n            else:  # 白方走法\n                moves_line += f\"{move.to_notation()} \"\n        \n        pgn_lines.append(moves_line.strip())\n        return '\\n'.join(pgn_lines)\n\n    def _update_tech_display(self):\n        \"\"\"更新技术信息显示\"\"\"\n        tech_info = f\"\"\"技术信息\n{'='*30}\n\n游戏引擎: STM32 Othello Engine v1.0\nPC客户端: STM32 Othello PC Client v1.0\nAI分析: DeepSeek API\n设计风格: Dieter Rams \"Less but better\"\n\n游戏统计:\n- 总手数: {self.game_state.move_count}\n- 黑子数量: {self.game_state.black_count}\n- 白子数量: {self.game_state.white_count}\n- 游戏时长: {self._format_duration(self.game_state.get_game_duration())}\n\n走法详情:\n\"\"\"\n        \n        for i, move in enumerate(self.game_state.moves_history):\n            player = \"黑方\" if move.player.value == 1 else \"白方\"\n            timestamp = datetime.fromtimestamp(move.timestamp).strftime(\"%H:%M:%S\")\n            tech_info += f\"{i+1:2d}. {player} {move.to_notation()} (时间: {timestamp}, 翻转: {move.flipped_count}子)\\n\"\n        \n        self.tech_text.config(state='normal')\n        self.tech_text.delete(1.0, tk.END)\n        self.tech_text.insert(tk.END, tech_info)\n        self.tech_text.config(state='disabled')\n\n    def _format_duration(self, duration: float) -> str:\n        \"\"\"格式化时长\"\"\"\n        minutes = int(duration // 60)\n        seconds = int(duration % 60)\n        return f\"{minutes:02d}:{seconds:02d}\"\n\n    def _save_report(self):\n        \"\"\"保存分析报告\"\"\"\n        if not self.analysis_result or not self.analysis_result['success']:\n            messagebox.showwarning(\"保存失败\", \"没有可保存的分析结果\")\n            return\n\n        try:\n            filename = filedialog.asksaveasfilename(\n                title=\"保存分析报告\",\n                defaultextension=\".txt\",\n                filetypes=[\n                    (\"文本文件\", \"*.txt\"),\n                    (\"所有文件\", \"*.*\")\n                ]\n            )\n\n            if filename:\n                with open(filename, 'w', encoding='utf-8') as f:\n                    f.write(\"DeepSeek AI 游戏分析报告\\n\")\n                    f.write(\"=\" * 50 + \"\\n\\n\")\n                    f.write(f\"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n\")\n                    f.write(\"游戏信息:\\n\")\n                    f.write(self._generate_game_info_text() + \"\\n\\n\")\n                    f.write(\"分析结果:\\n\")\n                    f.write(self.analysis_result['analysis'])\n                    f.write(\"\\n\\n\" + \"=\" * 50 + \"\\n\")\n                    f.write(\"棋谱记录:\\n\")\n                    f.write(self._generate_pgn_content())\n\n                messagebox.showinfo(\"保存成功\", f\"分析报告已保存到:\\n{filename}\")\n\n        except Exception as e:\n            messagebox.showerror(\"保存失败\", f\"保存分析报告时发生错误:\\n{e}\")\n\n    def _export_pdf(self):\n        \"\"\"导出PDF报告\"\"\"\n        # 这里可以集成PDF生成库，暂时显示提示\n        messagebox.showinfo(\"功能开发中\", \"PDF导出功能正在开发中，请使用保存报告功能。\")\n\n    def _refresh_analysis(self):\n        \"\"\"刷新分析\"\"\"\n        # 重置状态\n        self.analysis_result = None\n        self.save_btn.config(state='disabled')\n        self.export_btn.config(state='disabled')\n        \n        # 清空分析内容\n        self.analysis_text.config(state='normal')\n        self.analysis_text.delete(1.0, tk.END)\n        self.analysis_text.insert(tk.END, \"正在重新分析...\")\n        self.analysis_text.config(state='disabled')\n        \n        # 开始新的分析\n        self.start_analysis()\n\n    def on_closing(self):\n        \"\"\"窗口关闭事件\"\"\"\n        # 如果有正在进行的分析线程，等待其完成\n        if self.analysis_thread and self.analysis_thread.is_alive():\n            # 可以考虑添加取消机制\n            pass\n        \n        self.window.destroy()\n\n    def show(self):\n        \"\"\"显示窗口\"\"\"\n        self.window.transient(self.parent)\n        self.window.grab_set()\n        self.parent.wait_window(self.window)