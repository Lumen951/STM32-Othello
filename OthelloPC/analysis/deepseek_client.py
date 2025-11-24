#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek AI Client for STM32 Othello PC Client
DeepSeek AI分析客户端

@author: STM32 Othello Project Team
@version: 1.0
@date: 2025-11-22
"""

import requests
import json
import time
from typing import Optional, Dict, List
import logging
from datetime import datetime

from game.game_state import GameState, Move, PieceType, GameStatus

class DeepSeekClient:
    """DeepSeek AI分析客户端"""

    def __init__(self, api_key: str = None, base_url: str = "https://api.deepseek.com"):
        """
        初始化DeepSeek客户端

        Args:
            api_key: DeepSeek API密钥
            base_url: API基础URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)

        # 设置请求头
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })

        # 分析参数配置
        self.analysis_config = {
            'model': 'deepseek-chat',
            'temperature': 0.1,
            'max_tokens': 2000
        }

    def set_api_key(self, api_key: str):
        """设置API密钥"""
        self.api_key = api_key
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}'
        })

    def analyze_game(self, game_state: GameState, language: str = 'zh') -> Optional[Dict]:
        """
        分析完整游戏

        Args:
            game_state: 游戏状态对象
            language: 分析语言 ('zh' 中文, 'en' 英文)

        Returns:
            Dict: 分析结果
        """
        try:
            # 生成游戏描述
            game_description = self._generate_game_description(game_state, language)

            # 构建分析提示
            prompt = self._build_analysis_prompt(game_description, language)

            # 调用DeepSeek API
            response = self._call_deepseek_api(prompt)

            if response:
                return {
                    'success': True,
                    'analysis': response,
                    'game_info': {
                        'total_moves': game_state.move_count,
                        'final_score': f"{game_state.black_count}-{game_state.white_count}",
                        'winner': self._get_winner_text(game_state.status, language),
                        'duration': game_state.get_game_duration(),
                        'timestamp': datetime.now().isoformat()
                    }
                }
            else:
                return {
                    'success': False,
                    'error': '无法获取AI分析结果'
                }

        except Exception as e:
            self.logger.error(f"游戏分析失败: {e}")
            return {
                'success': False,
                'error': f'分析过程中发生错误: {str(e)}'
            }

    def analyze_position(self, game_state: GameState, language: str = 'zh') -> Optional[Dict]:
        """
        分析当前局面

        Args:
            game_state: 游戏状态对象
            language: 分析语言

        Returns:
            Dict: 局面分析结果
        """
        try:
            # 生成局面描述
            position_description = self._generate_position_description(game_state, language)

            # 构建局面分析提示
            prompt = self._build_position_analysis_prompt(position_description, language)

            # 调用DeepSeek API
            response = self._call_deepseek_api(prompt)

            if response:
                return {
                    'success': True,
                    'analysis': response,
                    'position_info': {
                        'move_count': game_state.move_count,
                        'current_score': f"{game_state.black_count}-{game_state.white_count}",
                        'current_player': '黑方' if game_state.current_player == PieceType.BLACK else '白方',
                        'valid_moves': len(game_state.get_valid_moves(game_state.current_player)),
                        'timestamp': datetime.now().isoformat()
                    }
                }
            else:
                return {
                    'success': False,
                    'error': '无法获取局面分析结果'
                }

        except Exception as e:
            self.logger.error(f"局面分析失败: {e}")
            return {
                'success': False,
                'error': f'局面分析过程中发生错误: {str(e)}'
            }

    def _generate_game_description(self, game_state: GameState, language: str) -> str:
        """生成游戏描述"""
        if language == 'zh':
            description = f"黑白棋游戏完整复盘分析\n\n"
            description += f"游戏结果: {self._get_winner_text(game_state.status, language)}\n"
            description += f"最终比分: 黑子{game_state.black_count} - 白子{game_state.white_count}\n"
            description += f"总手数: {game_state.move_count}手\n"
            description += f"游戏时长: {self._format_duration(game_state.get_game_duration())}\n\n"

            if game_state.moves_history:
                description += "完整棋谱:\n"
                for i, move in enumerate(game_state.moves_history):
                    move_num = i + 1
                    player = "黑" if move.player == PieceType.BLACK else "白"
                    notation = move.to_notation()
                    description += f"{move_num:2d}. {player}方 {notation}"
                    if move.flipped_count > 0:
                        description += f" (翻转{move.flipped_count}子)"
                    description += "\n"

            description += f"\n当前棋盘状态:\n{self._format_board(game_state)}"
        else:
            description = f"Othello Game Complete Analysis\n\n"
            description += f"Game Result: {self._get_winner_text(game_state.status, language)}\n"
            description += f"Final Score: Black {game_state.black_count} - White {game_state.white_count}\n"
            description += f"Total Moves: {game_state.move_count}\n"
            description += f"Game Duration: {self._format_duration(game_state.get_game_duration())}\n\n"

            if game_state.moves_history:
                description += "Complete Game Record:\n"
                for i, move in enumerate(game_state.moves_history):
                    move_num = i + 1
                    player = "Black" if move.player == PieceType.BLACK else "White"
                    notation = move.to_notation()
                    description += f"{move_num:2d}. {player} {notation}"
                    if move.flipped_count > 0:
                        description += f" (flipped {move.flipped_count})"
                    description += "\n"

            description += f"\nFinal Board Position:\n{self._format_board(game_state)}"

        return description

    def _generate_position_description(self, game_state: GameState, language: str) -> str:
        """生成局面描述"""
        if language == 'zh':
            description = f"黑白棋局面分析\n\n"
            description += f"当前回合: {game_state.move_count}手\n"
            description += f"轮到: {'黑方' if game_state.current_player == PieceType.BLACK else '白方'}\n"
            description += f"当前比分: 黑子{game_state.black_count} - 白子{game_state.white_count}\n"
            description += f"可选走法: {len(game_state.get_valid_moves(game_state.current_player))}个\n\n"
            description += f"当前棋盘:\n{self._format_board(game_state)}\n"

            # 添加最近几步走法
            if game_state.moves_history:
                recent_moves = game_state.moves_history[-5:]  # 最近5步
                description += "\n最近走法:\n"
                start_num = max(1, game_state.move_count - len(recent_moves) + 1)
                for i, move in enumerate(recent_moves):
                    move_num = start_num + i
                    player = "黑" if move.player == PieceType.BLACK else "白"
                    description += f"{move_num}. {player}方 {move.to_notation()}\n"
        else:
            description = f"Othello Position Analysis\n\n"
            description += f"Move Number: {game_state.move_count}\n"
            description += f"To Move: {'Black' if game_state.current_player == PieceType.BLACK else 'White'}\n"
            description += f"Current Score: Black {game_state.black_count} - White {game_state.white_count}\n"
            description += f"Legal Moves: {len(game_state.get_valid_moves(game_state.current_player))}\n\n"
            description += f"Current Board:\n{self._format_board(game_state)}\n"

            if game_state.moves_history:
                recent_moves = game_state.moves_history[-5:]
                description += "\nRecent Moves:\n"
                start_num = max(1, game_state.move_count - len(recent_moves) + 1)
                for i, move in enumerate(recent_moves):
                    move_num = start_num + i
                    player = "Black" if move.player == PieceType.BLACK else "White"
                    description += f"{move_num}. {player} {move.to_notation()}\n"

        return description

    def _build_analysis_prompt(self, game_description: str, language: str) -> str:
        """构建完整游戏分析提示"""
        if language == 'zh':
            prompt = """你是一位专业的黑白棋(Othello)分析师。请对以下游戏进行深入分析:

{game_description}

请从以下角度进行详细分析:
1. 开局阶段: 分析开局走法的优劣，是否符合黑白棋基本原理
2. 中局发展: 评估中局的关键转折点，分析重要走法的得失
3. 残局技巧: 分析残局阶段的技术要点和胜负手
4. 整体战术: 评估双方的整体战略思路和执行效果
5. 关键走法: 指出影响胜负的关键走法和失误
6. 学习建议: 给出具体的改进建议和学习要点

请用专业但通俗的语言进行分析，让普通玩家也能理解。分析应该具体、客观，并给出实用的建议。""".format(game_description=game_description)
        else:
            prompt = """You are a professional Othello/Reversi analyst. Please provide a comprehensive analysis of the following game:

{game_description}

Please analyze from the following perspectives:
1. Opening Play: Evaluate the opening moves and adherence to basic Othello principles
2. Middle Game: Assess key turning points and critical move evaluations
3. Endgame Technique: Analyze endgame tactics and decisive moves
4. Overall Strategy: Evaluate both players' strategic approaches and execution
5. Key Moves: Identify game-changing moves and critical mistakes
6. Learning Points: Provide specific improvement suggestions and study recommendations

Use professional but accessible language that general players can understand. The analysis should be specific, objective, and provide practical advice.""".format(game_description=game_description)

        return prompt

    def _build_position_analysis_prompt(self, position_description: str, language: str) -> str:
        """构建局面分析提示"""
        if language == 'zh':
            prompt = """你是一位专业的黑白棋(Othello)分析师。请对以下局面进行分析:

{position_description}

请从以下角度分析当前局面:
1. 局面评估: 分析当前局面的优劣形势
2. 关键区域: 指出棋盘上的关键位置和控制要点
3. 可选走法: 评估主要的可选走法及其后果
4. 战术建议: 给出具体的战术建议和注意事项
5. 风险评估: 分析可能的风险和机会

请用简洁明了的语言进行分析，重点突出实用性。""".format(position_description=position_description)
        else:
            prompt = """You are a professional Othello/Reversi analyst. Please analyze the following position:

{position_description}

Please analyze the current position from these perspectives:
1. Position Evaluation: Assess the current advantage/disadvantage
2. Key Areas: Identify critical squares and control points on the board
3. Move Options: Evaluate main move choices and their consequences
4. Tactical Advice: Provide specific tactical recommendations and considerations
5. Risk Assessment: Analyze potential risks and opportunities

Use clear and concise language with focus on practical insights.""".format(position_description=position_description)

        return prompt

    def _call_deepseek_api(self, prompt: str) -> Optional[str]:
        """调用DeepSeek API"""
        if not self.api_key:
            self.logger.error("未设置DeepSeek API密钥")
            return None

        try:
            payload = {
                'model': self.analysis_config['model'],
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': self.analysis_config['temperature'],
                'max_tokens': self.analysis_config['max_tokens']
            }

            response = self.session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content']
                else:
                    self.logger.error("API响应格式异常")
                    return None
            else:
                self.logger.error(f"API请求失败: {response.status_code} - {response.text}")
                return None

        except requests.RequestException as e:
            self.logger.error(f"网络请求错误: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析错误: {e}")
            return None

    def _format_board(self, game_state: GameState) -> str:
        """格式化棋盘显示"""
        board_str = "   A B C D E F G H\n"
        for row in range(8):
            board_str += f"{row + 1}  "
            for col in range(8):
                piece = game_state.board[row][col]
                if piece == PieceType.BLACK:
                    board_str += "● "
                elif piece == PieceType.WHITE:
                    board_str += "○ "
                else:
                    board_str += "· "
            board_str += f" {row + 1}\n"
        board_str += "   A B C D E F G H"
        return board_str

    def _get_winner_text(self, status: GameStatus, language: str) -> str:
        """获取胜负结果文本"""
        if language == 'zh':
            if status == GameStatus.BLACK_WIN:
                return "黑方获胜"
            elif status == GameStatus.WHITE_WIN:
                return "白方获胜"
            elif status == GameStatus.DRAW:
                return "平局"
            else:
                return "游戏进行中"
        else:
            if status == GameStatus.BLACK_WIN:
                return "Black Wins"
            elif status == GameStatus.WHITE_WIN:
                return "White Wins"
            elif status == GameStatus.DRAW:
                return "Draw"
            else:
                return "Game in Progress"

    def _format_duration(self, duration: float) -> str:
        """格式化时长显示"""
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def test_connection(self) -> Dict:
        """测试API连接"""
        try:
            test_prompt = "Hello, this is a connection test."
            result = self._call_deepseek_api(test_prompt)

            if result:
                return {
                    'success': True,
                    'message': 'DeepSeek API连接正常'
                }
            else:
                return {
                    'success': False,
                    'message': 'DeepSeek API连接失败'
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'连接测试失败: {str(e)}'
            }

class AnalysisCache:
    """分析结果缓存"""

    def __init__(self, max_size: int = 50):
        self.cache: Dict[str, Dict] = {}
        self.max_size = max_size
        self.access_times: Dict[str, float] = {}

    def get_cache_key(self, game_state: GameState) -> str:
        """生成缓存键"""
        moves_str = ",".join([f"{m.row}{m.col}" for m in game_state.moves_history])
        return f"{game_state.move_count}_{moves_str}_{game_state.status.value}"

    def get(self, key: str) -> Optional[Dict]:
        """获取缓存结果"""
        if key in self.cache:
            self.access_times[key] = time.time()
            return self.cache[key]
        return None

    def put(self, key: str, analysis: Dict):
        """存储分析结果"""
        # 如果缓存已满，移除最久未使用的项
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            del self.cache[oldest_key]
            del self.access_times[oldest_key]

        self.cache[key] = analysis
        self.access_times[key] = time.time()

    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.access_times.clear()