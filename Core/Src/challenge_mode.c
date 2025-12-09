/**
 * @file challenge_mode.c
 * @brief Challenge Mode Manager Implementation
 * @version 1.0
 * @date 2025-12-09
 */

/* Includes ------------------------------------------------------------------*/
#include "challenge_mode.h"
#include "led_text.h"
#include <string.h>

/* Private typedef -----------------------------------------------------------*/
/* Private define ------------------------------------------------------------*/
/* Private macro -------------------------------------------------------------*/
/* Private variables ---------------------------------------------------------*/

/**
 * @brief Challenge mode context (singleton)
 */
static Challenge_Context_t g_challenge_ctx = {0};

/* Private function prototypes -----------------------------------------------*/
static void Challenge_UpdateState(void);
static void Challenge_DisplayResult(Challenge_Status_t result);

/* Exported functions --------------------------------------------------------*/

/**
 * @brief Initialize challenge mode module
 */
Challenge_Status_t Challenge_Init(void)
{
    memset(&g_challenge_ctx, 0, sizeof(Challenge_Context_t));
    g_challenge_ctx.state = CHALLENGE_STATE_INACTIVE;
    g_challenge_ctx.initialized = true;

    return CHALLENGE_OK;
}

/**
 * @brief Start new challenge session
 */
Challenge_Status_t Challenge_Start(void)
{
    if (!g_challenge_ctx.initialized) {
        return CHALLENGE_ERROR;
    }

    // Reset all statistics
    g_challenge_ctx.state = CHALLENGE_STATE_ACTIVE;
    g_challenge_ctx.total_score = 0;
    g_challenge_ctx.consecutive_losses = 0;
    g_challenge_ctx.games_played = 0;
    g_challenge_ctx.games_won = 0;
    g_challenge_ctx.games_lost = 0;
    g_challenge_ctx.games_drawn = 0;
    g_challenge_ctx.start_time = HAL_GetTick();

    // Send initial status to PC
    Challenge_SendStatusUpdate();

    return CHALLENGE_OK;
}

/**
 * @brief End current challenge session
 */
Challenge_Status_t Challenge_End(void)
{
    if (!g_challenge_ctx.initialized) {
        return CHALLENGE_ERROR;
    }

    g_challenge_ctx.state = CHALLENGE_STATE_INACTIVE;

    // Send final status to PC
    Challenge_SendStatusUpdate();

    return CHALLENGE_OK;
}

/**
 * @brief Process game result and update challenge state
 */
Challenge_Status_t Challenge_ProcessGameResult(const GameState_t* game_state)
{
    if (!g_challenge_ctx.initialized || !game_state) {
        return CHALLENGE_ERROR;
    }

    if (g_challenge_ctx.state != CHALLENGE_STATE_ACTIVE) {
        return CHALLENGE_ERROR;
    }

    // Increment games played
    g_challenge_ctx.games_played++;

    // Determine game result (assuming player is BLACK)
    PieceType_t winner = Othello_GetWinner(game_state);
    uint8_t player_score = game_state->black_count;

    if (winner == PIECE_BLACK) {
        // Player won
        g_challenge_ctx.games_won++;
        g_challenge_ctx.consecutive_losses = 0;  // Reset consecutive losses
        g_challenge_ctx.total_score += player_score;
    } else if (winner == PIECE_WHITE) {
        // Player lost
        g_challenge_ctx.games_lost++;
        g_challenge_ctx.consecutive_losses++;
        // No score added for losses
    } else {
        // Draw
        g_challenge_ctx.games_drawn++;
        g_challenge_ctx.consecutive_losses = 0;  // Reset consecutive losses
        g_challenge_ctx.total_score += player_score;  // Add score for draw
    }

    // Update state based on conditions
    Challenge_UpdateState();

    // Send status update to PC
    Challenge_SendStatusUpdate();

    // Check for special conditions
    if (g_challenge_ctx.state == CHALLENGE_STATE_WIN) {
        Challenge_DisplayResult(CHALLENGE_WIN);
        return CHALLENGE_WIN;
    } else if (g_challenge_ctx.state == CHALLENGE_STATE_GAME_OVER) {
        Challenge_DisplayResult(CHALLENGE_GAME_OVER);
        return CHALLENGE_GAME_OVER;
    }

    return CHALLENGE_OK;
}

/**
 * @brief Get current challenge context
 */
const Challenge_Context_t* Challenge_GetContext(void)
{
    return &g_challenge_ctx;
}

/**
 * @brief Get current challenge state
 */
Challenge_State_t Challenge_GetState(void)
{
    return g_challenge_ctx.state;
}

/**
 * @brief Get total cumulative score
 */
uint16_t Challenge_GetTotalScore(void)
{
    return g_challenge_ctx.total_score;
}

/**
 * @brief Get consecutive loss count
 */
uint8_t Challenge_GetConsecutiveLosses(void)
{
    return g_challenge_ctx.consecutive_losses;
}

/**
 * @brief Get games played count
 */
uint8_t Challenge_GetGamesPlayed(void)
{
    return g_challenge_ctx.games_played;
}

/**
 * @brief Check if win condition is met
 */
bool Challenge_IsWinConditionMet(void)
{
    return (g_challenge_ctx.total_score >= CHALLENGE_WIN_SCORE);
}

/**
 * @brief Check if game over condition is met
 */
bool Challenge_IsGameOverConditionMet(void)
{
    return (g_challenge_ctx.consecutive_losses >= CHALLENGE_MAX_LOSSES);
}

/**
 * @brief Reset challenge statistics
 */
Challenge_Status_t Challenge_Reset(void)
{
    return Challenge_Start();  // Reuse start logic
}

/**
 * @brief Send challenge status update to PC
 */
Challenge_Status_t Challenge_SendStatusUpdate(void)
{
    // Use CMD_SCORE_UPDATE to send challenge status
    // game_result: 0=ongoing, 1=win, 2=game_over
    uint8_t game_result = 0;
    if (g_challenge_ctx.state == CHALLENGE_STATE_WIN) {
        game_result = 1;
    } else if (g_challenge_ctx.state == CHALLENGE_STATE_GAME_OVER) {
        game_result = 2;
    }

    Protocol_SendScoreUpdate(
        g_challenge_ctx.games_won,
        g_challenge_ctx.games_lost,
        g_challenge_ctx.total_score,
        game_result
    );

    return CHALLENGE_OK;
}

/**
 * @brief Get challenge duration in seconds
 */
uint32_t Challenge_GetDuration(void)
{
    if (g_challenge_ctx.state == CHALLENGE_STATE_INACTIVE) {
        return 0;
    }

    return (HAL_GetTick() - g_challenge_ctx.start_time) / 1000;
}

/* Private functions ---------------------------------------------------------*/

/**
 * @brief Update challenge state based on conditions
 */
static void Challenge_UpdateState(void)
{
    // Check win condition first
    if (Challenge_IsWinConditionMet()) {
        g_challenge_ctx.state = CHALLENGE_STATE_WIN;
        return;
    }

    // Check game over condition
    if (Challenge_IsGameOverConditionMet()) {
        g_challenge_ctx.state = CHALLENGE_STATE_GAME_OVER;
        return;
    }

    // Otherwise remain active
    g_challenge_ctx.state = CHALLENGE_STATE_ACTIVE;
}

/**
 * @brief Display result on LED matrix
 */
static void Challenge_DisplayResult(Challenge_Status_t result)
{
    if (result == CHALLENGE_WIN) {
        // Display "WIN" on LED matrix
        LED_Text_Display("WIN", WS2812B_COLOR_GREEN);
    } else if (result == CHALLENGE_GAME_OVER) {
        // Display "OVER" on LED matrix
        LED_Text_Display("OVER", WS2812B_COLOR_RED);
    }
}
