/**
 * @file keypad_driver.h
 * @brief 4×4 Matrix Keypad Driver for STM32F103C8T6
 * @version 1.0
 * @date 2025-11-22
 *
 * @note This driver implements row-scanning algorithm for 4×4 matrix keypad
 *       Row pins: PB12-PB15 (KEY_R1-KEY_R4) - GPIO Output
 *       Col pins: PB5-PB8 (KEY_C1-KEY_C4) - GPIO Input with Pull-up
 */

#ifndef __KEYPAD_DRIVER_H
#define __KEYPAD_DRIVER_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "stm32f1xx_hal.h"
#include <stdbool.h>

/* Exported types ------------------------------------------------------------*/

/**
 * @brief Keypad driver status enumeration
 */
typedef enum {
    KEYPAD_OK = 0,
    KEYPAD_ERROR,
    KEYPAD_BUSY,
    KEYPAD_TIMEOUT
} Keypad_Status_t;

/**
 * @brief Key state enumeration
 */
typedef enum {
    KEY_RELEASED = 0,        ///< Key released state
    KEY_PRESSED,            ///< Key pressed state
    KEY_LONG_PRESSED        ///< Key long pressed state (>1000ms)
} KeyState_t;

/**
 * @brief Key structure
 */
typedef struct {
    uint8_t row;                ///< Key row position (0-3)
    uint8_t col;                ///< Key column position (0-3)
    KeyState_t state;           ///< Current key state
    KeyState_t prev_state;      ///< Previous key state
    uint32_t press_timestamp;   ///< Press start timestamp
    uint32_t debounce_timer;    ///< Debounce timer
} Key_t;

/**
 * @brief Keypad event callback function type
 */
typedef void (*Keypad_Callback_t)(uint8_t row, uint8_t col, KeyState_t state);

/* Exported constants --------------------------------------------------------*/

/** @defgroup Keypad_Configuration Keypad Configuration
 * @{
 */
#define KEYPAD_ROWS                 4       ///< Number of keypad rows
#define KEYPAD_COLS                 4       ///< Number of keypad columns
#define KEYPAD_TOTAL_KEYS           16      ///< Total number of keys
#define KEYPAD_DEBOUNCE_TIME_MS     10      ///< Debounce time in milliseconds
#define KEYPAD_LONG_PRESS_TIME_MS   1000    ///< Long press threshold in milliseconds
#define KEYPAD_SCAN_INTERVAL_MS     5       ///< Scan interval in milliseconds (200Hz)
/**
 * @}
 */

/** @defgroup Keypad_Pin_Definitions Pin Definitions
 * @{
 */
// Row pins (Output)
#define KEY_R1_Pin          GPIO_PIN_12
#define KEY_R1_GPIO_Port    GPIOB
#define KEY_R2_Pin          GPIO_PIN_13
#define KEY_R2_GPIO_Port    GPIOB
#define KEY_R3_Pin          GPIO_PIN_14
#define KEY_R3_GPIO_Port    GPIOB
#define KEY_R4_Pin          GPIO_PIN_15
#define KEY_R4_GPIO_Port    GPIOB

// Column pins (Input with pull-up)
#define KEY_C1_Pin          GPIO_PIN_5
#define KEY_C1_GPIO_Port    GPIOB
#define KEY_C2_Pin          GPIO_PIN_6
#define KEY_C2_GPIO_Port    GPIOB
#define KEY_C3_Pin          GPIO_PIN_7
#define KEY_C3_GPIO_Port    GPIOB
#define KEY_C4_Pin          GPIO_PIN_8
#define KEY_C4_GPIO_Port    GPIOB
/**
 * @}
 */

/** @defgroup Keypad_Key_Codes Key Code Definitions
 * @{
 */
#define KEY_CODE_0          0       ///< Key code for button at (0,0)
#define KEY_CODE_1          1       ///< Key code for button at (0,1)
#define KEY_CODE_2          2       ///< Key code for button at (0,2)
#define KEY_CODE_3          3       ///< Key code for button at (0,3)
#define KEY_CODE_4          4       ///< Key code for button at (1,0)
#define KEY_CODE_5          5       ///< Key code for button at (1,1)
#define KEY_CODE_6          6       ///< Key code for button at (1,2)
#define KEY_CODE_7          7       ///< Key code for button at (1,3)
#define KEY_CODE_8          8       ///< Key code for button at (2,0)
#define KEY_CODE_9          9       ///< Key code for button at (2,1)
#define KEY_CODE_A          10      ///< Key code for button at (2,2)
#define KEY_CODE_B          11      ///< Key code for button at (2,3)
#define KEY_CODE_C          12      ///< Key code for button at (3,0)
#define KEY_CODE_D          13      ///< Key code for button at (3,1)
#define KEY_CODE_E          14      ///< Key code for button at (3,2)
#define KEY_CODE_F          15      ///< Key code for button at (3,3)
#define KEY_CODE_NONE       0xFF    ///< No key pressed
/**
 * @}
 */

/* Exported macro ------------------------------------------------------------*/

/**
 * @brief Convert row,col coordinates to key code
 * @param row Row index (0-3)
 * @param col Column index (0-3)
 * @retval Key code (0-15)
 */
#define KEYPAD_GET_CODE(row, col)   ((row) * KEYPAD_COLS + (col))

/**
 * @brief Extract row from key code
 * @param code Key code (0-15)
 * @retval Row index (0-3)
 */
#define KEYPAD_GET_ROW(code)        ((code) / KEYPAD_COLS)

/**
 * @brief Extract column from key code
 * @param code Key code (0-15)
 * @retval Column index (0-3)
 */
#define KEYPAD_GET_COL(code)        ((code) % KEYPAD_COLS)

/**
 * @brief Check if coordinates are valid
 * @param row Row index
 * @param col Column index
 * @retval 1 if valid, 0 if invalid
 */
#define KEYPAD_IS_VALID_COORD(row, col) \
    ((row) < KEYPAD_ROWS && (col) < KEYPAD_COLS)

/**
 * @brief Check if key code is valid
 * @param code Key code
 * @retval 1 if valid, 0 if invalid
 */
#define KEYPAD_IS_VALID_CODE(code) \
    ((code) < KEYPAD_TOTAL_KEYS)

/* Exported functions prototypes ---------------------------------------------*/

/**
 * @brief Initialize keypad driver
 * @retval Keypad_Status_t Status of initialization
 * @note Must be called after HAL_Init() and GPIO configuration
 */
Keypad_Status_t Keypad_Init(void);

/**
 * @brief DeInitialize keypad driver
 * @retval Keypad_Status_t Status of deinitialization
 */
Keypad_Status_t Keypad_DeInit(void);

/**
 * @brief Perform one keypad scan cycle
 * @retval None
 * @note Should be called periodically (every 5ms recommended)
 */
void Keypad_Scan(void);

/**
 * @brief Get next key event from queue
 * @retval Key_t Key event structure, check state for validity
 * @note Returns key with state KEY_RELEASED if no events in queue
 */
Key_t Keypad_GetKey(void);

/**
 * @brief Check if specific key is currently pressed
 * @param row Row index (0-3)
 * @param col Column index (0-3)
 * @retval true if key is pressed, false otherwise
 */
bool Keypad_IsKeyPressed(uint8_t row, uint8_t col);

/**
 * @brief Get current state of specific key
 * @param row Row index (0-3)
 * @param col Column index (0-3)
 * @retval KeyState_t Current key state
 */
KeyState_t Keypad_GetKeyState(uint8_t row, uint8_t col);

/**
 * @brief Get press duration of specific key
 * @param row Row index (0-3)
 * @param col Column index (0-3)
 * @retval uint32_t Press duration in milliseconds, 0 if not pressed
 */
uint32_t Keypad_GetPressDuration(uint8_t row, uint8_t col);

/**
 * @brief Get all currently pressed keys as bitmask
 * @retval uint16_t Bitmask where bit N represents key N (0-15)
 */
uint16_t Keypad_GetPressedKeys(void);

/**
 * @brief Register callback function for key events
 * @param callback Function pointer to callback function
 * @retval Keypad_Status_t Status of registration
 * @note Callback is called whenever key state changes
 */
Keypad_Status_t Keypad_Register_Callback(Keypad_Callback_t callback);

/**
 * @brief Quick check if any key is pressed
 * @retval true if any key is pressed, false if no keys pressed
 * @note Fast detection method, useful for optimization
 */
bool Keypad_Quick_Check(void);

/**
 * @brief Set debounce time
 * @param debounce_ms Debounce time in milliseconds
 * @retval Keypad_Status_t Status of operation
 */
Keypad_Status_t Keypad_SetDebounceTime(uint32_t debounce_ms);

/**
 * @brief Set long press threshold time
 * @param longpress_ms Long press threshold in milliseconds
 * @retval Keypad_Status_t Status of operation
 */
Keypad_Status_t Keypad_SetLongPressTime(uint32_t longpress_ms);

/**
 * @brief Get keypad statistics
 * @param total_scans Total number of scans performed
 * @param total_events Total number of key events generated
 * @retval Keypad_Status_t Status of operation
 */
Keypad_Status_t Keypad_GetStatistics(uint32_t *total_scans, uint32_t *total_events);

/**
 * @brief Reset keypad statistics
 * @retval Keypad_Status_t Status of operation
 */
Keypad_Status_t Keypad_ResetStatistics(void);

/**
 * @brief Keypad scan task - call this from SysTick or timer interrupt
 * @retval None
 * @note This is the main scanning function for interrupt-driven operation
 */
void Keypad_Scan_Task(void);

/**
 * @brief Keypad key event handler (application callback)
 * @param row Key row position (0-3)
 * @param col Key column position (0-3)
 * @param state Key state
 * @retval None
 * @note This function is implemented in main.c and called by keypad driver
 */
void Keypad_Key_Event_Handler(uint8_t row, uint8_t col, KeyState_t state);

/**
 * @brief Application key event processor
 * @param key_event Pointer to key event structure
 * @retval None
 * @note This function is implemented in main.c for processing key events
 */
void App_ProcessKeyEvent(Key_t* key_event);

#ifdef __cplusplus
}
#endif

#endif /* __KEYPAD_DRIVER_H */