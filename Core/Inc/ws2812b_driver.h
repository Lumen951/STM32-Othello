/**
 * @file ws2812b_driver.h
 * @brief WS2812B LED Matrix Driver for STM32F103C8T6
 * @version 1.0
 * @date 2025-11-22
 *
 * @note This driver uses TIM2_CH1 PWM + DMA to control 8x8 WS2812B LED matrix
 *       Connected to PA0 (LED_DATA pin as per CLAUDE.md specifications)
 */

#ifndef __WS2812B_DRIVER_H
#define __WS2812B_DRIVER_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "stm32f1xx_hal.h"

/* Exported types ------------------------------------------------------------*/

/**
 * @brief RGB Color structure
 */
typedef struct {
    uint8_t red;    ///< Red component (0-255)
    uint8_t green;  ///< Green component (0-255)
    uint8_t blue;   ///< Blue component (0-255)
} RGB_Color_t;

/**
 * @brief WS2812B Driver Status
 */
typedef enum {
    WS2812B_OK = 0,
    WS2812B_ERROR,
    WS2812B_BUSY,
    WS2812B_TIMEOUT
} WS2812B_Status_t;

/* Exported constants --------------------------------------------------------*/

/** @defgroup WS2812B_Matrix_Config Matrix Configuration
 * @{
 */
#define WS2812B_LED_ROWS        8       ///< Number of LED rows
#define WS2812B_LED_COLS        8       ///< Number of LED columns
#define WS2812B_LED_COUNT       (WS2812B_LED_ROWS * WS2812B_LED_COLS) ///< Total LED count (64)
#define WS2812B_BITS_PER_LED    24      ///< Bits per LED (8R + 8G + 8B)
#define WS2812B_RESET_PULSE     40      ///< Reset pulse duration (40 × 1.25μs = 50μs)
/**
 * @}
 */

/** @defgroup WS2812B_PWM_Values PWM Values for WS2812B Protocol
 * @{
 */
#define WS2812B_LOGIC_0         29      ///< PWM value for logic '0' (~0.4μs high)
#define WS2812B_LOGIC_1         58      ///< PWM value for logic '1' (~0.8μs high)
#define WS2812B_RESET_VAL       0       ///< PWM value for reset (0V)
/**
 * @}
 */

/** @defgroup WS2812B_Predefined_Colors Predefined Colors
 * @{
 */
#define WS2812B_COLOR_OFF       ((RGB_Color_t){0, 0, 0})
#define WS2812B_COLOR_BLACK     ((RGB_Color_t){0, 0, 0})
#define WS2812B_COLOR_RED       ((RGB_Color_t){255, 0, 0})
#define WS2812B_COLOR_GREEN     ((RGB_Color_t){0, 255, 0})
#define WS2812B_COLOR_BLUE      ((RGB_Color_t){0, 0, 255})
#define WS2812B_COLOR_WHITE     ((RGB_Color_t){255, 255, 255})
#define WS2812B_COLOR_YELLOW    ((RGB_Color_t){255, 255, 0})
#define WS2812B_COLOR_MAGENTA   ((RGB_Color_t){255, 0, 255})
#define WS2812B_COLOR_CYAN      ((RGB_Color_t){0, 255, 255})
/**
 * @}
 */

/* Exported macro ------------------------------------------------------------*/

/**
 * @brief Convert row,col coordinates to linear LED index
 * @param row Row index (0-7)
 * @param col Column index (0-7)
 * @retval Linear LED index (0-63)
 * @note Uses serpentine (zigzag) mapping for typical LED matrix wiring
 */
#define WS2812B_GET_LED_INDEX(row, col) \
    (((row) % 2 == 0) ? ((row) * WS2812B_LED_COLS + (col)) : ((row) * WS2812B_LED_COLS + (WS2812B_LED_COLS - 1 - (col))))

/**
 * @brief Check if coordinates are valid
 * @param row Row index
 * @param col Column index
 * @retval 1 if valid, 0 if invalid
 */
#define WS2812B_IS_VALID_COORD(row, col) \
    ((row) < WS2812B_LED_ROWS && (col) < WS2812B_LED_COLS)

/* Exported variables --------------------------------------------------------*/
extern TIM_HandleTypeDef htim2;   ///< Timer handle (defined in main.c)
extern DMA_HandleTypeDef hdma_tim2_ch1; ///< DMA handle (defined in main.c)

/* Exported functions prototypes ---------------------------------------------*/

/**
 * @brief Initialize WS2812B driver
 * @retval WS2812B_Status_t Status of initialization
 * @note Must be called after HAL_Init() and TIM2/DMA configuration
 */
WS2812B_Status_t WS2812B_Init(void);

/**
 * @brief Set color of specific LED at row,col position
 * @param row Row index (0-7)
 * @param col Column index (0-7)
 * @param color RGB color to set
 * @retval WS2812B_Status_t Status of operation
 * @note Color is staged in buffer, call WS2812B_Update() to display
 */
WS2812B_Status_t WS2812B_SetPixel(uint8_t row, uint8_t col, RGB_Color_t color);

/**
 * @brief Set color of specific LED by linear index
 * @param index Linear LED index (0-63)
 * @param color RGB color to set
 * @retval WS2812B_Status_t Status of operation
 */
WS2812B_Status_t WS2812B_SetPixelByIndex(uint8_t index, RGB_Color_t color);

/**
 * @brief Clear all LEDs (set to black)
 * @retval WS2812B_Status_t Status of operation
 * @note Call WS2812B_Update() to display changes
 */
WS2812B_Status_t WS2812B_Clear(void);

/**
 * @brief Update LED matrix display
 * @retval WS2812B_Status_t Status of operation
 * @note Starts DMA transfer to send data to LEDs
 */
WS2812B_Status_t WS2812B_Update(void);

/**
 * @brief Set brightness for all LEDs
 * @param brightness Brightness level (0-255)
 * @retval WS2812B_Status_t Status of operation
 * @note Affects all subsequent color operations
 */
WS2812B_Status_t WS2812B_SetBrightness(uint8_t brightness);

/**
 * @brief Get current brightness level
 * @retval Current brightness (0-255)
 */
uint8_t WS2812B_GetBrightness(void);

/**
 * @brief Check if WS2812B driver is busy (DMA transfer in progress)
 * @retval 1 if busy, 0 if ready
 */
uint8_t WS2812B_IsBusy(void);

/**
 * @brief Fill entire matrix with single color
 * @param color RGB color to fill
 * @retval WS2812B_Status_t Status of operation
 */
WS2812B_Status_t WS2812B_Fill(RGB_Color_t color);

/**
 * @brief DMA transfer complete callback
 * @param hdma DMA handle
 * @note Called automatically by HAL when DMA transfer completes
 */
void WS2812B_DMA_Complete_Callback(DMA_HandleTypeDef *hdma);

/**
 * @brief Test function - Display RGB test pattern
 * @retval WS2812B_Status_t Status of operation
 * @note For debugging and verification purposes
 */
WS2812B_Status_t WS2812B_Test_RGB_Pattern(void);

#ifdef __cplusplus
}
#endif

#endif /* __WS2812B_DRIVER_H */