# STM32 Othello - Debug日志系统

## 版本：v1.0 (Production Release)
## 更新日期：2025-12-03

---

## 一、日志系统概述

本项目使用 `debug_print.h` 模块通过UART1串口输出调试日志。

### 1.1 串口配置

- **波特率**：115200
- **数据位**：8
- **停止位**：1
- **校验**：无
- **接口**：PA9(TX), PA10(RX)

### 1.2 日志级别

本项目使用以下日志宏：

```c
DEBUG_PRINT_BANNER()    // 启动横幅
DEBUG_INFO(fmt, ...)    // 一般信息
DEBUG_ERROR(fmt, ...)   // 错误信息
```

---

## 二、启动日志（正常流程）

系统启动后会输出完整的初始化序列：

```
========================================
  STM32 Othello Game System
  Version: 0.2.0
  Date: 2025-12-03
========================================

[INIT] HAL Initialized
[INIT] System Clock Configured
[INIT] GPIO Initialized
[INIT] DMA Initialized
[INIT] TIM2 Initialized
[INIT] USART1 Initialized
[INIT] WS2812B Driver...OK
[INIT] Keypad Driver...OK
[INIT] Keypad Quick Check: No keys
[INIT] UART Protocol...SKIPPED (Debug mode)
[INIT] Othello Engine...OK
[INIT] Application...OK
[BOOT] System Ready!
```

**说明**：
- `UART Protocol...SKIPPED` 是正常的，因为当前版本优先使用Debug串口
- 完整初始化约需200-300ms

---

## 三、运行时日志

### 3.1 按键事件日志

每次按键状态改变时会输出：

```
[APP] KeyEvent: R1 C1 State=1 Logical=5
[APP] ProcessKey: R1 C1 Logical=5 State=1
[APP] Place piece at cursor (3,4)
[APP] Move SUCCESS: flipped 2 pieces
```

**日志解析**：
- `R1 C1`：物理按键行列（0-3）
- `State=1`：状态（0=释放, 1=按下, 2=长按）
- `Logical=5`：逻辑按键编号（参见按键映射表）

### 3.2 光标移动日志

```
[APP] Cursor UP: (2,3)
[APP] Cursor LEFT: (2,2)
[APP] Cursor RIGHT: (2,3)
[APP] Cursor DOWN: (3,3)
```

### 3.3 无效操作日志

```
[APP] Cursor at top edge
[APP] Cursor at left edge
[APP] Invalid move at (3,4)
```

### 3.4 新游戏/重置日志

```
[APP] New Game
```

### 3.5 游戏结束日志

游戏结束时会输出完整的游戏历史：

```
========== Game History ==========
Total moves: 28
Black count: 35, White count: 29
Game status: 1

Last move:
  Player: 1, Position: (5,3), Flipped: 4

Game Result:
  Winner: BLACK (Orange)
==================================
```

---

## 四、按键映射参考

用于解析日志中的 `Logical=X` 字段：

| Logical Key | 物理位置 | 功能 |
|:----------:|:------:|:-----|
| 1  | (0,0) | 新游戏 |
| 2  | (0,1) | 向上 |
| 3  | (0,2) | (预留) |
| 10 | (0,3) | A (预留) |
| 4  | (1,0) | 向左 |
| 5  | (1,1) | 落子 |
| 6  | (1,2) | 向右 |
| 11 | (1,3) | B (预留) |
| 7  | (2,0) | (预留) |
| 8  | (2,1) | 向下 |
| 9  | (2,2) | 发送状态 |
| 12 | (2,3) | C (预留) |
| 14 | (3,0) | * (预留) |
| 0  | (3,1) | 重置 |
| 15 | (3,2) | # (预留) |
| 13 | (3,3) | D (预留) |

---

## 五、错误日志

### 5.1 初始化失败

如果某个模块初始化失败，会输出：

```
[INIT] WS2812B Driver...FAILED
[INIT] Keypad Driver...FAILED (status=1)
[INIT] Othello Engine...FAILED
```

系统会进入 `Error_Handler()` 并停止运行。

### 5.2 常见错误原因

| 错误 | 可能原因 | 解决方案 |
|:---|:---|:---|
| WS2812B...FAILED | LED数据线未连接到PA0 | 检查硬件连接 |
| Keypad...FAILED | 按键矩阵GPIO未配置 | 检查CubeMX配置 |
| Othello Engine...FAILED | 内存不足 | 检查堆栈设置 |

---

## 六、日志抓取与分析

### 6.1 推荐工具

**Windows**:
- PuTTY
- TeraTerm
- Realterm

**Linux/Mac**:
- screen
- minicom
- picocom

### 6.2 PuTTY配置示例

```
Connection type: Serial
Serial line: COM3 (根据实际端口)
Speed: 115200
Data bits: 8
Stop bits: 1
Parity: None
Flow control: None
```

### 6.3 抓取日志到文件

**PuTTY**:
1. Session → Logging
2. Session logging: All session output
3. Log file name: `othello_log.txt`

**Linux screen**:
```bash
screen -L -Logfile othello_log.txt /dev/ttyUSB0 115200
```

---

## 七、性能监控

### 7.1 关键性能指标

虽然当前版本已移除实时性能日志，但可以通过以下方式监控：

**按键响应延迟**：
- 从按下到 `[APP] ProcessKey` 应在 10-20ms 内
- 如果超过50ms，检查扫描频率配置

**LED更新延迟**：
- 从 `[APP] Move SUCCESS` 到LED实际更新应在5ms内
- 如果有明显延迟，检查DMA配置

**游戏逻辑延迟**：
- 从落子到翻转完成应在1ms内
- 如果卡顿，检查算法效率

---

## 八、调试技巧

### 8.1 快速诊断流程

1. **系统不启动**
   - 检查串口输出是否有启动横幅
   - 检查 `[INIT]` 序列在哪里停止

2. **按键无响应**
   - 观察是否有 `[APP] KeyEvent` 日志
   - 如果没有，检查硬件连接
   - 如果有但无 `ProcessKey`，检查按键映射

3. **LED显示错误**
   - 观察初始棋盘是否显示
   - 检查 `[APP] Move SUCCESS` 后LED是否更新
   - 确认LED物理连接正确

4. **游戏逻辑错误**
   - 观察 `Game History` 输出
   - 检查 `flipped` 数量是否合理
   - 确认 `current_player` 切换正确

### 8.2 日志过滤技巧

**只看错误**：
```bash
grep "\[ERROR\]" othello_log.txt
```

**只看按键事件**：
```bash
grep "\[APP\] ProcessKey" othello_log.txt
```

**只看游戏逻辑**：
```bash
grep "Move SUCCESS\|Game History" othello_log.txt
```

---

## 九、历史问题记录

### 问题1：按键无响应（已修复 v0.2.0）

**症状**：硬件测试检测到按键，但驱动层无事件生成
**原因**：`Keypad_ProcessDebounce()` 去抖逻辑有bug，stable_count永远无法累加
**解决**：简化为10ms timer去抖，移除stable_count机制

### 问题2：LED坐标映射错误（已修复 v0.2.0）

**症状**：光标移动时出现对角线偏移，四角显示位置错误
**原因**：误判LED矩阵为Z字形布线，实际为标准线性布线
**解决**：确认为简单线性映射 `(row * 8 + col)`，移除serpentine逻辑

---

## 十、版本历史

### v1.0 (2025-12-03) - Production Release
**清理内容**：
- ❌ 删除 HEARTBEAT 心跳日志
- ❌ 删除按键状态轮询日志
- ❌ 删除硬件诊断测试日志
- ❌ 删除LED映射测试日志
- ❌ 删除详细的debounce调试日志
- ❌ 删除LED测试函数调用

**保留内容**：
- ✅ 系统初始化日志
- ✅ 按键事件日志
- ✅ 游戏逻辑日志
- ✅ 错误日志
- ✅ 游戏历史统计

**功能验证**：
- ✅ 光标移动完全正确
- ✅ 落子功能完全正常
- ✅ LED坐标映射正确
- ✅ 按键响应及时

### v0.2.0 (2025-12-03) - Debug Version
- 修复按键去抖bug
- 修复LED坐标映射
- 包含完整的诊断功能
- 硬件测试函数
- 详细的调试日志

### v0.1.0 (2025-11-28) - Initial Version
- 基础日志系统
- 初始化序列日志

---

## 十一、常见问题

### Q1: 为什么没有心跳日志了？
A: Production版本移除了HEARTBEAT日志以减少串口干扰。如需监控系统运行，可观察按键事件日志。

### Q2: 如何查看实时按键状态？
A: 当前版本只在按键状态改变时输出日志。如需轮询，可临时启用DEBUG模式。

### Q3: 日志输出会影响性能吗？
A: 正常游戏过程中日志量很小（每次按键约2-3条），对性能影响可忽略。游戏结束时的历史输出约50行，耗时约10ms。

### Q4: 如何临时禁用日志？
A: 在 `debug_print.h` 中注释掉 `#define DEBUG_ENABLE`。

---

**文档版本**：1.0
**最后更新**：2025-12-03
**状态**：Production Release
**维护者**：Claude Code
**反馈**：项目GitHub仓库
