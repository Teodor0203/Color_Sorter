#include "arm.h"
#include "cmsis_os.h"

static uint8_t current_value_base = 0;
static uint8_t current_value_shoulder = 100;
static uint8_t current_value_elbow = 35;
static uint8_t current_value_wrist_ver = 90;
static uint8_t current_value_wrist_rot = 90;
static uint8_t current_value_gripper = 40;

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

//	 Set arm to initial position
	Set_Servo_Angle(&htim2, TIM_CHANNEL_1, current_value_base);
	HAL_Delay(200);

	Set_Servo_Angle(&htim4, TIM_CHANNEL_1, current_value_shoulder);
	HAL_Delay(200);

	Set_Servo_Angle(&htim3, TIM_CHANNEL_2, current_value_elbow);
	HAL_Delay(200);

	Set_Servo_Angle(&htim2, TIM_CHANNEL_3, current_value_wrist_ver);
	HAL_Delay(200);

	Set_Servo_Angle(&htim3, TIM_CHANNEL_1, current_value_wrist_rot);
	HAL_Delay(200);

	Set_Servo_Angle(&htim2, TIM_CHANNEL_2, current_value_gripper);
	HAL_Delay(200);
}

void MoveArm(uint8_t base_angle, uint8_t shoulder_angle, uint8_t elbow_angle, uint8_t wrist_ver_angle, uint8_t wrist_rot_angle, uint8_t gripper_angle)
{
    int isMoving = 1;

    while (isMoving)
    {
        isMoving = 0;

        // Wrist Vertical
        if (current_value_wrist_ver != wrist_ver_angle)
        {
            if (current_value_wrist_ver < wrist_ver_angle)
            {
                current_value_wrist_ver++;
            }
            else
            {
                current_value_wrist_ver--;
            }
            Set_Servo_Angle(&htim2, TIM_CHANNEL_3, current_value_wrist_ver);
            isMoving = 1;
        }

        // Base
        if (current_value_base != base_angle)
        {
            if (current_value_base < base_angle)
            {
                current_value_base++;
            }
            else
            {
                current_value_base--;
            }
            Set_Servo_Angle(&htim2, TIM_CHANNEL_1, current_value_base);
            isMoving = 1;
        }

        // Shoulder
        if (current_value_shoulder != shoulder_angle)
        {
            if (current_value_shoulder < shoulder_angle)
            {
                current_value_shoulder++;
            }
            else
            {
                current_value_shoulder--;
            }
            Set_Servo_Angle(&htim4, TIM_CHANNEL_1, current_value_shoulder);
            isMoving = 1;
        }

        // Elbow
        if (current_value_elbow != elbow_angle)
        {
            if (current_value_elbow < elbow_angle)
            {
                current_value_elbow++;
            }
            else
            {
                current_value_elbow--;
            }
            Set_Servo_Angle(&htim3, TIM_CHANNEL_2, current_value_elbow);
            isMoving = 1;
        }

        // Wrist Rotation
        if (current_value_wrist_rot != wrist_rot_angle)
        {
            if (current_value_wrist_rot < wrist_rot_angle)
            {
                current_value_wrist_rot++;
            }
            else
            {
                current_value_wrist_rot--;
            }
            Set_Servo_Angle(&htim3, TIM_CHANNEL_1, current_value_wrist_rot);
            isMoving = 1;
        }

        // Gripper
        if (current_value_gripper != gripper_angle)
        {
            if (current_value_gripper < gripper_angle)
            {
                current_value_gripper++;
            }
            else
            {
                current_value_gripper--;
            }
            Set_Servo_Angle(&htim2, TIM_CHANNEL_2, current_value_gripper);
            isMoving = 1;
        }

        osDelay(15);
    }
}

// object pick-up routine
void pick_up_object(uint8_t base_angle, uint8_t shoulder_angle, uint8_t elbow_angle, uint8_t colour)
{
	uint8_t detected_grab_angle = detect_object_zone(shoulder_angle);                                         // detect object zone

	MoveArm(base_angle, shoulder_angle, elbow_angle, WRIST_RAISED_ANGLE,  WRIST_ROT_ANGLE, GRIPPER_OPPENED ); // move to object
//	osDelay(15);
	MoveArm(base_angle, shoulder_angle, elbow_angle, detected_grab_angle, WRIST_ROT_ANGLE, GRIPPER_OPPENED ); // lower arm
//	osDelay(15);
	MoveArm(base_angle, shoulder_angle, elbow_angle, detected_grab_angle, WRIST_ROT_ANGLE, GRIPPER_CLOSED  ); // grab object
//	osDelay(15);
	MoveArm(base_angle, shoulder_angle, elbow_angle, WRIST_RAISED_ANGLE,  WRIST_ROT_ANGLE, GRIPPER_CLOSED  ); // raise object
//	osDelay(15);
	MoveArm(base_angle, INIT_FOLD_SHOULDER, INIT_FOLD_ELBOW, WRIST_RAISED_ANGLE,  WRIST_ROT_ANGLE, GRIPPER_CLOSED  ); // fold to init                                                                              // fold to initial position
//	osDelay(15);
	move_to_pile(colour);
//	osDelay(15);
	return_to_init_position();
//	osDelay(15);
}

// check which zone the object is in
// 3 zones defined: far zone    (      shoulder_ang e <= 35 )
//                  middle zone ( 35 < shoulder_angle <= 45 )
//                  near zone   ( 45 < shoulder_angle
<<<<<<< Updated upstream
uint8_t detect_object_zone(uint8_t shoulder_angle){
	if(shoulder_angle <= 35) return WRIST_GRAB_ANGLE       ; else
	if(shoulder_angle <= 45) return WRIST_GRAB_ANGLE_ZONE_2; else
	if(shoulder_angle <= 55) return WRIST_GRAB_ANGLE_ZONE_1; else
	if(shoulder_angle <= 75) return WRIST_GRAB_ANGLE_ZONE_0; else
		                     return WRIST_GRAB_ANGLE_UNDER ;
}

void return_to_init_position(){
	MoveArm(INIT_FOLD_BASE, INIT_FOLD_SHOULDER, INIT_FOLD_ELBOW, WRIST_RAISED_ANGLE, INIT_FOLD_WRIST_HOR, GRIPPER_OPPENED);
=======

uint8_t detect_object_zone(uint8_t shoulder_angle)
{
	if(shoulder_angle <= 35)
	{
		return WRIST_GRAB_ANGLE;
	}
    else if(shoulder_angle <= 45)
    {
    	return WRIST_GRAB_ANGLE_ZONE_2;
    }
    else if(shoulder_angle <= 55)
    {
    	return WRIST_GRAB_ANGLE_ZONE_1;
    }
    else if(shoulder_angle <= 65)
    {
    	return WRIST_GRAB_ANGLE_ZONE_0;
    }
    else
    {
    	return WRIST_GRAB_ANGLE_UNDER ;
    }
}

void return_to_init_position()
{
	MoveArm(INIT_FOLD_BASE, INIT_FOLD_SHOULDER, INIT_FOLD_ELBOW, INIT_FOLD_WRIST_VER, INIT_FOLD_WRIST_HOR, GRIPPER_CLOSED);
>>>>>>> Stashed changes
}

// moves the object to its designated pile
void move_to_pile(uint8_t colour)
{
	switch (colour)
	{
		case 0:
			MoveArm(BASE_LEFT_PILE, INIT_FOLD_SHOULDER, INIT_FOLD_ELBOW, WRIST_RAISED_ANGLE, INIT_FOLD_WRIST_HOR, GRIPPER_CLOSED  ); // go to left pile
			MoveArm(BASE_LEFT_PILE, SHOULDER_NEAR_PILE, ELBOW_NEAR_PILE, WRIST_NEAR_PILE,     WRIST_ROT_ANGLE,     GRIPPER_CLOSED  ); // get arm into position
			MoveArm(BASE_LEFT_PILE, SHOULDER_NEAR_PILE, ELBOW_NEAR_PILE, WRIST_NEAR_PILE,     WRIST_ROT_ANGLE,     GRIPPER_OPPENED ); // release object
			MoveArm(BASE_LEFT_PILE, INIT_FOLD_SHOULDER, INIT_FOLD_ELBOW, WRIST_RAISED_ANGLE, INIT_FOLD_WRIST_HOR, GRIPPER_OPPENED);
			break;

		case 1:
			MoveArm(BASE_LEFT_PILE, INIT_FOLD_SHOULDER, INIT_FOLD_ELBOW, WRIST_RAISED_ANGLE, INIT_FOLD_WRIST_HOR, GRIPPER_CLOSED  ); // go to left pile
			MoveArm(BASE_LEFT_PILE, SHOULDER_FAR_PILE,  ELBOW_FAR_PILE,  WRIST_NEAR_PILE,  WRIST_ROT_ANGLE,     GRIPPER_CLOSED  ); // get arm into position
			MoveArm(BASE_LEFT_PILE, SHOULDER_FAR_PILE,  ELBOW_FAR_PILE,  WRIST_FAR_PILE,      WRIST_ROT_ANGLE,     GRIPPER_OPPENED ); // release object
			MoveArm(BASE_LEFT_PILE,INIT_FOLD_SHOULDER, INIT_FOLD_ELBOW, WRIST_RAISED_ANGLE, INIT_FOLD_WRIST_HOR,GRIPPER_OPPENED);
			break;

		case 2:
			MoveArm(BASE_RIGHT_PILE, INIT_FOLD_SHOULDER, INIT_FOLD_ELBOW, WRIST_RAISED_ANGLE, INIT_FOLD_WRIST_HOR, GRIPPER_CLOSED  ); // go to blue pile
			MoveArm(BASE_RIGHT_PILE, SHOULDER_NEAR_PILE, ELBOW_NEAR_PILE, WRIST_NEAR_PILE,  WRIST_ROT_ANGLE,     GRIPPER_CLOSED  ); // get arm into position
			MoveArm(BASE_RIGHT_PILE, SHOULDER_NEAR_PILE, ELBOW_NEAR_PILE, WRIST_NEAR_PILE,     WRIST_ROT_ANGLE,     GRIPPER_OPPENED ); // release object
			MoveArm(BASE_RIGHT_PILE,INIT_FOLD_SHOULDER, INIT_FOLD_ELBOW, WRIST_RAISED_ANGLE, INIT_FOLD_WRIST_HOR,GRIPPER_OPPENED);
			break;

		case 3:
			MoveArm(BASE_RIGHT_PILE, INIT_FOLD_SHOULDER, INIT_FOLD_ELBOW, WRIST_RAISED_ANGLE, INIT_FOLD_WRIST_HOR, GRIPPER_CLOSED  ); // go to yellow pile
			MoveArm(BASE_RIGHT_PILE, SHOULDER_FAR_PILE,  ELBOW_FAR_PILE,  WRIST_NEAR_PILE,  WRIST_ROT_ANGLE,     GRIPPER_CLOSED  ); // get arm into position
			MoveArm(BASE_RIGHT_PILE, SHOULDER_FAR_PILE,  ELBOW_FAR_PILE,  WRIST_FAR_PILE,      WRIST_ROT_ANGLE,     GRIPPER_OPPENED ); // release object
			MoveArm(BASE_RIGHT_PILE,INIT_FOLD_SHOULDER, INIT_FOLD_ELBOW, WRIST_RAISED_ANGLE, INIT_FOLD_WRIST_HOR,GRIPPER_OPPENED);
			break;

		default:
			break;
	}
}

