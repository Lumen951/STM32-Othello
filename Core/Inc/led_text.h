/**
 * @file led_text.h
 * @brief LED Text Display Module for WS2812B Matrix
 * @version 1.0
 * @date 2025-12-09
 *
 * @note Displays text messages on 8x8 LED matrix
 *       Supports simple 5x7 font for characters
 */

#ifndef __LED_TEXT_H
#define __LED_TEXT_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "ws2812b_driver.h"
#include <stdint.h>
#include <stdbool.h>

/* Exported types ------------------------------------------------------------*/

/**
 * @brief LED text display status
 */
typedef enum {
    LED_TEXT_OK = 0,
    LED_TEXT_ERROR,
    LED_TEXT_INVALID_PARAM
} LED_Text_Status_t;

/**
 * @brief Text scroll direction
 */
typedef enum {
    SCROLL_LEFT = 0,
    SCROLL_RIGHT,
    SCROLL_UP,
    SCROLL_DOWN
} Scroll_Direction_t;

/* Exported constants --------------------------------------------------------*/

/**
 * @brief Font dimensions
 */
#define LED_TEXT_CHAR_WIDTH     5       ///< Character width in pixels
#define LED_TEXT_CHAR_HEIGHT    7       ///< Character height in pixels
#define LED_TEXT_CHAR_SPACING   1       ///< Spacing between characters

/* Exported macro ------------------------------------------------------------*/
/* Exported functions prototypes ---------------------------------------------*/

/**
 * @brief Initialize LED text display module
 * @retval LED_Text_Status_t Initialization status
 */
LED_Text_Status_t LED_Text_Init(void);

/**
 * @brief Display text on LED matrix (centered)
 * @param text Text string to display (max 4 characters for 8x8 matrix)
 * @param color RGB color for text
 * @retval LED_Text_Status_t Status of operation
 * @note Text is displayed centered on the matrix
 */
LED_Text_Status_t LED_Text_Display(const char* text, RGB_Color_t color);

/**
 * @brief Display single character on LED matrix
 * @param c Character to display
 * @param x X position (0-7)
 * @param y Y position (0-7)
 * @param color RGB color for character
 * @retval LED_Text_Status_t Status of operation
 */
LED_Text_Status_t LED_Text_DisplayChar(char c, uint8_t x, uint8_t y, RGB_Color_t color);

/**
 * @brief Scroll text across LED matrix
 * @param text Text string to scroll
 * @param color RGB color for text
 * @param direction Scroll direction
 * @param delay_ms Delay between scroll steps in milliseconds
 * @retval LED_Text_Status_t Status of operation
 */
LED_Text_Status_t LED_Text_Scroll(const char* text, RGB_Color_t color,
                                  Scroll_Direction_t direction, uint16_t delay_ms);

/**
 * @brief Clear text display
 * @retval LED_Text_Status_t Status of operation
 */
LED_Text_Status_t LED_Text_Clear(void);

#ifdef __cplusplus
}
#endif

#endif /* __LED_TEXT_H */
