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
    PACKET_HEADER = 0x02  # STX
    PACKET_FOOTER = 0x03  # ETX
    MAX_DATA_LENGTH = 255

    # 命令定义 (必须与STM32端uart_protocol.h保持一致)
    CMD_BOARD_STATE = 0x01      # 棋盘状态同步
    CMD_MAKE_MOVE = 0x02        # 走子命令
    CMD_GAME_CONFIG = 0x03      # 游戏配置/新游戏
    CMD_GAME_STATS = 0x04       # 游戏统计
    CMD_SYSTEM_INFO = 0x05      # 系统信息查询
    CMD_AI_REQUEST = 0x06       # AI走法请求
    CMD_HEARTBEAT = 0x07        # 心跳包
    CMD_ACK = 0x08              # 命令确认
    CMD_DEBUG_INFO = 0x09       # 调试信息
    CMD_KEY_EVENT = 0x0A        # 按键事件
    CMD_LED_CONTROL = 0x0B      # LED控制
    CMD_GAME_CONTROL = 0x0C     # 游戏控制
    CMD_MODE_SELECT = 0x0D      # 模式选择
    CMD_SCORE_UPDATE = 0x0E     # 分数更新
    CMD_TIMER_UPDATE = 0x0F     # 计时器更新
    CMD_CHEAT_COLOR_SELECT = 0x10  # [DEPRECATED] 作弊模式颜色选择（已废弃）
    CMD_CHEAT_TOGGLE = 0x11     # 作弊模式切换（叠加状态）
    CMD_ERROR = 0xFF            # 错误响应

    # 游戏控制动作
    GAME_ACTION_START = 0x01    # 开始游戏
    GAME_ACTION_PAUSE = 0x02    # 暂停游戏
    GAME_ACTION_RESUME = 0x03   # 继续游戏
    GAME_ACTION_END = 0x04      # 结束游戏
    GAME_ACTION_RESET = 0x05    # 重置游戏

    # 游戏模式
    GAME_MODE_NORMAL = 0x01     # 普通模式
    GAME_MODE_CHALLENGE = 0x02  # 闯关模式
    GAME_MODE_TIMED = 0x03      # 计时模式
    # GAME_MODE_CHEAT (0x04) 已删除 - 作弊功能改为叠加状态

    @staticmethod
    def calculate_checksum(command: int, length: int, data: bytes) -> int:
        """计算校验和 (XOR算法)"""
        checksum = command ^ length
        for byte in data:
            checksum ^= byte
        return checksum

    @staticmethod
    def create_packet(command: int, data: bytes = b'') -> bytes:
        """创建数据包 (格式: STX + CMD + LEN + DATA + CHECKSUM + ETX)"""
        if len(data) > SerialProtocol.MAX_DATA_LENGTH:
            raise ValueError("数据长度超出限制")

        packet = bytearray()
        packet.append(SerialProtocol.PACKET_HEADER)  # STX
        packet.append(command)
        packet.append(len(data))
        packet.extend(data)

        # 计算校验和 (XOR: CMD ^ LEN ^ DATA[0] ^ DATA[1] ^ ...)
        checksum = SerialProtocol.calculate_checksum(command, len(data), data)
        packet.append(checksum)
        packet.append(SerialProtocol.PACKET_FOOTER)  # ETX

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

        # 验证校验和 (XOR算法)
        calculated_checksum = SerialProtocol.calculate_checksum(command, data_len, packet_data)
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

            # 详细日志 - 命令名称映射
            cmd_name = {
                0x01: 'BOARD_STATE', 0x02: 'MAKE_MOVE', 0x03: 'GAME_CONFIG',
                0x04: 'GAME_STATS', 0x05: 'SYSTEM_INFO', 0x06: 'AI_REQUEST',
                0x07: 'HEARTBEAT', 0x08: 'ACK', 0x09: 'DEBUG_INFO',
                0x0A: 'KEY_EVENT', 0x0B: 'LED_CONTROL', 0x0C: 'GAME_CONTROL',
                0x0D: 'MODE_SELECT', 0x0E: 'SCORE_UPDATE', 0x0F: 'TIMER_UPDATE',
                0xFF: 'ERROR'
            }.get(command, f'UNKNOWN({command:02X})')

            self.logger.info(f"📤 发送命令: {cmd_name} (0x{command:02X}), 数据长度: {len(data)}")
            if len(data) > 0 and len(data) <= 16:
                self.logger.debug(f"   数据内容: {data.hex(' ')}")

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
        timestamp = int(time.time() * 1000) & 0xFFFFFFFF  # 毫秒级时间戳，4字节
        # 使用BBBxI格式确保8字节对齐（x表示1字节padding）
        # 对应C结构体: uint8_t[3] + padding[1] + uint32_t[4] = 8字节
        data = struct.pack('<BBBxI', row, col, player, timestamp)
        return self.send_command(SerialProtocol.CMD_MAKE_MOVE, data)

    def send_new_game(self) -> bool:
        """发送新游戏命令"""
        return self.send_command(SerialProtocol.CMD_GAME_CONFIG)

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

    def send_game_control(self, action: int) -> bool:
        """
        发送游戏控制命令

        Args:
            action: 游戏控制动作 (GAME_ACTION_START/PAUSE/RESUME/END/RESET)

        Returns:
            bool: 发送是否成功
        """
        timestamp = int(time.time() * 1000) & 0xFFFFFFFF
        # 使用BxxxI格式确保8字节对齐（xxx表示3字节padding）
        # 对应C结构体: uint8_t + padding[3] + uint32_t[4] = 8字节
        data = struct.pack('<BxxxI', action, timestamp)
        return self.send_command(SerialProtocol.CMD_GAME_CONTROL, data)

    def send_game_start(self) -> bool:
        """发送开始游戏命令"""
        return self.send_game_control(SerialProtocol.GAME_ACTION_START)

    def send_game_pause(self) -> bool:
        """发送暂停游戏命令"""
        return self.send_game_control(SerialProtocol.GAME_ACTION_PAUSE)

    def send_game_resume(self) -> bool:
        """发送继续游戏命令"""
        return self.send_game_control(SerialProtocol.GAME_ACTION_RESUME)

    def send_game_end(self) -> bool:
        """发送结束游戏命令"""
        return self.send_game_control(SerialProtocol.GAME_ACTION_END)

    def send_game_reset(self) -> bool:
        """发送重置游戏命令"""
        return self.send_game_control(SerialProtocol.GAME_ACTION_RESET)

    def send_mode_select(self, mode: int, time_limit: int = 0) -> bool:
        """
        发送模式选择命令

        Args:
            mode: 游戏模式 (GAME_MODE_NORMAL/CHALLENGE/TIMED)
                  ⚠️ GAME_MODE_CHEAT已废弃，请使用send_cheat_toggle()
            time_limit: 时间限制（秒），仅用于计时模式

        Returns:
            bool: 发送是否成功
        """
        # 拒绝废弃的作弊模式值
        if mode == 0x04:  # Old GAME_MODE_CHEAT
            self.logger.error("GAME_MODE_CHEAT is deprecated. Use send_cheat_toggle() instead.")
            return False

        data = struct.pack('<BH', mode, time_limit)
        return self.send_command(SerialProtocol.CMD_MODE_SELECT, data)

    def send_cheat_toggle(self, enable: bool, selected_color: int = 1) -> bool:
        """
        发送作弊模式切换命令

        Args:
            enable: True=启用作弊叠加, False=禁用作弊叠加
            selected_color: 选定的棋子颜色 (1=黑棋, 2=白棋)

        Returns:
            bool: 发送是否成功
        """
        # === 严格参数验证 ===
        if not isinstance(selected_color, int):
            self.logger.error(f"❌ Invalid color type: {type(selected_color).__name__}, expected int")
            return False

        if selected_color not in [1, 2]:
            self.logger.error(f"❌ Invalid selected color value: {selected_color}, must be 1 (BLACK) or 2 (WHITE)")
            return False

        # === 连接状态检查 ===
        if not self.is_connected():
            self.logger.error("❌ Cannot send cheat toggle: STM32 not connected")
            return False

        try:
            # 构造数据包: uint8_t enable + uint8_t selected_color
            enable_byte = 1 if enable else 0

            # 确保颜色值为有效的uint8_t
            color_byte = int(selected_color) & 0xFF

            data = struct.pack('<BB', enable_byte, color_byte)

            # 详细日志
            state_name = "ENABLED" if enable else "DISABLED"
            color_name = "BLACK" if selected_color == 1 else "WHITE"
            self.logger.info(f"📤 Sending cheat toggle: {state_name}, Color: {color_name} (enable={enable_byte}, color={color_byte})")

            # 发送命令
            success = self.send_command(SerialProtocol.CMD_CHEAT_TOGGLE, data)

            if success:
                self.logger.info(f"✅ Cheat toggle sent successfully")
            else:
                self.logger.error("❌ Failed to send cheat toggle command")

            return success

        except struct.error as e:
            self.logger.error(f"❌ Struct packing error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Error sending cheat toggle: {e}")
            import traceback
            traceback.print_exc()
            return False

    def send_cheat_color_select(self, player_color: int) -> bool:
        """
        [DEPRECATED] 发送作弊模式颜色选择命令
        请使用 send_cheat_toggle() 代替

        Args:
            player_color: 玩家颜色 (1=黑棋, 2=白棋)

        Returns:
            bool: 发送是否成功
        """
        self.logger.warning("send_cheat_color_select() is deprecated, use send_cheat_toggle() instead")
        # 为了向后兼容，转换为新格式
        return self.send_cheat_toggle(True, player_color)

    def send_score_update(self, black_score: int, white_score: int,
                         total_score: int = 0, game_result: int = 0) -> bool:
        """
        发送分数更新

        Args:
            black_score: 黑子分数
            white_score: 白子分数
            total_score: 累计总分（闯关模式）
            game_result: 游戏结果 (0=进行中, 1=黑胜, 2=白胜, 3=平局)

        Returns:
            bool: 发送是否成功
        """
        data = struct.pack('<BBHB', black_score, white_score, total_score, game_result)
        return self.send_command(SerialProtocol.CMD_SCORE_UPDATE, data)

    def send_timer_update(self, remaining_time: int, timer_state: int) -> bool:
        """
        发送计时器更新

        Args:
            remaining_time: 剩余时间（秒）
            timer_state: 计时器状态 (0=停止, 1=运行, 2=暂停, 3=超时)

        Returns:
            bool: 发送是否成功
        """
        data = struct.pack('<HB', remaining_time, timer_state)
        return self.send_command(SerialProtocol.CMD_TIMER_UPDATE, data)

    def send_full_game_state(self, game_state) -> bool:
        """发送完整游戏状态到STM32（用于手动同步）

        Args:
            game_state: GameState对象

        Returns:
            bool: 发送是否成功
        """
        try:
            # 构建72字节数据包
            data = bytearray(72)

            # 1. 棋盘数据 (0-63字节)
            for row in range(8):
                for col in range(8):
                    idx = row * 8 + col
                    data[idx] = game_state.board[row][col].value

            # 2. 当前玩家 (64字节)
            data[64] = game_state.current_player.value

            # 3. 棋子计数 (65-66字节)
            data[65] = game_state.black_count
            data[66] = game_state.white_count

            # 4. 游戏结束标志 (67字节)
            data[67] = 1 if game_state.status.value != 0 else 0

            # 5. 走法计数 (68-71字节, little-endian)
            struct.pack_into('<I', data, 68, game_state.move_count)

            self.logger.info(f"发送完整游戏状态: 玩家={game_state.current_player.name}, "
                            f"黑={game_state.black_count}, 白={game_state.white_count}")

            # 发送数据（使用CMD_BOARD_STATE命令）
            return self.send_command(SerialProtocol.CMD_BOARD_STATE, bytes(data))

        except Exception as e:
            self.logger.error(f"构建游戏状态数据失败: {e}")
            return False

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
        self.logger.info("串口接收线程已启动")
        while self.running:
            try:
                if self.serial_port and self.serial_port.is_open:
                    # 读取数据
                    if self.serial_port.in_waiting > 0:
                        data = self.serial_port.read(self.serial_port.in_waiting)
                        self.logger.debug(f"接收到原始数据 ({len(data)}字节): {data.hex(' ')}")
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

        self.logger.info("串口接收线程已停止")

    def _send_worker(self):
        """发送数据工作线程"""
        while self.running:
            try:
                # 从队列获取数据包
                packet = self.send_queue.get(timeout=1.0)

                if self.serial_port and self.serial_port.is_open:
                    # 添加详细的十六进制日志
                    self.logger.debug(f"发送数据包 ({len(packet)}字节): {packet.hex(' ')}")

                    self.serial_port.write(packet)
                    self.serial_port.flush()
                    self.stats['packets_sent'] += 1

                    # 发送成功日志
                    cmd_byte = packet[1] if len(packet) > 1 else 0
                    len_byte = packet[2] if len(packet) > 2 else 0
                    self.logger.info(f"✅ 发送成功 - 命令: 0x{cmd_byte:02X}, 数据长度: {len_byte}")
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
                self.logger.warning(f"未找到包头，丢弃 {len(self.receive_buffer)} 字节数据")
                self.receive_buffer.clear()
                break

            # 移除包头之前的数据
            if header_index > 0:
                self.logger.warning(f"包头前有 {header_index} 字节垃圾数据，已丢弃")
                self.receive_buffer = self.receive_buffer[header_index:]

            # 检查是否有完整的包
            if len(self.receive_buffer) < 3:
                break

            data_len = self.receive_buffer[2]
            packet_len = 5 + data_len

            if len(self.receive_buffer) < packet_len:
                self.logger.debug(f"数据包不完整，等待更多数据 (当前:{len(self.receive_buffer)}, 需要:{packet_len})")
                break  # 数据不完整，等待更多数据

            # 提取数据包
            packet_data = bytes(self.receive_buffer[:packet_len])
            self.receive_buffer = self.receive_buffer[packet_len:]

            self.logger.debug(f"提取数据包 ({packet_len}字节): {packet_data.hex(' ')}")

            # 解析数据包
            result = SerialProtocol.parse_packet(packet_data)
            if result:
                command, data = result
                self.stats['packets_received'] += 1

                self.logger.info(f"✅ 解析成功 - 命令: 0x{command:02X}, 数据长度: {len(data)}, 数据: {data.hex(' ') if len(data) <= 16 else data[:16].hex(' ') + '...'}")

                # 调用回调函数
                if self.callback:
                    try:
                        self.logger.debug(f"调用回调函数，命令: 0x{command:02X}")
                        self.callback(command, data)
                    except Exception as e:
                        self.logger.error(f"回调函数执行错误: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    self.logger.warning("⚠️ 回调函数未设置，数据包被忽略")

            else:
                self.logger.warning(f"❌ 数据包校验失败: {packet_data.hex(' ')}")
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