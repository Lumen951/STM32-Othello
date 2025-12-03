/**
 * @file keypad_mapping.h
 * @brief Keypad key mapping definitions and utilities
 * @version 1.0
 * @date 2025-11-22
 *
 * @note This file defines the physical to logical key mapping for 4×4 matrix keypad
 *       Layout follows standard numeric keypad arrangement with hex digits
 */

#ifndef __KEYPAD_MAPPING_H
#define __KEYPAD_MAPPING_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include <stdint.h>
#include <stdbool.h>

/* Exported types ------------------------------------------------------------*/

/**
 * @brief Logical key code enumeration
 * @note Maps to standard hexadecimal keypad layout
 */
typedef enum {
    // Row 0
    KEYPAD_KEY_1 = 0,       ///< Key '1' at position (0,0)
    KEYPAD_KEY_2,           ///< Key '2' at position (0,1)
    KEYPAD_KEY_3,           ///< Key '3' at position (0,2)
    KEYPAD_KEY_A,           ///< Key 'A' at position (0,3)

    // Row 1
    KEYPAD_KEY_4,           ///< Key '4' at position (1,0)
    KEYPAD_KEY_5,           ///< Key '5' at position (1,1)
    KEYPAD_KEY_6,           ///< Key '6' at position (1,2)
    KEYPAD_KEY_B,           ///< Key 'B' at position (1,3)

    // Row 2
    KEYPAD_KEY_7,           ///< Key '7' at position (2,0)
    KEYPAD_KEY_8,           ///< Key '8' at position (2,1)
    KEYPAD_KEY_9,           ///< Key '9' at position (2,2)
    KEYPAD_KEY_C,           ///< Key 'C' at position (2,3)

    // Row 3
    KEYPAD_KEY_STAR,        ///< Key '*' at position (3,0)
    KEYPAD_KEY_0,           ///< Key '0' at position (3,1)
    KEYPAD_KEY_HASH,        ///< Key '#' at position (3,2)
    KEYPAD_KEY_D,           ///< Key 'D' at position (3,3)

    KEYPAD_KEY_INVALID = 0xFF   ///< Invalid key code
} Keypad_LogicalKey_t;

/**
 * @brief Othello game specific key functions
 */
typedef enum {
    OTHELLO_MOVE_UP = KEYPAD_KEY_2,         ///< Move cursor up
    OTHELLO_MOVE_LEFT = KEYPAD_KEY_4,       ///< Move cursor left
    OTHELLO_MOVE_RIGHT = KEYPAD_KEY_6,      ///< Move cursor right
    OTHELLO_MOVE_DOWN = KEYPAD_KEY_8,       ///< Move cursor down
    OTHELLO_SELECT = KEYPAD_KEY_5,          ///< Select/Place piece
    OTHELLO_MENU = KEYPAD_KEY_STAR,         ///< Enter menu
    OTHELLO_BACK = KEYPAD_KEY_0,            ///< Back/Cancel
    OTHELLO_CONFIRM = KEYPAD_KEY_HASH,      ///< Confirm action
    OTHELLO_OPTION_A = KEYPAD_KEY_A,        ///< Game option A
    OTHELLO_OPTION_B = KEYPAD_KEY_B,        ///< Game option B
    OTHELLO_OPTION_C = KEYPAD_KEY_C,        ///< Game option C
    OTHELLO_OPTION_D = KEYPAD_KEY_D         ///< Game option D
} Othello_KeyFunction_t;

/* Exported constants --------------------------------------------------------*/

/**
 * @brief Physical keypad layout mapping
 * @note Array indexed by [row][col] returns logical key code
 */
static const Keypad_LogicalKey_t KEYPAD_LAYOUT[4][4] = {
    // Col:  0                1                2                3
    {KEYPAD_KEY_1,     KEYPAD_KEY_2,     KEYPAD_KEY_3,     KEYPAD_KEY_A},     // Row 0
    {KEYPAD_KEY_4,     KEYPAD_KEY_5,     KEYPAD_KEY_6,     KEYPAD_KEY_B},     // Row 1
    {KEYPAD_KEY_7,     KEYPAD_KEY_8,     KEYPAD_KEY_9,     KEYPAD_KEY_C},     // Row 2
    {KEYPAD_KEY_STAR,  KEYPAD_KEY_0,     KEYPAD_KEY_HASH,  KEYPAD_KEY_D}      // Row 3
};

/**
 * @brief Key character mapping for display
 */
static const char KEYPAD_CHAR_MAP[] = {
    '1', '2', '3', 'A',     // Row 0
    '4', '5', '6', 'B',     // Row 1
    '7', '8', '9', 'C',     // Row 2
    '*', '0', '#', 'D'      // Row 3
};

/**
 * @brief Key name strings for debugging
 */
#ifdef DEBUG
__attribute__((unused)) static const char* KEYPAD_KEY_NAMES[] = {
    "KEY_1", "KEY_2", "KEY_3", "KEY_A",
    "KEY_4", "KEY_5", "KEY_6", "KEY_B",
    "KEY_7", "KEY_8", "KEY_9", "KEY_C",
    "KEY_*", "KEY_0", "KEY_#", "KEY_D"
};
#endif

/* Exported macro ------------------------------------------------------------*/

/**
 * @brief Convert physical coordinates to logical key
 * @param row Physical row (0-3)
 * @param col Physical column (0-3)
 * @retval Keypad_LogicalKey_t Logical key code
 */
#define KEYPAD_COORD_TO_KEY(row, col) \
    (KEYPAD_LAYOUT[row][col])

/**
 * @brief Convert logical key to character
 * @param key Logical key code
 * @retval char Character representation
 */
#define KEYPAD_KEY_TO_CHAR(key) \
    (KEYPAD_CHAR_MAP[key])

/**
 * @brief Convert logical key to name string
 * @param key Logical key code
 * @retval const char* Key name string
 */
#ifdef DEBUG
#define KEYPAD_KEY_TO_NAME(key) \
    (KEYPAD_KEY_NAMES[key])
#else
#define KEYPAD_KEY_TO_NAME(key) ("")
#endif

/**
 * @brief Check if key is numeric (0-9)
 * @param key Logical key code
 * @retval bool true if numeric key
 */
#define KEYPAD_IS_NUMERIC(key) \
    (((key) >= KEYPAD_KEY_0 && (key) <= KEYPAD_KEY_9) || (key) == KEYPAD_KEY_0)

/**
 * @brief Check if key is hex letter (A-D)
 * @param key Logical key code
 * @retval bool true if hex letter key
 */
#define KEYPAD_IS_HEX_LETTER(key) \
    ((key) >= KEYPAD_KEY_A && (key) <= KEYPAD_KEY_D)

/**
 * @brief Check if key is directional (2,4,6,8)
 * @param key Logical key code
 * @retval bool true if directional key
 */
#define KEYPAD_IS_DIRECTIONAL(key) \
    ((key) == KEYPAD_KEY_2 || (key) == KEYPAD_KEY_4 || \
     (key) == KEYPAD_KEY_6 || (key) == KEYPAD_KEY_8)

/**
 * @brief Check if key is special (* or #)
 * @param key Logical key code
 * @retval bool true if special key
 */
#define KEYPAD_IS_SPECIAL(key) \
    ((key) == KEYPAD_KEY_STAR || (key) == KEYPAD_KEY_HASH)

/* Exported functions prototypes ---------------------------------------------*/

/**
 * @brief Convert physical row,col to logical key
 * @param row Physical row (0-3)
 * @param col Physical column (0-3)
 * @retval Keypad_LogicalKey_t Logical key, KEYPAD_KEY_INVALID if invalid coords
 */
Keypad_LogicalKey_t Keypad_PhysicalToLogical(uint8_t row, uint8_t col);

/**
 * @brief Convert logical key to physical coordinates
 * @param key Logical key code
 * @param row Pointer to store row coordinate
 * @param col Pointer to store column coordinate
 * @retval bool true if conversion successful, false if invalid key
 */
bool Keypad_LogicalToPhysical(Keypad_LogicalKey_t key, uint8_t *row, uint8_t *col);

/**
 * @brief Get character representation of logical key
 * @param key Logical key code
 * @retval char Character, '\0' if invalid key
 */
char Keypad_GetKeyChar(Keypad_LogicalKey_t key);

/**
 * @brief Get name string of logical key
 * @param key Logical key code
 * @retval const char* Key name, "INVALID" if invalid key
 */
const char* Keypad_GetKeyName(Keypad_LogicalKey_t key);

/**
 * @brief Convert numeric key to number
 * @param key Logical key code
 * @retval uint8_t Number (0-9), 0xFF if not numeric key
 */
uint8_t Keypad_KeyToNumber(Keypad_LogicalKey_t key);

/**
 * @brief Convert hex key (0-9,A-F) to hex value
 * @param key Logical key code
 * @retval uint8_t Hex value (0-15), 0xFF if not hex key
 */
uint8_t Keypad_KeyToHex(Keypad_LogicalKey_t key);

/**
 * @brief Get Othello game direction from key
 * @param key Logical key code
 * @param dx Pointer to store X direction (-1, 0, 1)
 * @param dy Pointer to store Y direction (-1, 0, 1)
 * @retval bool true if key is directional, false otherwise
 */
bool Keypad_GetDirection(Keypad_LogicalKey_t key, int8_t *dx, int8_t *dy);

/**
 * @brief Check if key combination forms valid move
 * @param key1 First key
 * @param key2 Second key
 * @retval bool true if valid move combination
 * @note For Othello: number keys can form coordinate pairs
 */
bool Keypad_IsValidMoveCombination(Keypad_LogicalKey_t key1, Keypad_LogicalKey_t key2);

#ifdef __cplusplus
}
#endif

#endif /* __KEYPAD_MAPPING_H */