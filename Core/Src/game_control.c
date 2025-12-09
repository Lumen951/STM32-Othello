/**
 * @file game_control.c
 * @brief Game Control State Machine Implementation
 * @version 1.0
 * @date 2025-12-09
 *
 * @details
 * This implements a state machine for game control:
 * - IDLE → PLAYING (Start)
 * - PLAYING → PAUSED (Pause)
 * - PAUSED → PLAYING (Resume)
 * - PLAYING/PAUSED → ENDED (End)
 * - ANY → IDLE (Reset)
 */

/* Includes ------------------------------------------------------------------*/
#include "game_control.h"
#include "keypad_mapping.h"
#include <string.h>

/* Private typedef -----------------------------------------------------------*/

/* Private define ------------------------------------------------------------*/

/* Private variables ---------------------------------------------------------*/
static Game_Control_Context_t game_ctrl_ctx = {0};

/* Private function prototypes -----------------------------------------------*/
static void Game_Control_EnterState(Game_Control_State_t new_state);
static void Game_Control_SendStateUpdate(void);

/* Exported functions --------------------------------------------------------*/

/**
 * @brief Initialize game control module
 */
Game_Control_Status_t Game_Control_Init(void)
{
    if (game_ctrl_ctx.initialized) {
        return GAME_CTRL_OK;
    }

    // Initialize context
    memset(&game_ctrl_ctx, 0, sizeof(Game_Control_Context_t));
    game_ctrl_ctx.state = GAME_CTRL_STATE_IDLE;
    game_ctrl_ctx.prev_state = GAME_CTRL_STATE_IDLE;
    game_ctrl_ctx.state_enter_time = HAL_GetTick();
    game_ctrl_ctx.initialized = true;

    return GAME_CTRL_OK;
}

/**
 * @brief Deinitialize game control module
 */
Game_Control_Status_t Game_Control_DeInit(void)
{
    if (!game_ctrl_ctx.initialized) {
        return GAME_CTRL_ERROR;
    }

    memset(&game_ctrl_ctx, 0, sizeof(Game_Control_Context_t));
    return GAME_CTRL_OK;
}

/**
 * @brief Start new game
 */
Game_Control_Status_t Game_Control_Start(GameState_t* game_state)
{
    if (!game_ctrl_ctx.initialized || !game_state) {
        return GAME_CTRL_ERROR;
    }

    // Can only start from IDLE or ENDED state
    if (game_ctrl_ctx.state != GAME_CTRL_STATE_IDLE &&
        game_ctrl_ctx.state != GAME_CTRL_STATE_ENDED) {
        return GAME_CTRL_INVALID_STATE;
    }

    // Initialize new game
    Othello_NewGame(game_state);

    // Reset pause time tracking
    game_ctrl_ctx.total_pause_time = 0;
    game_ctrl_ctx.pause_start_time = 0;

    // Enter PLAYING state
    Game_Control_EnterState(GAME_CTRL_STATE_PLAYING);

    // Send state update via protocol
    Game_Control_SendStateUpdate();

    return GAME_CTRL_OK;
}

/**
 * @brief Pause game
 */
Game_Control_Status_t Game_Control_Pause(void)
{
    if (!game_ctrl_ctx.initialized) {
        return GAME_CTRL_ERROR;
    }

    // Can only pause from PLAYING state
    if (game_ctrl_ctx.state != GAME_CTRL_STATE_PLAYING) {
        return GAME_CTRL_INVALID_STATE;
    }

    // Record pause start time
    game_ctrl_ctx.pause_start_time = HAL_GetTick();

    // Enter PAUSED state
    Game_Control_EnterState(GAME_CTRL_STATE_PAUSED);

    // Send state update via protocol
    Game_Control_SendStateUpdate();

    return GAME_CTRL_OK;
}

/**
 * @brief Resume game
 */
Game_Control_Status_t Game_Control_Resume(void)
{
    if (!game_ctrl_ctx.initialized) {
        return GAME_CTRL_ERROR;
    }

    // Can only resume from PAUSED state
    if (game_ctrl_ctx.state != GAME_CTRL_STATE_PAUSED) {
        return GAME_CTRL_INVALID_STATE;
    }

    // Calculate pause duration and add to total
    uint32_t pause_duration = HAL_GetTick() - game_ctrl_ctx.pause_start_time;
    game_ctrl_ctx.total_pause_time += pause_duration;
    game_ctrl_ctx.pause_start_time = 0;

    // Enter PLAYING state
    Game_Control_EnterState(GAME_CTRL_STATE_PLAYING);

    // Send state update via protocol
    Game_Control_SendStateUpdate();

    return GAME_CTRL_OK;
}

/**
 * @brief End game
 */
Game_Control_Status_t Game_Control_End(GameState_t* game_state)
{
    if (!game_ctrl_ctx.initialized || !game_state) {
        return GAME_CTRL_ERROR;
    }

    // Can end from PLAYING or PAUSED state
    if (game_ctrl_ctx.state != GAME_CTRL_STATE_PLAYING &&
        game_ctrl_ctx.state != GAME_CTRL_STATE_PAUSED) {
        return GAME_CTRL_INVALID_STATE;
    }

    // If paused, finalize pause time
    if (game_ctrl_ctx.state == GAME_CTRL_STATE_PAUSED) {
        uint32_t pause_duration = HAL_GetTick() - game_ctrl_ctx.pause_start_time;
        game_ctrl_ctx.total_pause_time += pause_duration;
        game_ctrl_ctx.pause_start_time = 0;
    }

    // Mark game as ended
    if (game_state->status == GAME_STATUS_PLAYING) {
        // Force game over if still playing
        game_state->status = GAME_STATUS_DRAW;
    }

    // Enter ENDED state
    Game_Control_EnterState(GAME_CTRL_STATE_ENDED);

    // Send state update via protocol
    Game_Control_SendStateUpdate();

    return GAME_CTRL_OK;
}

/**
 * @brief Reset game (return to idle state)
 */
Game_Control_Status_t Game_Control_Reset(GameState_t* game_state)
{
    if (!game_ctrl_ctx.initialized || !game_state) {
        return GAME_CTRL_ERROR;
    }

    // Can reset from any state
    // Reset game state
    Othello_ResetState(game_state);

    // Reset pause time tracking
    game_ctrl_ctx.total_pause_time = 0;
    game_ctrl_ctx.pause_start_time = 0;

    // Enter IDLE state
    Game_Control_EnterState(GAME_CTRL_STATE_IDLE);

    // Send state update via protocol
    Game_Control_SendStateUpdate();

    return GAME_CTRL_OK;
}

/**
 * @brief Handle game control action
 */
Game_Control_Status_t Game_Control_HandleAction(Game_Control_Action_t action, GameState_t* game_state)
{
    if (!game_ctrl_ctx.initialized || !game_state) {
        return GAME_CTRL_ERROR;
    }

    Game_Control_Status_t status = GAME_CTRL_OK;

    switch (action) {
        case GAME_ACTION_START:
            status = Game_Control_Start(game_state);
            break;

        case GAME_ACTION_PAUSE:
            status = Game_Control_Pause();
            break;

        case GAME_ACTION_RESUME:
            status = Game_Control_Resume();
            break;

        case GAME_ACTION_END:
            status = Game_Control_End(game_state);
            break;

        case GAME_ACTION_RESET:
            status = Game_Control_Reset(game_state);
            break;

        default:
            status = GAME_CTRL_INVALID_ACTION;
            break;
    }

    return status;
}

/**
 * @brief Handle keypad input for game control
 */
bool Game_Control_HandleKey(Keypad_LogicalKey_t key, GameState_t* game_state)
{
    if (!game_ctrl_ctx.initialized || !game_state) {
        return false;
    }

    Game_Control_Status_t status = GAME_CTRL_OK;
    bool handled = true;

    switch (key) {
        case GAME_CTRL_KEY_START:  // Key '1'
            status = Game_Control_Start(game_state);
            break;

        case GAME_CTRL_KEY_PAUSE:  // Key '*'
            status = Game_Control_Pause();
            break;

        case GAME_CTRL_KEY_RESUME: // Key '#'
            status = Game_Control_Resume();
            break;

        case GAME_CTRL_KEY_END:    // Key 'D'
            status = Game_Control_End(game_state);
            break;

        case GAME_CTRL_KEY_RESET:  // Key '0'
            status = Game_Control_Reset(game_state);
            break;

        default:
            handled = false;
            break;
    }

    // If action failed due to invalid state, still consider key as handled
    // to prevent it from being processed by other handlers
    if (status == GAME_CTRL_INVALID_STATE) {
        handled = true;
    }

    return handled;
}

/**
 * @brief Get current game control state
 */
Game_Control_State_t Game_Control_GetState(void)
{
    return game_ctrl_ctx.state;
}

/**
 * @brief Get game control context
 */
const Game_Control_Context_t* Game_Control_GetContext(void)
{
    return &game_ctrl_ctx;
}

/**
 * @brief Get time in current state (milliseconds)
 */
uint32_t Game_Control_GetTimeInState(void)
{
    if (!game_ctrl_ctx.initialized) {
        return 0;
    }

    return HAL_GetTick() - game_ctrl_ctx.state_enter_time;
}

/**
 * @brief Get total pause time (milliseconds)
 */
uint32_t Game_Control_GetTotalPauseTime(void)
{
    uint32_t total = game_ctrl_ctx.total_pause_time;

    // If currently paused, add current pause duration
    if (game_ctrl_ctx.state == GAME_CTRL_STATE_PAUSED) {
        total += (HAL_GetTick() - game_ctrl_ctx.pause_start_time);
    }

    return total;
}

/**
 * @brief Get effective game time (excluding pause time)
 */
uint32_t Game_Control_GetEffectiveGameTime(const GameState_t* game_state)
{
    if (!game_state) {
        return 0;
    }

    // Get total game time
    uint32_t total_time = Othello_GetGameDuration(game_state);

    // Subtract pause time
    uint32_t pause_time_sec = Game_Control_GetTotalPauseTime() / 1000;

    if (total_time > pause_time_sec) {
        return total_time - pause_time_sec;
    }

    return 0;
}

/**
 * @brief Check if action is valid in current state
 */
bool Game_Control_IsActionValid(Game_Control_Action_t action)
{
    if (!game_ctrl_ctx.initialized) {
        return false;
    }

    switch (action) {
        case GAME_ACTION_START:
            return (game_ctrl_ctx.state == GAME_CTRL_STATE_IDLE ||
                    game_ctrl_ctx.state == GAME_CTRL_STATE_ENDED);

        case GAME_ACTION_PAUSE:
            return (game_ctrl_ctx.state == GAME_CTRL_STATE_PLAYING);

        case GAME_ACTION_RESUME:
            return (game_ctrl_ctx.state == GAME_CTRL_STATE_PAUSED);

        case GAME_ACTION_END:
            return (game_ctrl_ctx.state == GAME_CTRL_STATE_PLAYING ||
                    game_ctrl_ctx.state == GAME_CTRL_STATE_PAUSED);

        case GAME_ACTION_RESET:
            return true;  // Can reset from any state

        default:
            return false;
    }
}

/**
 * @brief Get state name string (for debugging)
 */
const char* Game_Control_GetStateName(Game_Control_State_t state)
{
    switch (state) {
        case GAME_CTRL_STATE_IDLE:    return "IDLE";
        case GAME_CTRL_STATE_PLAYING: return "PLAYING";
        case GAME_CTRL_STATE_PAUSED:  return "PAUSED";
        case GAME_CTRL_STATE_ENDED:   return "ENDED";
        default:                      return "UNKNOWN";
    }
}

/* Private functions ---------------------------------------------------------*/

/**
 * @brief Enter new state (internal state transition)
 */
static void Game_Control_EnterState(Game_Control_State_t new_state)
{
    game_ctrl_ctx.prev_state = game_ctrl_ctx.state;
    game_ctrl_ctx.state = new_state;
    game_ctrl_ctx.state_enter_time = HAL_GetTick();
}

/**
 * @brief Send state update via protocol
 */
static void Game_Control_SendStateUpdate(void)
{
    // Send game control state as debug message
    // In future, can define a dedicated protocol command for state updates
    char msg[64];
    snprintf(msg, sizeof(msg), "Game State: %s", Game_Control_GetStateName(game_ctrl_ctx.state));
    Protocol_SendDebugMessage(msg);
}
