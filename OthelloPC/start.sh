#!/bin/bash
# STM32 Othello PC Client Startup Script for Linux/macOS
# STM32黑白棋PC上位机启动脚本(Linux/macOS)

echo "===================================="
echo "STM32 黑白棋 PC上位机 v1.0"
echo "STM32 Othello PC Client"
echo "===================================="
echo

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3解释器"
    echo "请确保Python3已正确安装"
    exit 1
fi

# 检查是否存在虚拟环境
if [ -d "venv" ]; then
    echo "检测到虚拟环境，正在激活..."
    source venv/bin/activate
fi

# 安装依赖
echo "正在检查依赖项..."
python3 -c "import tkinter, serial, requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "正在安装依赖项..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "依赖项安装失败，请手动运行: pip3 install -r requirements.txt"
        exit 1
    fi
fi

# 启动应用
echo "正在启动应用..."
echo
python3 run.py

exit_code=$?

# 如果应用异常退出，显示错误信息
if [ $exit_code -ne 0 ]; then
    echo
    echo "应用异常退出，错误代码: $exit_code"
fi

exit $exit_code