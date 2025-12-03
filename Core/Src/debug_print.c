/**
 * @file debug_print.c
 * @brief Debug Printing Utility Implementation
 * @version 1.0
 * @date 2025-12-03
 */

/* Includes ------------------------------------------------------------------*/
#include "debug_print.h"
#include <stdio.h>
#include <string.h>

/* Private typedef -----------------------------------------------------------*/
/* Private define ------------------------------------------------------------*/
/* Private macro -------------------------------------------------------------*/
/* Private variables ---------------------------------------------------------*/
static bool debug_initialized = false;

/* Private function prototypes -----------------------------------------------*/
/* Exported functions --------------------------------------------------------*/

/**
 * @brief Initialize debug print module
 */
bool Debug_Init(void)
{
    debug_initialized = true;
    return true;
}

/**
 * @brief Print formatted debug message
 */
bool Debug_Printf(Debug_Level_t level, const char* fmt, ...)
{
#ifdef ENABLE_DEBUG
#if ENABLE_DEBUG == 1
    if (!fmt) {
        return false;
    }

    char debug_buffer[DEBUG_BUFFER_SIZE];
    va_list args;
    va_start(args, fmt);

    int len = vsnprintf(debug_buffer, DEBUG_BUFFER_SIZE, fmt, args);

    va_end(args);

    if (len > 0 && len < DEBUG_BUFFER_SIZE) {
        HAL_StatusTypeDef status = HAL_UART_Transmit(&huart1, (uint8_t*)debug_buffer, len, DEBUG_UART_TIMEOUT_MS);
        return (status == HAL_OK);
    }

    return false;
#else
    return true;
#endif
#else
    return true;
#endif
}

/**
 * @brief Print raw string without formatting
 */
bool Debug_Print_Raw(const char* str)
{
#ifdef ENABLE_DEBUG
#if ENABLE_DEBUG == 1
    if (!str) {
        return false;
    }

    uint16_t len = strlen(str);
    if (len > 0) {
        HAL_StatusTypeDef status = HAL_UART_Transmit(&huart1, (uint8_t*)str, len, DEBUG_UART_TIMEOUT_MS);
        return (status == HAL_OK);
    }

    return false;
#else
    return true;
#endif
#else
    return true;
#endif
}

/**
 * @brief Print buffer in hexadecimal format
 */
bool Debug_Print_Hex(const uint8_t* data, uint16_t len, const char* label)
{
#ifdef ENABLE_DEBUG
#if ENABLE_DEBUG == 1
    if (!data || len == 0) {
        return false;
    }

    if (label) {
        Debug_Printf(DEBUG_LEVEL_INFO, "[HEX] %s: ", label);
    }

    char debug_buffer[DEBUG_BUFFER_SIZE];
    for (uint16_t i = 0; i < len; i++) {
        snprintf(debug_buffer, DEBUG_BUFFER_SIZE, "%02X ", data[i]);
        HAL_UART_Transmit(&huart1, (uint8_t*)debug_buffer, 3, DEBUG_UART_TIMEOUT_MS);
    }

    Debug_Printf(DEBUG_LEVEL_INFO, "\r\n");
    return true;
#else
    return true;
#endif
#else
    return true;
#endif
}

/**
 * @brief Print system information banner
 */
bool Debug_Print_Banner(void)
{
#ifdef ENABLE_DEBUG
#if ENABLE_DEBUG == 1
    Debug_Print_Raw("========================================\r\n");
    Debug_Print_Raw("STM32 Othello System v1.0.0\r\n");
    Debug_Print_Raw("Built: " __DATE__ " " __TIME__ "\r\n");
    Debug_Print_Raw("========================================\r\n");
    return true;
#else
    return true;
#endif
#else
    return true;
#endif
}

/* Private functions ---------------------------------------------------------*/
