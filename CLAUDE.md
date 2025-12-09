# Project: STM32 Reversi with Dual-Mode AI & DeepSeek Analytics
# Version: 1.0
# Target MCU: STM32F103C8T6
# IDE: STM32CubeIDE (HAL Library)

## 1. WORKFLOW PROTOCOL (MANDATORY)
You MUST strictly follow this 7-step loop for every interaction. Do not skip steps.

**[Step 1] Progress Check**
- Read the `## 5. Development Roadmap` section.
- Identify the current status and the next immediate unchecked item.

**[Step 2] Context Retrieval**
- Search this document (`Claude.md`) for specific technical constraints related to the current task (e.g., Pinouts, DMA settings, Protocol format).

**[Step 3] Plan & Confirm**
- Propose a detailed execution plan for the current step.
- List the files to be created or modified.
- **STOP and WAIT** for the user to reply "Confirmed" or "Proceed".

**[Step 4] Execution**
- Upon user confirmation, generate the code.
- Ensure all code strictly follows the HAL Library standards and Hardware Specifications defined below.

**[Step 5] Verification Instructions**
- Tell the user exactly how to test the new code (e.g., "Check if LED at (0,0) turns Red", "Measure voltage at PB12").

**[Step 6] Update Roadmap**
- Ask the user if the test passed.
- If passed, mark the item in `## 5. Development Roadmap` as [x].

**[Step 7] Loop**
- Return to Step 1 for the next task.

---

## 2. HARDWARE SPECIFICATIONS (STRICT)

### 2.1 Pinout & User Labels
You must use these exact Labels in the code (defined in `main.h`).

| Feature | Pin | User Label | Configuration / Mode |
| :--- | :--- | :--- | :--- |
| **LED Matrix** | PA0 | `LED_DATA` | TIM2_CH1 (PWM Generation) |
| **UART (PC)** | PA9 | `PC_TX` | USART1_TX |
| **UART (PC)** | PA10| `PC_RX` | USART1_RX |
| **Keypad R1** | PB12| `KEY_R1` | GPIO_Output (High) |
| **Keypad R2** | PB13| `KEY_R2` | GPIO_Output (High) |
| **Keypad R3** | PB14| `KEY_R3` | GPIO_Output (High) |
| **Keypad R4** | PB15| `KEY_R4` | GPIO_Output (High) |
| **Keypad C1** | PB5 | `KEY_C1` | GPIO_Input (Pull-up) |
| **Keypad C2** | PB6 | `KEY_C2` | GPIO_Input (Pull-up) |
| **Keypad C3** | PB7 | `KEY_C3` | GPIO_Input (Pull-up) |
| **Keypad C4** | PB8 | `KEY_C4` | GPIO_Input (Pull-up) |

### 2.2 Critical Driver Settings
* **WS2812B Timer (TIM2):**
    * Prescaler: `0`, Period: `89` (800kHz).
    * **DMA Mode:**
        * Direction: Memory To Peripheral.
        * **Peripheral Data Width:** Half Word (16-bit).
        * **Memory Data Width:** Half Word (16-bit) (**As requested by user**).
        * Note: The DMA buffer in C code must be `uint16_t pwm_buffer[]`.
* **UART:**
    * Baud Rate: **115200**.
    * Interrupt: Enabled (NVIC) for RX.

### 2.3 Communication Strategy (Updated 2025-12-03)

**IMPORTANT CHANGE**: To avoid resource conflict between Debug output and Protocol communication, Debug has been **disabled**.

#### Single UART Mode (Current Configuration)
* **USART1 (PA9/PA10)**:
    * **Purpose**: PC Communication Protocol (**Exclusive**)
    * **Baud Rate**: 115200
    * **Mode**: Full-duplex, 8N1
    * **Interrupt**: Enabled (NVIC Priority: 1)
    * **Connection**: USB-TTL Module → PC (Default: **COM7**)

#### Debug Output Status
* **Debug Print**: **DISABLED** (`ENABLE_DEBUG = 0` in `debug_print.h`)
* **Rationale**: USART1 resource is exclusively allocated to Protocol communication
* **Alternative**: Use Protocol's `CMD_DEBUG_INFO (0x09)` to send debug messages to PC
* **Re-enable Debug**: Set `ENABLE_DEBUG 1` and disable `Protocol_Init()` (for debugging only)

#### Protocol Communication Details
* **Packet Format**: `STX(0x02) + CMD + LEN + DATA + CHECKSUM + ETX(0x03)`
* **Checksum Algorithm**: XOR of (CMD ^ LEN ^ DATA[0] ^ DATA[1] ^ ...)
* **Timeout**: 1000ms per packet reception
* **Heartbeat**: Bi-directional, every 5 seconds
* **Commands Supported**:
    * `CMD_BOARD_STATE (0x01)`: Game board synchronization
    * `CMD_MAKE_MOVE (0x02)`: Move command from PC
    * `CMD_GAME_CONFIG (0x03)`: New game / reset command
    * `CMD_SYSTEM_INFO (0x05)`: System information query
    * `CMD_HEARTBEAT (0x07)`: Connection heartbeat
    * `CMD_ACK (0x08)`: Command acknowledgment
    * `CMD_DEBUG_INFO (0x09)`: Debug message
    * `CMD_KEY_EVENT (0x0A)`: Keypad event notification
    * `CMD_LED_CONTROL (0x0B)`: LED control command
    * `CMD_ERROR (0xFF)`: Error response

#### Connection Verification Flow
```
PC → STM32: CMD_SYSTEM_INFO (0x05)
         ↓
STM32 → PC: System Info Response (firmware version, uptime, memory, CPU usage)
         ↓
PC: Mark as "Connected" (timeout: 3 seconds)
```

#### Hardware Connection Diagram
```
USB-TTL Module (CH340/CP2102/FT232)     STM32F103C8T6
┌─────────────┐                         ┌─────────────┐
│             │                         │             │
│  TXD  ──────┼─────────────────────────┤ PA10 (RX)   │
│  RXD  ──────┼─────────────────────────┤ PA9  (TX)   │
│  GND  ──────┼─────────────────────────┤ GND         │
│  VCC        │                         │ (not conn.) │
└─────────────┘                         └─────────────┘
   (3.3V)                                (powered by ST-Link)

IMPORTANT: TX-RX are cross-connected (TXD→RX, RXD→TX)
```

#### PC Upper Computer Configuration
* **Default Serial Port**: COM7 (configurable in `config.json`)
* **Configuration File**: `OthelloPC/config.json`
    ```json
    {
      "serial": {
        "baud_rate": 115200,
        "timeout": 1.0,
        "auto_connect": false,
        "preferred_port": "COM7"
      }
    }
    ```
* **Connection Verification**: PC sends `CMD_SYSTEM_INFO` on connect and waits 3s for response

#### Code Usage Examples

**STM32 Side (C)**:
```c
/* main.c initialization */
// Protocol_Init() is now ENABLED (Debug is disabled)
if (Protocol_Init() != PROTOCOL_OK) {
    Error_Handler();
}
Protocol_RegisterCallback(Protocol_Command_Handler);

/* Main loop */
while(1) {
    Protocol_Task();  // Handle timeouts & send heartbeat
    Keypad_Scan_Task();
    App_Main_Loop();
    HAL_Delay(1);
}

/* Send game state to PC */
Game_State_Data_t state = { /* ... */ };
Protocol_SendGameState(&state);

/* Send debug info (replaces DEBUG_INFO macro) */
Protocol_SendDebugMessage("Move executed successfully");

/* Handle received commands */
void Protocol_Command_Handler(Protocol_Command_t cmd, uint8_t* data, uint8_t len) {
    switch(cmd) {
        case CMD_GAME_CONFIG:  // New game from PC
            Othello_Reset();
            App_DisplayGameBoard();
            Protocol_SendAck(cmd, 0);
            Send_GameState_Via_Protocol(&game_state);
            break;
        // ... other commands
    }
}
```

**PC Side (Python)**:
```python
# Connect to STM32
serial_handler.connect(port='COM7')  # Uses config.serial_port

# Send new game command
serial_handler.send_new_game()

# Handle responses in callback
def on_serial_data_received(command, data):
    if command == SerialProtocol.CMD_ACK:
        original_cmd, status = data[0], data[1]
        if status == 0:
            print(f"Command 0x{original_cmd:02X} succeeded")
    elif command == SerialProtocol.CMD_SYSTEM_INFO:
        # Connection verified
        connection_verified = True
```

### 2.4 NVIC Interrupt Priority Configuration
**CRITICAL: These interrupt priorities MUST be used exactly as specified.**

| Interrupt Source | NVIC Priority | Notes |
| :--- | :---: | :--- |
| **USART1 global interrupt** | `1` | High priority for real-time communication |
| **TIM2 global interrupt** | `2` | Medium priority for WS2812B timing |
| **DMA1 channel1 global interrupt** | `2` | Medium priority for LED data transfer |

**Important Notes:**
- Lower number = Higher priority (0 is highest, 15 is lowest)
- USART1 has highest priority for responsive PC communication
- TIM2 and DMA1 CH1 share same priority level for LED operations
- All other interrupts should use priority 3 or lower