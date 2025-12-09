#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF Report Generator for STM32 Othello PC Client
PDF报告生成器

@author: STM32 Othello Project Team
@version: 1.0
@date: 2025-12-09
"""

import os
from datetime import datetime
from typing import List, Optional
import logging

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

from game.game_state import GameState, Move, PieceType, GameStatus


class PDFReportGenerator:
    """PDF报告生成器"""

    def __init__(self, output_path: str):
        """
        初始化PDF生成器

        Args:
            output_path: PDF输出路径
        """
        self.output_path = output_path
        self.logger = logging.getLogger(__name__)

        # 文档元素列表
        self.story = []

        # 页面设置
        self.page_width, self.page_height = A4

        # 注册中文字体（使用系统字体）
        self._register_chinese_fonts()

        # 创建样式
        self.styles = self._create_styles()

    def _register_chinese_fonts(self):
        """注册中文字体"""
        try:
            # Windows系统字体路径
            font_paths = [
                'C:/Windows/Fonts/msyh.ttc',      # 微软雅黑
                'C:/Windows/Fonts/simhei.ttf',    # 黑体
                'C:/Windows/Fonts/simsun.ttc',    # 宋体
            ]

            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                        self.logger.info(f"成功注册中文字体: {font_path}")
                        return
                    except Exception as e:
                        self.logger.warning(f"注册字体失败 {font_path}: {e}")
                        continue

            # 如果所有字体都失败，使用默认字体
            self.logger.warning("未找到中文字体，将使用默认字体（可能无法显示中文）")

        except Exception as e:
            self.logger.error(f"注册中文字体时发生错误: {e}")

    def _create_styles(self):
        """创建文档样式"""
        styles = getSampleStyleSheet()

        # 标题样式
        styles.add(ParagraphStyle(
            name='ChineseTitle',
            parent=styles['Title'],
            fontName='ChineseFont',
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))

        # 副标题样式
        styles.add(ParagraphStyle(
            name='ChineseHeading',
            parent=styles['Heading1'],
            fontName='ChineseFont',
            fontSize=16,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12,
            spaceBefore=12
        ))

        # 正文样式
        styles.add(ParagraphStyle(
            name='ChineseBody',
            parent=styles['BodyText'],
            fontName='ChineseFont',
            fontSize=11,
            leading=16,
            textColor=colors.HexColor('#333333'),
            alignment=TA_JUSTIFY
        ))

        # 小字样式
        styles.add(ParagraphStyle(
            name='ChineseSmall',
            parent=styles['Normal'],
            fontName='ChineseFont',
            fontSize=9,
            textColor=colors.HexColor('#666666')
        ))

        return styles

    def add_header(self, title: str, subtitle: str = ""):
        """
        添加报告头部

        Args:
            title: 主标题
            subtitle: 副标题
        """
        # 主标题
        title_para = Paragraph(title, self.styles['ChineseTitle'])
        self.story.append(title_para)

        # 副标题
        if subtitle:
            subtitle_para = Paragraph(subtitle, self.styles['ChineseSmall'])
            self.story.append(subtitle_para)

        # 生成时间
        timestamp = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        time_para = Paragraph(f"生成时间: {timestamp}", self.styles['ChineseSmall'])
        self.story.append(time_para)

        self.story.append(Spacer(1, 0.5*cm))

    def add_game_info(self, game_state: GameState):
        """
        添加游戏信息

        Args:
            game_state: 游戏状态对象
        """
        # 标题
        heading = Paragraph("游戏信息", self.styles['ChineseHeading'])
        self.story.append(heading)

        # 游戏状态
        status_map = {
            GameStatus.PLAYING: "进行中",
            GameStatus.BLACK_WIN: "黑方获胜",
            GameStatus.WHITE_WIN: "白方获胜",
            GameStatus.DRAW: "平局",
            GameStatus.NOT_STARTED: "未开始"
        }
        status_text = status_map.get(game_state.status, "未知")

        # 游戏时长
        duration = game_state.get_game_duration()
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        duration_text = f"{minutes:02d}:{seconds:02d}"

        # 创建信息表格
        data = [
            ["游戏状态", status_text],
            ["最终比分", f"黑子 {game_state.black_count} - 白子 {game_state.white_count}"],
            ["总手数", f"{game_state.move_count} 手"],
            ["游戏时长", duration_text]
        ]

        table = Table(data, colWidths=[4*cm, 12*cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'ChineseFont'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666666')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#333333')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))

        self.story.append(table)
        self.story.append(Spacer(1, 0.5*cm))

    def add_board_diagram(self, game_state: GameState):
        """
        添加棋盘图示

        Args:
            game_state: 游戏状态对象
        """
        # 标题
        heading = Paragraph("最终棋盘", self.styles['ChineseHeading'])
        self.story.append(heading)

        # 创建棋盘表格数据
        board_data = []

        # 列标题行
        header_row = [''] + [chr(ord('A') + i) for i in range(8)]
        board_data.append(header_row)

        # 棋盘行
        for row in range(8):
            row_data = [str(row + 1)]
            for col in range(8):
                piece = game_state.board[row][col]
                if piece == PieceType.BLACK:
                    row_data.append('●')
                elif piece == PieceType.WHITE:
                    row_data.append('○')
                else:
                    row_data.append('·')
            board_data.append(row_data)

        # 创建表格
        cell_size = 1.5*cm
        table = Table(board_data, colWidths=[cell_size] * 9, rowHeights=[cell_size] * 9)

        # 设置样式
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'ChineseFont'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (1, 1), (-1, -1), 1, colors.HexColor('#333333')),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8e8e8')),
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#e8e8e8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#666666')),
            ('TEXTCOLOR', (0, 1), (0, -1), colors.HexColor('#666666')),
        ]))

        self.story.append(table)
        self.story.append(Spacer(1, 0.5*cm))

    def add_analysis_text(self, analysis: str):
        """
        添加分析文本

        Args:
            analysis: 分析内容
        """
        # 标题
        heading = Paragraph("DeepSeek AI 分析报告", self.styles['ChineseHeading'])
        self.story.append(heading)

        # 分析内容（按段落分割）
        paragraphs = analysis.split('\n\n')
        for para_text in paragraphs:
            if para_text.strip():
                # 替换换行符为<br/>标签
                para_text = para_text.replace('\n', '<br/>')
                para = Paragraph(para_text, self.styles['ChineseBody'])
                self.story.append(para)
                self.story.append(Spacer(1, 0.3*cm))

    def add_pgn_moves(self, moves: List[Move]):
        """
        添加棋谱记录

        Args:
            moves: 走法列表
        """
        if not moves:
            return

        # 标题
        heading = Paragraph("棋谱记录", self.styles['ChineseHeading'])
        self.story.append(heading)

        # 创建棋谱表格
        data = []
        data.append(['手数', '黑方', '白方'])

        for i in range(0, len(moves), 2):
            move_num = i // 2 + 1
            black_move = moves[i].to_notation()
            white_move = moves[i + 1].to_notation() if i + 1 < len(moves) else ''
            data.append([str(move_num), black_move, white_move])

        # 创建表格
        table = Table(data, colWidths=[2*cm, 5*cm, 5*cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'ChineseFont'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))

        self.story.append(table)

    def generate(self) -> bool:
        """
        生成PDF文件

        Returns:
            bool: 是否成功生成
        """
        try:
            # 创建PDF文档
            doc = SimpleDocTemplate(
                self.output_path,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )

            # 构建PDF
            doc.build(self.story)

            self.logger.info(f"PDF报告已生成: {self.output_path}")
            return True

        except Exception as e:
            self.logger.error(f"生成PDF失败: {e}")
            return False
