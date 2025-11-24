@echo off
REM STM32 Othello PC Client Startup Script
REM STM32黑白棋PC上位机启动脚本

title STM32 Othello PC Client

echo ====================================
echo STM32 黑白棋 PC上位机 v1.0
echo STM32 Othello PC Client
echo ====================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python解释器
    echo 请确保Python已正确安装并添加到系统PATH中
    echo.
    pause
    exit /b 1
)

REM 检查是否存在虚拟环境
if exist "venv\Scripts\activate.bat" (
    echo 检测到虚拟环境，正在激活...
    call venv\Scripts\activate.bat
)

REM 安装依赖
echo 正在检查依赖项...
python -c "import tkinter, serial, requests" >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装依赖项...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo 依赖项安装失败，请手动运行: pip install -r requirements.txt
        pause
        exit /b 1
    )
)

REM 启动应用
echo 正在启动应用...
echo.
python run.py

REM 如果应用异常退出，暂停以查看错误信息
if %errorlevel% neq 0 (
    echo.
    echo 应用异常退出，错误代码: %errorlevel%
    pause
)

exit /b %errorlevel%