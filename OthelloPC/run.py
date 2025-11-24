#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STM32 Othello PC Application Runner Script
STM32黑白棋PC应用启动脚本

@author: STM32 Othello Project Team
@version: 1.0
@date: 2025-11-22
"""

import sys
import os

# 添加项目根目录到Python路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

def check_dependencies():
    """检查依赖项"""
    required_modules = [
        'tkinter',
        'serial',
        'requests'
    ]

    missing_modules = []

    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)

    if missing_modules:
        print("错误: 缺少必需的模块:")
        for module in missing_modules:
            print(f"  - {module}")
        print("\n请使用以下命令安装:")
        print(f"pip install {' '.join(missing_modules)}")
        return False

    return True

def main():
    """主启动函数"""
    print("=" * 60)
    print("STM32 黑白棋 PC上位机 v1.0")
    print("STM32 Othello PC Client")
    print("=" * 60)

    # 检查依赖项
    if not check_dependencies():
        input("按任意键退出...")
        return 1

    try:
        # 导入主程序
        from main import main as app_main

        # 运行应用
        return app_main()

    except KeyboardInterrupt:
        print("\n应用已被用户中断")
        return 0
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("按任意键退出...")
        return 1

if __name__ == "__main__":
    sys.exit(main())