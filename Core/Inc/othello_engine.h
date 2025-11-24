/**
 * @file othello_engine.h
 * @brief Othello Game Logic Engine for STM32 Platform
 * @version 1.0
 * @date 2025-11-22
 *
 * @note Implements complete Othello/Reversi game rules:
 *       - 8×8 board management
 *       - Move validation and execution
 *       - Piece flipping logic
 *       - Game state management
 *       - Win condition detection
 */

#ifndef __OTHELLO_ENGINE_H
#define __OTHELLO_ENGINE_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include <stdint.h>
#include <stdbool.h>

/* Exported types ------------------------------------------------------------*/

/**
 * @brief Piece type enumeration
 */
typedef enum {
    PIECE_EMPTY = 0,        ///< Empty square
    PIECE_BLACK = 1,        ///< Black piece
    PIECE_WHITE = 2         ///< White piece
} PieceType_t;

/**
 * @brief Game status enumeration
 */
typedef enum {
    GAME_STATUS_PLAYING = 0,    ///< Game in progress
    GAME_STATUS_BLACK_WIN,      ///< Black player wins
    GAME_STATUS_WHITE_WIN,      ///< White player wins
    GAME_STATUS_DRAW,           ///< Game is a draw
    GAME_STATUS_ERROR           ///< Game error state
} GameStatus_t;

/**
 * @brief Game engine status enumeration
 */
typedef enum {
    OTHELLO_OK = 0,
    OTHELLO_ERROR,
    OTHELLO_INVALID_MOVE,
    OTHELLO_GAME_OVER,
    OTHELLO_NO_VALID_MOVES
} Othello_Status_t;

/**
 * @brief Move direction structure
 */
typedef struct {
    int8_t dx;              ///< X direction (-1, 0, 1)
    int8_t dy;              ///< Y direction (-1, 0, 1)
} Direction_t;

/**
 * @brief Move structure
 */
typedef struct {
    uint8_t row;            ///< Move row (0-7)
    uint8_t col;            ///< Move column (0-7)
    PieceType_t player;     ///< Player making move
    uint8_t flipped_count;  ///< Number of pieces flipped
    uint32_t timestamp;     ///< Move timestamp
} Move_t;

/**
 * @brief Game state structure
 */
typedef struct {
    PieceType_t board[8][8];        ///< Game board
    PieceType_t current_player;     ///< Current player
    uint8_t black_count;            ///< Number of black pieces
    uint8_t white_count;            ///< Number of white pieces
    GameStatus_t status;            ///< Current game status
    uint32_t move_count;            ///< Total number of moves
    Move_t last_move;               ///< Last move made
    uint8_t consecutive_passes;     ///< Consecutive passes (game ends after 2)
    uint32_t game_start_time;       ///< Game start timestamp
    bool valid_moves_cache[8][8];   ///< Cache of valid moves for current player
    bool valid_moves_cached;        ///< Whether cache is valid
} GameState_t;

/**
 * @brief Game statistics structure
 */
typedef struct {
    uint32_t total_games;           ///< Total games played
    uint32_t black_wins;            ///< Black wins count
    uint32_t white_wins;            ///< White wins count
    uint32_t draws;                 ///< Draw games count
    uint32_t total_moves;           ///< Total moves in all games
    uint32_t longest_game;          ///< Longest game (move count)
    uint32_t shortest_game;         ///< Shortest game (move count)
    uint32_t total_game_time;       ///< Total game time in seconds
} GameStats_t;

/* Exported constants --------------------------------------------------------*/

/** @defgroup Board_Constants Board Constants
 * @{
 */
#define OTHELLO_BOARD_SIZE          8       ///< Board size (8×8)
#define OTHELLO_MAX_MOVES           60      ///< Maximum possible moves
#define OTHELLO_INITIAL_PIECES      4       ///< Initial pieces on board
#define OTHELLO_MAX_DIRECTIONS      8       ///< Maximum search directions
/**
 * @}
 */

/** @defgroup Initial_Position Initial Board Position
 * @{
 */
#define INITIAL_BLACK_ROW1          3       ///< Initial black piece row 1
#define INITIAL_BLACK_COL1          3       ///< Initial black piece col 1
#define INITIAL_BLACK_ROW2          4       ///< Initial black piece row 2
#define INITIAL_BLACK_COL2          4       ///< Initial black piece col 2
#define INITIAL_WHITE_ROW1          3       ///< Initial white piece row 1
#define INITIAL_WHITE_COL1          4       ///< Initial white piece col 1
#define INITIAL_WHITE_ROW2          4       ///< Initial white piece row 2
#define INITIAL_WHITE_COL2          3       ///< Initial white piece col 2
/**
 * @}
 */

/* Exported macro ------------------------------------------------------------*/

/**
 * @brief Check if coordinates are valid
 * @param row Row coordinate
 * @param col Column coordinate
 * @retval true if coordinates are valid
 */
#define OTHELLO_IS_VALID_COORD(row, col) \
    ((row) >= 0 && (row) < OTHELLO_BOARD_SIZE && (col) >= 0 && (col) < OTHELLO_BOARD_SIZE)

/**
 * @brief Get opposite player
 * @param player Current player
 * @retval Opposite player
 */
#define OTHELLO_OPPOSITE_PLAYER(player) \
    ((player) == PIECE_BLACK ? PIECE_WHITE : PIECE_BLACK)

/**
 * @brief Check if game has ended
 * @param state Game state pointer
 * @retval true if game has ended
 */
#define OTHELLO_IS_GAME_OVER(state) \
    ((state)->status != GAME_STATUS_PLAYING)

/* Exported variables --------------------------------------------------------*/
extern const Direction_t SEARCH_DIRECTIONS[8]; ///< All 8 search directions

/* Exported functions prototypes ---------------------------------------------*/

/* Core game functions -------------------------------------------------------*/

/**
 * @brief Initialize game engine
 * @retval Othello_Status_t Initialization status
 */
Othello_Status_t Othello_Init(void);

/**
 * @brief Start new game
 * @param state Pointer to game state structure
 * @retval Othello_Status_t Status of operation
 */
Othello_Status_t Othello_NewGame(GameState_t* state);

/**
 * @brief Check if move is valid
 * @param state Pointer to game state
 * @param row Move row (0-7)
 * @param col Move column (0-7)
 * @param player Player making move
 * @retval bool true if move is valid
 */
bool Othello_IsValidMove(const GameState_t* state, uint8_t row, uint8_t col, PieceType_t player);

/**
 * @brief Make a move
 * @param state Pointer to game state
 * @param row Move row (0-7)
 * @param col Move column (0-7)
 * @param player Player making move
 * @retval uint8_t Number of pieces flipped, 0 if move invalid
 */
uint8_t Othello_MakeMove(GameState_t* state, uint8_t row, uint8_t col, PieceType_t player);

/**
 * @brief Pass turn (when no valid moves available)
 * @param state Pointer to game state
 * @retval Othello_Status_t Status of operation
 */
Othello_Status_t Othello_PassTurn(GameState_t* state);

/**
 * @brief Check if game is over
 * @param state Pointer to game state
 * @retval bool true if game is over
 */
bool Othello_IsGameOver(const GameState_t* state);

/**
 * @brief Get winner
 * @param state Pointer to game state
 * @retval PieceType_t Winner (PIECE_BLACK, PIECE_WHITE, or PIECE_EMPTY for draw)
 */
PieceType_t Othello_GetWinner(const GameState_t* state);

/**
 * @brief Get current game status
 * @param state Pointer to game state
 * @retval GameStatus_t Current game status
 */
GameStatus_t Othello_GetGameStatus(const GameState_t* state);

/* Move validation and generation --------------------------------------------*/

/**
 * @brief Get all valid moves for current player
 * @param state Pointer to game state
 * @param moves Array to store valid moves (max 64 elements)
 * @param max_moves Maximum number of moves to store
 * @retval uint8_t Number of valid moves found
 */
uint8_t Othello_GetValidMoves(const GameState_t* state, Move_t* moves, uint8_t max_moves);

/**
 * @brief Count valid moves for current player
 * @param state Pointer to game state
 * @param player Player to count moves for
 * @retval uint8_t Number of valid moves
 */
uint8_t Othello_CountValidMoves(const GameState_t* state, PieceType_t player);

/**
 * @brief Check if player has any valid moves
 * @param state Pointer to game state
 * @param player Player to check
 * @retval bool true if player has valid moves
 */
bool Othello_HasValidMoves(const GameState_t* state, PieceType_t player);

/**
 * @brief Simulate move without modifying state
 * @param state Pointer to game state
 * @param row Move row (0-7)
 * @param col Move column (0-7)
 * @param player Player making move
 * @retval uint8_t Number of pieces that would be flipped, 0 if invalid
 */
uint8_t Othello_SimulateMove(const GameState_t* state, uint8_t row, uint8_t col, PieceType_t player);

/* Board analysis functions --------------------------------------------------*/

/**
 * @brief Count pieces on board
 * @param state Pointer to game state
 * @param player Player to count (PIECE_EMPTY counts empty squares)
 * @retval uint8_t Number of pieces
 */
uint8_t Othello_CountPieces(const GameState_t* state, PieceType_t player);

/**
 * @brief Get board piece at position
 * @param state Pointer to game state
 * @param row Row (0-7)
 * @param col Column (0-7)
 * @retval PieceType_t Piece at position
 */
PieceType_t Othello_GetPiece(const GameState_t* state, uint8_t row, uint8_t col);

/**
 * @brief Check if position is on board edge
 * @param row Row (0-7)
 * @param col Column (0-7)
 * @retval bool true if position is on edge
 */
bool Othello_IsEdgePosition(uint8_t row, uint8_t col);

/**
 * @brief Check if position is a corner
 * @param row Row (0-7)
 * @param col Column (0-7)
 * @retval bool true if position is a corner
 */
bool Othello_IsCornerPosition(uint8_t row, uint8_t col);

/* Game state management -----------------------------------------------------*/

/**
 * @brief Copy game state
 * @param dest Destination state
 * @param src Source state
 * @retval Othello_Status_t Status of operation
 */
Othello_Status_t Othello_CopyState(GameState_t* dest, const GameState_t* src);

/**
 * @brief Reset game state
 * @param state Pointer to game state
 * @retval Othello_Status_t Status of operation
 */
Othello_Status_t Othello_ResetState(GameState_t* state);

/**
 * @brief Update game statistics
 * @param stats Pointer to statistics structure
 * @param final_state Pointer to final game state
 * @retval Othello_Status_t Status of operation
 */
Othello_Status_t Othello_UpdateStats(GameStats_t* stats, const GameState_t* final_state);

/**
 * @brief Get game duration in seconds
 * @param state Pointer to game state
 * @retval uint32_t Game duration in seconds
 */
uint32_t Othello_GetGameDuration(const GameState_t* state);

/* Utility functions ---------------------------------------------------------*/

/**
 * @brief Convert piece type to character
 * @param piece Piece type
 * @retval char Character representation ('.', 'B', 'W')
 */
char Othello_PieceToChar(PieceType_t piece);

/**
 * @brief Convert character to piece type
 * @param c Character ('.' or ' ' = empty, 'B' or 'b' = black, 'W' or 'w' = white)
 * @retval PieceType_t Piece type
 */
PieceType_t Othello_CharToPiece(char c);

/**
 * @brief Print board to debug string
 * @param state Pointer to game state
 * @param buffer Buffer to store board string (minimum 200 bytes)
 * @param buffer_size Size of buffer
 * @retval Othello_Status_t Status of operation
 */
Othello_Status_t Othello_PrintBoard(const GameState_t* state, char* buffer, uint16_t buffer_size);

/**
 * @brief Validate board state integrity
 * @param state Pointer to game state
 * @retval bool true if board state is valid
 */
bool Othello_ValidateBoardState(const GameState_t* state);

#ifdef __cplusplus
}
#endif

#endif /* __OTHELLO_ENGINE_H */