# STM32 Othello PC Client

基于Dieter Rams设计理念的STM32黑白棋PC上位机客户端。

## 功能特性

- **简洁优雅的界面设计**: 遵循Dieter Rams "Less but better" 设计理念
- **STM32硬件交互**: 通过串口与STM32F103C8T6开发板实时通信
- **智能AI分析**: 集成DeepSeek AI进行游戏分析和复盘指导
- **完整游戏记录**: PGN格式棋谱保存和回放功能
- **实时游戏状态**: 棋盘状态同步和历史记录管理

## 系统要求

- Python 3.7+
- Windows 10/11 或 Linux/macOS
- 至少512MB可用内存
- USB串口（用于STM32连接）

## 快速开始

### 1. 安装依赖

```bash
# 克隆项目（如果从仓库获取）
git clone <repository-url>
cd STM32_Othello/OthelloPC

# 安装Python依赖
pip install -r requirements.txt
```

### 2. 配置DeepSeek API（可选）

1. 访问 [DeepSeek官网](https://platform.deepseek.com/) 获取API密钥
2. 在应用中通过 "分析" -> "DeepSeek设置" 配置API密钥

### 3. 启动应用

#### Windows:
```bash
# 方法1: 使用批处理脚本
start.bat

# 方法2: 直接运行Python
python run.py
```

#### Linux/macOS:
```bash
# 方法1: 使用Shell脚本
chmod +x start.sh
./start.sh

# 方法2: 直接运行Python
python3 run.py
```

## 项目结构

```
OthelloPC/
├── main.py                 # 应用程序主入口
├── run.py                  # 启动脚本
├── requirements.txt        # 依赖包列表
├── start.bat              # Windows启动脚本
├── start.sh               # Linux/macOS启动脚本
│
├── gui/                   # 用户界面模块
│   ├── __init__.py
│   ├── main_window.py     # 主窗口
│   ├── game_board.py      # 游戏棋盘组件
│   ├── history_panel.py   # 历史记录面板
│   ├── analysis_window.py # 分析报告窗口
│   └── styles.py          # Dieter Rams设计系统
│
├── game/                  # 游戏逻辑模块
│   ├── __init__.py
│   └── game_state.py      # 游戏状态管理
│
├── communication/         # 通信模块
│   ├── __init__.py
│   └── serial_handler.py  # STM32串口通信
│
├── analysis/              # AI分析模块
│   ├── __init__.py
│   └── deepseek_client.py # DeepSeek API客户端
│
└── utils/                 # 工具模块
    ├── __init__.py
    ├── logger.py          # 日志管理
    └── config.py          # 配置管理
```

## 使用说明

### 基本操作

1. **新游戏**: 点击"新游戏"按钮开始新的黑白棋游戏
2. **连接STM32**: 点击"连接STM32"按钮连接硬件设备
3. **下棋**: 在棋盘上点击有效位置进行落子
4. **查看历史**: 右侧面板显示游戏历史和统计信息

### 高级功能

1. **DeepSeek分析**: 游戏结束后可使用AI分析功能
   - 提供开局、中局、残局的详细分析
   - 指出关键走法和改进建议
   - 生成专业的复盘报告

2. **棋谱管理**:
   - 自动记录游戏过程
   - 支持PGN格式导出
   - 可保存和加载游戏状态

3. **设置选项**:
   - DeepSeek API配置
   - 串口连接设置
   - 界面显示选项

## STM32硬件连接

确保STM32设备按照以下配置连接：

- **串口通信**: USART1 (PA9-TX, PA10-RX), 115200波特率
- **LED矩阵**: WS2812B连接到PA0 (TIM2_CH1)
- **按键矩阵**: 4×4按键连接到PB5-PB8(列), PB12-PB15(行)

详细硬件配置请参考STM32固件部分的文档。

## 配置文件

应用会自动创建 `config.json` 配置文件，包含：

```json
{
  "serial": {
    "baud_rate": 115200,
    "auto_connect": true
  },
  "deepseek": {
    "api_key": "",
    "base_url": "https://api.deepseek.com"
  },
  "ui": {
    "language": "zh",
    "theme": "dieter_rams"
  },
  "game": {
    "show_valid_moves": true,
    "auto_analysis": false
  }
}
```

## 故障排除

### 常见问题

1. **无法连接STM32**
   - 检查USB线缆连接
   - 确认STM32固件已正确刷入
   - 检查串口驱动是否安装

2. **DeepSeek分析失败**
   - 验证API密钥是否正确
   - 检查网络连接
   - 确认API余额充足

3. **界面显示异常**
   - 确认Python tkinter模块正常
   - 检查屏幕分辨率和DPI设置
   - 尝试重新启动应用

### 日志文件

应用会在 `logs/` 目录下生成日志文件：
- `STM32_Othello_YYYYMMDD.log`: 详细运行日志
- `STM32_Othello_error_YYYYMMDD.log`: 错误日志

## 开发信息

- **开发团队**: STM32 Othello Project Team
- **设计理念**: Dieter Rams "Less but better"
- **技术栈**: Python, tkinter, DeepSeek API
- **硬件平台**: STM32F103C8T6

## 版本历史

- **v1.0** (2025-11-22): 初始版本发布
  - 完整的游戏功能
  - STM32硬件支持
  - DeepSeek AI集成
  - Dieter Rams设计系统

## 许可证

本项目为教育和研究目的开发，请遵循相关开源协议。

---

© 2025 STM32 Othello Project Team