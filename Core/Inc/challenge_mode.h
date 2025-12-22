/**
 * @file challenge_mode.h
 * @brief Challenge Mode Manager for STM32 Othello
 * @version 1.0
 * @date 2025-12-09
 *
 * @note Challenge mode features:
 *       - Cumulative score tracking across multiple games
 *       - Consecutive loss detection (2 losses → GAME OVER)
 *       - Win condition (total score ≥ 50 → WIN)
 *       - LED text display for WIN/OVER messages
 */

#ifndef __CHALLENGE_MODE_H
#define __CHALLENGE_MODE_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "othello_engine.h"
#include "uart_protocol.h"
#include <stdint.h>
#include <stdbool.h>

/* Exported types ------------------------------------------------------------*/

/**
 * @brief Challenge mode status enumeration
 */
typedef enum {
    CHALLENGE_OK = 0,
    CHALLENGE_ERROR,
    CHALLENGE_WIN,              ///< Player achieved win condition
    CHALLENGE_GAME_OVER         ///< Player lost twice consecutively
} Challenge_Status_t;

/**
 * @brief Challenge mode state enumeration
 */
typedef enum {
    CHALLENGE_STATE_INACTIVE = 0,   ///< Challenge mode not active
    CHALLENGE_STATE_ACTIVE,         ///< Challenge mode active, game in progress
    CHALLENGE_STATE_WIN,            ///< Win condition achieved
    CHALLENGE_STATE_GAME_OVER       ///< Game over condition reached
} Challenge_State_t;

/**
 * @brief Challenge mode context structure
 */
typedef struct {
    Challenge_State_t state;        ///< Current challenge state
    uint16_t total_score;           ///< Cumulative score across all games
    uint8_t consecutive_losses;     ///< Consecutive loss count
    uint8_t games_played;           ///< Total games played in this challenge
    uint8_t games_won;              ///< Total games won
    uint8_t games_lost;             ///< Total games lost
    uint8_t games_drawn;            ///< Total games drawn
    uint32_t start_time;            ///< Challenge start timestamp
    bool initialized;               ///< Initialization flag
} Challenge_Context_t;

/* Exported constants --------------------------------------------------------*/

/**
 * @brief Challenge mode thresholds
 */
#define CHALLENGE_WIN_SCORE         50     ///< Total score needed to win (3 games × ~63 avg)
#define CHALLENGE_MAX_LOSSES        2       ///< Maximum consecutive losses before game over
#define CHALLENGE_MAX_GAMES         10      ///< Maximum games in one challenge session

/* Exported macro ------------------------------------------------------------*/

/**
 * @brief Check if challenge mode is active
 * @param ctx Pointer to challenge context
 * @retval bool true if challenge mode is active
 */
#define CHALLENGE_IS_ACTIVE(ctx) \
    ((ctx)->state == CHALLENGE_STATE_ACTIVE)

/**
 * @brief Check if challenge is won
 * @param ctx Pointer to challenge context
 * @retval bool true if challenge is won
 */
#define CHALLENGE_IS_WIN(ctx) \
    ((ctx)->state == CHALLENGE_STATE_WIN)

/**
 * @brief Check if challenge is game over
 * @param ctx Pointer to challenge context
 * @retval bool true if challenge is game over
 */
#define CHALLENGE_IS_GAME_OVER(ctx) \
    ((ctx)->state == CHALLENGE_STATE_GAME_OVER)

/* Exported functions prototypes ---------------------------------------------*/

/**
 * @brief Initialize challenge mode module
 * @retval Challenge_Status_t Initialization status
 */
Challenge_Status_t Challenge_Init(void);

/**
 * @brief Start new challenge session
 * @retval Challenge_Status_t Status of operation
 */
Challenge_Status_t Challenge_Start(void);

/**
 * @brief End current challenge session
 * @retval Challenge_Status_t Status of operation
 */
Challenge_Status_t Challenge_End(void);

/**
 * @brief Process game result and update challenge state
 * @param game_state Pointer to final game state
 * @retval Challenge_Status_t Status of operation (CHALLENGE_WIN or CHALLENGE_GAME_OVER if condition met)
 */
Challenge_Status_t Challenge_ProcessGameResult(const GameState_t* game_state);

/**
 * @brief Get current challenge context
 * @retval const Challenge_Context_t* Pointer to context (read-only)
 */
const Challenge_Context_t* Challenge_GetContext(void);

/**
 * @brief Get current challenge state
 * @retval Challenge_State_t Current state
 */
Challenge_State_t Challenge_GetState(void);

/**
 * @brief Get total cumulative score
 * @retval uint16_t Total score
 */
uint16_t Challenge_GetTotalScore(void);

/**
 * @brief Get consecutive loss count
 * @retval uint8_t Consecutive losses
 */
uint8_t Challenge_GetConsecutiveLosses(void);

/**
 * @brief Get games played count
 * @retval uint8_t Games played
 */
uint8_t Challenge_GetGamesPlayed(void);

/**
 * @brief Check if win condition is met
 * @retval bool true if total score ≥ CHALLENGE_WIN_SCORE
 */
bool Challenge_IsWinConditionMet(void);

/**
 * @brief Check if game over condition is met
 * @retval bool true if consecutive losses ≥ CHALLENGE_MAX_LOSSES
 */
bool Challenge_IsGameOverConditionMet(void);

/**
 * @brief Reset challenge statistics
 * @retval Challenge_Status_t Status of operation
 */
Challenge_Status_t Challenge_Reset(void);

/**
 * @brief Send challenge status update to PC
 * @retval Challenge_Status_t Status of operation
 */
Challenge_Status_t Challenge_SendStatusUpdate(void);

/**
 * @brief Get challenge duration in seconds
 * @retval uint32_t Challenge duration
 */
uint32_t Challenge_GetDuration(void);

#ifdef __cplusplus
}
#endif

#endif /* __CHALLENGE_MODE_H */
