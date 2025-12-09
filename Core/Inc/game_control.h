/**
 * @file game_control.h
 * @brief Game Control State Machine for STM32 Othello
 * @version 1.0
 * @date 2025-12-09
 *
 * @note This module manages game control states and actions:
 *       - Start/Pause/Resume/End/Reset game
 *       - Keypad control mapping (1=Start, *=Pause, #=Resume, D=End, 0=Reset)
 *       - Protocol command handling
 *       - State machine management
 */

#ifndef __GAME_CONTROL_H
#define __GAME_CONTROL_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "uart_protocol.h"
#include "othello_engine.h"
#include "keypad_mapping.h"
#include <stdint.h>
#include <stdbool.h>

/* Exported types ------------------------------------------------------------*/

/**
 * @brief Game control state enumeration
 */
typedef enum {
    GAME_CTRL_STATE_IDLE = 0,       ///< Game not started
    GAME_CTRL_STATE_PLAYING,        ///< Game in progress
    GAME_CTRL_STATE_PAUSED,         ///< Game paused
    GAME_CTRL_STATE_ENDED           ///< Game ended
} Game_Control_State_t;

/**
 * @brief Game control status enumeration
 */
typedef enum {
    GAME_CTRL_OK = 0,
    GAME_CTRL_ERROR,
    GAME_CTRL_INVALID_STATE,
    GAME_CTRL_INVALID_ACTION
} Game_Control_Status_t;

/**
 * @brief Game control context structure
 */
typedef struct {
    Game_Control_State_t state;     ///< Current control state
    Game_Control_State_t prev_state;///< Previous control state
    uint32_t state_enter_time;      ///< Time when entered current state
    uint32_t pause_start_time;      ///< Time when game was paused
    uint32_t total_pause_time;      ///< Total paused time in milliseconds
    bool initialized;               ///< Initialization flag
} Game_Control_Context_t;

/* Exported constants --------------------------------------------------------*/

/**
 * @brief Keypad mapping for game control
 */
#define GAME_CTRL_KEY_START         KEYPAD_KEY_1    ///< Key '1' = Start game
#define GAME_CTRL_KEY_PAUSE         KEYPAD_KEY_STAR ///< Key '*' = Pause game
#define GAME_CTRL_KEY_RESUME        KEYPAD_KEY_HASH ///< Key '#' = Resume game
#define GAME_CTRL_KEY_END           KEYPAD_KEY_D    ///< Key 'D' = End game
#define GAME_CTRL_KEY_RESET         KEYPAD_KEY_0    ///< Key '0' = Reset game

/* Exported macro ------------------------------------------------------------*/

/**
 * @brief Check if game is in playing state
 * @param ctx Pointer to game control context
 * @retval bool true if game is playing
 */
#define GAME_CTRL_IS_PLAYING(ctx) \
    ((ctx)->state == GAME_CTRL_STATE_PLAYING)

/**
 * @brief Check if game is paused
 * @param ctx Pointer to game control context
 * @retval bool true if game is paused
 */
#define GAME_CTRL_IS_PAUSED(ctx) \
    ((ctx)->state == GAME_CTRL_STATE_PAUSED)

/**
 * @brief Check if game is idle
 * @param ctx Pointer to game control context
 * @retval bool true if game is idle
 */
#define GAME_CTRL_IS_IDLE(ctx) \
    ((ctx)->state == GAME_CTRL_STATE_IDLE)

/**
 * @brief Check if game is ended
 * @param ctx Pointer to game control context
 * @retval bool true if game is ended
 */
#define GAME_CTRL_IS_ENDED(ctx) \
    ((ctx)->state == GAME_CTRL_STATE_ENDED)

/* Exported functions prototypes ---------------------------------------------*/

/**
 * @brief Initialize game control module
 * @retval Game_Control_Status_t Initialization status
 */
Game_Control_Status_t Game_Control_Init(void);

/**
 * @brief Deinitialize game control module
 * @retval Game_Control_Status_t Deinitialization status
 */
Game_Control_Status_t Game_Control_DeInit(void);

/**
 * @brief Start new game
 * @param game_state Pointer to game state structure
 * @retval Game_Control_Status_t Status of operation
 */
Game_Control_Status_t Game_Control_Start(GameState_t* game_state);

/**
 * @brief Pause game
 * @retval Game_Control_Status_t Status of operation
 */
Game_Control_Status_t Game_Control_Pause(void);

/**
 * @brief Resume game
 * @retval Game_Control_Status_t Status of operation
 */
Game_Control_Status_t Game_Control_Resume(void);

/**
 * @brief End game
 * @param game_state Pointer to game state structure
 * @retval Game_Control_Status_t Status of operation
 */
Game_Control_Status_t Game_Control_End(GameState_t* game_state);

/**
 * @brief Reset game (return to idle state)
 * @param game_state Pointer to game state structure
 * @retval Game_Control_Status_t Status of operation
 */
Game_Control_Status_t Game_Control_Reset(GameState_t* game_state);

/**
 * @brief Handle game control action
 * @param action Game control action (from protocol or keypad)
 * @param game_state Pointer to game state structure
 * @retval Game_Control_Status_t Status of operation
 */
Game_Control_Status_t Game_Control_HandleAction(Game_Control_Action_t action, GameState_t* game_state);

/**
 * @brief Handle keypad input for game control
 * @param key Logical key code
 * @param game_state Pointer to game state structure
 * @retval bool true if key was handled by game control
 */
bool Game_Control_HandleKey(Keypad_LogicalKey_t key, GameState_t* game_state);

/**
 * @brief Get current game control state
 * @retval Game_Control_State_t Current state
 */
Game_Control_State_t Game_Control_GetState(void);

/**
 * @brief Get game control context
 * @retval const Game_Control_Context_t* Pointer to context (read-only)
 */
const Game_Control_Context_t* Game_Control_GetContext(void);

/**
 * @brief Get time in current state (milliseconds)
 * @retval uint32_t Time in current state
 */
uint32_t Game_Control_GetTimeInState(void);

/**
 * @brief Get total pause time (milliseconds)
 * @retval uint32_t Total pause time
 */
uint32_t Game_Control_GetTotalPauseTime(void);

/**
 * @brief Get effective game time (excluding pause time)
 * @param game_state Pointer to game state structure
 * @retval uint32_t Effective game time in seconds
 */
uint32_t Game_Control_GetEffectiveGameTime(const GameState_t* game_state);

/**
 * @brief Check if action is valid in current state
 * @param action Game control action
 * @retval bool true if action is valid
 */
bool Game_Control_IsActionValid(Game_Control_Action_t action);

/**
 * @brief Get state name string (for debugging)
 * @param state Game control state
 * @retval const char* State name string
 */
const char* Game_Control_GetStateName(Game_Control_State_t state);

#ifdef __cplusplus
}
#endif

#endif /* __GAME_CONTROL_H */
