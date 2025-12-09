/**
 * @file uart_protocol.c
 * @brief UART Communication Protocol Implementation
 * @version 1.0
 * @date 2025-11-22
 *
 * @details
 * This implements a robust packet-based communication protocol:
 * - Interrupt-driven reception
 * - XOR checksum verification
 * - Timeout handling
 * - Circular buffer management
 * - High-level convenience functions
 */

/* Includes ------------------------------------------------------------------*/
#include "uart_protocol.h"
#include <string.h>
#include <stdio.h>

/* Private typedef -----------------------------------------------------------*/

/**
 * @brief Protocol driver state
 */
typedef struct {
    Packet_Buffer_t rx_buffer;          ///< Reception buffer
    uint8_t tx_buffer[PROTOCOL_TX_BUFFER_SIZE]; ///< Transmission buffer
    uint16_t tx_head, tx_tail;          ///< TX buffer pointers
    bool tx_busy;                       ///< Transmission busy flag
    Protocol_Callback_t callback;      ///< User callback function
    Protocol_Stats_t stats;             ///< Protocol statistics
    uint32_t last_heartbeat;            ///< Last heartbeat timestamp
    bool initialized;                   ///< Initialization flag
    uint8_t rx_byte;                    ///< Single byte RX buffer for interrupt
} Protocol_State_t;

/* Private define ------------------------------------------------------------*/
#define PROTOCOL_HEARTBEAT_INTERVAL_MS  5000    ///< Heartbeat interval
#define FIRMWARE_VERSION_MAJOR          1       ///< Major version
#define FIRMWARE_VERSION_MINOR          0       ///< Minor version
#define FIRMWARE_VERSION_PATCH          0       ///< Patch version
#define FIRMWARE_VERSION_BUILD          1       ///< Build number

/* Private variables ---------------------------------------------------------*/
static Protocol_State_t protocol_state = {0};

/* Private function prototypes -----------------------------------------------*/
static void Protocol_ResetRxBuffer(void);
static uint8_t Protocol_CalculateChecksum(const Protocol_Packet_t* packet);
static Protocol_Status_t Protocol_TransmitBytes(uint8_t* data, uint16_t len);
static void Protocol_HandleCompletePacket(void);
static uint32_t Protocol_GetFreeMemory(void);
static uint8_t Protocol_GetCpuUsage(void);

/* Exported functions --------------------------------------------------------*/

/**
 * @brief Initialize UART protocol
 */
Protocol_Status_t Protocol_Init(void)
{
    if (protocol_state.initialized) {
        return PROTOCOL_OK;
    }

    // Initialize protocol state
    memset(&protocol_state, 0, sizeof(Protocol_State_t));

    // Reset RX buffer
    Protocol_ResetRxBuffer();

    // Start UART reception in interrupt mode
    if (HAL_UART_Receive_IT(&huart1, &protocol_state.rx_byte, 1) != HAL_OK) {
        return PROTOCOL_ERROR;
    }

    protocol_state.last_heartbeat = HAL_GetTick();
    protocol_state.initialized = true;

    return PROTOCOL_OK;
}

/**
 * @brief Deinitialize UART protocol
 */
Protocol_Status_t Protocol_DeInit(void)
{
    if (!protocol_state.initialized) {
        return PROTOCOL_ERROR;
    }

    // Stop UART reception
    HAL_UART_AbortReceive_IT(&huart1);

    // Clear state
    memset(&protocol_state, 0, sizeof(Protocol_State_t));

    return PROTOCOL_OK;
}

/**
 * @brief Send packet over UART
 */
Protocol_Status_t Protocol_SendPacket(Protocol_Command_t cmd, uint8_t* data, uint8_t len)
{
    if (!protocol_state.initialized || len > PROTOCOL_MAX_DATA_LEN) {
        return PROTOCOL_ERROR;
    }

    Protocol_Packet_t packet;
    uint8_t tx_data[PROTOCOL_MAX_DATA_LEN + 6]; // STX + CMD + LEN + DATA + CHK + ETX
    uint16_t tx_len = 0;

    // Build packet
    packet.stx = PROTOCOL_STX;
    packet.cmd = cmd;
    packet.len = len;
    if (data && len > 0) {
        memcpy(packet.data, data, len);
    }
    packet.checksum = Protocol_CalculateChecksum(&packet);
    packet.etx = PROTOCOL_ETX;

    // Serialize packet
    tx_data[tx_len++] = packet.stx;
    tx_data[tx_len++] = packet.cmd;
    tx_data[tx_len++] = packet.len;

    if (len > 0) {
        memcpy(&tx_data[tx_len], packet.data, len);
        tx_len += len;
    }

    tx_data[tx_len++] = packet.checksum;
    tx_data[tx_len++] = packet.etx;

    // Transmit
    Protocol_Status_t status = Protocol_TransmitBytes(tx_data, tx_len);
    if (status == PROTOCOL_OK) {
        protocol_state.stats.packets_sent++;
    }

    return status;
}

/**
 * @brief Process received UART byte
 */
Protocol_Status_t Protocol_ProcessByte(uint8_t byte)
{
    if (!protocol_state.initialized) {
        return PROTOCOL_ERROR;
    }

    Packet_Buffer_t* buf = &protocol_state.rx_buffer;
    uint32_t current_time = HAL_GetTick();

    // Check for timeout
    if (buf->state != PACKET_STATE_WAIT_STX &&
        (current_time - buf->timeout_timer) > PROTOCOL_TIMEOUT_MS) {
        Protocol_ResetRxBuffer();
        protocol_state.stats.timeout_errors++;
    }

    switch (buf->state) {
        case PACKET_STATE_WAIT_STX:
            if (byte == PROTOCOL_STX) {
                buf->packet.stx = byte;
                buf->state = PACKET_STATE_WAIT_CMD;
                buf->timeout_timer = current_time;
            }
            break;

        case PACKET_STATE_WAIT_CMD:
            buf->packet.cmd = byte;
            buf->state = PACKET_STATE_WAIT_LEN;
            break;

        case PACKET_STATE_WAIT_LEN:
            buf->packet.len = byte;
            buf->data_index = 0;
            if (byte > 0) {
                buf->state = PACKET_STATE_WAIT_DATA;
            } else {
                buf->state = PACKET_STATE_WAIT_CHK;
            }
            break;

        case PACKET_STATE_WAIT_DATA:
            if (buf->data_index < buf->packet.len) {
                buf->packet.data[buf->data_index++] = byte;
                if (buf->data_index >= buf->packet.len) {
                    buf->state = PACKET_STATE_WAIT_CHK;
                }
            } else {
                // Data overflow
                Protocol_ResetRxBuffer();
                protocol_state.stats.buffer_overruns++;
            }
            break;

        case PACKET_STATE_WAIT_CHK:
            buf->packet.checksum = byte;
            buf->state = PACKET_STATE_WAIT_ETX;
            break;

        case PACKET_STATE_WAIT_ETX:
            if (byte == PROTOCOL_ETX) {
                buf->packet.etx = byte;
                buf->state = PACKET_STATE_COMPLETE;

                // Verify checksum
                uint8_t calc_checksum = Protocol_CalculateChecksum(&buf->packet);
                if (calc_checksum == buf->packet.checksum) {
                    buf->packet_ready = true;
                    protocol_state.stats.packets_received++;
                    Protocol_HandleCompletePacket();
                } else {
                    protocol_state.stats.checksum_errors++;
                    Protocol_ResetRxBuffer();
                }
            } else {
                // Invalid ETX
                Protocol_ResetRxBuffer();
            }
            break;

        default:
            Protocol_ResetRxBuffer();
            break;
    }

    return PROTOCOL_OK;
}

/**
 * @brief Check if packet is ready for processing
 */
bool Protocol_IsPacketReady(void)
{
    return protocol_state.initialized && protocol_state.rx_buffer.packet_ready;
}

/**
 * @brief Get received packet
 */
Protocol_Status_t Protocol_GetPacket(Protocol_Command_t* cmd, uint8_t* data, uint8_t* len)
{
    if (!protocol_state.initialized || !Protocol_IsPacketReady() ||
        !cmd || !data || !len) {
        return PROTOCOL_ERROR;
    }

    Packet_Buffer_t* buf = &protocol_state.rx_buffer;

    *cmd = (Protocol_Command_t)buf->packet.cmd;
    *len = buf->packet.len;

    if (*len > 0) {
        memcpy(data, buf->packet.data, *len);
    }

    // Reset buffer for next packet
    Protocol_ResetRxBuffer();

    return PROTOCOL_OK;
}

/**
 * @brief Register callback for received packets
 */
Protocol_Status_t Protocol_RegisterCallback(Protocol_Callback_t callback)
{
    if (!protocol_state.initialized) {
        return PROTOCOL_ERROR;
    }

    protocol_state.callback = callback;
    return PROTOCOL_OK;
}

/**
 * @brief Send acknowledgment packet
 */
Protocol_Status_t Protocol_SendAck(Protocol_Command_t original_cmd, uint8_t status)
{
    uint8_t ack_data[2] = {original_cmd, status};
    return Protocol_SendPacket(CMD_ACK, ack_data, sizeof(ack_data));
}

/**
 * @brief Send error packet
 */
Protocol_Status_t Protocol_SendError(uint8_t error_code, uint8_t* error_data, uint8_t error_len)
{
    uint8_t err_packet[256];
    err_packet[0] = error_code;

    if (error_data && error_len > 0 && error_len < 255) {
        memcpy(&err_packet[1], error_data, error_len);
        error_len += 1;
    } else {
        error_len = 1;
    }

    return Protocol_SendPacket(CMD_ERROR, err_packet, error_len);
}

/**
 * @brief Send heartbeat packet
 */
Protocol_Status_t Protocol_SendHeartbeat(void)
{
    uint32_t uptime = HAL_GetTick() / 1000; // Convert to seconds
    return Protocol_SendPacket(CMD_HEARTBEAT, (uint8_t*)&uptime, sizeof(uptime));
}

/**
 * @brief Get protocol statistics
 */
Protocol_Status_t Protocol_GetStatistics(Protocol_Stats_t* stats)
{
    if (!protocol_state.initialized || !stats) {
        return PROTOCOL_ERROR;
    }

    *stats = protocol_state.stats;
    return PROTOCOL_OK;
}

/**
 * @brief Reset protocol statistics
 */
Protocol_Status_t Protocol_ResetStatistics(void)
{
    if (!protocol_state.initialized) {
        return PROTOCOL_ERROR;
    }

    memset(&protocol_state.stats, 0, sizeof(Protocol_Stats_t));
    return PROTOCOL_OK;
}

/**
 * @brief Process protocol timeouts and maintenance
 */
void Protocol_Task(void)
{
    if (!protocol_state.initialized) {
        return;
    }

    uint32_t current_time = HAL_GetTick();

    // Send periodic heartbeat
    if ((current_time - protocol_state.last_heartbeat) >= PROTOCOL_HEARTBEAT_INTERVAL_MS) {
        Protocol_SendHeartbeat();
        protocol_state.last_heartbeat = current_time;
    }

    // Check for RX timeout
    Packet_Buffer_t* buf = &protocol_state.rx_buffer;
    if (buf->state != PACKET_STATE_WAIT_STX &&
        (current_time - buf->timeout_timer) > PROTOCOL_TIMEOUT_MS) {
        Protocol_ResetRxBuffer();
        protocol_state.stats.timeout_errors++;
    }
}

/* High-level convenience functions ------------------------------------------*/

/**
 * @brief Send current game state
 */
Protocol_Status_t Protocol_SendGameState(const Game_State_Data_t* game_state)
{
    if (!game_state) {
        return PROTOCOL_ERROR;
    }

    return Protocol_SendPacket(CMD_BOARD_STATE, (uint8_t*)game_state, sizeof(Game_State_Data_t));
}

/**
 * @brief Send key event
 */
Protocol_Status_t Protocol_SendKeyEvent(uint8_t row, uint8_t col, uint8_t state, uint8_t logical_key)
{
    Key_Event_Data_t key_event = {
        .row = row,
        .col = col,
        .state = state,
        .logical_key = logical_key,
        .timestamp = HAL_GetTick()
    };

    return Protocol_SendPacket(CMD_KEY_EVENT, (uint8_t*)&key_event, sizeof(Key_Event_Data_t));
}

/**
 * @brief Send system information
 */
Protocol_Status_t Protocol_SendSystemInfo(void)
{
    System_Info_Data_t sys_info = {
        .uptime = HAL_GetTick() / 1000,
        .firmware_version = {FIRMWARE_VERSION_MAJOR, FIRMWARE_VERSION_MINOR,
                           FIRMWARE_VERSION_PATCH, FIRMWARE_VERSION_BUILD},
        .free_memory = Protocol_GetFreeMemory(),
        .cpu_usage = Protocol_GetCpuUsage(),
        .keypad_scans = 200, // Approximate scans per second
        .led_updates = 30    // Approximate updates per second
    };

    return Protocol_SendPacket(CMD_SYSTEM_INFO, (uint8_t*)&sys_info, sizeof(System_Info_Data_t));
}

/**
 * @brief Send debug message
 */
Protocol_Status_t Protocol_SendDebugMessage(const char* message)
{
    if (!message) {
        return PROTOCOL_ERROR;
    }

    uint8_t len = strlen(message);
    if (len > PROTOCOL_MAX_DATA_LEN) {
        len = PROTOCOL_MAX_DATA_LEN;
    }

    return Protocol_SendPacket(CMD_DEBUG_INFO, (uint8_t*)message, len);
}

/**
 * @brief Send game control command
 */
Protocol_Status_t Protocol_SendGameControl(Game_Control_Action_t action)
{
    Game_Control_Data_t control_data = {
        .action = action,
        .timestamp = HAL_GetTick()
    };

    return Protocol_SendPacket(CMD_GAME_CONTROL, (uint8_t*)&control_data, sizeof(Game_Control_Data_t));
}

/**
 * @brief Send mode select command
 */
Protocol_Status_t Protocol_SendModeSelect(Game_Mode_t mode, uint16_t time_limit)
{
    Mode_Select_Data_t mode_data = {
        .mode = mode,
        .time_limit = time_limit
    };

    return Protocol_SendPacket(CMD_MODE_SELECT, (uint8_t*)&mode_data, sizeof(Mode_Select_Data_t));
}

/**
 * @brief Send score update
 */
Protocol_Status_t Protocol_SendScoreUpdate(uint8_t black_score, uint8_t white_score,
                                          uint16_t total_score, uint8_t game_result)
{
    Score_Update_Data_t score_data = {
        .black_score = black_score,
        .white_score = white_score,
        .total_score = total_score,
        .game_result = game_result
    };

    return Protocol_SendPacket(CMD_SCORE_UPDATE, (uint8_t*)&score_data, sizeof(Score_Update_Data_t));
}

/**
 * @brief Send timer update
 */
Protocol_Status_t Protocol_SendTimerUpdate(uint16_t remaining_time, uint8_t timer_state)
{
    Timer_Update_Data_t timer_data = {
        .remaining_time = remaining_time,
        .timer_state = timer_state
    };

    return Protocol_SendPacket(CMD_TIMER_UPDATE, (uint8_t*)&timer_data, sizeof(Timer_Update_Data_t));
}

/**
 * @brief UART RX interrupt callback
 */
void Protocol_UART_RxCallback(UART_HandleTypeDef *huart)
{
    if (huart == &huart1) {
        // Process the received byte
        Protocol_ProcessByte(protocol_state.rx_byte);

        // Restart reception for next byte
        HAL_UART_Receive_IT(&huart1, &protocol_state.rx_byte, 1);
    }
}

/* Private functions ---------------------------------------------------------*/

/**
 * @brief Reset reception buffer
 */
static void Protocol_ResetRxBuffer(void)
{
    Packet_Buffer_t* buf = &protocol_state.rx_buffer;
    memset(buf, 0, sizeof(Packet_Buffer_t));
    buf->state = PACKET_STATE_WAIT_STX;
}

/**
 * @brief Calculate packet checksum
 */
static uint8_t Protocol_CalculateChecksum(const Protocol_Packet_t* packet)
{
    uint8_t checksum = packet->cmd ^ packet->len;

    for (uint8_t i = 0; i < packet->len; i++) {
        checksum ^= packet->data[i];
    }

    return checksum;
}

/**
 * @brief Transmit bytes over UART
 */
static Protocol_Status_t Protocol_TransmitBytes(uint8_t* data, uint16_t len)
{
    if (!data || len == 0) {
        return PROTOCOL_ERROR;
    }

    // Use blocking transmission for simplicity
    // In production, consider using DMA or interrupt-driven TX
    HAL_StatusTypeDef status = HAL_UART_Transmit(&huart1, data, len, 1000);

    return (status == HAL_OK) ? PROTOCOL_OK : PROTOCOL_ERROR;
}

/**
 * @brief Handle complete packet reception
 */
static void Protocol_HandleCompletePacket(void)
{
    if (protocol_state.callback) {
        Packet_Buffer_t* buf = &protocol_state.rx_buffer;
        protocol_state.callback((Protocol_Command_t)buf->packet.cmd,
                              buf->packet.data,
                              buf->packet.len);
    }
}

/**
 * @brief Get approximate free memory (placeholder)
 */
static uint32_t Protocol_GetFreeMemory(void)
{
    // Simplified memory estimation
    // In production, implement proper heap monitoring
    return 1024; // Placeholder value
}

/**
 * @brief Get approximate CPU usage (placeholder)
 */
static uint8_t Protocol_GetCpuUsage(void)
{
    // Simplified CPU usage estimation
    // In production, implement proper CPU load monitoring
    return 25; // Placeholder value (25%)
}