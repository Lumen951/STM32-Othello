/**
 * @file ws2812b_driver.c
 * @brief WS2812B LED Matrix Driver Implementation
 * @version 1.0
 * @date 2025-11-22
 *
 * @details
 * This driver implements WS2812B protocol using TIM2_CH1 PWM + DMA:
 * - Timer: TIM2, Prescaler=0, Period=89 (800kHz PWM)
 * - DMA: Memory to Peripheral, 16-bit data width
 * - Protocol: Logic '0' = 29/90 duty (~0.4μs), Logic '1' = 58/90 duty (~0.8μs)
 * - Reset: 40 × 1.25μs = 50μs low pulse
 */

/* Includes ------------------------------------------------------------------*/
#include "ws2812b_driver.h"
#include <string.h>

/* Private typedef -----------------------------------------------------------*/

/**
 * @brief Driver state structure
 */
typedef struct {
    uint8_t brightness;           ///< Global brightness (0-255)
    uint8_t is_busy;             ///< DMA transfer busy flag
    uint8_t initialized;         ///< Initialization flag
} WS2812B_State_t;

/* Private define ------------------------------------------------------------*/
#define WS2812B_BUFFER_SIZE     (WS2812B_LED_COUNT * WS2812B_BITS_PER_LED + WS2812B_RESET_PULSE)
#define WS2812B_DEFAULT_BRIGHTNESS  255

/* Private macro -------------------------------------------------------------*/

/**
 * @brief Apply brightness scaling to color component
 * @param color Original color component (0-255)
 * @param brightness Brightness level (0-255)
 * @retval Scaled color component
 */
#define APPLY_BRIGHTNESS(color, brightness) ((uint8_t)(((uint16_t)(color) * (brightness)) >> 8))

/* Private variables ---------------------------------------------------------*/

/**
 * @brief PWM data buffer for DMA transfer
 * @note Must be uint16_t as specified in CLAUDE.md requirements
 */
static uint16_t pwm_buffer[WS2812B_BUFFER_SIZE];

/**
 * @brief LED color buffer (RGB values for each LED)
 */
static RGB_Color_t led_buffer[WS2812B_LED_COUNT];

/**
 * @brief Driver state
 */
static WS2812B_State_t ws2812b_state = {
    .brightness = WS2812B_DEFAULT_BRIGHTNESS,
    .is_busy = 0,
    .initialized = 0
};

/* Private function prototypes -----------------------------------------------*/
static void WS2812B_Convert_RGB_to_PWM(void);
static void WS2812B_Set_LED_Color_Raw(uint8_t index, uint8_t red, uint8_t green, uint8_t blue);

/* Exported functions --------------------------------------------------------*/

/**
 * @brief Initialize WS2812B driver
 */
WS2812B_Status_t WS2812B_Init(void)
{
    /* Check if TIM2 and DMA are properly configured */
    if (htim2.Instance != TIM2) {
        return WS2812B_ERROR;
    }

    /* Clear all buffers */
    memset(pwm_buffer, 0, sizeof(pwm_buffer));
    memset(led_buffer, 0, sizeof(led_buffer));

    /* Initialize reset pulse at the end of buffer */
    for (uint16_t i = WS2812B_LED_COUNT * WS2812B_BITS_PER_LED; i < WS2812B_BUFFER_SIZE; i++) {
        pwm_buffer[i] = WS2812B_RESET_VAL;
    }

    /* Set driver state */
    ws2812b_state.brightness = WS2812B_DEFAULT_BRIGHTNESS;
    ws2812b_state.is_busy = 0;
    ws2812b_state.initialized = 1;

    /* Start PWM but don't start DMA yet */
    if (HAL_TIM_PWM_Start(&htim2, TIM_CHANNEL_1) != HAL_OK) {
        return WS2812B_ERROR;
    }

    return WS2812B_OK;
}

/**
 * @brief Set color of specific LED at row,col position
 */
WS2812B_Status_t WS2812B_SetPixel(uint8_t row, uint8_t col, RGB_Color_t color)
{
    /* Check initialization */
    if (!ws2812b_state.initialized) {
        return WS2812B_ERROR;
    }

    /* Validate coordinates */
    if (!WS2812B_IS_VALID_COORD(row, col)) {
        return WS2812B_ERROR;
    }

    /* Convert to linear index */
    uint8_t index = WS2812B_GET_LED_INDEX(row, col);

    /* Set color in buffer */
    led_buffer[index] = color;

    return WS2812B_OK;
}

/**
 * @brief Set color of specific LED by linear index
 */
WS2812B_Status_t WS2812B_SetPixelByIndex(uint8_t index, RGB_Color_t color)
{
    /* Check initialization and index */
    if (!ws2812b_state.initialized || index >= WS2812B_LED_COUNT) {
        return WS2812B_ERROR;
    }

    /* Set color in buffer */
    led_buffer[index] = color;

    return WS2812B_OK;
}

/**
 * @brief Clear all LEDs
 */
WS2812B_Status_t WS2812B_Clear(void)
{
    /* Check initialization */
    if (!ws2812b_state.initialized) {
        return WS2812B_ERROR;
    }

    /* Clear LED buffer */
    memset(led_buffer, 0, sizeof(led_buffer));

    return WS2812B_OK;
}

/**
 * @brief Update LED matrix display
 */
WS2812B_Status_t WS2812B_Update(void)
{
    /* Check initialization */
    if (!ws2812b_state.initialized) {
        return WS2812B_ERROR;
    }

    /* Check if DMA is busy */
    if (ws2812b_state.is_busy) {
        return WS2812B_BUSY;
    }

    /* Convert RGB values to PWM data */
    WS2812B_Convert_RGB_to_PWM();

    /* Set busy flag */
    ws2812b_state.is_busy = 1;

    /* Start DMA transfer */
    if (HAL_TIM_PWM_Start_DMA(&htim2, TIM_CHANNEL_1, (uint32_t*)pwm_buffer, WS2812B_BUFFER_SIZE) != HAL_OK) {
        ws2812b_state.is_busy = 0;
        return WS2812B_ERROR;
    }

    return WS2812B_OK;
}

/**
 * @brief Set brightness for all LEDs
 */
WS2812B_Status_t WS2812B_SetBrightness(uint8_t brightness)
{
    /* Check initialization */
    if (!ws2812b_state.initialized) {
        return WS2812B_ERROR;
    }

    ws2812b_state.brightness = brightness;

    return WS2812B_OK;
}

/**
 * @brief Get current brightness level
 */
uint8_t WS2812B_GetBrightness(void)
{
    return ws2812b_state.brightness;
}

/**
 * @brief Check if WS2812B driver is busy
 */
uint8_t WS2812B_IsBusy(void)
{
    return ws2812b_state.is_busy;
}

/**
 * @brief Fill entire matrix with single color
 */
WS2812B_Status_t WS2812B_Fill(RGB_Color_t color)
{
    /* Check initialization */
    if (!ws2812b_state.initialized) {
        return WS2812B_ERROR;
    }

    /* Fill all LEDs with the same color */
    for (uint8_t i = 0; i < WS2812B_LED_COUNT; i++) {
        led_buffer[i] = color;
    }

    return WS2812B_OK;
}

/**
 * @brief DMA transfer complete callback
 */
void WS2812B_DMA_Complete_Callback(DMA_HandleTypeDef *hdma)
{
    /* Check if this is our DMA channel */
    if (hdma->Instance == DMA1_Channel1) {
        /* Stop PWM DMA */
        HAL_TIM_PWM_Stop_DMA(&htim2, TIM_CHANNEL_1);

        /* Clear busy flag */
        ws2812b_state.is_busy = 0;
    }
}

/**
 * @brief Test function - Display RGB test pattern
 */
WS2812B_Status_t WS2812B_Test_RGB_Pattern(void)
{
    /* Check initialization */
    if (!ws2812b_state.initialized) {
        return WS2812B_ERROR;
    }

    /* Create test pattern */
    for (uint8_t row = 0; row < WS2812B_LED_ROWS; row++) {
        for (uint8_t col = 0; col < WS2812B_LED_COLS; col++) {
            RGB_Color_t color;

            if (row < 3) {
                /* Red gradient */
                color.red = (col * 32) + 31;
                color.green = 0;
                color.blue = 0;
            } else if (row < 6) {
                /* Green gradient */
                color.red = 0;
                color.green = (col * 32) + 31;
                color.blue = 0;
            } else {
                /* Blue gradient */
                color.red = 0;
                color.green = 0;
                color.blue = (col * 32) + 31;
            }

            WS2812B_SetPixel(row, col, color);
        }
    }

    return WS2812B_Update();
}

/* Private functions ---------------------------------------------------------*/

/**
 * @brief Convert RGB buffer to PWM data buffer
 */
static void WS2812B_Convert_RGB_to_PWM(void)
{
    uint16_t buffer_index = 0;

    /* Process each LED */
    for (uint8_t led = 0; led < WS2812B_LED_COUNT; led++) {
        /* Apply brightness scaling */
        uint8_t red = APPLY_BRIGHTNESS(led_buffer[led].red, ws2812b_state.brightness);
        uint8_t green = APPLY_BRIGHTNESS(led_buffer[led].green, ws2812b_state.brightness);
        uint8_t blue = APPLY_BRIGHTNESS(led_buffer[led].blue, ws2812b_state.brightness);

        /* WS2812B expects GRB order */
        uint8_t grb_data[3] = {green, red, blue};

        /* Convert each color component to PWM values */
        for (uint8_t color_byte = 0; color_byte < 3; color_byte++) {
            for (int8_t bit = 7; bit >= 0; bit--) {
                /* Check if bit is set */
                if (grb_data[color_byte] & (1 << bit)) {
                    pwm_buffer[buffer_index] = WS2812B_LOGIC_1;  /* ~0.8μs high */
                } else {
                    pwm_buffer[buffer_index] = WS2812B_LOGIC_0;  /* ~0.4μs high */
                }
                buffer_index++;
            }
        }
    }

    /* Reset pulse is already set during initialization */
}

/**
 * @brief Set LED color directly by index (internal function)
 */
static void WS2812B_Set_LED_Color_Raw(uint8_t index, uint8_t red, uint8_t green, uint8_t blue) __attribute__((unused));
static void WS2812B_Set_LED_Color_Raw(uint8_t index, uint8_t red, uint8_t green, uint8_t blue)
{
    if (index < WS2812B_LED_COUNT) {
        led_buffer[index].red = red;
        led_buffer[index].green = green;
        led_buffer[index].blue = blue;
    }
}