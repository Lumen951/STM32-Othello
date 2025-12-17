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

        # Connection verification flags
        self._connection_verified = False
        self._last_heartbeat_time = 0

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

            # 传递连接验证标志检查函数给主窗口
            self.main_window._connection_verified_flag = lambda: self._connection_verified
            # 传递重置方法给主窗口
            self.main_window._reset_connection_verification = self.reset_connection_verification

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
            from communication.serial_handler import SerialProtocol

            if command == SerialProtocol.CMD_BOARD_STATE:  # 0x01
                # 棋盘状态同步
                self.game_manager.update_board_state(data)
                if self.main_window:
                    self.main_window.update_game_board()
                self.logger.info("收到棋盘状态同步")

            elif command == SerialProtocol.CMD_ACK:  # 0x08
                # 确认响应
                if len(data) >= 2:
                    original_cmd = data[0]
                    status = data[1]

                    # 命令名称映射
                    cmd_names = {
                        0x01: 'BOARD_STATE', 0x02: 'MAKE_MOVE', 0x03: 'GAME_CONFIG',
                        0x04: 'GAME_STATS', 0x05: 'SYSTEM_INFO', 0x06: 'AI_REQUEST',
                        0x07: 'HEARTBEAT', 0x0B: 'LED_CONTROL', 0x0C: 'GAME_CONTROL',
                        0x0D: 'MODE_SELECT', 0x0E: 'SCORE_UPDATE', 0x0F: 'TIMER_UPDATE'
                    }
                    cmd_name = cmd_names.get(original_cmd, f'UNKNOWN(0x{original_cmd:02X})')

                    if status == 0:
                        self.logger.info(f"✅ 命令执行成功: {cmd_name} (0x{original_cmd:02X})")
                    else:
                        # 状态码详细说明
                        status_meanings = {
                            1: '无效走法(invalid move) - 位置不合法或无法翻转',
                            2: '走法失败(move failed) - 未翻转任何棋子',
                            3: '数据长度错误(invalid length) - 数据包大小不匹配',
                            4: '无效状态(invalid state) - 当前游戏状态不允许此操作'
                        }
                        status_msg = status_meanings.get(status, f'未知错误码: {status}')
                        self.logger.warning(f"❌ 命令执行失败: {cmd_name} (0x{original_cmd:02X}), 状态码: {status}\n   原因: {status_msg}")
                else:
                    self.logger.warning("收到格式错误的ACK响应")

            elif command == SerialProtocol.CMD_ERROR:  # 0xFF
                # 错误响应
                if len(data) >= 1:
                    error_code = data[0]
                    self.logger.error(f"STM32错误: 错误码 {error_code}")
                    if self.main_window:
                        # 在主线程中显示错误提示
                        self.root.after(0, lambda: messagebox.showwarning(
                            "STM32错误",
                            f"设备返回错误码: {error_code}\n可能是命令不支持或参数错误"
                        ))

            elif command == SerialProtocol.CMD_KEY_EVENT:  # 0x0A
                # 按键事件
                if self.main_window:
                    self.main_window.handle_key_event(data)
                self.logger.debug(f"收到按键事件，数据长度: {len(data)}")

            elif command == SerialProtocol.CMD_SYSTEM_INFO:  # 0x05
                # 系统信息
                if self.main_window:
                    self.main_window.update_system_info(data)
                # 标记连接已验证
                self._connection_verified = True
                self.logger.info("收到系统信息，连接验证成功")

            elif command == SerialProtocol.CMD_HEARTBEAT:  # 0x07
                # 心跳响应
                self._last_heartbeat_time = time.time()
                if self.main_window:
                    # 修复：转换布尔值为字符串状态
                    self.main_window.update_connection_status('connected')
                self.logger.debug("收到心跳响应")

            elif command == SerialProtocol.CMD_GAME_CONFIG:  # 0x03
                # 游戏配置响应（新游戏确认）
                self.logger.info("收到新游戏确认")

            elif command == SerialProtocol.CMD_MODE_SELECT:  # 0x0D
                # 模式选择通知
                if len(data) >= 3:
                    import struct
                    mode, time_limit = struct.unpack('<BH', data[:3])

                    # 模式映射
                    mode_map = {
                        1: 'normal',     # GAME_MODE_NORMAL
                        2: 'challenge',  # GAME_MODE_CHALLENGE
                        3: 'timed'       # GAME_MODE_TIMED
                    }
                    mode_name = mode_map.get(mode, 'normal')

                    self.logger.info(f"📋 收到模式选择: {mode_name}, 时限={time_limit}秒")

                    # 通知主窗口更新模式
                    if self.main_window:
                        self.main_window.on_mode_changed_from_stm32(mode_name, time_limit)
                else:
                    self.logger.warning("CMD_MODE_SELECT数据长度不足")

            else:
                self.logger.debug(f"收到未知命令: 0x{command:02X}, 数据长度: {len(data)}")

        except Exception as e:
            self.logger.error(f"处理串口数据失败: {e}")
            import traceback
            traceback.print_exc()

    def reset_connection_verification(self):
        """重置连接验证标志"""
        self._connection_verified = False
        self.logger.debug("连接验证标志已重置")

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
                            # 修复：转换布尔值为字符串状态
                            status = 'connected' if is_connected else 'disconnected'
                            self.main_window.update_connection_status(status)

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