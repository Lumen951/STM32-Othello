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

### 2.3 NVIC Interrupt Priority Configuration
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