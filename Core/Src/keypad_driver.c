/**
 * @file keypad_driver.c
 * @brief 4×4 Matrix Keypad Driver Implementation
 * @version 1.0
 * @date 2025-11-22
 *
 * @details
 * This driver implements row-scanning algorithm with debouncing:
 * - Row pins: PB12-PB15 (Output, active low scanning)
 * - Column pins: PB5-PB8 (Input with pull-up)
 * - Debounce time: 20ms
 * - Long press threshold: 1000ms
 * - Scan frequency: 200Hz (5ms interval)
 */

/* Includes ------------------------------------------------------------------*/
#include "keypad_driver.h"
#include "keypad_mapping.h"
#include <string.h>

/* Private typedef -----------------------------------------------------------*/

/**
 * @brief Keypad driver internal state
 */
typedef struct {
    Key_t keys[KEYPAD_ROWS][KEYPAD_COLS];   ///< Key state matrix
    Key_t event_queue[16];                  ///< Event queue (circular buffer)
    uint8_t queue_head;                     ///< Queue head index
    uint8_t queue_tail;                     ///< Queue tail index
    uint8_t queue_count;                    ///< Number of events in queue
    Keypad_Callback_t callback;             ///< User callback function
    uint32_t debounce_time_ms;              ///< Configurable debounce time
    uint32_t longpress_time_ms;             ///< Configurable long press time
    uint32_t last_scan_time;                ///< Last scan timestamp
    uint32_t total_scans;                   ///< Total scan count (statistics)
    uint32_t total_events;                  ///< Total event count (statistics)
    bool initialized;                       ///< Initialization flag
} Keypad_Driver_t;

/* Private define ------------------------------------------------------------*/
#define KEYPAD_EVENT_QUEUE_SIZE     16      ///< Maximum events in queue
#define KEYPAD_ROW_SETUP_DELAY_US   2       ///< Row setup delay in microseconds

/* Private variables ---------------------------------------------------------*/
static Keypad_Driver_t keypad_driver = {0};

/* Private function prototypes -----------------------------------------------*/
static void Keypad_SetRowState(uint8_t row, GPIO_PinState state);
static GPIO_PinState Keypad_ReadColumn(uint8_t col);
static bool Keypad_ProcessDebounce(Key_t* key, bool current_pressed);
static void Keypad_AddEvent(Key_t* key);
static void Keypad_ResetKey(Key_t* key, uint8_t row, uint8_t col);
static void Keypad_DelayUs(uint32_t microseconds);

/* Row pin configuration arrays */
static const uint16_t row_pins[] = {KEY_R1_Pin, KEY_R2_Pin, KEY_R3_Pin, KEY_R4_Pin};
static GPIO_TypeDef* row_ports[] = {KEY_R1_GPIO_Port, KEY_R2_GPIO_Port, KEY_R3_GPIO_Port, KEY_R4_GPIO_Port};

/* Column pin configuration arrays */
static const uint16_t col_pins[] = {KEY_C1_Pin, KEY_C2_Pin, KEY_C3_Pin, KEY_C4_Pin};
static GPIO_TypeDef* col_ports[] = {KEY_C1_GPIO_Port, KEY_C2_GPIO_Port, KEY_C3_GPIO_Port, KEY_C4_GPIO_Port};

/* Exported functions --------------------------------------------------------*/

/**
 * @brief Initialize keypad driver
 */
Keypad_Status_t Keypad_Init(void)
{
    // Check if already initialized
    if (keypad_driver.initialized) {
        return KEYPAD_OK;
    }

    // Initialize driver state
    memset(&keypad_driver, 0, sizeof(Keypad_Driver_t));

    // Set default configuration
    keypad_driver.debounce_time_ms = KEYPAD_DEBOUNCE_TIME_MS;
    keypad_driver.longpress_time_ms = KEYPAD_LONG_PRESS_TIME_MS;

    // Initialize all keys
    for (uint8_t row = 0; row < KEYPAD_ROWS; row++) {
        for (uint8_t col = 0; col < KEYPAD_COLS; col++) {
            Keypad_ResetKey(&keypad_driver.keys[row][col], row, col);
        }
    }

    // Set all rows to high (inactive state)
    for (uint8_t row = 0; row < KEYPAD_ROWS; row++) {
        Keypad_SetRowState(row, GPIO_PIN_SET);
    }

    keypad_driver.last_scan_time = HAL_GetTick();
    keypad_driver.initialized = true;

    return KEYPAD_OK;
}

/**
 * @brief DeInitialize keypad driver
 */
Keypad_Status_t Keypad_DeInit(void)
{
    if (!keypad_driver.initialized) {
        return KEYPAD_ERROR;
    }

    // Set all rows to high
    for (uint8_t row = 0; row < KEYPAD_ROWS; row++) {
        Keypad_SetRowState(row, GPIO_PIN_SET);
    }

    // Clear driver state
    memset(&keypad_driver, 0, sizeof(Keypad_Driver_t));

    return KEYPAD_OK;
}

/**
 * @brief Perform one keypad scan cycle
 */
void Keypad_Scan(void)
{
    if (!keypad_driver.initialized) {
        return;
    }

    uint32_t current_time = HAL_GetTick();
    keypad_driver.total_scans++;

    // Scan each row
    for (uint8_t row = 0; row < KEYPAD_ROWS; row++) {
        // Set current row low, others high
        for (uint8_t r = 0; r < KEYPAD_ROWS; r++) {
            Keypad_SetRowState(r, (r == row) ? GPIO_PIN_RESET : GPIO_PIN_SET);
        }

        // Allow settling time
        Keypad_DelayUs(KEYPAD_ROW_SETUP_DELAY_US);

        // Read all columns for this row
        for (uint8_t col = 0; col < KEYPAD_COLS; col++) {
            GPIO_PinState col_state = Keypad_ReadColumn(col);
            bool current_pressed = (col_state == GPIO_PIN_RESET); // Active low

            Key_t* key = &keypad_driver.keys[row][col];

            // Process debouncing and state changes
            if (Keypad_ProcessDebounce(key, current_pressed)) {
                // State change detected, add to event queue
                Keypad_AddEvent(key);
                keypad_driver.total_events++;

                // Call user callback if registered
                if (keypad_driver.callback) {
                    keypad_driver.callback(row, col, key->state);
                }
            }

            // Update long press detection
            if (key->state == KEY_PRESSED && current_pressed) {
                uint32_t press_duration = current_time - key->press_timestamp;
                if (press_duration >= keypad_driver.longpress_time_ms &&
                    key->state != KEY_LONG_PRESSED) {

                    key->prev_state = key->state;
                    key->state = KEY_LONG_PRESSED;

                    Keypad_AddEvent(key);
                    keypad_driver.total_events++;

                    if (keypad_driver.callback) {
                        keypad_driver.callback(row, col, key->state);
                    }
                }
            }
        }
    }

    // Restore all rows to high
    for (uint8_t row = 0; row < KEYPAD_ROWS; row++) {
        Keypad_SetRowState(row, GPIO_PIN_SET);
    }

    keypad_driver.last_scan_time = current_time;
}

/**
 * @brief Get next key event from queue
 */
Key_t Keypad_GetKey(void)
{
    Key_t empty_key = {0, 0, KEY_RELEASED, KEY_RELEASED, 0, 0, 0};

    if (!keypad_driver.initialized || keypad_driver.queue_count == 0) {
        return empty_key;
    }

    // Get event from queue
    Key_t event = keypad_driver.event_queue[keypad_driver.queue_tail];

    // Update queue pointers
    keypad_driver.queue_tail = (keypad_driver.queue_tail + 1) % KEYPAD_EVENT_QUEUE_SIZE;
    keypad_driver.queue_count--;

    return event;
}

/**
 * @brief Check if specific key is currently pressed
 */
bool Keypad_IsKeyPressed(uint8_t row, uint8_t col)
{
    if (!keypad_driver.initialized || !KEYPAD_IS_VALID_COORD(row, col)) {
        return false;
    }

    KeyState_t state = keypad_driver.keys[row][col].state;
    return (state == KEY_PRESSED || state == KEY_LONG_PRESSED);
}

/**
 * @brief Get current state of specific key
 */
KeyState_t Keypad_GetKeyState(uint8_t row, uint8_t col)
{
    if (!keypad_driver.initialized || !KEYPAD_IS_VALID_COORD(row, col)) {
        return KEY_RELEASED;
    }

    return keypad_driver.keys[row][col].state;
}

/**
 * @brief Get press duration of specific key
 */
uint32_t Keypad_GetPressDuration(uint8_t row, uint8_t col)
{
    if (!keypad_driver.initialized || !KEYPAD_IS_VALID_COORD(row, col)) {
        return 0;
    }

    Key_t* key = &keypad_driver.keys[row][col];
    if (key->state == KEY_RELEASED) {
        return 0;
    }

    return HAL_GetTick() - key->press_timestamp;
}

/**
 * @brief Get all currently pressed keys as bitmask
 */
uint16_t Keypad_GetPressedKeys(void)
{
    if (!keypad_driver.initialized) {
        return 0;
    }

    uint16_t pressed_mask = 0;

    for (uint8_t row = 0; row < KEYPAD_ROWS; row++) {
        for (uint8_t col = 0; col < KEYPAD_COLS; col++) {
            if (Keypad_IsKeyPressed(row, col)) {
                uint8_t key_index = KEYPAD_GET_CODE(row, col);
                pressed_mask |= (1 << key_index);
            }
        }
    }

    return pressed_mask;
}

/**
 * @brief Register callback function for key events
 */
Keypad_Status_t Keypad_Register_Callback(Keypad_Callback_t callback)
{
    if (!keypad_driver.initialized) {
        return KEYPAD_ERROR;
    }

    keypad_driver.callback = callback;
    return KEYPAD_OK;
}

/**
 * @brief Quick check if any key is pressed
 */
bool Keypad_Quick_Check(void)
{
    if (!keypad_driver.initialized) {
        return false;
    }

    // Set all rows low
    for (uint8_t row = 0; row < KEYPAD_ROWS; row++) {
        Keypad_SetRowState(row, GPIO_PIN_RESET);
    }

    // Small delay for settling
    Keypad_DelayUs(5);

    // Check if any column is low
    bool any_pressed = false;
    for (uint8_t col = 0; col < KEYPAD_COLS; col++) {
        if (Keypad_ReadColumn(col) == GPIO_PIN_RESET) {
            any_pressed = true;
            break;
        }
    }

    // Restore all rows to high
    for (uint8_t row = 0; row < KEYPAD_ROWS; row++) {
        Keypad_SetRowState(row, GPIO_PIN_SET);
    }

    return any_pressed;
}

/**
 * @brief Set debounce time
 */
Keypad_Status_t Keypad_SetDebounceTime(uint32_t debounce_ms)
{
    if (!keypad_driver.initialized || debounce_ms > 1000) {
        return KEYPAD_ERROR;
    }

    keypad_driver.debounce_time_ms = debounce_ms;
    return KEYPAD_OK;
}

/**
 * @brief Set long press threshold time
 */
Keypad_Status_t Keypad_SetLongPressTime(uint32_t longpress_ms)
{
    if (!keypad_driver.initialized || longpress_ms < 100 || longpress_ms > 10000) {
        return KEYPAD_ERROR;
    }

    keypad_driver.longpress_time_ms = longpress_ms;
    return KEYPAD_OK;
}

/**
 * @brief Get keypad statistics
 */
Keypad_Status_t Keypad_GetStatistics(uint32_t *total_scans, uint32_t *total_events)
{
    if (!keypad_driver.initialized || !total_scans || !total_events) {
        return KEYPAD_ERROR;
    }

    *total_scans = keypad_driver.total_scans;
    *total_events = keypad_driver.total_events;
    return KEYPAD_OK;
}

/**
 * @brief Reset keypad statistics
 */
Keypad_Status_t Keypad_ResetStatistics(void)
{
    if (!keypad_driver.initialized) {
        return KEYPAD_ERROR;
    }

    keypad_driver.total_scans = 0;
    keypad_driver.total_events = 0;
    return KEYPAD_OK;
}

/**
 * @brief Keypad scan task for interrupt-driven operation
 */
void Keypad_Scan_Task(void)
{
    static uint32_t last_scan = 0;
    uint32_t current_time = HAL_GetTick();

    // Check if enough time has passed since last scan
    if (current_time - last_scan >= KEYPAD_SCAN_INTERVAL_MS) {
        Keypad_Scan();
        last_scan = current_time;
    }
}

/* Private functions ---------------------------------------------------------*/

/**
 * @brief Set row pin state
 */
static void Keypad_SetRowState(uint8_t row, GPIO_PinState state)
{
    if (row < KEYPAD_ROWS) {
        HAL_GPIO_WritePin(row_ports[row], row_pins[row], state);
    }
}

/**
 * @brief Read column pin state
 */
static GPIO_PinState Keypad_ReadColumn(uint8_t col)
{
    if (col < KEYPAD_COLS) {
        return HAL_GPIO_ReadPin(col_ports[col], col_pins[col]);
    }
    return GPIO_PIN_SET;
}

/**
 * @brief Process debouncing for a key
 */
static bool Keypad_ProcessDebounce(Key_t* key, bool current_pressed)
{
    uint32_t current_time = HAL_GetTick();
    bool state_changed = false;

    if (current_pressed) {
        // Key is currently pressed
        if (key->state == KEY_RELEASED) {
            // Transition from released to potentially pressed
            key->debounce_timer = current_time;
            key->stable_count = 1;
        } else {
            // Key was already pressed or in debounce
            key->stable_count++;

            if (key->stable_count >= KEYPAD_STABLE_COUNT &&
                (current_time - key->debounce_timer) >= keypad_driver.debounce_time_ms) {
                // Stable press detected
                if (key->state == KEY_RELEASED) {
                    key->prev_state = key->state;
                    key->state = KEY_PRESSED;
                    key->press_timestamp = current_time;
                    state_changed = true;
                }
            }
        }
    } else {
        // Key is currently released
        if (key->state != KEY_RELEASED) {
            // Transition from pressed to released
            key->debounce_timer = current_time;
            key->stable_count = 1;
        } else {
            // Key was already released or in debounce
            if (key->debounce_timer != 0) {
                key->stable_count++;

                if (key->stable_count >= KEYPAD_STABLE_COUNT &&
                    (current_time - key->debounce_timer) >= keypad_driver.debounce_time_ms) {
                    // Stable release confirmed
                    key->debounce_timer = 0;
                }
            }
        }

        // If debounce timer expired and key was pressed, mark as released
        if (key->state != KEY_RELEASED && key->debounce_timer != 0 &&
            (current_time - key->debounce_timer) >= keypad_driver.debounce_time_ms &&
            key->stable_count >= KEYPAD_STABLE_COUNT) {

            key->prev_state = key->state;
            key->state = KEY_RELEASED;
            key->debounce_timer = 0;
            state_changed = true;
        }
    }

    return state_changed;
}

/**
 * @brief Add event to queue
 */
static void Keypad_AddEvent(Key_t* key)
{
    if (keypad_driver.queue_count >= KEYPAD_EVENT_QUEUE_SIZE) {
        // Queue full, overwrite oldest event
        keypad_driver.queue_tail = (keypad_driver.queue_tail + 1) % KEYPAD_EVENT_QUEUE_SIZE;
        keypad_driver.queue_count--;
    }

    // Add new event
    keypad_driver.event_queue[keypad_driver.queue_head] = *key;
    keypad_driver.queue_head = (keypad_driver.queue_head + 1) % KEYPAD_EVENT_QUEUE_SIZE;
    keypad_driver.queue_count++;
}

/**
 * @brief Reset key to initial state
 */
static void Keypad_ResetKey(Key_t* key, uint8_t row, uint8_t col)
{
    key->row = row;
    key->col = col;
    key->state = KEY_RELEASED;
    key->prev_state = KEY_RELEASED;
    key->press_timestamp = 0;
    key->debounce_timer = 0;
    key->stable_count = 0;
}

/**
 * @brief Microsecond delay function
 */
static void Keypad_DelayUs(uint32_t microseconds)
{
    uint32_t start = DWT->CYCCNT;
    uint32_t cycles = microseconds * (SystemCoreClock / 1000000);
    while ((DWT->CYCCNT - start) < cycles);
}

/* Key mapping utility functions ---------------------------------------------*/

/**
 * @brief Convert physical row,col to logical key
 */
Keypad_LogicalKey_t Keypad_PhysicalToLogical(uint8_t row, uint8_t col)
{
    if (!KEYPAD_IS_VALID_COORD(row, col)) {
        return KEYPAD_KEY_INVALID;
    }
    return KEYPAD_COORD_TO_KEY(row, col);
}

/**
 * @brief Convert logical key to physical coordinates
 */
bool Keypad_LogicalToPhysical(Keypad_LogicalKey_t key, uint8_t *row, uint8_t *col)
{
    if (!row || !col || key >= KEYPAD_TOTAL_KEYS) {
        return false;
    }

    for (uint8_t r = 0; r < KEYPAD_ROWS; r++) {
        for (uint8_t c = 0; c < KEYPAD_COLS; c++) {
            if (KEYPAD_LAYOUT[r][c] == key) {
                *row = r;
                *col = c;
                return true;
            }
        }
    }
    return false;
}

/**
 * @brief Get character representation of logical key
 */
char Keypad_GetKeyChar(Keypad_LogicalKey_t key)
{
    if (key >= KEYPAD_TOTAL_KEYS) {
        return '\0';
    }
    return KEYPAD_KEY_TO_CHAR(key);
}

/**
 * @brief Get name string of logical key
 */
const char* Keypad_GetKeyName(Keypad_LogicalKey_t key)
{
    if (key >= KEYPAD_TOTAL_KEYS) {
        return "INVALID";
    }
    return KEYPAD_KEY_TO_NAME(key);
}

/**
 * @brief Convert numeric key to number
 */
uint8_t Keypad_KeyToNumber(Keypad_LogicalKey_t key)
{
    if (key >= KEYPAD_KEY_1 && key <= KEYPAD_KEY_9) {
        return (key - KEYPAD_KEY_1) + 1;
    } else if (key == KEYPAD_KEY_0) {
        return 0;
    }
    return 0xFF; // Invalid
}

/**
 * @brief Convert hex key (0-9,A-F) to hex value
 */
uint8_t Keypad_KeyToHex(Keypad_LogicalKey_t key)
{
    if (key >= KEYPAD_KEY_1 && key <= KEYPAD_KEY_9) {
        return (key - KEYPAD_KEY_1) + 1;
    } else if (key == KEYPAD_KEY_0) {
        return 0;
    } else if (key >= KEYPAD_KEY_A && key <= KEYPAD_KEY_D) {
        return (key - KEYPAD_KEY_A) + 10;
    }
    return 0xFF; // Invalid
}

/**
 * @brief Get Othello game direction from key
 */
bool Keypad_GetDirection(Keypad_LogicalKey_t key, int8_t *dx, int8_t *dy)
{
    if (!dx || !dy) {
        return false;
    }

    switch (key) {
        case KEYPAD_KEY_2: // Up
            *dx = 0; *dy = -1;
            return true;
        case KEYPAD_KEY_4: // Left
            *dx = -1; *dy = 0;
            return true;
        case KEYPAD_KEY_6: // Right
            *dx = 1; *dy = 0;
            return true;
        case KEYPAD_KEY_8: // Down
            *dx = 0; *dy = 1;
            return true;
        default:
            *dx = 0; *dy = 0;
            return false;
    }
}

/**
 * @brief Check if key combination forms valid move
 */
bool Keypad_IsValidMoveCombination(Keypad_LogicalKey_t key1, Keypad_LogicalKey_t key2)
{
    // For Othello: row(1-8) + column(1-8) combination
    uint8_t num1 = Keypad_KeyToNumber(key1);
    uint8_t num2 = Keypad_KeyToNumber(key2);

    return (num1 >= 1 && num1 <= 8) && (num2 >= 1 && num2 <= 8);
}