#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STM32 Othello PC Client - Main Entry Point
PC上位机主程序入口

@author: STM32 Othello Project Team
@version: 1.0
@date: 2025-11-22
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import threading
import time

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow
from communication.serial_handler import SerialHandler
from game.game_state import GameStateManager
from utils.logger import Logger
from utils.config import Config

class OthelloPC:
    """
    STM32 Othello PC Client主应用类
    """

    def __init__(self):
        """初始化应用程序"""
        self.logger = Logger()
        self.config = Config()
        self.serial_handler = None
        self.game_manager = None
        self.main_window = None
        self.root = None
        self.running = False

    def initialize(self):
        """初始化所有组件"""
        try:
            self.logger.info("初始化STM32 Othello PC客户端...")

            # 创建主窗口
            self.root = tk.Tk()
            self.root.title("STM32 Othello - PC上位机 v1.0")
            self.root.geometry("1200x800")
            self.root.resizable(True, True)

            # 设置窗口图标和样式
            self.root.configure(bg='#f0f0f0')

            # 初始化游戏状态管理器
            self.game_manager = GameStateManager()

            # 初始化串口处理器
            self.serial_handler = SerialHandler(
                callback=self.on_serial_data_received,
                config=self.config
            )

            # 创建主界面
            self.main_window = MainWindow(
                root=self.root,
                serial_handler=self.serial_handler,
                game_manager=self.game_manager,
                config=self.config
            )

            # 设置退出处理
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

            self.running = True
            self.logger.info("应用程序初始化完成")
            return True

        except Exception as e:
            self.logger.error(f"初始化失败: {e}")
            messagebox.showerror("初始化错误", f"应用程序初始化失败:\n{e}")
            return False

    def on_serial_data_received(self, command, data):
        """处理从STM32接收到的数据"""
        try:
            if command == 0x01:  # CMD_BOARD_STATE
                self.game_manager.update_board_state(data)
                if self.main_window:
                    self.main_window.update_game_board()
            elif command == 0x0A:  # CMD_KEY_EVENT
                if self.main_window:
                    self.main_window.handle_key_event(data)
            elif command == 0x05:  # CMD_SYSTEM_INFO
                if self.main_window:
                    self.main_window.update_system_info(data)
            elif command == 0x07:  # CMD_HEARTBEAT
                if self.main_window:
                    self.main_window.update_connection_status(True)
            else:
                self.logger.debug(f"收到未知命令: 0x{command:02X}")

        except Exception as e:
            self.logger.error(f"处理串口数据失败: {e}")

    def on_closing(self):
        """应用程序关闭处理"""
        try:
            self.logger.info("正在关闭应用程序...")
            self.running = False

            # 关闭串口连接
            if self.serial_handler:
                self.serial_handler.disconnect()

            # 保存配置
            if self.config:
                self.config.save()

            # 销毁窗口
            if self.root:
                self.root.quit()
                self.root.destroy()

            self.logger.info("应用程序已正常关闭")

        except Exception as e:
            self.logger.error(f"关闭应用程序时出错: {e}")
        finally:
            sys.exit(0)

    def run(self):
        """运行应用程序主循环"""
        if not self.initialize():
            return False

        try:
            self.logger.info("启动应用程序主循环")

            # 启动定期任务
            self.start_periodic_tasks()

            # 启动Tkinter主循环
            self.root.mainloop()

        except KeyboardInterrupt:
            self.logger.info("收到键盘中断信号")
        except Exception as e:
            self.logger.error(f"运行时错误: {e}")
            messagebox.showerror("运行时错误", f"程序运行时发生错误:\n{e}")
        finally:
            self.on_closing()

        return True

    def start_periodic_tasks(self):
        """启动定期任务"""
        def periodic_task():
            while self.running:
                try:
                    # 检查串口连接状态
                    if self.serial_handler:
                        is_connected = self.serial_handler.is_connected()
                        if self.main_window:
                            self.main_window.update_connection_status(is_connected)

                    # 发送心跳包
                    if self.serial_handler and self.serial_handler.is_connected():
                        self.serial_handler.send_heartbeat()

                    time.sleep(1)  # 每秒执行一次

                except Exception as e:
                    self.logger.error(f"定期任务执行错误: {e}")
                    time.sleep(5)  # 出错时等待5秒

        # 在后台线程中运行定期任务
        task_thread = threading.Thread(target=periodic_task, daemon=True)
        task_thread.start()

def main():
    """主函数"""
    print("=" * 50)
    print("STM32 Othello PC Client v1.0")
    print("PC上位机交互前端")
    print("=" * 50)

    try:
        app = OthelloPC()
        success = app.run()
        return 0 if success else 1

    except Exception as e:
        print(f"程序启动失败: {e}")
        messagebox.showerror("启动错误", f"程序启动失败:\n{e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())