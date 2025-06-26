#ifndef INC_ARM_H_
#define INC_ARM_H_

#include "stm32f4xx_hal.h"
#include "stdint.h"

extern TIM_HandleTypeDef htim2;
extern TIM_HandleTypeDef htim3;
extern TIM_HandleTypeDef htim4;

#define BASE_LEFT_PILE 0
#define BASE_RIGHT_PILE 180

#define SHOULDER_NEAR_PILE 90
#define SHOULDER_FAR_PILE 40

#define ELBOW_NEAR_PILE 35
#define ELBOW_FAR_PILE 70

#define WRIST_NEAR_PILE 20
#define WRIST_FAR_PILE 40

#define WRIST_RAISED_ANGLE  90
#define WRIST_GRAB_ANGLE  10
#define WRIST_ALTERNATE_MEDIUM_GRAB_ANGLE 20
#define WRIST_ALTERNATE_NEAR_GRAB_ANGLE 40

#define WRIST_ROT_ANGLE 90

#define GRIPPER_CLOSED  70
#define GRIPPER_OPPENED 40

#define INIT_FOLD_BASE 95
#define INIT_FOLD_SHOULDER 100
#define INIT_FOLD_ELBOW 35
#define INIT_FOLD_WRIST_VER 15
#define INIT_FOLD_WRIST_HOR 90

void Init_arm(void);
void MoveArm(uint8_t base_angle, uint8_t shoulder_angle, uint8_t elbow_angle,
             uint8_t wrist_ver_angle, uint8_t wrist_rot_angle, uint8_t gripper_angle);
void Set_Servo_Angle(TIM_HandleTypeDef *htim, uint32_t channel, uint8_t angle);

void pick_up_object(uint8_t base_angle, uint8_t shoulder_angle, uint8_t elbow_angle, uint8_t colour);
uint8_t detect_object_zone(uint8_t shoulder_angle);
void return_to_init_position();
void move_to_pile(uint8_t colour);

#endif /* INC_ARM_H_ */
