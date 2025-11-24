/**
 * @file uart_protocol.h
 * @brief UART Communication Protocol for STM32 Othello Game
 * @version 1.0
 * @date 2025-11-22
 *
 * @note This protocol enables communication between STM32 and PC for:
 *       - Game state synchronization
 *       - Command transmission
 *       - Data logging and analysis
 *       UART: 115200 baud, 8N1, interrupt-driven reception
 */

#ifndef __UART_PROTOCOL_H
#define __UART_PROTOCOL_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "stm32f1xx_hal.h"
#include <stdint.h>
#include <stdbool.h>

/* Exported types ------------------------------------------------------------*/

/**
 * @brief Protocol status enumeration
 */
typedef enum {
    PROTOCOL_OK = 0,
    PROTOCOL_ERROR,
    PROTOCOL_BUSY,
    PROTOCOL_TIMEOUT,
    PROTOCOL_CHECKSUM_ERROR,
    PROTOCOL_BUFFER_FULL,
    PROTOCOL_INVALID_LENGTH
} Protocol_Status_t;

/**
 * @brief Protocol command enumeration
 */
typedef enum {
    CMD_BOARD_STATE     = 0x01,     ///< Send board state to PC
    CMD_MAKE_MOVE      = 0x02,     ///< Receive move command from PC
    CMD_GAME_CONFIG    = 0x03,     ///< Game configuration
    CMD_GAME_STATS     = 0x04,     ///< Game statistics
    CMD_SYSTEM_INFO    = 0x05,     ///< System information
    CMD_AI_REQUEST     = 0x06,     ///< AI analysis request
    CMD_HEARTBEAT      = 0x07,     ///< Heartbeat packet
    CMD_ACK            = 0x08,     ///< Acknowledgment
    CMD_DEBUG_INFO     = 0x09,     ///< Debug information
    CMD_KEY_EVENT      = 0x0A,     ///< Keypad event
    CMD_LED_CONTROL    = 0x0B,     ///< LED control command
    CMD_ERROR          = 0xFF      ///< Error response
} Protocol_Command_t;

/**
 * @brief Packet reception state
 */
typedef enum {
    PACKET_STATE_WAIT_STX = 0,
    PACKET_STATE_WAIT_CMD,
    PACKET_STATE_WAIT_LEN,
    PACKET_STATE_WAIT_DATA,
    PACKET_STATE_WAIT_CHK,
    PACKET_STATE_WAIT_ETX,
    PACKET_STATE_COMPLETE
} Packet_State_t;

/**
 * @brief Protocol packet structure
 */
typedef struct {
    uint8_t stx;                    ///< Start marker (0x02)
    uint8_t cmd;                    ///< Command byte
    uint8_t len;                    ///< Data length (0-255)
    uint8_t data[256];              ///< Data payload
    uint8_t checksum;               ///< XOR checksum
    uint8_t etx;                    ///< End marker (0x03)
} Protocol_Packet_t;

/**
 * @brief Packet reception buffer
 */
typedef struct {
    Protocol_Packet_t packet;       ///< Current packet being received
    Packet_State_t state;           ///< Current reception state
    uint8_t data_index;             ///< Current data index
    uint32_t timeout_timer;         ///< Timeout timer
    bool packet_ready;              ///< Packet ready flag
} Packet_Buffer_t;

/**
 * @brief Protocol statistics
 */
typedef struct {
    uint32_t packets_sent;          ///< Total packets sent
    uint32_t packets_received;      ///< Total packets received
    uint32_t checksum_errors;       ///< Checksum error count
    uint32_t timeout_errors;        ///< Timeout error count
    uint32_t buffer_overruns;       ///< Buffer overrun count
} Protocol_Stats_t;

/**
 * @brief Game state data structure (for CMD_BOARD_STATE)
 */
typedef struct {
    uint8_t board[8][8];            ///< Board state (0=empty, 1=black, 2=white)
    uint8_t current_player;         ///< Current player (1=black, 2=white)
    uint8_t black_count;            ///< Black pieces count
    uint8_t white_count;            ///< White pieces count
    uint8_t game_over;              ///< Game over flag
    uint32_t move_count;            ///< Total moves made
} Game_State_Data_t;

/**
 * @brief Move command data structure (for CMD_MAKE_MOVE)
 */
typedef struct {
    uint8_t row;                    ///< Move row (0-7)
    uint8_t col;                    ///< Move column (0-7)
    uint8_t player;                 ///< Player making move (1=black, 2=white)
    uint32_t timestamp;             ///< Move timestamp
} Move_Command_Data_t;

/**
 * @brief Key event data structure (for CMD_KEY_EVENT)
 */
typedef struct {
    uint8_t row;                    ///< Key row (0-3)
    uint8_t col;                    ///< Key column (0-3)
    uint8_t state;                  ///< Key state (0=released, 1=pressed, 2=long_pressed)
    uint8_t logical_key;            ///< Logical key code
    uint32_t timestamp;             ///< Event timestamp
} Key_Event_Data_t;

/**
 * @brief System info data structure (for CMD_SYSTEM_INFO)
 */
typedef struct {
    uint32_t uptime;                ///< System uptime in seconds
    uint8_t firmware_version[4];    ///< Firmware version [major, minor, patch, build]
    uint32_t free_memory;           ///< Free memory in bytes
    uint8_t cpu_usage;              ///< CPU usage percentage
    uint16_t keypad_scans;          ///< Keypad scans per second
    uint16_t led_updates;           ///< LED updates per second
} System_Info_Data_t;

/**
 * @brief Protocol callback function type
 */
typedef void (*Protocol_Callback_t)(Protocol_Command_t cmd, uint8_t* data, uint8_t len);

/* Exported constants --------------------------------------------------------*/

/** @defgroup Protocol_Constants Protocol Constants
 * @{
 */
#define PROTOCOL_STX                0x02        ///< Start marker
#define PROTOCOL_ETX                0x03        ///< End marker
#define PROTOCOL_MAX_DATA_LEN       255         ///< Maximum data length
#define PROTOCOL_TIMEOUT_MS         1000        ///< Packet timeout in milliseconds
#define PROTOCOL_TX_BUFFER_SIZE     512         ///< Transmission buffer size
#define PROTOCOL_RX_BUFFER_SIZE     512         ///< Reception buffer size
/**
 * @}
 */

/* Exported macro ------------------------------------------------------------*/

/**
 * @brief Calculate packet checksum (XOR of CMD + LEN + DATA)
 * @param packet Pointer to packet structure
 * @retval uint8_t Calculated checksum
 */
#define PROTOCOL_CALCULATE_CHECKSUM(packet) \
    ({ uint8_t chk = (packet)->cmd ^ (packet)->len; \
       for (int i = 0; i < (packet)->len; i++) chk ^= (packet)->data[i]; \
       chk; })

/**
 * @brief Check if packet checksum is valid
 * @param packet Pointer to packet structure
 * @retval bool true if checksum is valid
 */
#define PROTOCOL_VERIFY_CHECKSUM(packet) \
    (PROTOCOL_CALCULATE_CHECKSUM(packet) == (packet)->checksum)

/* Exported variables --------------------------------------------------------*/
extern UART_HandleTypeDef huart1;  ///< UART handle (defined in main.c)

/* Exported functions prototypes ---------------------------------------------*/

/**
 * @brief Initialize UART protocol
 * @retval Protocol_Status_t Initialization status
 */
Protocol_Status_t Protocol_Init(void);

/**
 * @brief Deinitialize UART protocol
 * @retval Protocol_Status_t Deinitialization status
 */
Protocol_Status_t Protocol_DeInit(void);

/**
 * @brief Send packet over UART
 * @param cmd Command to send
 * @param data Pointer to data buffer
 * @param len Data length (0-255)
 * @retval Protocol_Status_t Send status
 */
Protocol_Status_t Protocol_SendPacket(Protocol_Command_t cmd, uint8_t* data, uint8_t len);

/**
 * @brief Process received UART byte
 * @param byte Received byte
 * @retval Protocol_Status_t Processing status
 * @note Call this from UART RX interrupt handler
 */
Protocol_Status_t Protocol_ProcessByte(uint8_t byte);

/**
 * @brief Check if packet is ready for processing
 * @retval bool true if packet is ready
 */
bool Protocol_IsPacketReady(void);

/**
 * @brief Get received packet
 * @param cmd Pointer to store command
 * @param data Pointer to store data buffer
 * @param len Pointer to store data length
 * @retval Protocol_Status_t Status of operation
 * @note Packet must be ready (check with Protocol_IsPacketReady)
 */
Protocol_Status_t Protocol_GetPacket(Protocol_Command_t* cmd, uint8_t* data, uint8_t* len);

/**
 * @brief Register callback for received packets
 * @param callback Function to call when packet is received
 * @retval Protocol_Status_t Registration status
 */
Protocol_Status_t Protocol_RegisterCallback(Protocol_Callback_t callback);

/**
 * @brief Send acknowledgment packet
 * @param original_cmd Command being acknowledged
 * @param status Status code (0=OK, non-zero=error)
 * @retval Protocol_Status_t Send status
 */
Protocol_Status_t Protocol_SendAck(Protocol_Command_t original_cmd, uint8_t status);

/**
 * @brief Send error packet
 * @param error_code Error code
 * @param error_data Additional error data
 * @param error_len Length of error data
 * @retval Protocol_Status_t Send status
 */
Protocol_Status_t Protocol_SendError(uint8_t error_code, uint8_t* error_data, uint8_t error_len);

/**
 * @brief Send heartbeat packet
 * @retval Protocol_Status_t Send status
 */
Protocol_Status_t Protocol_SendHeartbeat(void);

/**
 * @brief Get protocol statistics
 * @param stats Pointer to statistics structure
 * @retval Protocol_Status_t Status of operation
 */
Protocol_Status_t Protocol_GetStatistics(Protocol_Stats_t* stats);

/**
 * @brief Reset protocol statistics
 * @retval Protocol_Status_t Status of operation
 */
Protocol_Status_t Protocol_ResetStatistics(void);

/**
 * @brief Process protocol timeouts and maintenance
 * @retval None
 * @note Call this periodically (e.g., every 10ms)
 */
void Protocol_Task(void);

/* High-level convenience functions ------------------------------------------*/

/**
 * @brief Send current game state
 * @param game_state Pointer to game state structure
 * @retval Protocol_Status_t Send status
 */
Protocol_Status_t Protocol_SendGameState(const Game_State_Data_t* game_state);

/**
 * @brief Send key event
 * @param row Key row (0-3)
 * @param col Key column (0-3)
 * @param state Key state
 * @param logical_key Logical key code
 * @retval Protocol_Status_t Send status
 */
Protocol_Status_t Protocol_SendKeyEvent(uint8_t row, uint8_t col, uint8_t state, uint8_t logical_key);

/**
 * @brief Send system information
 * @retval Protocol_Status_t Send status
 */
Protocol_Status_t Protocol_SendSystemInfo(void);

/**
 * @brief Send debug message
 * @param message Debug message string
 * @retval Protocol_Status_t Send status
 */
Protocol_Status_t Protocol_SendDebugMessage(const char* message);

/**
 * @brief UART RX interrupt callback (call from HAL_UART_RxCpltCallback)
 * @param huart UART handle
 * @retval None
 */
void Protocol_UART_RxCallback(UART_HandleTypeDef *huart);

/**
 * @brief Protocol command handler (application callback)
 * @param cmd Received command
 * @param data Command data
 * @param len Data length
 * @retval None
 * @note This function is implemented in main.c and called by protocol handler
 */
void Protocol_Command_Handler(Protocol_Command_t cmd, uint8_t* data, uint8_t len);

#ifdef __cplusplus
}
#endif

#endif /* __UART_PROTOCOL_H */