#ifndef INC_ARM_H_
#define INC_ARM_H_

#include "stm32f4xx_hal.h"
#include "stdint.h"

void Init_arm(void);
void MoveArm(uint8_t base_angle, uint8_t shoulder_angle, uint8_t elbow_angle,
             uint8_t wrist_ver_angle, uint8_t wrist_rot_angle, uint8_t gripper_angle);
void Set_Servo_Angle(TIM_HandleTypeDef *htim, uint32_t channel, uint8_t angle);

#endif /* INC_ARM_H_ */
