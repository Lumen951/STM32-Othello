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
from analysis.pdf_generator import PDFReportGenerator
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

        self.save_btn = DieterWidgets.create_button(
            left_buttons, "保存报告", self._save_report, 'secondary'
        )
        self.save_btn.pack(side='left', padx=(0, 5))
        self.save_btn.config(state='disabled')

        self.export_btn = DieterWidgets.create_button(
            left_buttons, "导出PDF", self._export_pdf, 'secondary'
        )
        self.export_btn.pack(side='left', padx=5)
        self.export_btn.config(state='disabled')

        # 右侧状态和刷新按钮
        right_buttons = tk.Frame(control_frame, bg=DieterStyle.COLORS['white'])
        right_buttons.pack(side='right')

        self.refresh_btn = DieterWidgets.create_button(
            right_buttons, "重新分析", self._refresh_analysis, 'secondary'
        )
        self.refresh_btn.pack(side='right', padx=(5, 0))

        # 分析状态标签
        self.status_label = DieterWidgets.create_label(
            right_buttons, "正在分析...", 'small'
        )
        self.status_label.pack(side='right', padx=(0, 10))
        self.status_label.config(fg=DieterStyle.COLORS['data_blue'])

        # === 分析内容区域 ===
        content_frame = DieterWidgets.create_panel(self.window, 'main')
        content_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # 创建加载动画容器（初始隐藏）
        self.loading_frame = tk.Frame(content_frame, bg=DieterStyle.COLORS['white'])
        self.loading_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # 加载动画标签
        self.loading_label = tk.Label(
            self.loading_frame,
            text="⏳ 正在连接DeepSeek AI...",
            font=('Arial', 14, 'bold'),
            bg=DieterStyle.COLORS['white'],
            fg=DieterStyle.COLORS['data_blue']
        )
        self.loading_label.pack(expand=True)

        # 加载提示文本
        self.loading_hint = tk.Label(
            self.loading_frame,
            text="请稍候，AI正在分析您的棋局",
            font=('Arial', 10),
            bg=DieterStyle.COLORS['white'],
            fg=DieterStyle.COLORS['gray_dark']
        )
        self.loading_hint.pack(expand=True, pady=(10, 0))

        # 动画计数器
        self.loading_dots = 0
        self.animation_running = False

        # 创建标签页（初始隐藏）
        self.notebook = ttk.Notebook(content_frame)
        # 不立即pack，等分析完成后再显示

        # 分析报告标签页
        self.analysis_frame = tk.Frame(self.notebook, bg=DieterStyle.COLORS['white'])
        self.notebook.add(self.analysis_frame, text='分析报告')

        self.analysis_text = scrolledtext.ScrolledText(
            self.analysis_frame,
            font=DieterStyle.get_fonts()['body'],
            bg=DieterStyle.COLORS['white'],
            fg=DieterStyle.COLORS['black'],
            relief='flat',
            bd=0,
            wrap='word',
            state='disabled'
        )
        self.analysis_text.pack(fill='both', expand=True, padx=5, pady=5)

        # 棋谱记录标签页
        self.pgn_frame = tk.Frame(self.notebook, bg=DieterStyle.COLORS['white'])
        self.notebook.add(self.pgn_frame, text='棋谱记录')

        self.pgn_text = scrolledtext.ScrolledText(
            self.pgn_frame,
            font=DieterStyle.get_fonts()['data'],
            bg=DieterStyle.COLORS['gray_light'],
            fg=DieterStyle.COLORS['black'],
            relief='flat',
            bd=0,
            wrap='word',
            state='disabled'
        )
        self.pgn_text.pack(fill='both', expand=True, padx=5, pady=5)

        # 技术信息标签页
        self.tech_frame = tk.Frame(self.notebook, bg=DieterStyle.COLORS['white'])
        self.notebook.add(self.tech_frame, text='技术信息')

        self.tech_text = scrolledtext.ScrolledText(
            self.tech_frame,
            font=DieterStyle.get_fonts()['small'],
            bg=DieterStyle.COLORS['gray_light'],
            fg=DieterStyle.COLORS['gray_dark'],
            relief='flat',
            bd=0,
            wrap='word',
            state='disabled'
        )
        self.tech_text.pack(fill='both', expand=True, padx=5, pady=5)

        # 预加载棋谱内容
        self._update_pgn_display()
        self._update_tech_display()

        # 显示窗口并置顶
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()

    def _generate_game_info_text(self) -> str:
        """生成游戏信息文本"""
        status_map = {
            0: "进行中",
            1: "黑方获胜",
            2: "白方获胜",
            3: "平局",
            4: "未开始"
        }

        duration = self.game_state.get_game_duration()
        minutes = int(duration // 60)
        seconds = int(duration % 60)

        info_text = (
            f"游戏状态: {status_map.get(self.game_state.status.value, '未知')}  |  "
            f"最终比分: {self.game_state.black_count}-{self.game_state.white_count}  |  "
            f"总手数: {self.game_state.move_count}手  |  "
            f"用时: {minutes:02d}:{seconds:02d}"
        )
        return info_text

    def start_analysis(self):
        """开始分析"""
        # 启动加载动画
        self.animation_running = True
        self._animate_loading()

        self.analysis_thread = threading.Thread(target=self._perform_analysis, daemon=True)
        self.analysis_thread.start()

    def _animate_loading(self):
        """加载动画效果"""
        if not self.animation_running:
            return

        # 更新动画文本
        dots = "." * (self.loading_dots % 4)
        spaces = " " * (3 - (self.loading_dots % 4))
        self.loading_label.config(text=f"⏳ 正在分析中{dots}{spaces}")
        self.loading_dots += 1

        # 继续动画
        self.window.after(500, self._animate_loading)

    def _perform_analysis(self):
        """执行分析（在后台线程中）"""
        try:
            # 更新状态
            self.window.after(0, lambda: self.status_label.config(
                text="正在连接DeepSeek...",
                fg=DieterStyle.COLORS['data_blue']
            ))

            # 执行分析
            result = self.deepseek_client.analyze_game(self.game_state)

            # 在主线程中更新UI
            self.window.after(0, lambda: self._on_analysis_complete(result))

        except Exception as e:
            error_result = {
                'success': False,
                'error': f'分析过程中发生异常: {str(e)}'
            }
            self.window.after(0, lambda: self._on_analysis_complete(error_result))

    def _on_analysis_complete(self, result: Dict):
        """分析完成回调"""
        self.analysis_result = result

        # 停止加载动画
        self.animation_running = False

        # 隐藏加载动画，显示结果标签页
        self.loading_frame.pack_forget()
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        if result['success']:
            # 显示分析结果
            self._display_analysis_result(result)

            # 更新状态
            self.status_label.config(
                text="分析完成",
                fg=DieterStyle.COLORS['success_green']
            )

            # 启用按钮
            self.save_btn.config(state='normal')
            self.export_btn.config(state='normal')

        else:
            # 显示错误信息
            error_text = f"分析失败: {result.get('error', '未知错误')}"

            self.analysis_text.config(state='normal')
            self.analysis_text.delete(1.0, tk.END)
            self.analysis_text.insert(tk.END, error_text)
            self.analysis_text.config(state='disabled')

            # 更新状态
            self.status_label.config(
                text="分析失败",
                fg=DieterStyle.COLORS['error_red']
            )

    def _display_analysis_result(self, result: Dict):
        """显示分析结果"""
        analysis_content = result['analysis']

        # 添加分析时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_content = f"分析时间: {timestamp}\n{'='*50}\n\n{analysis_content}"

        # 更新分析文本
        self.analysis_text.config(state='normal')
        self.analysis_text.delete(1.0, tk.END)
        self.analysis_text.insert(tk.END, full_content)
        self.analysis_text.config(state='disabled')

    def _update_pgn_display(self):
        """更新棋谱显示"""
        # 这里可以集成游戏管理器的PGN生成功能
        pgn_content = self._generate_pgn_content()

        self.pgn_text.config(state='normal')
        self.pgn_text.delete(1.0, tk.END)
        self.pgn_text.insert(tk.END, pgn_content)
        self.pgn_text.config(state='disabled')

    def _generate_pgn_content(self) -> str:
        """生成PGN格式内容"""
        pgn_lines = []
        pgn_lines.append('[Event "STM32 Othello Game"]')
        pgn_lines.append(f'[Date "{datetime.now().strftime("%Y.%m.%d")}"]')
        pgn_lines.append('[Black "Player/AI"]')
        pgn_lines.append('[White "Player/AI"]')

        # 结果
        if self.game_state.status.value == 1:  # BLACK_WIN
            pgn_lines.append('[Result "1-0"]')
        elif self.game_state.status.value == 2:  # WHITE_WIN
            pgn_lines.append('[Result "0-1"]')
        elif self.game_state.status.value == 3:  # DRAW
            pgn_lines.append('[Result "1/2-1/2"]')
        else:
            pgn_lines.append('[Result "*"]')

        pgn_lines.append('')

        # 走法记录
        moves_line = ""
        for i, move in enumerate(self.game_state.moves_history):
            if i % 2 == 0:  # 黑方走法
                moves_line += f"{i//2 + 1}.{move.to_notation()} "
            else:  # 白方走法
                moves_line += f"{move.to_notation()} "

        pgn_lines.append(moves_line.strip())
        return '\n'.join(pgn_lines)

    def _update_tech_display(self):
        """更新技术信息显示"""
        tech_info = f"""技术信息
{'='*30}

游戏引擎: STM32 Othello Engine v1.0
PC客户端: STM32 Othello PC Client v1.0
AI分析: DeepSeek API
设计风格: Dieter Rams "Less but better"

游戏统计:
- 总手数: {self.game_state.move_count}
- 黑子数量: {self.game_state.black_count}
- 白子数量: {self.game_state.white_count}
- 游戏时长: {self._format_duration(self.game_state.get_game_duration())}

走法详情:
"""

        for i, move in enumerate(self.game_state.moves_history):
            player = "黑方" if move.player.value == 1 else "白方"
            timestamp = datetime.fromtimestamp(move.timestamp).strftime("%H:%M:%S")
            tech_info += f"{i+1:2d}. {player} {move.to_notation()} (时间: {timestamp}, 翻转: {move.flipped_count}子)\n"

        self.tech_text.config(state='normal')
        self.tech_text.delete(1.0, tk.END)
        self.tech_text.insert(tk.END, tech_info)
        self.tech_text.config(state='disabled')

    def _format_duration(self, duration: float) -> str:
        """格式化时长"""
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def _save_report(self):
        """保存分析报告"""
        if not self.analysis_result or not self.analysis_result['success']:
            messagebox.showwarning("保存失败", "没有可保存的分析结果")
            return

        try:
            filename = filedialog.asksaveasfilename(
                title="保存分析报告",
                defaultextension=".txt",
                filetypes=[
                    ("文本文件", "*.txt"),
                    ("所有文件", "*.*")
                ]
            )

            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("DeepSeek AI 游戏分析报告\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write("游戏信息:\n")
                    f.write(self._generate_game_info_text() + "\n\n")
                    f.write("分析结果:\n")
                    f.write(self.analysis_result['analysis'])
                    f.write("\n\n" + "=" * 50 + "\n")
                    f.write("棋谱记录:\n")
                    f.write(self._generate_pgn_content())

                messagebox.showinfo("保存成功", f"分析报告已保存到:\n{filename}")

        except Exception as e:
            messagebox.showerror("保存失败", f"保存分析报告时发生错误:\n{e}")

    def _export_pdf(self):
        """导出PDF报告"""
        if not self.analysis_result or not self.analysis_result['success']:
            messagebox.showwarning("导出失败", "没有可导出的分析结果")
            return

        try:
            # 选择保存路径
            filename = filedialog.asksaveasfilename(
                title="导出PDF报告",
                defaultextension=".pdf",
                filetypes=[
                    ("PDF文件", "*.pdf"),
                    ("所有文件", "*.*")
                ]
            )

            if filename:
                # 显示进度提示
                self.status_label.config(
                    text="正在生成PDF...",
                    fg=DieterStyle.COLORS['data_blue']
                )
                self.export_btn.config(state='disabled')
                self.window.update()

                # 创建PDF生成器
                pdf_gen = PDFReportGenerator(filename)

                # 添加报告头部
                pdf_gen.add_header(
                    "DeepSeek AI 游戏分析报告",
                    "STM32 Othello Project"
                )

                # 添加游戏信息
                pdf_gen.add_game_info(self.game_state)

                # 添加棋盘图示
                pdf_gen.add_board_diagram(self.game_state)

                # 添加分析文本
                pdf_gen.add_analysis_text(self.analysis_result['analysis'])

                # 添加棋谱记录
                pdf_gen.add_pgn_moves(self.game_state.moves_history)

                # 生成PDF
                if pdf_gen.generate():
                    self.status_label.config(
                        text="PDF导出成功",
                        fg=DieterStyle.COLORS['success_green']
                    )
                    messagebox.showinfo("导出成功", f"PDF报告已保存到:\n{filename}")
                else:
                    self.status_label.config(
                        text="PDF生成失败",
                        fg=DieterStyle.COLORS['error_red']
                    )
                    messagebox.showerror("导出失败", "PDF生成失败，请查看日志")

                # 恢复按钮状态
                self.export_btn.config(state='normal')

        except ImportError as e:
            messagebox.showerror(
                "依赖缺失",
                f"PDF导出功能需要安装reportlab库\n\n"
                f"请运行以下命令安装:\n"
                f"pip install reportlab\n\n"
                f"错误详情: {e}"
            )
        except Exception as e:
            self.status_label.config(
                text="导出失败",
                fg=DieterStyle.COLORS['error_red']
            )
            messagebox.showerror("导出失败", f"导出PDF时发生错误:\n{e}")
            self.export_btn.config(state='normal')

    def _refresh_analysis(self):
        """刷新分析"""
        # 重置状态
        self.analysis_result = None
        self.save_btn.config(state='disabled')
        self.export_btn.config(state='disabled')

        # 隐藏结果标签页，显示加载动画
        self.notebook.pack_forget()
        self.loading_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # 重置动画计数器
        self.loading_dots = 0

        # 开始新的分析
        self.start_analysis()

    def on_closing(self):
        """窗口关闭事件"""
        # 如果有正在进行的分析线程，等待其完成
        if self.analysis_thread and self.analysis_thread.is_alive():
            # 可以考虑添加取消机制
            pass

        self.window.destroy()