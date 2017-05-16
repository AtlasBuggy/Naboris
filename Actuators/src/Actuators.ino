/*
This is a test sketch for the Adafruit assembled Motor Shield for Arduino v2
It won't work with v1.x motor shields! Only for the v2's with built in PWM
control

For use with the Adafruit Motor Shield v2
---->	http://www.adafruit.com/products/1438

This sketch creates a fun motor party on your desk *whiirrr*
Connect a unipolar/bipolar stepper to M3/M4
Connect a DC motor to M1
Connect a hobby servo to SERVO1
*/

#include <Wire.h>
#include <Adafruit_MotorShield.h>
#include <Adafruit_NeoPixel.h>
#include "utility/Adafruit_MS_PWMServoDriver.h"
#include <Servo.h>
#include <Battery.h>
#include <Atlasbuggy.h>

// Create the motor shield object with the default I2C address
Adafruit_MotorShield AFMS = Adafruit_MotorShield();
// Or, create it with a different I2C address (say for stacking)
// Adafruit_MotorShield AFMS = Adafruit_MotorShield(0x61);

Atlasbuggy robot("naboris actuators");

struct MotorStruct {
    Adafruit_DCMotor* af_motor;
    int speed;
    int goal_speed;
    byte run_state;
};

MotorStruct init_motor(int motor_num) {
    MotorStruct new_motor;
    new_motor.af_motor = AFMS.getMotor(motor_num);
    new_motor.speed = 0;
    new_motor.goal_speed = 0;
    return new_motor;
}

#define AZIMUTH_PIN 9
#define YAW_PIN 10
#define NUM_MOTORS 4
#define TOPLEFT_OFFSET 5
#define BOTLEFT_OFFSET 5
#define TOPRIGHT_OFFSET 0
#define BOTRIGHT_OFFSET 0
int speed_increment = 10;
int speed_delay = 1;
MotorStruct* motors = new MotorStruct[NUM_MOTORS];
Servo servo1;
Servo servo2;

#define NUM_LEDS 24
#define LED_SIGNAL_PIN 6
Adafruit_NeoPixel strip = Adafruit_NeoPixel(NUM_LEDS, LED_SIGNAL_PIN, NEO_GRB + NEO_KHZ800);
uint32_t led_time = millis();
bool cycle_paused = false;

uint16_t lower_V = 4800;
uint16_t upper_V = 5000;
Battery battery(lower_V, upper_V, A0);

void setup() {
    robot.begin();
    AFMS.begin();
    strip.begin();
    battery.begin();

    strip.show();

    for (int motor_num = 1; motor_num <= NUM_MOTORS; motor_num++) {
        motors[motor_num - 1] = init_motor(motor_num);
    }

    String ledNumStr = String(NUM_LEDS);
    String speedIncreStr = String(speed_increment);
    String speedDelayStr = String(speed_delay);
    String lowerVstr = String(lower_V);
    String upperVstr = String(upper_V);
    String voltageLevelStr = String(battery.voltage());
    String voltageValueStr = String(battery.level());
    robot.setInitData(
        ledNumStr + "\t" +
        speedIncreStr + "\t" +
        speedDelayStr + "\t" +
        lowerVstr + "\t" +
        upperVstr + "\t" +
        voltageLevelStr + "\t" +
        voltageValueStr
    );
}

void attach_turret()
{
    servo1.attach(YAW_PIN);
    servo2.attach(AZIMUTH_PIN);
}

void detach_turret()
{
    servo1.detach();
    servo2.detach();
}

void set_turret(int yaw, int azimuth)
{
    servo1.write(yaw);
    delay(250);
    servo2.write(azimuth);
}

void set_motor_speed(int motor_num)
{
    if (motors[motor_num].speed > 0) {
        motors[motor_num].af_motor->run(FORWARD);
    }
    else if (motors[motor_num].speed == 0) {
        motors[motor_num].af_motor->run(BRAKE);
    }
    else {
        motors[motor_num].af_motor->run(BACKWARD);
    }
    motors[motor_num].af_motor->setSpeed(abs(motors[motor_num].speed));
}

void set_motor_goal(int motor_num, int speed, int offset) {
    motors[motor_num].goal_speed = speed;
    if (abs(motors[motor_num].goal_speed) > offset) {
        if (motors[motor_num].goal_speed > 0) {
            motors[motor_num].goal_speed -= offset;

            if (motors[motor_num].goal_speed < 0) {
                motors[motor_num].goal_speed = 0;
            }
            if (motors[motor_num].goal_speed > 255) {
                motors[motor_num].goal_speed = 255;
            }
        }
        else {
            motors[motor_num].goal_speed += offset;
            if (motors[motor_num].goal_speed > 0) {
                motors[motor_num].goal_speed = 0;
            }
            if (motors[motor_num].goal_speed < -255) {
                motors[motor_num].goal_speed = -255;
            }
        }
    }
}

// top left, top right, bottom left, bottom right
void set_motor_goals(int speed2, int speed1, int speed3, int speed4)
{
    set_motor_goal(0, speed1, TOPRIGHT_OFFSET);  // top right
    set_motor_goal(1, speed2, TOPLEFT_OFFSET);  // top left
    set_motor_goal(2, speed3, BOTLEFT_OFFSET);  // bottom left
    set_motor_goal(3, speed4, BOTRIGHT_OFFSET);  // bottom right
}

void drive(int angle, int speed)
{
    angle %= 360;

    if (0 <= angle && angle < 90) {
        int fraction_speed = -2 * speed / 90 * angle + speed;
        set_motor_goals(speed, fraction_speed, fraction_speed, speed);
    }
    else if (90 <= angle && angle < 180) {
        int fraction_speed = -2 * speed / 90 * (angle - 90) + speed;
        set_motor_goals(fraction_speed, -speed, -speed, fraction_speed);
    }
    else if (180 <= angle && angle < 270) {
        int fraction_speed = 2 * speed / 90 * (angle - 180) - speed;
        set_motor_goals(-speed, fraction_speed, fraction_speed, -speed);
    }
    else if (270 <= angle && angle < 360) {
        int fraction_speed = 2 * speed / 90 * (angle - 270) - speed;
        set_motor_goals(fraction_speed, speed, speed, fraction_speed);
    }
}

void spin(int speed) {
    set_motor_goals(speed, -speed, speed, -speed);
}

void stop_motors() {
    set_motor_goals(0, 0, 0, 0);
}

void release_motors()
{
    for (int motor_num = 0; motor_num < NUM_MOTORS; motor_num++)
    {
        motors[motor_num].goal_speed = 0;
        motors[motor_num].speed = 0;
        motors[motor_num].af_motor->run(RELEASE);
    }
}

void update_motors()
{
    for (int motor_num = 0; motor_num < NUM_MOTORS; motor_num++)
    {
        set_motor_speed(motor_num);

        if (motors[motor_num].speed < motors[motor_num].goal_speed) {
            motors[motor_num].speed += speed_increment;
        }
        else {
            motors[motor_num].speed -= speed_increment;
        }

        if (abs(motors[motor_num].speed - motors[motor_num].goal_speed) < 2 * speed_increment) {
            motors[motor_num].speed = motors[motor_num].goal_speed;
        }
    }
    delay(speed_delay);
}

int current_index = 0;
int prev_index = 0;
void update_leds()
{
    strip.setPixelColor(prev_index, strip.Color(5, 5, 5));
    strip.setPixelColor(current_index, strip.Color(0, 5, 0));

    prev_index = current_index;
    current_index = (current_index + 1) % NUM_LEDS;
    strip.show();
}

void loop()
{
    while (robot.available())
    {
        int status = robot.readSerial();
        if (status == 0) {  // user command
            String command = robot.getCommand();
            if (command.charAt(0) == 'p') {  // drive command
                int angle = 360 - command.substring(2, 5).toInt();
                int speed = -command.substring(5, 8).toInt();
                if (command.charAt(1) == '1') {
                    speed *= -1;
                }
                drive(angle, speed);
            }
            else if (command.charAt(0) == 'r') {  // spin command
                int speed = command.substring(2, 5).toInt();
                if (command.charAt(1) == '1') {
                    speed *= -1;
                }
                spin(speed);
            }
            else if (command.charAt(0) == 'h') {  // stop command
                stop_motors();
            }
            else if (command.charAt(0) == 'd') {  // release command
                release_motors();
            }
            else if (command.charAt(0) == 'c') {  // camera command
                int yaw = command.substring(1, 4).toInt();
                int azimuth = command.substring(4, 7).toInt();
                set_turret(yaw, azimuth);
            }
            else if (command.charAt(0) == 'o') {  // pixel command
                if (command.length() == 1) {
                    cycle_paused = !cycle_paused;
                }
                else
                {
                    int led_num = command.substring(1, 4).toInt();
                    if (led_num < 0) {
                        led_num = 0;
                    }
                    int r = command.substring(4, 7).toInt();
                    int g = command.substring(7, 10).toInt();
                    int b = command.substring(10, 13).toInt();
                    if (command.length() > 13)
                    {
                        int stop_num = command.substring(13, 16).toInt();
                        if (stop_num > NUM_LEDS) {
                            stop_num = NUM_LEDS;
                        }
                        for (int index = led_num; index < stop_num; index++) {
                            strip.setPixelColor(index, strip.Color(r, g, b));
                        }
                    }
                    else {
                        strip.setPixelColor(led_num, strip.Color(r, g, b));
                    }
                }
            }
            else if (command.charAt(0) == 'x') {  // show command
                strip.show();
            }
            else if (command.charAt(0) == 'b') {
                if (command.length() == 1)
                {
                    Serial.print('b');
                    Serial.print(battery.voltage());
                    Serial.print('\t');
                    Serial.print(battery.level());
                    Serial.print('\n');
                }
                else {
                    lower_V = command.substring(1, 5).toInt();
                    upper_V = command.substring(5, 9).toInt();
                    battery.setMinMax(lower_V, upper_V);
                }
            }
        }
        else if (status == 1) {  // stop event
            stop_motors();
            release_motors();
            detach_turret();
            for (int index = 0; index < NUM_LEDS; index++) {
                strip.setPixelColor(index, 0);
            }
            strip.show();
        }
        else if (status == 2) {  // start event
            stop_motors();
            attach_turret();
        }
    }

    if (!robot.isPaused()) {
        update_motors();

        if (!cycle_paused) {
            if (led_time > millis()) led_time = millis();
            if ((millis() - led_time) > 50) {
                update_leds();
                led_time = millis();
            }
        }
    }
}
