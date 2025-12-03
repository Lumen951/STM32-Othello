#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dieter Rams Design System for STM32 Othello
迪特拉姆斯设计系统 - 遵循"Less but better"理念

@author: STM32 Othello Project Team
@version: 1.0
@date: 2025-11-22
"""

import tkinter as tk
from tkinter import font

class DieterStyle:
    """迪特拉姆斯设计系统样式定义"""

    # === 核心色彩系统 ===
    COLORS = {
        # 基础色
        'white': '#FFFFFF',
        'black': '#000000',
        'gray_dark': '#333333',
        'gray_mid': '#808080',
        'gray_light': '#F5F5F5',

        # 功能色
        'braun_orange': '#FF6600',  # 博朗橙 - 交互元素
        'data_blue': '#0066CC',     # 数据蓝 - 链接信息
        'success_green': '#008000', # 成功绿 - 正确状态
        'error_red': '#FF0000',     # 错误红 - 错误警告

        # 棋盘专用色
        'board_bg': '#F8F8F8',      # 棋盘背景
        'board_grid': '#E0E0E0',    # 棋盘网格线
        'piece_black': '#FF6600',   # 黑子 (博朗橙色，与下位机一致)
        'piece_white': '#FFFFFF',   # 白子
        'piece_border': '#333333',  # 棋子边框

        # 面板色
        'panel_bg': '#FAFAFA',      # 面板背景
        'panel_border': '#D0D0D0',  # 面板边框
    }

    # === 字体系统 ===
    @staticmethod
    def get_fonts():
        """获取字体配置"""
        return {
            'title': ('Arial', 16, 'bold'),     # 标题字体
            'heading': ('Arial', 14, 'bold'),   # 标题字体
            'body': ('Arial', 12, 'normal'),    # 正文字体
            'data': ('Consolas', 11, 'normal'), # 数据字体 (等宽)
            'small': ('Arial', 10, 'normal'),   # 小字体
            'button': ('Arial', 11, 'normal'),  # 按钮字体
        }

    # === 尺寸系统 ===
    SIZES = {
        # 间距
        'padding_small': 8,
        'padding_medium': 16,
        'padding_large': 24,
        'margin_small': 4,
        'margin_medium': 8,
        'margin_large': 16,

        # 按钮尺寸
        'button_width': 100,
        'button_height': 32,
        'button_small_width': 80,
        'button_small_height': 28,

        # 面板尺寸
        'panel_border_width': 1,
        'panel_relief': 'solid',

        # 棋盘尺寸
        'board_size': 560,
        'cell_size': 70,
        'piece_radius': 25,
    }

    # === 组件样式配置 ===
    @staticmethod
    def get_widget_styles():
        """获取控件样式配置"""
        return {
            # 主窗口
            'main_window': {
                'bg': DieterStyle.COLORS['white'],
                'relief': 'flat',
            },

            # 按钮样式
            'button_primary': {
                'bg': DieterStyle.COLORS['braun_orange'],
                'fg': DieterStyle.COLORS['white'],
                'activebackground': '#E55A00',
                'activeforeground': DieterStyle.COLORS['white'],
                'relief': 'flat',
                'bd': 0,
                'cursor': 'hand2',
            },

            'button_secondary': {
                'bg': DieterStyle.COLORS['gray_light'],
                'fg': DieterStyle.COLORS['black'],
                'activebackground': DieterStyle.COLORS['gray_mid'],
                'activeforeground': DieterStyle.COLORS['white'],
                'relief': 'flat',
                'bd': 1,
                'cursor': 'hand2',
            },

            # 标签样式
            'label_title': {
                'bg': DieterStyle.COLORS['white'],
                'fg': DieterStyle.COLORS['black'],
                'anchor': 'w',
            },

            'label_body': {
                'bg': DieterStyle.COLORS['white'],
                'fg': DieterStyle.COLORS['gray_dark'],
                'anchor': 'w',
            },

            'label_data': {
                'bg': DieterStyle.COLORS['white'],
                'fg': DieterStyle.COLORS['data_blue'],
                'anchor': 'w',
            },

            # 面板样式
            'panel_main': {
                'bg': DieterStyle.COLORS['panel_bg'],
                'relief': 'solid',
                'bd': DieterStyle.SIZES['panel_border_width'],
                'highlightcolor': DieterStyle.COLORS['panel_border'],
            },

            'panel_game': {
                'bg': DieterStyle.COLORS['white'],
                'relief': 'flat',
                'bd': 0,
            },

            # 文本框样式
            'text_readonly': {
                'bg': DieterStyle.COLORS['gray_light'],
                'fg': DieterStyle.COLORS['black'],
                'relief': 'flat',
                'bd': 1,
                'state': 'disabled',
                'wrap': 'word',
            },

            # 列表框样式
            'listbox_main': {
                'bg': DieterStyle.COLORS['white'],
                'fg': DieterStyle.COLORS['black'],
                'selectbackground': DieterStyle.COLORS['braun_orange'],
                'selectforeground': DieterStyle.COLORS['white'],
                'relief': 'flat',
                'bd': 1,
                'activestyle': 'none',
            },
        }

class DieterWidgets:
    """迪特拉姆斯风格控件工厂"""

    @staticmethod
    def create_button(parent, text, command=None, style='primary', width=None, height=None):
        """创建迪特拉姆斯风格按钮"""
        styles = DieterStyle.get_widget_styles()
        fonts = DieterStyle.get_fonts()

        if style == 'primary':
            config = styles['button_primary']
        else:
            config = styles['button_secondary']

        if width is None:
            width = DieterStyle.SIZES['button_width']
        if height is None:
            height = DieterStyle.SIZES['button_height']

        button = tk.Button(
            parent,
            text=text,
            command=command,
            font=fonts['button'],
            width=12,  # 字符宽度
            height=1,
            **config
        )

        return button

    @staticmethod
    def create_label(parent, text, style='body'):
        """创建迪特拉姆斯风格标签"""
        styles = DieterStyle.get_widget_styles()
        fonts = DieterStyle.get_fonts()

        if style == 'title':
            config = styles['label_title']
            font_config = fonts['title']
        elif style == 'heading':
            config = styles['label_title']
            font_config = fonts['heading']
        elif style == 'data':
            config = styles['label_data']
            font_config = fonts['data']
        else:
            config = styles['label_body']
            font_config = fonts['body']

        label = tk.Label(
            parent,
            text=text,
            font=font_config,
            **config
        )

        return label

    @staticmethod
    def create_panel(parent, style='main'):
        """创建迪特拉姆斯风格面板"""
        styles = DieterStyle.get_widget_styles()

        if style == 'main':
            config = styles['panel_main']
        else:
            config = styles['panel_game']

        frame = tk.Frame(parent, **config)
        return frame

    @staticmethod
    def create_text_area(parent, width=50, height=10, readonly=True):
        """创建迪特拉姆斯风格文本区域"""
        styles = DieterStyle.get_widget_styles()
        fonts = DieterStyle.get_fonts()

        text = tk.Text(
            parent,
            width=width,
            height=height,
            font=fonts['data'],
            **styles['text_readonly']
        )

        if readonly:
            text.config(state='disabled')

        return text

    @staticmethod
    def create_listbox(parent, width=30, height=10):
        """创建迪特拉姆斯风格列表框"""
        styles = DieterStyle.get_widget_styles()
        fonts = DieterStyle.get_fonts()

        listbox = tk.Listbox(
            parent,
            width=width,
            height=height,
            font=fonts['data'],
            **styles['listbox_main']
        )

        return listbox

# === 应用程序主题配置 ===
class AppTheme:
    """应用程序主题管理"""

    @staticmethod
    def apply_to_window(window):
        """为窗口应用迪特拉姆斯主题"""
        window.configure(bg=DieterStyle.COLORS['white'])

        # 设置窗口样式
        window.option_add('*TCombobox*Listbox.selectBackground', DieterStyle.COLORS['braun_orange'])

    @staticmethod
    def get_board_colors():
        """获取棋盘专用颜色配置"""
        return {
            'background': DieterStyle.COLORS['board_bg'],
            'grid': DieterStyle.COLORS['board_grid'],
            'black_piece': DieterStyle.COLORS['piece_black'],
            'white_piece': DieterStyle.COLORS['piece_white'],
            'piece_border': DieterStyle.COLORS['piece_border'],
            'hover_highlight': DieterStyle.COLORS['braun_orange'],
            'valid_move': DieterStyle.COLORS['success_green'],
            'invalid_move': DieterStyle.COLORS['error_red'],
        }