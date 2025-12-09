/**
 * @file led_text.c
 * @brief LED Text Display Module Implementation
 * @version 1.0
 * @date 2025-12-09
 */

/* Includes ------------------------------------------------------------------*/
#include "led_text.h"
#include <string.h>
#include <ctype.h>

/* Private typedef -----------------------------------------------------------*/
/* Private define ------------------------------------------------------------*/
/* Private macro -------------------------------------------------------------*/
/* Private variables ---------------------------------------------------------*/

/**
 * @brief 5x7 font bitmap for uppercase letters and digits
 * @note Each character is 5 bytes (5 columns × 7 rows)
 *       Bit 0 = top row, Bit 6 = bottom row
 */
static const uint8_t font_5x7[][5] = {
    // Space (0x20)
    {0x00, 0x00, 0x00, 0x00, 0x00},
    // ! (0x21)
    {0x00, 0x00, 0x5F, 0x00, 0x00},
    // " (0x22)
    {0x00, 0x07, 0x00, 0x07, 0x00},
    // # (0x23)
    {0x14, 0x7F, 0x14, 0x7F, 0x14},
    // $ (0x24)
    {0x24, 0x2A, 0x7F, 0x2A, 0x12},
    // % (0x25)
    {0x23, 0x13, 0x08, 0x64, 0x62},
    // & (0x26)
    {0x36, 0x49, 0x55, 0x22, 0x50},
    // ' (0x27)
    {0x00, 0x05, 0x03, 0x00, 0x00},
    // ( (0x28)
    {0x00, 0x1C, 0x22, 0x41, 0x00},
    // ) (0x29)
    {0x00, 0x41, 0x22, 0x1C, 0x00},
    // * (0x2A)
    {0x14, 0x08, 0x3E, 0x08, 0x14},
    // + (0x2B)
    {0x08, 0x08, 0x3E, 0x08, 0x08},
    // , (0x2C)
    {0x00, 0x50, 0x30, 0x00, 0x00},
    // - (0x2D)
    {0x08, 0x08, 0x08, 0x08, 0x08},
    // . (0x2E)
    {0x00, 0x60, 0x60, 0x00, 0x00},
    // / (0x2F)
    {0x20, 0x10, 0x08, 0x04, 0x02},
    // 0 (0x30)
    {0x3E, 0x51, 0x49, 0x45, 0x3E},
    // 1 (0x31)
    {0x00, 0x42, 0x7F, 0x40, 0x00},
    // 2 (0x32)
    {0x42, 0x61, 0x51, 0x49, 0x46},
    // 3 (0x33)
    {0x21, 0x41, 0x45, 0x4B, 0x31},
    // 4 (0x34)
    {0x18, 0x14, 0x12, 0x7F, 0x10},
    // 5 (0x35)
    {0x27, 0x45, 0x45, 0x45, 0x39},
    // 6 (0x36)
    {0x3C, 0x4A, 0x49, 0x49, 0x30},
    // 7 (0x37)
    {0x01, 0x71, 0x09, 0x05, 0x03},
    // 8 (0x38)
    {0x36, 0x49, 0x49, 0x49, 0x36},
    // 9 (0x39)
    {0x06, 0x49, 0x49, 0x29, 0x1E},
    // : (0x3A)
    {0x00, 0x36, 0x36, 0x00, 0x00},
    // ; (0x3B)
    {0x00, 0x56, 0x36, 0x00, 0x00},
    // < (0x3C)
    {0x08, 0x14, 0x22, 0x41, 0x00},
    // = (0x3D)
    {0x14, 0x14, 0x14, 0x14, 0x14},
    // > (0x3E)
    {0x00, 0x41, 0x22, 0x14, 0x08},
    // ? (0x3F)
    {0x02, 0x01, 0x51, 0x09, 0x06},
    // @ (0x40)
    {0x32, 0x49, 0x79, 0x41, 0x3E},
    // A (0x41)
    {0x7E, 0x11, 0x11, 0x11, 0x7E},
    // B (0x42)
    {0x7F, 0x49, 0x49, 0x49, 0x36},
    // C (0x43)
    {0x3E, 0x41, 0x41, 0x41, 0x22},
    // D (0x44)
    {0x7F, 0x41, 0x41, 0x22, 0x1C},
    // E (0x45)
    {0x7F, 0x49, 0x49, 0x49, 0x41},
    // F (0x46)
    {0x7F, 0x09, 0x09, 0x09, 0x01},
    // G (0x47)
    {0x3E, 0x41, 0x49, 0x49, 0x7A},
    // H (0x48)
    {0x7F, 0x08, 0x08, 0x08, 0x7F},
    // I (0x49)
    {0x00, 0x41, 0x7F, 0x41, 0x00},
    // J (0x4A)
    {0x20, 0x40, 0x41, 0x3F, 0x01},
    // K (0x4B)
    {0x7F, 0x08, 0x14, 0x22, 0x41},
    // L (0x4C)
    {0x7F, 0x40, 0x40, 0x40, 0x40},
    // M (0x4D)
    {0x7F, 0x02, 0x0C, 0x02, 0x7F},
    // N (0x4E)
    {0x7F, 0x04, 0x08, 0x10, 0x7F},
    // O (0x4F)
    {0x3E, 0x41, 0x41, 0x41, 0x3E},
    // P (0x50)
    {0x7F, 0x09, 0x09, 0x09, 0x06},
    // Q (0x51)
    {0x3E, 0x41, 0x51, 0x21, 0x5E},
    // R (0x52)
    {0x7F, 0x09, 0x19, 0x29, 0x46},
    // S (0x53)
    {0x46, 0x49, 0x49, 0x49, 0x31},
    // T (0x54)
    {0x01, 0x01, 0x7F, 0x01, 0x01},
    // U (0x55)
    {0x3F, 0x40, 0x40, 0x40, 0x3F},
    // V (0x56)
    {0x1F, 0x20, 0x40, 0x20, 0x1F},
    // W (0x57)
    {0x3F, 0x40, 0x38, 0x40, 0x3F},
    // X (0x58)
    {0x63, 0x14, 0x08, 0x14, 0x63},
    // Y (0x59)
    {0x07, 0x08, 0x70, 0x08, 0x07},
    // Z (0x5A)
    {0x61, 0x51, 0x49, 0x45, 0x43}
};

/* Private function prototypes -----------------------------------------------*/
static const uint8_t* LED_Text_GetCharBitmap(char c);
static void LED_Text_DrawBitmap(const uint8_t* bitmap, uint8_t x, uint8_t y, RGB_Color_t color);

/* Exported functions --------------------------------------------------------*/

/**
 * @brief Initialize LED text display module
 */
LED_Text_Status_t LED_Text_Init(void)
{
    // LED driver should already be initialized
    return LED_TEXT_OK;
}

/**
 * @brief Display text on LED matrix (centered)
 */
LED_Text_Status_t LED_Text_Display(const char* text, RGB_Color_t color)
{
    if (!text) {
        return LED_TEXT_INVALID_PARAM;
    }

    // Clear display first
    WS2812B_Clear();

    uint8_t text_len = strlen(text);
    if (text_len == 0) {
        WS2812B_Update();
        return LED_TEXT_OK;
    }

    // Calculate total width needed
    uint8_t total_width = text_len * (LED_TEXT_CHAR_WIDTH + LED_TEXT_CHAR_SPACING) - LED_TEXT_CHAR_SPACING;

    // Center text horizontally
    int8_t start_x = (WS2812B_LED_COLS - total_width) / 2;
    if (start_x < 0) start_x = 0;

    // Center text vertically
    int8_t start_y = (WS2812B_LED_ROWS - LED_TEXT_CHAR_HEIGHT) / 2;
    if (start_y < 0) start_y = 0;

    // Draw each character
    uint8_t x_pos = start_x;
    for (uint8_t i = 0; i < text_len; i++) {
        if (x_pos + LED_TEXT_CHAR_WIDTH > WS2812B_LED_COLS) {
            break;  // No more space
        }

        LED_Text_DisplayChar(text[i], x_pos, start_y, color);
        x_pos += LED_TEXT_CHAR_WIDTH + LED_TEXT_CHAR_SPACING;
    }

    // Update display
    WS2812B_Update();

    return LED_TEXT_OK;
}

/**
 * @brief Display single character on LED matrix
 */
LED_Text_Status_t LED_Text_DisplayChar(char c, uint8_t x, uint8_t y, RGB_Color_t color)
{
    const uint8_t* bitmap = LED_Text_GetCharBitmap(c);
    if (!bitmap) {
        return LED_TEXT_INVALID_PARAM;
    }

    LED_Text_DrawBitmap(bitmap, x, y, color);

    return LED_TEXT_OK;
}

/**
 * @brief Scroll text across LED matrix
 */
LED_Text_Status_t LED_Text_Scroll(const char* text, RGB_Color_t color,
                                  Scroll_Direction_t direction, uint16_t delay_ms)
{
    if (!text) {
        return LED_TEXT_INVALID_PARAM;
    }

    // Simple left scroll implementation
    uint8_t text_len = strlen(text);
    uint8_t total_width = text_len * (LED_TEXT_CHAR_WIDTH + LED_TEXT_CHAR_SPACING);

    for (int16_t offset = WS2812B_LED_COLS; offset > -total_width; offset--) {
        WS2812B_Clear();

        int16_t x_pos = offset;
        for (uint8_t i = 0; i < text_len; i++) {
            if (x_pos >= -LED_TEXT_CHAR_WIDTH && x_pos < WS2812B_LED_COLS) {
                LED_Text_DisplayChar(text[i], x_pos, 0, color);
            }
            x_pos += LED_TEXT_CHAR_WIDTH + LED_TEXT_CHAR_SPACING;
        }

        WS2812B_Update();
        HAL_Delay(delay_ms);
    }

    return LED_TEXT_OK;
}

/**
 * @brief Clear text display
 */
LED_Text_Status_t LED_Text_Clear(void)
{
    WS2812B_Clear();
    WS2812B_Update();
    return LED_TEXT_OK;
}

/* Private functions ---------------------------------------------------------*/

/**
 * @brief Get character bitmap from font table
 */
static const uint8_t* LED_Text_GetCharBitmap(char c)
{
    // Convert to uppercase
    c = toupper(c);

    // Check if character is in font table
    if (c >= 0x20 && c <= 0x5A) {
        return font_5x7[c - 0x20];
    }

    // Return space for unknown characters
    return font_5x7[0];
}

/**
 * @brief Draw character bitmap on LED matrix
 */
static void LED_Text_DrawBitmap(const uint8_t* bitmap, uint8_t x, uint8_t y, RGB_Color_t color)
{
    for (uint8_t col = 0; col < LED_TEXT_CHAR_WIDTH; col++) {
        uint8_t column_data = bitmap[col];

        for (uint8_t row = 0; row < LED_TEXT_CHAR_HEIGHT; row++) {
            if (column_data & (1 << row)) {
                uint8_t pixel_x = x + col;
                uint8_t pixel_y = y + row;

                if (pixel_x < WS2812B_LED_COLS && pixel_y < WS2812B_LED_ROWS) {
                    WS2812B_SetPixel(pixel_y, pixel_x, color);
                }
            }
        }
    }
}
