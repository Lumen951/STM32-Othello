#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serial Communication Handler for STM32 Othello PC Client
STM32串口通信处理器

@author: STM32 Othello Project Team
@version: 1.0
@date: 2025-11-22
"""

import serial
import serial.tools.list_ports
import threading
import time
import struct
from typing import Optional, Callable, List, Dict
from queue import Queue, Empty
import logging

class SerialProtocol:
    """串口协议定义"""

    # 协议常量
    PACKET_HEADER = 0xAA
    PACKET_FOOTER = 0x55
    MAX_DATA_LENGTH = 64

    # 命令定义
    CMD_BOARD_STATE = 0x01      # 棋盘状态同步
    CMD_MAKE_MOVE = 0x02        # 走子命令
    CMD_NEW_GAME = 0x03         # 新游戏命令
    CMD_GAME_OVER = 0x04        # 游戏结束
    CMD_SYSTEM_INFO = 0x05      # 系统信息查询
    CMD_AI_REQUEST = 0x06       # AI走法请求
    CMD_HEARTBEAT = 0x07        # 心跳包
    CMD_CONFIG_SET = 0x08       # 配置设置
    CMD_CONFIG_GET = 0x09       # 配置获取
    CMD_KEY_EVENT = 0x0A        # 按键事件

    @staticmethod
    def calculate_checksum(data: bytes) -> int:
        """计算校验和"""
        return sum(data) & 0xFF

    @staticmethod
    def create_packet(command: int, data: bytes = b'') -> bytes:
        """创建数据包"""
        if len(data) > SerialProtocol.MAX_DATA_LENGTH:
            raise ValueError("数据长度超出限制")

        packet = bytearray()
        packet.append(SerialProtocol.PACKET_HEADER)
        packet.append(command)
        packet.append(len(data))
        packet.extend(data)

        # 计算校验和（不包括包头包尾）
        checksum = SerialProtocol.calculate_checksum(packet[1:])
        packet.append(checksum)
        packet.append(SerialProtocol.PACKET_FOOTER)

        return bytes(packet)

    @staticmethod
    def parse_packet(data: bytes) -> Optional[tuple]:
        """解析数据包，返回(command, data)或None"""
        if len(data) < 5:  # 最小包长度
            return None

        if data[0] != SerialProtocol.PACKET_HEADER or data[-1] != SerialProtocol.PACKET_FOOTER:
            return None

        command = data[1]
        data_len = data[2]

        if len(data) != 5 + data_len:
            return None

        packet_data = data[3:3+data_len]
        checksum = data[3+data_len]

        # 验证校验和
        calculated_checksum = SerialProtocol.calculate_checksum(data[1:-2])
        if checksum != calculated_checksum:
            return None

        return command, packet_data

class SerialHandler:
    """STM32串口通信处理器"""

    def __init__(self, callback: Optional[Callable] = None, config=None):
        """
        初始化串口处理器

        Args:
            callback: 数据接收回调函数 callback(command, data)
            config: 配置对象
        """
        self.callback = callback
        self.config = config

        # 串口对象
        self.serial_port: Optional[serial.Serial] = None
        self.port_name = None
        self.baud_rate = 115200

        # 线程控制
        self.running = False
        self.receive_thread: Optional[threading.Thread] = None
        self.send_queue = Queue()
        self.send_thread: Optional[threading.Thread] = None

        # 数据缓冲
        self.receive_buffer = bytearray()
        self.packet_buffer = []

        # 状态监控
        self.connection_status = False
        self.last_heartbeat = 0
        self.heartbeat_interval = 5.0  # 5秒心跳间隔

        # 日志
        self.logger = logging.getLogger(__name__)

        # 统计信息
        self.stats = {
            'packets_sent': 0,
            'packets_received': 0,
            'errors': 0,
            'reconnect_count': 0
        }

    def get_available_ports(self) -> List[Dict]:
        """获取可用串口列表"""
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append({
                'device': port.device,
                'description': port.description,
                'hwid': port.hwid
            })
        return ports

    def connect(self, port: str = None, baud_rate: int = None) -> bool:
        """
        连接串口

        Args:
            port: 串口名称，如果为None则自动检测
            baud_rate: 波特率，默认115200

        Returns:
            bool: 连接是否成功
        """
        try:
            # 断开现有连接
            if self.is_connected():
                self.disconnect()

            # 设置参数
            if port:
                self.port_name = port
            elif not self.port_name:
                # 自动检测STM32设备
                self.port_name = self._auto_detect_port()
                if not self.port_name:
                    self.logger.error("未找到STM32设备")
                    return False

            if baud_rate:
                self.baud_rate = baud_rate

            # 创建串口连接
            self.serial_port = serial.Serial(
                port=self.port_name,
                baudrate=self.baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0,
                write_timeout=1.0
            )

            if not self.serial_port.is_open:
                self.serial_port.open()

            # 清空缓冲区
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()

            # 启动通信线程
            self.running = True
            self.receive_thread = threading.Thread(target=self._receive_worker, daemon=True)
            self.send_thread = threading.Thread(target=self._send_worker, daemon=True)

            self.receive_thread.start()
            self.send_thread.start()

            self.connection_status = True
            self.stats['reconnect_count'] += 1
            self.logger.info(f"成功连接串口: {self.port_name}")

            # 发送初始化命令
            self.send_system_info_request()

            return True

        except Exception as e:
            self.logger.error(f"连接串口失败: {e}")
            self.connection_status = False
            return False

    def disconnect(self):
        """断开串口连接"""
        try:
            self.running = False
            self.connection_status = False

            # 等待线程结束
            if self.receive_thread and self.receive_thread.is_alive():
                self.receive_thread.join(timeout=2.0)

            if self.send_thread and self.send_thread.is_alive():
                self.send_thread.join(timeout=2.0)

            # 关闭串口
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
                self.serial_port = None

            self.logger.info("串口连接已断开")

        except Exception as e:
            self.logger.error(f"断开串口连接时出错: {e}")

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return (self.connection_status and
                self.serial_port and
                self.serial_port.is_open and
                self.running)

    def send_command(self, command: int, data: bytes = b'') -> bool:
        """
        发送命令

        Args:
            command: 命令代码
            data: 数据内容

        Returns:
            bool: 发送是否成功
        """
        try:
            packet = SerialProtocol.create_packet(command, data)
            self.send_queue.put(packet, timeout=1.0)
            return True
        except Exception as e:
            self.logger.error(f"发送命令失败: {e}")
            return False

    def send_board_state(self, board_data: bytes) -> bool:
        """发送棋盘状态"""
        if len(board_data) != 64:
            self.logger.error("棋盘数据长度必须为64字节")
            return False
        return self.send_command(SerialProtocol.CMD_BOARD_STATE, board_data)

    def send_make_move(self, row: int, col: int, player: int) -> bool:
        """发送走棋命令"""
        data = struct.pack('BBB', row, col, player)
        return self.send_command(SerialProtocol.CMD_MAKE_MOVE, data)

    def send_new_game(self) -> bool:
        """发送新游戏命令"""
        return self.send_command(SerialProtocol.CMD_NEW_GAME)

    def send_ai_request(self, difficulty: int = 1) -> bool:
        """请求AI走法"""
        data = struct.pack('B', difficulty)
        return self.send_command(SerialProtocol.CMD_AI_REQUEST, data)

    def send_heartbeat(self) -> bool:
        """发送心跳包"""
        current_time = time.time()
        if current_time - self.last_heartbeat >= self.heartbeat_interval:
            self.last_heartbeat = current_time
            return self.send_command(SerialProtocol.CMD_HEARTBEAT)
        return True

    def send_system_info_request(self) -> bool:
        """请求系统信息"""
        return self.send_command(SerialProtocol.CMD_SYSTEM_INFO)

    def send_config_set(self, config_data: bytes) -> bool:
        """设置配置"""
        return self.send_command(SerialProtocol.CMD_CONFIG_SET, config_data)

    def send_config_get(self) -> bool:
        """获取配置"""
        return self.send_command(SerialProtocol.CMD_CONFIG_GET)

    def _auto_detect_port(self) -> Optional[str]:
        """自动检测STM32设备端口"""
        ports = self.get_available_ports()

        # STM32设备的常见标识
        stm32_indicators = [
            'STM32',
            'STMicroelectronics',
            'Virtual COM Port',
            'USB Serial',
            'CH340',
            'CP210'
        ]

        for port_info in ports:
            description = port_info['description'].upper()
            hwid = port_info['hwid'].upper()

            for indicator in stm32_indicators:
                if indicator.upper() in description or indicator.upper() in hwid:
                    self.logger.info(f"检测到STM32设备: {port_info['device']} - {port_info['description']}")
                    return port_info['device']

        # 如果没有找到特定标识，返回第一个可用端口
        if ports:
            self.logger.warning(f"未检测到STM32设备标识，使用第一个可用端口: {ports[0]['device']}")
            return ports[0]['device']

        return None

    def _receive_worker(self):
        """接收数据工作线程"""
        while self.running:
            try:
                if self.serial_port and self.serial_port.is_open:
                    # 读取数据
                    if self.serial_port.in_waiting > 0:
                        data = self.serial_port.read(self.serial_port.in_waiting)
                        self.receive_buffer.extend(data)

                        # 解析数据包
                        self._parse_received_data()

                    time.sleep(0.01)  # 10ms轮询间隔
                else:
                    time.sleep(0.1)

            except Exception as e:
                self.logger.error(f"接收数据错误: {e}")
                self.stats['errors'] += 1
                time.sleep(0.1)

    def _send_worker(self):
        """发送数据工作线程"""
        while self.running:
            try:
                # 从队列获取数据包
                packet = self.send_queue.get(timeout=1.0)

                if self.serial_port and self.serial_port.is_open:
                    self.serial_port.write(packet)
                    self.serial_port.flush()
                    self.stats['packets_sent'] += 1
                else:
                    self.logger.warning("串口未连接，丢弃数据包")

            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"发送数据错误: {e}")
                self.stats['errors'] += 1

    def _parse_received_data(self):
        """解析接收到的数据"""
        while len(self.receive_buffer) >= 5:  # 最小包长度
            # 查找包头
            header_index = self.receive_buffer.find(SerialProtocol.PACKET_HEADER)
            if header_index == -1:
                # 没有找到包头，清空缓冲区
                self.receive_buffer.clear()
                break

            # 移除包头之前的数据
            if header_index > 0:
                self.receive_buffer = self.receive_buffer[header_index:]

            # 检查是否有完整的包
            if len(self.receive_buffer) < 3:
                break

            data_len = self.receive_buffer[2]
            packet_len = 5 + data_len

            if len(self.receive_buffer) < packet_len:
                break  # 数据不完整，等待更多数据

            # 提取数据包
            packet_data = bytes(self.receive_buffer[:packet_len])
            self.receive_buffer = self.receive_buffer[packet_len:]

            # 解析数据包
            result = SerialProtocol.parse_packet(packet_data)
            if result:
                command, data = result
                self.stats['packets_received'] += 1

                # 调用回调函数
                if self.callback:
                    try:
                        self.callback(command, data)
                    except Exception as e:
                        self.logger.error(f"回调函数执行错误: {e}")

                self.logger.debug(f"接收到命令: 0x{command:02X}, 数据长度: {len(data)}")
            else:
                self.logger.warning("接收到无效数据包")
                self.stats['errors'] += 1

    def get_connection_info(self) -> Dict:
        """获取连接信息"""
        return {
            'connected': self.is_connected(),
            'port': self.port_name,
            'baud_rate': self.baud_rate,
            'stats': self.stats.copy()
        }

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'packets_sent': 0,
            'packets_received': 0,
            'errors': 0,
            'reconnect_count': 0
        }