#include "arm.h"
#include "cmsis_os.h"

static uint8_t current_value_base = 90;
static uint8_t current_value_shoulder = 100;
static uint8_t current_value_elbow = 35;
static uint8_t current_value_wrist_ver = 15;
static uint8_t current_value_wrist_rot = 90;
static uint8_t current_value_gripper = 10;

TIM_HandleTypeDef htim2;
TIM_HandleTypeDef htim3;
TIM_HandleTypeDef htim4;

void Set_Servo_Angle(TIM_HandleTypeDef *htim, uint32_t channel, uint8_t angle)
{
    uint32_t pulse_length = 210 + (angle * (1050 - 210) / 180);
    __HAL_TIM_SET_COMPARE(htim, channel, pulse_length);
}

void Init_arm()
{
	HAL_GPIO_WritePin(GPIOA, GPIO_PIN_6, 1); // Enable motors

	HAL_TIM_PWM_Start(&htim2, TIM_CHANNEL_1); // A0  - M1
	HAL_TIM_PWM_Start(&htim4, TIM_CHANNEL_1); // D10 - M2
	HAL_TIM_PWM_Start(&htim3, TIM_CHANNEL_2); // D9  - M3
	HAL_TIM_PWM_Start(&htim2, TIM_CHANNEL_3); // D6  - M4
	HAL_TIM_PWM_Start(&htim3, TIM_CHANNEL_1); // D5  - M5
	HAL_TIM_PWM_Start(&htim2, TIM_CHANNEL_2); // D3  - M6

	// Set arm to initial position
	Set_Servo_Angle(&htim2, TIM_CHANNEL_1, current_value_base);
	    HAL_Delay(1000);

	    Set_Servo_Angle(&htim4, TIM_CHANNEL_1, current_value_shoulder);
	    HAL_Delay(1000);

	    Set_Servo_Angle(&htim3, TIM_CHANNEL_2, current_value_elbow);
	    HAL_Delay(1000);

	    Set_Servo_Angle(&htim2, TIM_CHANNEL_3, current_value_wrist_ver);
	    HAL_Delay(1000);

	    Set_Servo_Angle(&htim3, TIM_CHANNEL_1, current_value_wrist_rot);
	    HAL_Delay(1000);

	    Set_Servo_Angle(&htim2, TIM_CHANNEL_2, current_value_gripper);
	    HAL_Delay(1000);
}


void MoveArm(uint8_t base_angle, uint8_t shoulder_angle, uint8_t elbow_angle, uint8_t wrist_ver_angle, uint8_t wrist_rot_angle, uint8_t gripper_angle)
{
    int isMoving = 1;

    while (isMoving)
    {
        while (current_value_elbow != elbow_angle)
        {
            if (current_value_elbow > elbow_angle)
            {
            	current_value_elbow--;
            }
            else
            {
            	current_value_elbow++;
            }

            Set_Servo_Angle(&htim3, TIM_CHANNEL_2, current_value_elbow);

            osDelay(15);
        }

        while (current_value_base != base_angle)
        {
            if (current_value_base > base_angle)
            {
            	current_value_base--;
            }
            else
            {
            	current_value_base++;
            }

            Set_Servo_Angle(&htim2, TIM_CHANNEL_1, current_value_base);

            osDelay(15);
        }

        while ((current_value_shoulder) != shoulder_angle)
        {
            if ((current_value_shoulder) > shoulder_angle)
            {
            	current_value_shoulder--;
            }
            else
            {
            	current_value_shoulder++;
            }

            Set_Servo_Angle(&htim4, TIM_CHANNEL_1, current_value_shoulder);

            osDelay(15);
        }

        while (current_value_wrist_ver != wrist_ver_angle)
        {
            if (current_value_wrist_ver > wrist_ver_angle)
            {
            	current_value_wrist_ver--;
            }
            else
            {
            	current_value_wrist_ver++;
            }

            Set_Servo_Angle(&htim2, TIM_CHANNEL_3, current_value_wrist_ver);

            osDelay(15);
        }

        while (current_value_wrist_rot != wrist_rot_angle)
        {
            if (current_value_wrist_rot > wrist_rot_angle)
            {
            	current_value_wrist_rot--;
            }
            else
                current_value_wrist_rot++;

            Set_Servo_Angle(&htim3, TIM_CHANNEL_1, current_value_wrist_rot);

            osDelay(15);
        }

        while (current_value_gripper != gripper_angle)
        {
            if (current_value_gripper > gripper_angle)
            {
            	current_value_gripper--;
            }
            else
            {
            	current_value_gripper++;
            }

            Set_Servo_Angle(&htim2, TIM_CHANNEL_2, current_value_gripper);

            osDelay(15);
        }

        if ((current_value_base == base_angle) &&
            (current_value_shoulder + 45 == shoulder_angle + 45) &&
            (current_value_elbow == elbow_angle) &&
            (current_value_wrist_ver == wrist_ver_angle) &&
            (current_value_wrist_rot == wrist_rot_angle) &&
            (current_value_gripper == gripper_angle))
        {
        	isMoving = 0;
        }
    }
}



