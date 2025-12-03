/**
 * @file debug_print.h
 * @brief Debug Printing Utility for UART Diagnostics
 * @version 1.0
 * @date 2025-12-03
 *
 * @note Provides convenient debug printing functions via UART1
 *       - Enable/disable via ENABLE_DEBUG macro
 *       - Supports formatted output like printf
 *       - Three log levels: INFO, WARN, ERROR
 */

#ifndef __DEBUG_PRINT_H
#define __DEBUG_PRINT_H

/* Enable debug output globally - set to 0 to disable */
#ifndef ENABLE_DEBUG
#define ENABLE_DEBUG 1
#endif

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include <stdint.h>
#include <stdbool.h>
#include <stdarg.h>

/* Exported types ------------------------------------------------------------*/

/**
 * @brief Debug log level enumeration
 */
typedef enum {
    DEBUG_LEVEL_INFO = 0,
    DEBUG_LEVEL_WARN,
    DEBUG_LEVEL_ERROR
} Debug_Level_t;

/* Exported constants --------------------------------------------------------*/

/** @defgroup Debug_Config Debug Configuration
 * @{
 */
#define DEBUG_BUFFER_SIZE       256     ///< Maximum debug message length
#define DEBUG_UART_TIMEOUT_MS   100     ///< UART transmit timeout
/**
 * @}
 */

/* Exported macro ------------------------------------------------------------*/

/**
 * @brief Main debug print macro
 * @note Only active when ENABLE_DEBUG is defined as 1
 */
#ifdef ENABLE_DEBUG
#if ENABLE_DEBUG == 1
    #define DEBUG_PRINT(fmt, ...) Debug_Printf(DEBUG_LEVEL_INFO, fmt, ##__VA_ARGS__)
    #define DEBUG_INFO(fmt, ...)  Debug_Printf(DEBUG_LEVEL_INFO, fmt, ##__VA_ARGS__)
    #define DEBUG_WARN(fmt, ...)  Debug_Printf(DEBUG_LEVEL_WARN, "[WARN] " fmt, ##__VA_ARGS__)
    #define DEBUG_ERROR(fmt, ...) Debug_Printf(DEBUG_LEVEL_ERROR, "[ERROR] " fmt, ##__VA_ARGS__)
    #define DEBUG_PRINT_BANNER()  Debug_Print_Banner()
#else
    #define DEBUG_PRINT(fmt, ...) ((void)0)
    #define DEBUG_INFO(fmt, ...)  ((void)0)
    #define DEBUG_WARN(fmt, ...)  ((void)0)
    #define DEBUG_ERROR(fmt, ...) ((void)0)
    #define DEBUG_PRINT_BANNER()  ((void)0)
#endif
#else
    #define DEBUG_PRINT(fmt, ...) ((void)0)
    #define DEBUG_INFO(fmt, ...)  ((void)0)
    #define DEBUG_WARN(fmt, ...)  ((void)0)
    #define DEBUG_ERROR(fmt, ...) ((void)0)
    #define DEBUG_PRINT_BANNER()  ((void)0)
#endif

/* Exported functions prototypes ---------------------------------------------*/

/**
 * @brief Initialize debug print module
 * @retval true if initialization successful
 * @note This function is optional, debug printing works without explicit init
 */
bool Debug_Init(void);

/**
 * @brief Print formatted debug message
 * @param level Debug level (INFO, WARN, ERROR)
 * @param fmt Format string (printf-style)
 * @param ... Variable arguments
 * @retval true if print successful
 */
bool Debug_Printf(Debug_Level_t level, const char* fmt, ...);

/**
 * @brief Print raw string without formatting
 * @param str String to print
 * @retval true if print successful
 */
bool Debug_Print_Raw(const char* str);

/**
 * @brief Print buffer in hexadecimal format
 * @param data Pointer to data buffer
 * @param len Length of data
 * @param label Optional label to print before hex dump
 * @retval true if print successful
 */
bool Debug_Print_Hex(const uint8_t* data, uint16_t len, const char* label);

/**
 * @brief Print system information banner
 * @retval true if print successful
 */
bool Debug_Print_Banner(void);

#ifdef __cplusplus
}
#endif

#endif /* __DEBUG_PRINT_H */
