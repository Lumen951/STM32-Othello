################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (13.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Core/Src/challenge_mode.c \
../Core/Src/debug_print.c \
../Core/Src/game_control.c \
../Core/Src/keypad_driver.c \
../Core/Src/led_text.c \
../Core/Src/main.c \
../Core/Src/othello_engine.c \
../Core/Src/stm32f1xx_hal_msp.c \
../Core/Src/stm32f1xx_it.c \
../Core/Src/syscalls.c \
../Core/Src/sysmem.c \
../Core/Src/system_stm32f1xx.c \
../Core/Src/uart_protocol.c \
../Core/Src/ws2812b_driver.c 

OBJS += \
./Core/Src/challenge_mode.o \
./Core/Src/debug_print.o \
./Core/Src/game_control.o \
./Core/Src/keypad_driver.o \
./Core/Src/led_text.o \
./Core/Src/main.o \
./Core/Src/othello_engine.o \
./Core/Src/stm32f1xx_hal_msp.o \
./Core/Src/stm32f1xx_it.o \
./Core/Src/syscalls.o \
./Core/Src/sysmem.o \
./Core/Src/system_stm32f1xx.o \
./Core/Src/uart_protocol.o \
./Core/Src/ws2812b_driver.o 

C_DEPS += \
./Core/Src/challenge_mode.d \
./Core/Src/debug_print.d \
./Core/Src/game_control.d \
./Core/Src/keypad_driver.d \
./Core/Src/led_text.d \
./Core/Src/main.d \
./Core/Src/othello_engine.d \
./Core/Src/stm32f1xx_hal_msp.d \
./Core/Src/stm32f1xx_it.d \
./Core/Src/syscalls.d \
./Core/Src/sysmem.d \
./Core/Src/system_stm32f1xx.d \
./Core/Src/uart_protocol.d \
./Core/Src/ws2812b_driver.d 


# Each subdirectory must supply rules for building sources it contributes
Core/Src/%.o Core/Src/%.su Core/Src/%.cyclo: ../Core/Src/%.c Core/Src/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m3 -std=gnu11 -g3 -DDEBUG -DUSE_HAL_DRIVER -DSTM32F103xB -c -I../Core/Inc -I../Drivers/STM32F1xx_HAL_Driver/Inc/Legacy -I../Drivers/STM32F1xx_HAL_Driver/Inc -I../Drivers/CMSIS/Device/ST/STM32F1xx/Include -I../Drivers/CMSIS/Include -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfloat-abi=soft -mthumb -o "$@"

clean: clean-Core-2f-Src

clean-Core-2f-Src:
	-$(RM) ./Core/Src/challenge_mode.cyclo ./Core/Src/challenge_mode.d ./Core/Src/challenge_mode.o ./Core/Src/challenge_mode.su ./Core/Src/debug_print.cyclo ./Core/Src/debug_print.d ./Core/Src/debug_print.o ./Core/Src/debug_print.su ./Core/Src/game_control.cyclo ./Core/Src/game_control.d ./Core/Src/game_control.o ./Core/Src/game_control.su ./Core/Src/keypad_driver.cyclo ./Core/Src/keypad_driver.d ./Core/Src/keypad_driver.o ./Core/Src/keypad_driver.su ./Core/Src/led_text.cyclo ./Core/Src/led_text.d ./Core/Src/led_text.o ./Core/Src/led_text.su ./Core/Src/main.cyclo ./Core/Src/main.d ./Core/Src/main.o ./Core/Src/main.su ./Core/Src/othello_engine.cyclo ./Core/Src/othello_engine.d ./Core/Src/othello_engine.o ./Core/Src/othello_engine.su ./Core/Src/stm32f1xx_hal_msp.cyclo ./Core/Src/stm32f1xx_hal_msp.d ./Core/Src/stm32f1xx_hal_msp.o ./Core/Src/stm32f1xx_hal_msp.su ./Core/Src/stm32f1xx_it.cyclo ./Core/Src/stm32f1xx_it.d ./Core/Src/stm32f1xx_it.o ./Core/Src/stm32f1xx_it.su ./Core/Src/syscalls.cyclo ./Core/Src/syscalls.d ./Core/Src/syscalls.o ./Core/Src/syscalls.su ./Core/Src/sysmem.cyclo ./Core/Src/sysmem.d ./Core/Src/sysmem.o ./Core/Src/sysmem.su ./Core/Src/system_stm32f1xx.cyclo ./Core/Src/system_stm32f1xx.d ./Core/Src/system_stm32f1xx.o ./Core/Src/system_stm32f1xx.su ./Core/Src/uart_protocol.cyclo ./Core/Src/uart_protocol.d ./Core/Src/uart_protocol.o ./Core/Src/uart_protocol.su ./Core/Src/ws2812b_driver.cyclo ./Core/Src/ws2812b_driver.d ./Core/Src/ws2812b_driver.o ./Core/Src/ws2812b_driver.su

.PHONY: clean-Core-2f-Src

