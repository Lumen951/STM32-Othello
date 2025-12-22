/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2025 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <string.h>
#include "ws2812b_driver.h"
#include "keypad_driver.h"
#include "keypad_mapping.h"
#include "uart_protocol.h"
#include "othello_engine.h"
#include "game_control.h"
#include "challenge_mode.h"
#include "led_text.h"
#include "debug_print.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
TIM_HandleTypeDef htim2;
DMA_HandleTypeDef hdma_tim2_ch1;

UART_HandleTypeDef huart1;

/* USER CODE BEGIN PV */
/* Game state variables */
static GameState_t game_state;
static GameStats_t game_stats;
static bool game_initialized = false;

/* Cursor control variables */
static uint8_t cursor_row = 3;          // Cursor row position (initial: board center)
static uint8_t cursor_col = 3;          // Cursor column position (initial: board center)
static bool cursor_visible = true;      // Cursor visibility (for blinking)
static uint32_t cursor_blink_timer = 0; // Cursor blink timer

/* Game mode variables */
static Game_Mode_t current_game_mode = GAME_MODE_NORMAL;  // Current game mode
static bool is_displaying_result = false;  // Flag: displaying game result (prevent state updates)

/* Game end handling flag (set in interrupt context, processed in main loop) */
static volatile bool game_end_pending = false;
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_DMA_Init(void);
static void MX_TIM2_Init(void);
static void MX_USART1_UART_Init(void);
/* USER CODE BEGIN PFP */
static void Convert_GameState_to_Protocol(const GameState_t* game_state, Game_State_Data_t* protocol_state);
static Protocol_Status_t Send_GameState_Via_Protocol(const GameState_t* game_state);
void App_UpdateCursor(void);
void App_PrintGameHistory(void);
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
/**
 * @brief Convert GameState_t to Game_State_Data_t for protocol transmission
 * @param game_state Source game state
 * @param protocol_state Destination protocol state
 */
static void Convert_GameState_to_Protocol(const GameState_t* game_state, Game_State_Data_t* protocol_state)
{
  if (!game_state || !protocol_state) {
    return;
  }

  // Copy board state (convert from PieceType_t to uint8_t)
  for (int row = 0; row < 8; row++) {
    for (int col = 0; col < 8; col++) {
      protocol_state->board[row][col] = (uint8_t)game_state->board[row][col];
    }
  }

  protocol_state->current_player = (uint8_t)game_state->current_player;
  protocol_state->black_count = game_state->black_count;
  protocol_state->white_count = game_state->white_count;
  protocol_state->game_over = (game_state->status != GAME_STATUS_PLAYING) ? 1 : 0;
  protocol_state->move_count = game_state->move_count;
}

/**
 * @brief Send game state via protocol (wrapper function)
 * @param game_state Source game state
 * @return Protocol_Status_t Protocol status
 */
static Protocol_Status_t Send_GameState_Via_Protocol(const GameState_t* game_state)
{
  Game_State_Data_t protocol_state;
  Convert_GameState_to_Protocol(game_state, &protocol_state);
  return Protocol_SendGameState(&protocol_state);
}
/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_DMA_Init();
  MX_TIM2_Init();
  MX_USART1_UART_Init();
  /* USER CODE BEGIN 2 */
  /* IMPORTANT: Debug output must be AFTER USART1 initialization */
  HAL_Delay(100);  // Small delay to allow UART to stabilize

  DEBUG_PRINT_BANNER();
  DEBUG_INFO("[INIT] HAL Initialized\r\n");
  DEBUG_INFO("[INIT] System Clock Configured\r\n");
  DEBUG_INFO("[INIT] GPIO Initialized\r\n");
  DEBUG_INFO("[INIT] DMA Initialized\r\n");
  DEBUG_INFO("[INIT] TIM2 Initialized\r\n");
  DEBUG_INFO("[INIT] USART1 Initialized\r\n");

  /* Enable DWT counter for microsecond delays */
  CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
  DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;

  /* Initialize WS2812B driver */
  if (WS2812B_Init() != WS2812B_OK) {
    DEBUG_ERROR("[INIT] WS2812B Driver...FAILED\r\n");
    Error_Handler(); /* WS2812B initialization failed */
  }
  DEBUG_INFO("[INIT] WS2812B Driver...OK\r\n");

  /* Initialize Keypad driver */
  Keypad_Status_t keypad_status = Keypad_Init();
  if (keypad_status != KEYPAD_OK) {
    DEBUG_ERROR("[INIT] Keypad Driver...FAILED (status=%d)\r\n", keypad_status);
    Error_Handler(); /* Keypad initialization failed */
  }
  DEBUG_INFO("[INIT] Keypad Driver...OK\r\n");

  /* Test keypad quick check (disabled when DEBUG is off) */
  #if ENABLE_DEBUG
  bool any_key = Keypad_Quick_Check();
  DEBUG_INFO("[INIT] Keypad Quick Check: %s\r\n", any_key ? "Keys detected" : "No keys");
  #else
  (void)Keypad_Quick_Check();  /* Run check but ignore result when debug disabled */
  #endif

  /* Initialize UART Protocol (USART1 for PC communication) */
  if (Protocol_Init() != PROTOCOL_OK) {
    /* Protocol initialization failed - indicate with LED */
    /* Flash all LEDs red as error indicator */
    for (uint8_t i = 0; i < 8; i++) {
      for (uint8_t j = 0; j < 8; j++) {
        WS2812B_SetPixel(i, j, WS2812B_COLOR_RED);
      }
    }
    WS2812B_Update();
    Error_Handler();
  }

  /* Protocol initialized successfully - send initial heartbeat */
  HAL_Delay(100);  /* Wait for UART to stabilize */
  Protocol_SendHeartbeat();

  /* Register keypad event callback */
  Keypad_Register_Callback(Keypad_Key_Event_Handler);

  /* Register protocol command callback */
  Protocol_RegisterCallback(Protocol_Command_Handler);

  /* Initialize game engine */
  if (Othello_Init() != OTHELLO_OK) {
    DEBUG_ERROR("[INIT] Othello Engine...FAILED\r\n");
    Error_Handler(); /* Game engine initialization failed */
  }
  DEBUG_INFO("[INIT] Othello Engine...OK\r\n");

  /* Application-specific initialization */
  App_Init();
  DEBUG_INFO("[INIT] Application...OK\r\n");

  DEBUG_INFO("[BOOT] System Ready!\r\n");
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
    /* Main application loop */
    App_Main_Loop();

    /* Keypad scanning (if not using interrupt-driven mode) */
    Keypad_Scan_Task();

    /* Update cursor blinking */
    App_UpdateCursor();

    /* Protocol maintenance tasks (heartbeat & timeout handling) */
    Protocol_Task();

    /* Small delay to prevent excessive CPU usage */
    HAL_Delay(1);
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL9;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief TIM2 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM2_Init(void)
{

  /* USER CODE BEGIN TIM2_Init 0 */

  /* USER CODE END TIM2_Init 0 */

  TIM_ClockConfigTypeDef sClockSourceConfig = {0};
  TIM_MasterConfigTypeDef sMasterConfig = {0};
  TIM_OC_InitTypeDef sConfigOC = {0};

  /* USER CODE BEGIN TIM2_Init 1 */

  /* USER CODE END TIM2_Init 1 */
  htim2.Instance = TIM2;
  htim2.Init.Prescaler = 0;
  htim2.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim2.Init.Period = 90-1;
  htim2.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim2.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
  if (HAL_TIM_Base_Init(&htim2) != HAL_OK)
  {
    Error_Handler();
  }
  sClockSourceConfig.ClockSource = TIM_CLOCKSOURCE_INTERNAL;
  if (HAL_TIM_ConfigClockSource(&htim2, &sClockSourceConfig) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_PWM_Init(&htim2) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim2, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sConfigOC.OCMode = TIM_OCMODE_PWM1;
  sConfigOC.Pulse = 0;
  sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
  sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
  if (HAL_TIM_PWM_ConfigChannel(&htim2, &sConfigOC, TIM_CHANNEL_1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM2_Init 2 */

  /* USER CODE END TIM2_Init 2 */
  HAL_TIM_MspPostInit(&htim2);

}

/**
  * @brief USART1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART1_UART_Init(void)
{

  /* USER CODE BEGIN USART1_Init 0 */

  /* USER CODE END USART1_Init 0 */

  /* USER CODE BEGIN USART1_Init 1 */

  /* USER CODE END USART1_Init 1 */
  huart1.Instance = USART1;
  huart1.Init.BaudRate = 115200;
  huart1.Init.WordLength = UART_WORDLENGTH_8B;
  huart1.Init.StopBits = UART_STOPBITS_1;
  huart1.Init.Parity = UART_PARITY_NONE;
  huart1.Init.Mode = UART_MODE_TX_RX;
  huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart1.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART1_Init 2 */

  /* USER CODE END USART1_Init 2 */

}

/**
  * Enable DMA controller clock
  */
static void MX_DMA_Init(void)
{

  /* DMA controller clock enable */
  __HAL_RCC_DMA1_CLK_ENABLE();

  /* DMA interrupt init */
  /* DMA1_Channel5_IRQn interrupt configuration */
  HAL_NVIC_SetPriority(DMA1_Channel5_IRQn, 2, 0);
  HAL_NVIC_EnableIRQ(DMA1_Channel5_IRQn);

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};
  /* USER CODE BEGIN MX_GPIO_Init_1 */

  /* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOD_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOB, KEY_R1_Pin|KEY_R2_Pin|KEY_R3_Pin|KEY_R4_Pin, GPIO_PIN_SET);

  /*Configure GPIO pins : KEY_R1_Pin KEY_R2_Pin KEY_R3_Pin KEY_R4_Pin */
  GPIO_InitStruct.Pin = KEY_R1_Pin|KEY_R2_Pin|KEY_R3_Pin|KEY_R4_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  /*Configure GPIO pins : KEY_C1_Pin KEY_C2_Pin KEY_C3_Pin KEY_C4_Pin */
  GPIO_InitStruct.Pin = KEY_C1_Pin|KEY_C2_Pin|KEY_C3_Pin|KEY_C4_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  /* USER CODE BEGIN MX_GPIO_Init_2 */

  /* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */
/**
 * @brief DMA transfer complete callback for WS2812B
 * @param hdma: DMA handle
 * @retval None
 */
void HAL_TIM_PWM_PulseFinishedCallback(TIM_HandleTypeDef *htim)
{
  /* Check if this is TIM2 channel 1 */
  if (htim->Instance == TIM2) {
    WS2812B_DMA_Complete_Callback(&hdma_tim2_ch1);
  }
}

/**
 * @brief WS2812B DMA Complete IRQ Handler (called from main.h)
 * @retval None
 */
void WS2812B_DMA_Complete_IRQ_Handler(void)
{
  WS2812B_DMA_Complete_Callback(&hdma_tim2_ch1);
}

/**
 * @brief Application initialization function
 * @retval None
 */
void App_Init(void)
{
  /* Initialize game statistics */
  memset(&game_stats, 0, sizeof(GameStats_t));

  /* Initialize game control module */
  if (Game_Control_Init() != GAME_CTRL_OK) {
    DEBUG_ERROR("[INIT] Game Control...FAILED\r\n");
    Error_Handler();
  }
  DEBUG_INFO("[INIT] Game Control...OK\r\n");

  /* Initialize challenge mode module */
  if (Challenge_Init() != CHALLENGE_OK) {
    DEBUG_ERROR("[INIT] Challenge Mode...FAILED\r\n");
    Error_Handler();
  }
  DEBUG_INFO("[INIT] Challenge Mode...OK\r\n");

  /* Initialize LED text display module */
  if (LED_Text_Init() != LED_TEXT_OK) {
    DEBUG_ERROR("[INIT] LED Text...FAILED\r\n");
    Error_Handler();
  }
  DEBUG_INFO("[INIT] LED Text...OK\r\n");

  /* Start new game */
  if (Othello_NewGame(&game_state) == OTHELLO_OK) {
    game_initialized = true;
  }

  /* Initialize LED display */
  WS2812B_Clear();

  /* Display initial game board */
  App_DisplayGameBoard();
}

/**
 * @brief Main application loop function
 * @retval None
 */
void App_Main_Loop(void)
{
  /* === Priority 1: Process pending game end (set from interrupt context) === */
  if (game_end_pending) {
    game_end_pending = false;  // Clear flag
    DEBUG_INFO("[APP_LOOP] Processing pending game end from interrupt...\r\n");
    App_HandleGameOver();  // Safe to call in main loop context
    DEBUG_INFO("[APP_LOOP] Game end processing completed\r\n");
    return;  // Process only game end in this iteration
  }

  /* Process keypad events */
  Key_t key_event = Keypad_GetKey();
  if (key_event.state != KEY_RELEASED) {
    /* Key event occurred, process it */
    App_ProcessKeyEvent(&key_event);
  }

  /* Update game board display */
  App_UpdateGameDisplay();

  /* Check for game over conditions (local game end) */
  if (game_initialized && Othello_IsGameOver(&game_state)) {
    App_HandleGameOver();
  }
}

/**
 * @brief Update cursor display with blinking effect
 * @retval None
 */
void App_UpdateCursor(void)
{
  if (!game_initialized) {
    return;
  }

  uint32_t current_time = HAL_GetTick();

  // Toggle cursor visibility every 500ms
  if (current_time - cursor_blink_timer >= 500) {
    cursor_blink_timer = current_time;
    cursor_visible = !cursor_visible;

    // Redraw board to update cursor
    App_DisplayGameBoard();
  }
}

/**
 * @brief Display game board on LED matrix
 * @retval None
 */
void App_DisplayGameBoard(void)
{
  if (!game_initialized) {
    return;
  }

  WS2812B_Clear();

  /* Display game pieces on LED matrix */
  for (uint8_t row = 0; row < 8; row++) {
    for (uint8_t col = 0; col < 8; col++) {
      PieceType_t piece = Othello_GetPiece(&game_state, row, col);

      if (piece == PIECE_BLACK) {
        WS2812B_SetPixel(row, col, WS2812B_COLOR_ORANGE);  // Black piece (Orange for visibility)
      } else if (piece == PIECE_WHITE) {
        WS2812B_SetPixel(row, col, WS2812B_COLOR_WHITE);  // White piece
      }
      /* Empty positions remain off */
    }
  }

  /* Display cursor (green blinking) */
  if (cursor_visible) {
    PieceType_t cursor_piece = Othello_GetPiece(&game_state, cursor_row, cursor_col);
    if (cursor_piece == PIECE_EMPTY) {
      // Empty position: show green cursor
      WS2812B_SetPixel(cursor_row, cursor_col, WS2812B_COLOR_GREEN);
    }
    // If there's a piece at cursor position, don't show cursor (or could use dimmed green)
  }

  WS2812B_Update();
}

/**
 * @brief Process key event for game controls
 * @param key_event Pointer to key event structure
 * @retval None
 */
void App_ProcessKeyEvent(Key_t* key_event)
{
  if (!game_initialized || !key_event) {
    return;
  }

  Keypad_LogicalKey_t logical_key = Keypad_PhysicalToLogical(key_event->row, key_event->col);

  DEBUG_INFO("[APP] ProcessKey: R%d C%d Logical=%d State=%d\r\n",
             key_event->row, key_event->col, logical_key, key_event->state);

  /* Handle key press */
  if (key_event->state == KEY_PRESSED) {
    // First, try to handle as game control key
    if (Game_Control_HandleKey(logical_key, &game_state)) {
      DEBUG_INFO("[APP] Game control key handled: %d\r\n", logical_key);
      App_DisplayGameBoard();
      Send_GameState_Via_Protocol(&game_state);
      return;  // Key was handled by game control
    }

    // Handle 'C' key for cheat mode toggle
    if (logical_key == KEYPAD_KEY_C) {
      // Toggle cheat mode
      if (current_game_mode == GAME_MODE_CHEAT) {
        // Exit cheat mode, return to normal mode
        current_game_mode = GAME_MODE_NORMAL;
        game_state.game_mode = GAME_MODE_NORMAL;
        game_state.current_player = PIECE_BLACK;
        DEBUG_INFO("[APP] Exited cheat mode -> Normal mode\r\n");
      } else {
        // Enter cheat mode
        current_game_mode = GAME_MODE_CHEAT;
        Othello_ResetState(&game_state);
        game_state.game_mode = GAME_MODE_CHEAT;
        // Keep current_player as is (will be set by PC or default BLACK)
        DEBUG_INFO("[APP] Entered cheat mode\r\n");
      }

      App_DisplayGameBoard();
      Send_GameState_Via_Protocol(&game_state);
      return;
    }

    // Check if game is in playing state before processing game keys
    if (!GAME_CTRL_IS_PLAYING(Game_Control_GetContext())) {
      DEBUG_INFO("[APP] Game not in PLAYING state, ignoring key\r\n");
      return;
    }

    switch (logical_key) {
      // === Core Function Keys ===

      case KEYPAD_KEY_1: // Start Game (handled by game control above)
        // This case is now handled by Game_Control_HandleKey
        break;

      case KEYPAD_KEY_2: // Move Up
        if (cursor_row > 0) {
          cursor_row--;
          DEBUG_INFO("[APP] Cursor UP: (%d,%d)\r\n", cursor_row, cursor_col);
          cursor_visible = true;  // Show cursor immediately when moving
          cursor_blink_timer = HAL_GetTick();  // Reset blink timer
          App_DisplayGameBoard();
        } else {
          DEBUG_INFO("[APP] Cursor at top edge\r\n");
        }
        break;

      case KEYPAD_KEY_4: // Move Left
        if (cursor_col > 0) {
          cursor_col--;
          DEBUG_INFO("[APP] Cursor LEFT: (%d,%d)\r\n", cursor_row, cursor_col);
          cursor_visible = true;
          cursor_blink_timer = HAL_GetTick();
          App_DisplayGameBoard();
        } else {
          DEBUG_INFO("[APP] Cursor at left edge\r\n");
        }
        break;

      case KEYPAD_KEY_5: // Place Piece at Cursor
        DEBUG_INFO("[APP] Place piece at cursor (%d,%d)\r\n", cursor_row, cursor_col);
        if (Othello_IsValidMove(&game_state, cursor_row, cursor_col, game_state.current_player)) {
          uint8_t flipped = Othello_MakeMove(&game_state, cursor_row, cursor_col, game_state.current_player);
          if (flipped > 0) {
            DEBUG_INFO("[APP] Move SUCCESS: flipped %d pieces\r\n", flipped);
            App_DisplayGameBoard();
            Send_GameState_Via_Protocol(&game_state);

            // Check if game is over
            if (game_state.status != GAME_STATUS_PLAYING) {
              DEBUG_INFO("[APP] Game Over! Winner: %d\r\n",
                        Othello_GetWinner(&game_state));
              // Print game history to debug console
              App_PrintGameHistory();
              // PC will show AI analysis dialog
            }
          }
        } else {
          DEBUG_INFO("[APP] Invalid move at (%d,%d)\r\n", cursor_row, cursor_col);
          // Invalid move - red flash
          WS2812B_SetPixel(cursor_row, cursor_col, WS2812B_COLOR_RED);
          WS2812B_Update();
          HAL_Delay(200);
          App_DisplayGameBoard();
        }
        break;

      case KEYPAD_KEY_6: // Move Right
        if (cursor_col < 7) {
          cursor_col++;
          DEBUG_INFO("[APP] Cursor RIGHT: (%d,%d)\r\n", cursor_row, cursor_col);
          cursor_visible = true;
          cursor_blink_timer = HAL_GetTick();
          App_DisplayGameBoard();
        } else {
          DEBUG_INFO("[APP] Cursor at right edge\r\n");
        }
        break;

      case KEYPAD_KEY_8: // Move Down
        if (cursor_row < 7) {
          cursor_row++;
          DEBUG_INFO("[APP] Cursor DOWN: (%d,%d)\r\n", cursor_row, cursor_col);
          cursor_visible = true;
          cursor_blink_timer = HAL_GetTick();
          App_DisplayGameBoard();
        } else {
          DEBUG_INFO("[APP] Cursor at bottom edge\r\n");
        }
        break;

      case KEYPAD_KEY_0: // Reset Game
        DEBUG_INFO("[APP] Reset Game\r\n");
        Othello_NewGame(&game_state);
        cursor_row = 3;
        cursor_col = 3;
        cursor_visible = true;
        App_DisplayGameBoard();
        break;

      case KEYPAD_KEY_9: // Send Board State to PC
        DEBUG_INFO("[APP] Send board state to PC\r\n");
        Send_GameState_Via_Protocol(&game_state);
        break;

      // === Reserved Function Keys ===

      case KEYPAD_KEY_3:
        DEBUG_INFO("[APP] Key 3 - Reserved\r\n");
        break;

      case KEYPAD_KEY_7:
        DEBUG_INFO("[APP] Key 7 - Reserved\r\n");
        break;

      case KEYPAD_KEY_STAR:
        DEBUG_INFO("[APP] Key * - Reserved (Menu)\r\n");
        break;

      case KEYPAD_KEY_HASH:
        DEBUG_INFO("[APP] Key # - Reserved (Confirm)\r\n");
        break;

      case KEYPAD_KEY_A:
        DEBUG_INFO("[APP] Key A - Reserved\r\n");
        break;

      case KEYPAD_KEY_B:
        DEBUG_INFO("[APP] Key B - Reserved\r\n");
        break;

      case KEYPAD_KEY_C:
        DEBUG_INFO("[APP] Key C - Reserved\r\n");
        break;

      case KEYPAD_KEY_D:
        DEBUG_INFO("[APP] Key D - Reserved\r\n");
        break;

      default:
        DEBUG_INFO("[APP] Unknown key: %d\r\n", logical_key);
        break;
    }
  }
}

/**
 * @brief Print game history to debug console
 * @retval None
 * @note Since full move history is not stored, we print summary statistics
 */
void App_PrintGameHistory(void)
{
  if (!game_initialized) {
    return;
  }

  DEBUG_INFO("\r\n========== Game History ==========\r\n");
  DEBUG_INFO("Total moves: %lu\r\n", game_state.move_count);
  DEBUG_INFO("Black count: %d, White count: %d\r\n",
             game_state.black_count, game_state.white_count);
  DEBUG_INFO("Game status: %d\r\n", game_state.status);

  if (game_state.move_count > 0) {
    DEBUG_INFO("\r\nLast move:\r\n");
    DEBUG_INFO("  Player: %d, Position: (%d,%d), Flipped: %d\r\n",
               game_state.last_move.player,
               game_state.last_move.row,
               game_state.last_move.col,
               game_state.last_move.flipped_count);
  }

  if (game_state.status != GAME_STATUS_PLAYING) {
    PieceType_t winner = Othello_GetWinner(&game_state);
    DEBUG_INFO("\r\nGame Result:\r\n");
    if (winner == PIECE_BLACK) {
      DEBUG_INFO("  Winner: BLACK (Orange)\r\n");
    } else if (winner == PIECE_WHITE) {
      DEBUG_INFO("  Winner: WHITE\r\n");
    } else {
      DEBUG_INFO("  Result: DRAW\r\n");
    }
  }

  DEBUG_INFO("==================================\r\n\r\n");
}

/**
 * @brief Update game display (animations, status indicators)
 * @retval None
 */
void App_UpdateGameDisplay(void)
{
  static uint32_t last_update = 0;
  uint32_t current_time = HAL_GetTick();

  /* Update display every 100ms */
  if (current_time - last_update >= 100) {
    last_update = current_time;

    /* Could add animations here, like cursor blinking */
    /* For now, just ensure board is current */
    if (game_initialized) {
      App_DisplayGameBoard();
    }
  }
}

/**
 * @brief Handle game over state
 * @retval None
 */
void App_HandleGameOver(void)
{
  static uint32_t last_handled_move_count = 0;

  // 检查是否已经处理过这局游戏（使用move_count作为版本号）
  if (game_state.move_count == last_handled_move_count) {
    DEBUG_INFO("[GAME_OVER] Already handled move_count=%lu, skipping\r\n", game_state.move_count);
    return;  // 已经处理过这局游戏
  }

  // 记录当前游戏的move_count
  last_handled_move_count = game_state.move_count;

  DEBUG_INFO("\r\n========== GAME OVER HANDLER START ==========\r\n");
  DEBUG_INFO("[GAME_OVER] Handling game over, move_count=%lu\r\n", game_state.move_count);
  DEBUG_INFO("[GAME_OVER] current_game_mode=%d (CHALLENGE=%d)\r\n",
             current_game_mode, GAME_MODE_CHALLENGE);
  DEBUG_INFO("[GAME_OVER] Winner: BLACK=%d WHITE=%d status=%d\r\n",
             game_state.black_count, game_state.white_count, game_state.status);

  // 设置正在显示结果的标志
  is_displaying_result = true;
  DEBUG_INFO("[GAME_OVER] Set is_displaying_result = TRUE\r\n");

  /* Update statistics */
  Othello_UpdateStats(&game_stats, &game_state);

  /* === 显示游戏结果文字（所有模式通用） === */
  PieceType_t winner = Othello_GetWinner(&game_state);

  DEBUG_INFO("[GAME_OVER] Displaying game result: Winner=%d (BLACK=%d, WHITE=%d)\r\n",
             winner, PIECE_BLACK, PIECE_WHITE);

  if (winner == PIECE_BLACK) {
    // Player (BLACK) wins - show WIN (letter by letter)
    DEBUG_INFO("[GAME_OVER] Displaying 'WIN' letter by letter...\r\n");
    LED_Text_Display_Sequential("W", WS2812B_COLOR_GREEN, 1000);
    LED_Text_Display_Sequential("I", WS2812B_COLOR_GREEN, 1000);
    LED_Text_Display_Sequential("N", WS2812B_COLOR_GREEN, 1000);
    DEBUG_INFO("[GAME_OVER] 'WIN' display completed\r\n");
  } else if (winner == PIECE_WHITE) {
    // AI/Opponent (WHITE) wins - show LOSE (letter by letter)
    DEBUG_INFO("[GAME_OVER] Displaying 'LOSE' letter by letter...\r\n");
    LED_Text_Display_Sequential("L", WS2812B_COLOR_RED, 1000);
    LED_Text_Display_Sequential("O", WS2812B_COLOR_RED, 1000);
    LED_Text_Display_Sequential("S", WS2812B_COLOR_RED, 1000);
    LED_Text_Display_Sequential("E", WS2812B_COLOR_RED, 1000);
    DEBUG_INFO("[GAME_OVER] 'LOSE' display completed\r\n");
  } else {
    // Draw game - show DRAW (letter by letter)
    DEBUG_INFO("[GAME_OVER] Displaying 'DRAW' letter by letter...\r\n");
    LED_Text_Display_Sequential("D", WS2812B_COLOR_YELLOW, 1000);
    LED_Text_Display_Sequential("R", WS2812B_COLOR_YELLOW, 1000);
    LED_Text_Display_Sequential("A", WS2812B_COLOR_YELLOW, 1000);
    LED_Text_Display_Sequential("W", WS2812B_COLOR_YELLOW, 1000);
    DEBUG_INFO("[GAME_OVER] 'DRAW' display completed\r\n");
  }

  // Clear display after text sequence
  DEBUG_INFO("[GAME_OVER] Clearing display...\r\n");
  WS2812B_Clear();
  WS2812B_Update();
  HAL_Delay(500);  // Brief pause before final board display

  /* Process challenge mode if active */
  if (current_game_mode == GAME_MODE_CHALLENGE) {
    DEBUG_INFO("[CHALLENGE] Processing challenge mode results...\r\n");

    /* === Process overall challenge status === */
    Challenge_Status_t challenge_status = Challenge_ProcessGameResult(&game_state);

    DEBUG_INFO("[CHALLENGE] Challenge status after processing: %d\r\n", challenge_status);

    if (challenge_status == CHALLENGE_WIN) {
      DEBUG_INFO("[CHALLENGE] WIN condition met! Total score: %d\r\n",
                 Challenge_GetTotalScore());
      DEBUG_INFO("[CHALLENGE] Displaying 'WIN' animation (3 seconds)...\r\n");
      // LED text display is handled by Challenge_ProcessGameResult
      HAL_Delay(3000);  // Display WIN for 3 seconds
      DEBUG_INFO("[CHALLENGE] WIN animation completed\r\n");
    } else if (challenge_status == CHALLENGE_GAME_OVER) {
      DEBUG_INFO("[CHALLENGE] GAME OVER! Consecutive losses: %d\r\n",
                 Challenge_GetConsecutiveLosses());
      DEBUG_INFO("[CHALLENGE] Displaying 'OVER' animation (3 seconds)...\r\n");
      // LED text display is handled by Challenge_ProcessGameResult
      HAL_Delay(3000);  // Display OVER for 3 seconds
      DEBUG_INFO("[CHALLENGE] OVER animation completed\r\n");
    } else {
      DEBUG_INFO("[CHALLENGE] Game %d completed. Total score: %d\r\n",
                 Challenge_GetGamesPlayed(), Challenge_GetTotalScore());
    }
  }

  /* Show winner on board */
  DEBUG_INFO("[GAME_OVER] Displaying final board state...\r\n");
  WS2812B_Clear();

  if (winner == PIECE_BLACK) {
    /* Display black wins - fill with black */
    WS2812B_Fill(WS2812B_COLOR_BLACK);
  } else if (winner == PIECE_WHITE) {
    /* Display white wins - fill with white */
    WS2812B_Fill(WS2812B_COLOR_WHITE);
  } else {
    /* Display draw - alternate black/white pattern */
    for (uint8_t row = 0; row < 8; row++) {
      for (uint8_t col = 0; col < 8; col++) {
        RGB_Color_t color = ((row + col) % 2 == 0) ? WS2812B_COLOR_BLACK : WS2812B_COLOR_WHITE;
        WS2812B_SetPixel(row, col, color);
      }
    }
  }

  WS2812B_Update();

  /* Send final game state */
  DEBUG_INFO("[GAME_OVER] Sending final game state to PC...\r\n");
  Send_GameState_Via_Protocol(&game_state);

  /* Show result for 5 seconds */
  DEBUG_INFO("[GAME_OVER] Displaying result for 5 seconds...\r\n");
  HAL_Delay(5000);

  // 清除正在显示结果的标志
  is_displaying_result = false;
  DEBUG_INFO("[GAME_OVER] Set is_displaying_result = FALSE\r\n");

  DEBUG_INFO("========== GAME OVER HANDLER END ==========\r\n\r\n");
}

/**
 * @brief Keypad key event callback handler
 * @param row: Key row position (0-3)
 * @param col: Key column position (0-3)
 * @param state: Key state (PRESSED, RELEASED, LONG_PRESSED)
 * @retval None
 */
void Keypad_Key_Event_Handler(uint8_t row, uint8_t col, KeyState_t state)
{
  /* This callback is called whenever a key state changes */
  /* Get logical key for more meaningful processing */
  Keypad_LogicalKey_t logical_key = Keypad_PhysicalToLogical(row, col);

  /* Debug log */
  DEBUG_INFO("[APP] KeyEvent: R%d C%d State=%d Logical=%d\r\n", row, col, state, logical_key);

  /* Send key event over UART protocol */
  Protocol_SendKeyEvent(row, col, (uint8_t)state, (uint8_t)logical_key);

  /* Demo: Simple LED feedback for key press */
  if (state == KEY_PRESSED) {
    /* Key just pressed - could add sound effect, LED flash, etc. */
    /* For now, just ensure immediate visual feedback */
    if (row < 8 && col < 8) {
      WS2812B_SetPixel(row, col, WS2812B_COLOR_GREEN);
      WS2812B_Update();
    }
  } else if (state == KEY_RELEASED) {
    /* Key released - restore normal display */
    /* This will be handled in App_Main_Loop for now */
  }

  /* Future: Add game logic event processing here */
  /* Example:
   * switch (logical_key) {
   *   case KEYPAD_KEY_5: // Select key
   *     if (state == KEY_PRESSED) {
   *       Game_ProcessMove();
   *     }
   *     break;
   *   case KEYPAD_KEY_STAR: // Menu key
   *     if (state == KEY_PRESSED) {
   *       Game_EnterMenu();
   *     }
   *     break;
   *   // ... other keys
   * }
   */
}

/**
 * @brief UART protocol command handler
 * @param cmd Received command
 * @param data Command data
 * @param len Data length
 * @retval None
 */
void Protocol_Command_Handler(Protocol_Command_t cmd, uint8_t* data, uint8_t len)
{
  /* Handle incoming protocol commands */
  switch (cmd) {
    case CMD_MAKE_MOVE:
      if (len == sizeof(Move_Command_Data_t)) {
        Move_Command_Data_t* move = (Move_Command_Data_t*)data;
        if (Othello_IsValidMove(&game_state, move->row, move->col, game_state.current_player)) {
          uint8_t flipped = Othello_MakeMove(&game_state, move->row, move->col, game_state.current_player);
          if (flipped > 0) {
            App_DisplayGameBoard();  // Update display
            Protocol_SendAck(cmd, 0); // 0 = success
            // REMOVED: 避免旧状态覆盖上位机的新状态
            // Send_GameState_Via_Protocol(&game_state);
          } else {
            Protocol_SendAck(cmd, 2); // 2 = move failed
          }
        } else {
          Protocol_SendAck(cmd, 1); // 1 = invalid move
        }
      } else {
        Protocol_SendAck(cmd, 3); // 3 = invalid length
      }
      break;

    case CMD_GAME_CONFIG:
      /* Handle game configuration / new game command */
      Othello_NewGame(&game_state);  // Reset game state to initial
      App_DisplayGameBoard();  // Refresh display
      Protocol_SendAck(cmd, 0);  // Send success confirmation
      Send_GameState_Via_Protocol(&game_state);  // Send initial board state
      break;

    case CMD_SYSTEM_INFO:
      /* Send system information */
      Protocol_SendSystemInfo();
      break;

    case CMD_AI_REQUEST:
      /* Handle AI analysis request */
      /* Send current game state for analysis */
      Send_GameState_Via_Protocol(&game_state);
      Protocol_SendAck(cmd, 0);
      break;

    case CMD_LED_CONTROL:
      /* Handle LED control commands */
      if (len >= 4) { // row, col, r, g, b
        uint8_t row = data[0];
        uint8_t col = data[1];
        RGB_Color_t color = {data[2], data[3], len > 4 ? data[4] : 0};
        if (row < 8 && col < 8) {
          WS2812B_SetPixel(row, col, color);
          WS2812B_Update();
          Protocol_SendAck(cmd, 0);
        } else {
          Protocol_SendAck(cmd, 2); // Invalid coordinates
        }
      } else {
        Protocol_SendAck(cmd, 1); // Invalid length
      }
      break;

    case CMD_HEARTBEAT:
      /* Respond to heartbeat */
      Protocol_SendHeartbeat();
      break;

    case CMD_BOARD_STATE:
      /* Receive and update game state from PC (Sync direction: PC → STM32) */

      // ========== 防止显示期间被覆盖 ==========
      if (is_displaying_result) {
        // 拒绝在显示游戏结果期间更新状态
        Protocol_SendAck(cmd, 4);  // 4 = Busy/Rejected
        DEBUG_INFO("[SYNC] Refused state update: displaying game result\r\n");
        break;
      }

      // ========== 正常状态更新流程 ==========
      if (len == 72) {  // Game_State_Data_t = 72 bytes
        // ========== 解析上位机发来的完整状态 ==========

        // 1. 更新棋盘 (0-63字节)
        for (uint8_t i = 0; i < 64; i++) {
          uint8_t row = i / 8;
          uint8_t col = i % 8;
          game_state.board[row][col] = (PieceType_t)data[i];
        }

        // 2. 更新当前玩家 (64字节)
        game_state.current_player = (PieceType_t)data[64];

        // 3. 更新棋子计数 (65-66字节)
        game_state.black_count = data[65];
        game_state.white_count = data[66];

        // 4. 更新游戏结束标志 (67字节)
        bool game_just_ended = false;  // 标记游戏是否刚刚结束
        if (data[67] == 1) {
          // 根据分数设置状态
          if (game_state.black_count > game_state.white_count) {
            game_state.status = GAME_STATUS_BLACK_WIN;
          } else if (game_state.black_count < game_state.white_count) {
            game_state.status = GAME_STATUS_WHITE_WIN;
          } else {
            game_state.status = GAME_STATUS_DRAW;
          }
          game_just_ended = true;  // 标记游戏结束
        } else {
          game_state.status = GAME_STATUS_PLAYING;
        }

        // 5. 更新走法计数 (68-71字节, little-endian)
        game_state.move_count = data[68] | ((uint32_t)data[69] << 8) |
                               ((uint32_t)data[70] << 16) | ((uint32_t)data[71] << 24);

        // ========== 如果游戏刚结束，设置标志让主循环处理（避免中断阻塞） ==========
        if (game_just_ended) {
          DEBUG_INFO("[SYNC] Game ended from PC, status=%d, setting game_end_pending flag\r\n", game_state.status);
          game_end_pending = true;  // 只设置标志，不阻塞中断
          App_DisplayGameBoard();    // 快速更新棋盘显示
        } else {
          // 游戏进行中，只更新棋盘显示
          App_DisplayGameBoard();
        }

        // 发送确认
        Protocol_SendAck(cmd, 0);  // Success

        DEBUG_INFO("[SYNC] Game state updated from PC: move_count=%lu, "
                   "player=%d, black=%d, white=%d\r\n",
                   game_state.move_count, game_state.current_player,
                   game_state.black_count, game_state.white_count);
      } else {
        // 数据长度错误
        Protocol_SendAck(cmd, 1);  // Invalid length
        DEBUG_ERROR("[SYNC] Invalid data length: %d (expected 72)\r\n", len);
      }
      break;

    case CMD_GAME_CONTROL:
      /* Handle game control commands */
      if (len == sizeof(Game_Control_Data_t)) {
        Game_Control_Data_t* ctrl_data = (Game_Control_Data_t*)data;
        Game_Control_Status_t status = Game_Control_HandleAction(
            (Game_Control_Action_t)ctrl_data->action, &game_state);

        if (status == GAME_CTRL_OK) {
          App_DisplayGameBoard();  // Update display
          Protocol_SendAck(cmd, 0);  // Success
          Send_GameState_Via_Protocol(&game_state);  // Send updated state
        } else if (status == GAME_CTRL_INVALID_STATE) {
          Protocol_SendAck(cmd, 1);  // Invalid state for this action
        } else {
          Protocol_SendAck(cmd, 2);  // Other error
        }
      } else {
        Protocol_SendAck(cmd, 3);  // Invalid length
      }
      break;

    case CMD_MODE_SELECT:
      /* Handle game mode selection */
      if (len == sizeof(Mode_Select_Data_t)) {
        Mode_Select_Data_t* mode_data = (Mode_Select_Data_t*)data;
        current_game_mode = (Game_Mode_t)mode_data->mode;

        if (current_game_mode == GAME_MODE_CHALLENGE) {
          // Start challenge mode
          if (Challenge_Start() == CHALLENGE_OK) {
            DEBUG_INFO("[MODE] Challenge mode started\r\n");
            Protocol_SendAck(cmd, 0);  // Success
          } else {
            Protocol_SendAck(cmd, 2);  // Challenge start failed
          }
        } else if (current_game_mode == GAME_MODE_NORMAL) {
          // End challenge mode if active
          if (Challenge_GetState() != CHALLENGE_STATE_INACTIVE) {
            Challenge_End();
          }
          DEBUG_INFO("[MODE] Normal mode selected\r\n");
          Protocol_SendAck(cmd, 0);  // Success
        } else if (current_game_mode == GAME_MODE_TIMED) {
          // Timed mode not yet implemented
          DEBUG_INFO("[MODE] Timed mode not yet implemented\r\n");
          Protocol_SendAck(cmd, 1);  // Not implemented
        } else if (current_game_mode == GAME_MODE_CHEAT) {
          // Cheat mode: free placement mode
          // End challenge mode if active
          if (Challenge_GetState() != CHALLENGE_STATE_INACTIVE) {
            Challenge_End();
          }

          // Reset game and set cheat mode
          Othello_ResetState(&game_state);
          game_state.game_mode = GAME_MODE_CHEAT;

          DEBUG_INFO("[MODE] Cheat mode selected - waiting for color selection\r\n");
          Protocol_SendAck(cmd, 0);  // Success

          // Send current game state to PC
          Send_GameState_Via_Protocol(&game_state);
        } else {
          Protocol_SendAck(cmd, 3);  // Invalid mode
        }
      } else {
        Protocol_SendAck(cmd, 4);  // Invalid length
      }
      break;

    case CMD_TIMER_UPDATE:
      /* Handle timer update from PC (timed mode) */
      if (len >= 2) {
        // Extract remaining time (2 bytes, big-endian)
        uint16_t remaining_time = (data[0] << 8) | data[1];

        // Optional: Display time on LED matrix if needed
        // For now, just acknowledge receipt
        DEBUG_INFO("[TIMER] Remaining: %d seconds\r\n", remaining_time);
        (void)remaining_time;  // Avoid unused variable warning when DEBUG is disabled
        Protocol_SendAck(cmd, 0);  // Success
      } else {
        Protocol_SendAck(cmd, 1);  // Invalid length
      }
      break;

    case CMD_CHEAT_COLOR_SELECT:
      /* Handle cheat mode color selection */
      if (len == sizeof(Cheat_Color_Select_Data_t)) {
        Cheat_Color_Select_Data_t* color_data = (Cheat_Color_Select_Data_t*)data;

        // Validate color (1=BLACK, 2=WHITE)
        if (color_data->player_color != PIECE_BLACK &&
            color_data->player_color != PIECE_WHITE) {
          DEBUG_ERROR("[CHEAT] Invalid color: %d\r\n", color_data->player_color);
          Protocol_SendAck(cmd, 1);  // Invalid parameter
          break;
        }

        // Only allow in cheat mode
        if (current_game_mode != GAME_MODE_CHEAT) {
          DEBUG_ERROR("[CHEAT] Not in cheat mode\r\n");
          Protocol_SendAck(cmd, 2);  // Wrong mode
          break;
        }

        // Set the selected color as current player
        game_state.current_player = (PieceType_t)color_data->player_color;

        DEBUG_INFO("[CHEAT] Color selected: %s\r\n",
                   color_data->player_color == PIECE_BLACK ? "BLACK" : "WHITE");

        Protocol_SendAck(cmd, 0);  // Success

        // Send updated game state to PC
        Send_GameState_Via_Protocol(&game_state);
      } else {
        Protocol_SendAck(cmd, 3);  // Invalid length
      }
      break;

    default:
      /* Unknown command */
      Protocol_SendError(1, (uint8_t*)&cmd, 1);
      break;
  }
}

/**
 * @brief HAL UART Receive Complete Callback
 * @param huart UART handle
 * @retval None
 */
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
  /* Call protocol RX callback */
  Protocol_UART_RxCallback(huart);
}

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
