#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serial Settings Dialog for STM32 Othello PC Client
串口参数设置对话框

@author: STM32 Othello Project Team
@version: 1.0
@date: 2025-12-09
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
import logging
import serial
import serial.tools.list_ports

from gui.styles import DieterStyle, DieterWidgets


class SerialSettingsDialog(tk.Toplevel):
    """串口参数设置对话框"""

    def __init__(self, parent, serial_handler, config):
        """
        初始化串口设置对话框

        Args:
            parent: 父窗口
            serial_handler: 串口处理器
            config: 配置对象
        """
        super().__init__(parent)

        self.serial_handler = serial_handler
        self.config = config
        self.logger = logging.getLogger(__name__)

        # 对话框设置
        self.title("串口参数设置")
        self.geometry("500x600")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # 应用主题
        self.configure(bg=DieterStyle.COLORS['white'])

        # 配置变量
        self.port_var = tk.StringVar()
        self.baud_rate_var = tk.StringVar()
        self.data_bits_var = tk.StringVar()
        self.stop_bits_var = tk.StringVar()
        self.parity_var = tk.StringVar()
        self.auto_connect_var = tk.BooleanVar()

        # 测试连接状态
        self.test_result_var = tk.StringVar(value="未测试")

        # 创建UI
        self._create_ui()

        # 加载当前配置
        self._load_current_settings()

        # 居中显示
        self._center_window()

    def _create_ui(self):
        """创建用户界面"""
        # === 主容器 ===
        main_frame = tk.Frame(self, bg=DieterStyle.COLORS['white'])
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # === 标题 ===
        title_label = tk.Label(
            main_frame,
            text="⚙️ 串口参数设置",
            font=('Arial', 16, 'bold'),
            bg=DieterStyle.COLORS['white'],
            fg=DieterStyle.COLORS['black']
        )
        title_label.pack(pady=(0, 20))

        # === 串口选择 ===
        port_frame = self._create_setting_row(main_frame, "串口:")
        self.port_combo = ttk.Combobox(
            port_frame,
            textvariable=self.port_var,
            state='readonly',
            width=25,
            font=('Arial', 10)
        )
        self.port_combo.pack(side='left', fill='x', expand=True)

        # 刷新按钮
        refresh_btn = DieterWidgets.create_button(
            port_frame, "🔄 刷新", self._refresh_ports, 'secondary'
        )
        refresh_btn.config(width=8)
        refresh_btn.pack(side='left', padx=(5, 0))

        # === 波特率 ===
        baud_frame = self._create_setting_row(main_frame, "波特率:")
        self.baud_combo = ttk.Combobox(
            baud_frame,
            textvariable=self.baud_rate_var,
            values=['9600', '19200', '38400', '57600', '115200', '230400', '460800', '921600'],
            state='readonly',
            width=25,
            font=('Arial', 10)
        )
        self.baud_combo.pack(side='left', fill='x', expand=True)

        # === 数据位 ===
        data_frame = self._create_setting_row(main_frame, "数据位:")
        self.data_combo = ttk.Combobox(
            data_frame,
            textvariable=self.data_bits_var,
            values=['5', '6', '7', '8'],
            state='readonly',
            width=25,
            font=('Arial', 10)
        )
        self.data_combo.pack(side='left', fill='x', expand=True)

        # === 停止位 ===
        stop_frame = self._create_setting_row(main_frame, "停止位:")
        self.stop_combo = ttk.Combobox(
            stop_frame,
            textvariable=self.stop_bits_var,
            values=['1', '1.5', '2'],
            state='readonly',
            width=25,
            font=('Arial', 10)
        )
        self.stop_combo.pack(side='left', fill='x', expand=True)

        # === 校验位 ===
        parity_frame = self._create_setting_row(main_frame, "校验位:")
        self.parity_combo = ttk.Combobox(
            parity_frame,
            textvariable=self.parity_var,
            values=['None', 'Odd', 'Even', 'Mark', 'Space'],
            state='readonly',
            width=25,
            font=('Arial', 10)
        )
        self.parity_combo.pack(side='left', fill='x', expand=True)

        # === 自动连接 ===
        auto_frame = tk.Frame(main_frame, bg=DieterStyle.COLORS['white'])
        auto_frame.pack(fill='x', pady=10)

        auto_check = tk.Checkbutton(
            auto_frame,
            text="启动时自动连接",
            variable=self.auto_connect_var,
            bg=DieterStyle.COLORS['white'],
            fg=DieterStyle.COLORS['black'],
            font=('Arial', 10),
            activebackground=DieterStyle.COLORS['white'],
            selectcolor=DieterStyle.COLORS['white']
        )
        auto_check.pack(anchor='w')

        # === 分隔线 ===
        separator = tk.Frame(main_frame, height=2, bg=DieterStyle.COLORS['gray_light'])
        separator.pack(fill='x', pady=15)

        # === 测试连接 ===
        test_frame = tk.Frame(main_frame, bg=DieterStyle.COLORS['white'])
        test_frame.pack(fill='x', pady=10)

        test_btn = DieterWidgets.create_button(
            test_frame, "🔌 测试连接", self._test_connection, 'secondary'
        )
        test_btn.pack(side='left', padx=(0, 10))

        self.test_result_label = tk.Label(
            test_frame,
            textvariable=self.test_result_var,
            font=('Arial', 10),
            bg=DieterStyle.COLORS['white'],
            fg=DieterStyle.COLORS['gray_mid']
        )
        self.test_result_label.pack(side='left')

        # === 提示信息 ===
        hint_frame = tk.Frame(main_frame, bg=DieterStyle.COLORS['gray_light'],
                             relief='solid', bd=1)
        hint_frame.pack(fill='x', pady=10)

        hint_label = tk.Label(
            hint_frame,
            text="💡 提示:\n"
                 "• 默认配置: 115200, 8N1\n"
                 "• 修改参数后需重新连接\n"
                 "• 建议先测试连接再保存",
            font=('Arial', 9),
            bg=DieterStyle.COLORS['gray_light'],
            fg=DieterStyle.COLORS['gray_dark'],
            justify='left'
        )
        hint_label.pack(padx=10, pady=10, anchor='w')

        # === 按钮区域 ===
        button_frame = tk.Frame(main_frame, bg=DieterStyle.COLORS['white'])
        button_frame.pack(fill='x', pady=(20, 0))

        # 保存按钮
        save_btn = DieterWidgets.create_button(
            button_frame, "💾 保存", self._save_settings, 'primary'
        )
        save_btn.pack(side='left', padx=(0, 10))

        # 取消按钮
        cancel_btn = DieterWidgets.create_button(
            button_frame, "❌ 取消", self._cancel, 'secondary'
        )
        cancel_btn.pack(side='left', padx=(0, 10))

        # 恢复默认按钮
        default_btn = DieterWidgets.create_button(
            button_frame, "🔄 恢复默认", self._restore_defaults, 'secondary'
        )
        default_btn.pack(side='left')

    def _create_setting_row(self, parent, label_text: str) -> tk.Frame:
        """创建设置行"""
        row_frame = tk.Frame(parent, bg=DieterStyle.COLORS['white'])
        row_frame.pack(fill='x', pady=5)

        label = tk.Label(
            row_frame,
            text=label_text,
            font=('Arial', 10, 'bold'),
            bg=DieterStyle.COLORS['white'],
            fg=DieterStyle.COLORS['gray_dark'],
            width=10,
            anchor='w'
        )
        label.pack(side='left', padx=(0, 10))

        return row_frame

    def _refresh_ports(self):
        """刷新可用串口列表"""
        try:
            ports = serial.tools.list_ports.comports()
            port_list = [port.device for port in ports]

            if not port_list:
                port_list = ['无可用串口']
                self.logger.warning("未找到可用串口")

            self.port_combo['values'] = port_list

            # 如果当前选择的端口不在列表中，选择第一个
            if self.port_var.get() not in port_list and port_list:
                self.port_var.set(port_list[0])

            self.logger.info(f"刷新串口列表: {len(port_list)}个端口")

        except Exception as e:
            self.logger.error(f"刷新串口列表失败: {e}")
            messagebox.showerror("错误", f"刷新串口列表失败:\n{e}")

    def _load_current_settings(self):
        """加载当前配置"""
        try:
            # 刷新端口列表
            self._refresh_ports()

            # 加载配置
            self.port_var.set(self.config.get('serial.port', 'COM7'))
            self.baud_rate_var.set(str(self.config.get('serial.baud_rate', 115200)))
            self.data_bits_var.set(str(self.config.get('serial.data_bits', 8)))
            self.stop_bits_var.set(str(self.config.get('serial.stop_bits', 1)))
            self.parity_var.set(self.config.get('serial.parity', 'None'))
            self.auto_connect_var.set(self.config.get('serial.auto_connect', False))

            self.logger.info("已加载当前串口配置")

        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")

    def _test_connection(self):
        """测试连接"""
        try:
            port = self.port_var.get()
            baud_rate = int(self.baud_rate_var.get())
            data_bits = int(self.data_bits_var.get())
            stop_bits = float(self.stop_bits_var.get())
            parity = self._get_parity_value(self.parity_var.get())

            if port == '无可用串口':
                self.test_result_var.set("❌ 无可用串口")
                self.test_result_label.config(fg=DieterStyle.COLORS['error_red'])
                return

            # 尝试打开串口
            test_serial = serial.Serial(
                port=port,
                baudrate=baud_rate,
                bytesize=data_bits,
                stopbits=stop_bits,
                parity=parity,
                timeout=1.0
            )

            # 测试成功
            test_serial.close()
            self.test_result_var.set("✅ 连接成功")
            self.test_result_label.config(fg=DieterStyle.COLORS['success_green'])
            self.logger.info(f"测试连接成功: {port}")

        except serial.SerialException as e:
            self.test_result_var.set("❌ 连接失败")
            self.test_result_label.config(fg=DieterStyle.COLORS['error_red'])
            self.logger.error(f"测试连接失败: {e}")
            messagebox.showerror("连接失败", f"无法连接到串口:\n{e}")

        except Exception as e:
            self.test_result_var.set("❌ 错误")
            self.test_result_label.config(fg=DieterStyle.COLORS['error_red'])
            self.logger.error(f"测试连接错误: {e}")
            messagebox.showerror("错误", f"测试连接时发生错误:\n{e}")

    def _save_settings(self):
        """保存设置"""
        try:
            # 验证参数
            port = self.port_var.get()
            if port == '无可用串口':
                messagebox.showwarning("警告", "请选择有效的串口")
                return

            # 保存到配置
            self.config.set('serial.port', port)
            self.config.set('serial.baud_rate', int(self.baud_rate_var.get()))
            self.config.set('serial.data_bits', int(self.data_bits_var.get()))
            self.config.set('serial.stop_bits', float(self.stop_bits_var.get()))
            self.config.set('serial.parity', self.parity_var.get())
            self.config.set('serial.auto_connect', self.auto_connect_var.get())

            # 保存配置文件
            self.config.save()

            self.logger.info("串口配置已保存")
            messagebox.showinfo("成功", "串口配置已保存\n\n如果已连接，请断开并重新连接以应用新配置")

            self.destroy()

        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            messagebox.showerror("错误", f"保存配置失败:\n{e}")

    def _cancel(self):
        """取消"""
        self.destroy()

    def _restore_defaults(self):
        """恢复默认设置"""
        if messagebox.askyesno("确认", "确定要恢复默认串口设置吗?"):
            self.port_var.set('COM7')
            self.baud_rate_var.set('115200')
            self.data_bits_var.set('8')
            self.stop_bits_var.set('1')
            self.parity_var.set('None')
            self.auto_connect_var.set(False)
            self.test_result_var.set("未测试")
            self.test_result_label.config(fg=DieterStyle.COLORS['gray_mid'])
            self.logger.info("已恢复默认串口设置")

    def _get_parity_value(self, parity_str: str) -> str:
        """获取校验位值"""
        parity_map = {
            'None': serial.PARITY_NONE,
            'Odd': serial.PARITY_ODD,
            'Even': serial.PARITY_EVEN,
            'Mark': serial.PARITY_MARK,
            'Space': serial.PARITY_SPACE
        }
        return parity_map.get(parity_str, serial.PARITY_NONE)

    def _center_window(self):
        """居中显示窗口"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
