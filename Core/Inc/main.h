/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
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

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32f1xx_hal.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
/* Forward declarations only - actual includes are in source files */
/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */

/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */

/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */

/* USER CODE END EM */

void HAL_TIM_MspPostInit(TIM_HandleTypeDef *htim);

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */
/* External variables for WS2812B driver */
extern TIM_HandleTypeDef htim2;
extern DMA_HandleTypeDef hdma_tim2_ch1;

/* WS2812B driver functions */
void WS2812B_DMA_Complete_IRQ_Handler(void);

/* External variables for UART driver */
extern UART_HandleTypeDef huart1;

/* Application initialization functions - using basic types only */
void App_Init(void);
void App_Main_Loop(void);

/* Application game functions - using basic types only */
void App_DisplayGameBoard(void);
void App_UpdateGameDisplay(void);
void App_HandleGameOver(void);

/* Note: Functions using custom types are declared in their respective headers */
/* See keypad_driver.h for Keypad_Key_Event_Handler */
/* See uart_protocol.h for Protocol_Command_Handler */
/* See respective headers for App_ProcessKeyEvent with Key_t* parameter */
/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define LED_DATA_Pin GPIO_PIN_0
#define LED_DATA_GPIO_Port GPIOA
#define KEY_R1_Pin GPIO_PIN_12
#define KEY_R1_GPIO_Port GPIOB
#define KEY_R2_Pin GPIO_PIN_13
#define KEY_R2_GPIO_Port GPIOB
#define KEY_R3_Pin GPIO_PIN_14
#define KEY_R3_GPIO_Port GPIOB
#define KEY_R4_Pin GPIO_PIN_15
#define KEY_R4_GPIO_Port GPIOB
#define PC_TX_Pin GPIO_PIN_9
#define PC_TX_GPIO_Port GPIOA
#define PC_RX_Pin GPIO_PIN_10
#define PC_RX_GPIO_Port GPIOA
#define KEY_C1_Pin GPIO_PIN_5
#define KEY_C1_GPIO_Port GPIOB
#define KEY_C2_Pin GPIO_PIN_6
#define KEY_C2_GPIO_Port GPIOB
#define KEY_C3_Pin GPIO_PIN_7
#define KEY_C3_GPIO_Port GPIOB
#define KEY_C4_Pin GPIO_PIN_8
#define KEY_C4_GPIO_Port GPIOB

/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
