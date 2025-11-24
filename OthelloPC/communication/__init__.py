#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Communication Package for STM32 Othello PC Client
通信模块

@author: STM32 Othello Project Team
@version: 1.0
@date: 2025-11-22
"""

from .serial_handler import SerialHandler, SerialProtocol

__all__ = ['SerialHandler', 'SerialProtocol']