/**
 * @file othello_engine.c
 * @brief Othello Game Logic Engine Implementation
 * @version 1.0
 * @date 2025-11-22
 *
 * @details
 * Complete implementation of Othello/Reversi game rules:
 * - Standard 8×8 board with initial 2×2 center setup
 * - Move validation with direction-based piece flipping
 * - Game state management and win condition detection
 * - Optimized for STM32 microcontroller constraints
 */

/* Includes ------------------------------------------------------------------*/
#include "othello_engine.h"
#include <string.h>
#include <stdio.h>

/* Private typedef -----------------------------------------------------------*/

/**
 * @brief Engine state structure
 */
typedef struct {
    bool initialized;               ///< Initialization flag
    GameStats_t global_stats;       ///< Global game statistics
} OthelloEngine_t;

/* Private define ------------------------------------------------------------*/

/* Private variables ---------------------------------------------------------*/
static OthelloEngine_t engine = {0};

/**
 * @brief All 8 search directions (N, NE, E, SE, S, SW, W, NW)
 */
const Direction_t SEARCH_DIRECTIONS[8] = {
    {-1,  0}, {-1,  1}, { 0,  1}, { 1,  1},
    { 1,  0}, { 1, -1}, { 0, -1}, {-1, -1}
};

/* Private function prototypes -----------------------------------------------*/
static uint8_t Othello_FlipPiecesInDirection(GameState_t* state, uint8_t row, uint8_t col,
                                            int8_t dx, int8_t dy, PieceType_t player, bool execute);
static void Othello_UpdatePieceCounts(GameState_t* state);
static void Othello_InvalidateValidMovesCache(GameState_t* state);
static void Othello_UpdateGameStatus(GameState_t* state);

/* Exported functions --------------------------------------------------------*/

/**
 * @brief Initialize game engine
 */
Othello_Status_t Othello_Init(void)
{
    if (engine.initialized) {
        return OTHELLO_OK;
    }

    // Initialize engine state
    memset(&engine, 0, sizeof(OthelloEngine_t));
    engine.initialized = true;

    return OTHELLO_OK;
}

/**
 * @brief Start new game
 */
Othello_Status_t Othello_NewGame(GameState_t* state)
{
    if (!engine.initialized || !state) {
        return OTHELLO_ERROR;
    }

    // Clear the board
    memset(state, 0, sizeof(GameState_t));

    // Set initial position (standard Othello setup)
    state->board[INITIAL_BLACK_ROW1][INITIAL_BLACK_COL1] = PIECE_BLACK;  // [3][3]
    state->board[INITIAL_BLACK_ROW2][INITIAL_BLACK_COL2] = PIECE_BLACK;  // [4][4]
    state->board[INITIAL_WHITE_ROW1][INITIAL_WHITE_COL1] = PIECE_WHITE;  // [3][4]
    state->board[INITIAL_WHITE_ROW2][INITIAL_WHITE_COL2] = PIECE_WHITE;  // [4][3]

    // Initialize game state
    state->current_player = PIECE_BLACK;  // Black starts first
    state->black_count = 2;
    state->white_count = 2;
    state->status = GAME_STATUS_PLAYING;
    state->move_count = 0;
    state->consecutive_passes = 0;
    state->game_start_time = HAL_GetTick();
    state->game_mode = GAME_MODE_NORMAL;  // Default to normal mode

    // Initialize last move
    state->last_move.row = 0xFF;  // Invalid position indicates no move yet
    state->last_move.col = 0xFF;
    state->last_move.player = PIECE_EMPTY;
    state->last_move.flipped_count = 0;
    state->last_move.timestamp = state->game_start_time;

    // Invalidate valid moves cache
    Othello_InvalidateValidMovesCache(state);

    return OTHELLO_OK;
}

/**
 * @brief Check if move is valid
 */
bool Othello_IsValidMove(const GameState_t* state, uint8_t row, uint8_t col, PieceType_t player)
{
    if (!state || !OTHELLO_IS_VALID_COORD(row, col) ||
        (player != PIECE_BLACK && player != PIECE_WHITE)) {
        return false;
    }

    // Position must be empty
    if (state->board[row][col] != PIECE_EMPTY) {
        return false;
    }

    // Must be able to flip at least one piece
    return Othello_SimulateMove(state, row, col, player) > 0;
}

/**
 * @brief Make a move
 */
uint8_t Othello_MakeMove(GameState_t* state, uint8_t row, uint8_t col, PieceType_t player)
{
    if (!state || state->status != GAME_STATUS_PLAYING ||
        !Othello_IsValidMove(state, row, col, player)) {
        return 0;
    }

    uint8_t total_flipped = 0;

    // Place the piece
    state->board[row][col] = player;

    // Flip pieces in all directions
    for (int i = 0; i < 8; i++) {
        total_flipped += Othello_FlipPiecesInDirection(state, row, col,
                                                     SEARCH_DIRECTIONS[i].dx,
                                                     SEARCH_DIRECTIONS[i].dy,
                                                     player, true);
    }

    // Update move history
    state->last_move.row = row;
    state->last_move.col = col;
    state->last_move.player = player;
    state->last_move.flipped_count = total_flipped;
    state->last_move.timestamp = HAL_GetTick();

    // Update game state
    state->move_count++;
    state->consecutive_passes = 0;  // Reset pass counter
    Othello_UpdatePieceCounts(state);
    Othello_InvalidateValidMovesCache(state);

    // Check game mode for player switching logic
    if (is_cheat_active) {
        // Cheat mode: Do NOT switch player, keep current_player unchanged
        // No need to check for valid moves or game over
        // Player can continue placing same color pieces
    } else {
        // Normal mode: Switch to next player
        state->current_player = OTHELLO_OPPOSITE_PLAYER(player);

        // Check if next player has any valid moves
        if (!Othello_HasValidMoves(state, state->current_player)) {
            if (!Othello_HasValidMoves(state, player)) {
                // Neither player can move - game over
                Othello_UpdateGameStatus(state);
            } else {
                // Next player passes, switch back
                state->current_player = player;
                state->consecutive_passes = 1;
            }
        }

        // Update game status if board is full
        if (state->black_count + state->white_count == 64) {
            Othello_UpdateGameStatus(state);
        }
    }

    return total_flipped;
}

/**
 * @brief Place piece and flip captured pieces (cheat mode version)
 * @note This function allows placing on ANY position (including non-empty)
 *       and flips all pieces that would be captured in all 8 directions.
 *       Does NOT check if the move is valid.
 * @param state Pointer to game state
 * @param row Row (0-7)
 * @param col Column (0-7)
 * @param player Color of piece to place
 * @retval uint8_t Number of pieces flipped
 */
uint8_t Othello_PlaceAndFlip(GameState_t* state, uint8_t row, uint8_t col, PieceType_t player)
{
    if (!state || state->status != GAME_STATUS_PLAYING ||
        row >= 8 || col >= 8 ||
        (player != PIECE_BLACK && player != PIECE_WHITE)) {
        return 0;
    }

    uint8_t total_flipped = 0;

    // Place the piece (overwrite if position not empty)
    state->board[row][col] = player;

    // Flip pieces in all 8 directions
    for (int i = 0; i < 8; i++) {
        total_flipped += Othello_FlipPiecesInDirection(state, row, col,
                                                     SEARCH_DIRECTIONS[i].dx,
                                                     SEARCH_DIRECTIONS[i].dy,
                                                     player, true);
    }

    // Update move history
    state->last_move.row = row;
    state->last_move.col = col;
    state->last_move.player = player;
    state->last_move.flipped_count = total_flipped;
    state->last_move.timestamp = HAL_GetTick();

    // Update game state
    state->move_count++;
    state->consecutive_passes = 0;  // Reset pass counter
    Othello_UpdatePieceCounts(state);
    Othello_InvalidateValidMovesCache(state);

    // In cheat mode, do NOT switch player (keep playing with same color)
    // The caller (App_ProcessKeyEvent) ensures is_cheat_active is true

    return total_flipped;
}

/**
 * @brief Pass turn
 */
Othello_Status_t Othello_PassTurn(GameState_t* state)
{
    if (!state || state->status != GAME_STATUS_PLAYING) {
        return OTHELLO_ERROR;
    }

    state->consecutive_passes++;
    state->current_player = OTHELLO_OPPOSITE_PLAYER(state->current_player);

    // If both players pass consecutively, game ends
    if (state->consecutive_passes >= 2) {
        Othello_UpdateGameStatus(state);
    }

    return OTHELLO_OK;
}

/**
 * @brief Check if game is over
 */
bool Othello_IsGameOver(const GameState_t* state)
{
    // Cheat mode active: Suspend game over detection
    if (is_cheat_active) {
        return false;  // Game never ends in cheat mode
    }

    return state ? (state->status != GAME_STATUS_PLAYING) : true;
}

/**
 * @brief Get winner
 */
PieceType_t Othello_GetWinner(const GameState_t* state)
{
    if (!state || state->status == GAME_STATUS_PLAYING) {
        return PIECE_EMPTY;
    }

    if (state->status == GAME_STATUS_BLACK_WIN) {
        return PIECE_BLACK;
    } else if (state->status == GAME_STATUS_WHITE_WIN) {
        return PIECE_WHITE;
    }

    return PIECE_EMPTY;  // Draw
}

/**
 * @brief Get current game status
 */
GameStatus_t Othello_GetGameStatus(const GameState_t* state)
{
    return state ? state->status : GAME_STATUS_ERROR;
}

/* Move validation and generation --------------------------------------------*/

/**
 * @brief Get all valid moves for current player
 */
uint8_t Othello_GetValidMoves(const GameState_t* state, Move_t* moves, uint8_t max_moves)
{
    if (!state || !moves || max_moves == 0) {
        return 0;
    }

    uint8_t move_count = 0;
    PieceType_t player = state->current_player;

    for (uint8_t row = 0; row < 8 && move_count < max_moves; row++) {
        for (uint8_t col = 0; col < 8 && move_count < max_moves; col++) {
            if (Othello_IsValidMove(state, row, col, player)) {
                moves[move_count].row = row;
                moves[move_count].col = col;
                moves[move_count].player = player;
                moves[move_count].flipped_count = Othello_SimulateMove(state, row, col, player);
                moves[move_count].timestamp = HAL_GetTick();
                move_count++;
            }
        }
    }

    return move_count;
}

/**
 * @brief Count valid moves for current player
 */
uint8_t Othello_CountValidMoves(const GameState_t* state, PieceType_t player)
{
    if (!state) {
        return 0;
    }

    uint8_t count = 0;

    for (uint8_t row = 0; row < 8; row++) {
        for (uint8_t col = 0; col < 8; col++) {
            if (Othello_IsValidMove(state, row, col, player)) {
                count++;
            }
        }
    }

    return count;
}

/**
 * @brief Check if player has any valid moves
 */
bool Othello_HasValidMoves(const GameState_t* state, PieceType_t player)
{
    if (!state) {
        return false;
    }

    for (uint8_t row = 0; row < 8; row++) {
        for (uint8_t col = 0; col < 8; col++) {
            if (Othello_IsValidMove(state, row, col, player)) {
                return true;
            }
        }
    }

    return false;
}

/**
 * @brief Simulate move without modifying state
 */
uint8_t Othello_SimulateMove(const GameState_t* state, uint8_t row, uint8_t col, PieceType_t player)
{
    if (!state || !OTHELLO_IS_VALID_COORD(row, col) ||
        state->board[row][col] != PIECE_EMPTY ||
        (player != PIECE_BLACK && player != PIECE_WHITE)) {
        return 0;
    }

    uint8_t total_flipped = 0;

    // Check all 8 directions
    for (int i = 0; i < 8; i++) {
        total_flipped += Othello_FlipPiecesInDirection((GameState_t*)state, row, col,
                                                     SEARCH_DIRECTIONS[i].dx,
                                                     SEARCH_DIRECTIONS[i].dy,
                                                     player, false);
    }

    return total_flipped;
}

/* Board analysis functions --------------------------------------------------*/

/**
 * @brief Count pieces on board
 */
uint8_t Othello_CountPieces(const GameState_t* state, PieceType_t player)
{
    if (!state) {
        return 0;
    }

    uint8_t count = 0;

    for (uint8_t row = 0; row < 8; row++) {
        for (uint8_t col = 0; col < 8; col++) {
            if (state->board[row][col] == player) {
                count++;
            }
        }
    }

    return count;
}

/**
 * @brief Get board piece at position
 */
PieceType_t Othello_GetPiece(const GameState_t* state, uint8_t row, uint8_t col)
{
    if (!state || !OTHELLO_IS_VALID_COORD(row, col)) {
        return PIECE_EMPTY;
    }

    return state->board[row][col];
}

/**
 * @brief Check if position is on board edge
 */
bool Othello_IsEdgePosition(uint8_t row, uint8_t col)
{
    return (row == 0 || row == 7 || col == 0 || col == 7);
}

/**
 * @brief Check if position is a corner
 */
bool Othello_IsCornerPosition(uint8_t row, uint8_t col)
{
    return ((row == 0 || row == 7) && (col == 0 || col == 7));
}

/* Game state management -----------------------------------------------------*/

/**
 * @brief Copy game state
 */
Othello_Status_t Othello_CopyState(GameState_t* dest, const GameState_t* src)
{
    if (!dest || !src) {
        return OTHELLO_ERROR;
    }

    memcpy(dest, src, sizeof(GameState_t));
    return OTHELLO_OK;
}

/**
 * @brief Reset game state
 */
Othello_Status_t Othello_ResetState(GameState_t* state)
{
    if (!state) {
        return OTHELLO_ERROR;
    }

    Game_Mode_t saved_mode = state->game_mode;  // Save current mode
    Othello_NewGame(state);
    state->game_mode = saved_mode;              // Restore mode

    return OTHELLO_OK;
}

/**
 * @brief Update game statistics
 */
Othello_Status_t Othello_UpdateStats(GameStats_t* stats, const GameState_t* final_state)
{
    if (!stats || !final_state) {
        return OTHELLO_ERROR;
    }

    stats->total_games++;
    stats->total_moves += final_state->move_count;

    // Update win counts
    switch (final_state->status) {
        case GAME_STATUS_BLACK_WIN:
            stats->black_wins++;
            break;
        case GAME_STATUS_WHITE_WIN:
            stats->white_wins++;
            break;
        case GAME_STATUS_DRAW:
            stats->draws++;
            break;
        default:
            break;
    }

    // Update game length records
    if (stats->total_games == 1) {
        stats->longest_game = final_state->move_count;
        stats->shortest_game = final_state->move_count;
    } else {
        if (final_state->move_count > stats->longest_game) {
            stats->longest_game = final_state->move_count;
        }
        if (final_state->move_count < stats->shortest_game) {
            stats->shortest_game = final_state->move_count;
        }
    }

    // Update total game time
    uint32_t game_duration = Othello_GetGameDuration(final_state);
    stats->total_game_time += game_duration;

    return OTHELLO_OK;
}

/**
 * @brief Get game duration in seconds
 */
uint32_t Othello_GetGameDuration(const GameState_t* state)
{
    if (!state) {
        return 0;
    }

    uint32_t current_time = HAL_GetTick();
    return (current_time - state->game_start_time) / 1000;  // Convert to seconds
}

/* Utility functions ---------------------------------------------------------*/

/**
 * @brief Convert piece type to character
 */
char Othello_PieceToChar(PieceType_t piece)
{
    switch (piece) {
        case PIECE_BLACK: return 'B';
        case PIECE_WHITE: return 'W';
        default: return '.';
    }
}

/**
 * @brief Convert character to piece type
 */
PieceType_t Othello_CharToPiece(char c)
{
    switch (c) {
        case 'B': case 'b': return PIECE_BLACK;
        case 'W': case 'w': return PIECE_WHITE;
        default: return PIECE_EMPTY;
    }
}

/**
 * @brief Print board to debug string
 */
Othello_Status_t Othello_PrintBoard(const GameState_t* state, char* buffer, uint16_t buffer_size)
{
    if (!state || !buffer || buffer_size < 200) {
        return OTHELLO_ERROR;
    }

    int pos = 0;

    // Print column headers
    pos += sprintf(&buffer[pos], "  01234567\n");

    // Print board rows
    for (uint8_t row = 0; row < 8; row++) {
        pos += sprintf(&buffer[pos], "%d ", row);
        for (uint8_t col = 0; col < 8; col++) {
            pos += sprintf(&buffer[pos], "%c", Othello_PieceToChar(state->board[row][col]));
        }
        pos += sprintf(&buffer[pos], "\n");
    }

    // Print game info
    pos += sprintf(&buffer[pos], "Black: %d, White: %d, Turn: %c\n",
                  state->black_count, state->white_count,
                  Othello_PieceToChar(state->current_player));

    return OTHELLO_OK;
}

/**
 * @brief Validate board state integrity
 */
bool Othello_ValidateBoardState(const GameState_t* state)
{
    if (!state) {
        return false;
    }

    // Count pieces manually
    uint8_t black_count = Othello_CountPieces(state, PIECE_BLACK);
    uint8_t white_count = Othello_CountPieces(state, PIECE_WHITE);

    // Verify piece counts match
    if (black_count != state->black_count || white_count != state->white_count) {
        return false;
    }

    // Verify total pieces is reasonable (at least initial 4)
    if (black_count + white_count < 4 || black_count + white_count > 64) {
        return false;
    }

    // Verify current player is valid
    if (state->current_player != PIECE_BLACK && state->current_player != PIECE_WHITE) {
        return false;
    }

    return true;
}

/* Private functions ---------------------------------------------------------*/

/**
 * @brief Flip pieces in one direction
 */
static uint8_t Othello_FlipPiecesInDirection(GameState_t* state, uint8_t row, uint8_t col,
                                           int8_t dx, int8_t dy, PieceType_t player, bool execute)
{
    PieceType_t opponent = OTHELLO_OPPOSITE_PLAYER(player);
    uint8_t flipped = 0;
    int8_t check_row = row + dx;
    int8_t check_col = col + dy;

    // Find opponent pieces in this direction
    while (OTHELLO_IS_VALID_COORD(check_row, check_col) &&
           state->board[check_row][check_col] == opponent) {
        flipped++;
        check_row += dx;
        check_col += dy;
    }

    // Must end with our piece to be valid
    if (flipped > 0 &&
        OTHELLO_IS_VALID_COORD(check_row, check_col) &&
        state->board[check_row][check_col] == player) {

        if (execute) {
            // Actually flip the pieces
            check_row = row + dx;
            check_col = col + dy;
            for (uint8_t i = 0; i < flipped; i++) {
                state->board[check_row][check_col] = player;
                check_row += dx;
                check_col += dy;
            }
        }

        return flipped;
    }

    return 0;  // No valid flip in this direction
}

/**
 * @brief Update piece counts from board state
 */
static void Othello_UpdatePieceCounts(GameState_t* state)
{
    if (!state) {
        return;
    }

    state->black_count = Othello_CountPieces(state, PIECE_BLACK);
    state->white_count = Othello_CountPieces(state, PIECE_WHITE);
}

/**
 * @brief Invalidate valid moves cache
 */
static void Othello_InvalidateValidMovesCache(GameState_t* state)
{
    if (state) {
        state->valid_moves_cached = false;
        memset(state->valid_moves_cache, 0, sizeof(state->valid_moves_cache));
    }
}

/**
 * @brief Update game status based on current state
 */
static void Othello_UpdateGameStatus(GameState_t* state)
{
    if (!state) {
        return;
    }

    // Game is over - determine winner
    if (state->black_count > state->white_count) {
        state->status = GAME_STATUS_BLACK_WIN;
    } else if (state->white_count > state->black_count) {
        state->status = GAME_STATUS_WHITE_WIN;
    } else {
        state->status = GAME_STATUS_DRAW;
    }
}

/**
 * @brief Recalculate piece counts after manual board modification
 *
 * This function is used in cheat mode to update piece counts
 * after direct piece replacement.
 *
 * @param state Pointer to game state
 */
void Othello_RecalculateCounts(GameState_t* state)
{
    if (state == NULL) {
        return;
    }

    state->black_count = 0;
    state->white_count = 0;

    for (int row = 0; row < 8; row++) {
        for (int col = 0; col < 8; col++) {
            if (state->board[row][col] == PIECE_BLACK) {
                state->black_count++;
            } else if (state->board[row][col] == PIECE_WHITE) {
                state->white_count++;
            }
        }
    }
}