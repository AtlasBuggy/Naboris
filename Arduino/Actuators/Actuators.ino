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
#include "utility/Adafruit_MS_PWMServoDriver.h"
#include <Servo.h>
#include <Atlasbuggy.h>

// Create the motor shield object with the default I2C address
Adafruit_MotorShield AFMS = Adafruit_MotorShield();
// Or, create it with a different I2C address (say for stacking)
// Adafruit_MotorShield AFMS = Adafruit_MotorShield(0x61);

Atlasbuggy buggy("naboris actuators");

// And connect a DC motor to port M1
Adafruit_DCMotor *motor_1 = AFMS.getMotor(1);
Adafruit_DCMotor *motor_2 = AFMS.getMotor(2);
Adafruit_DCMotor *motor_3 = AFMS.getMotor(3);
Adafruit_DCMotor *motor_4 = AFMS.getMotor(4);

// We'll also test out the built in Arduino Servo library
Servo servo1;
Servo servo2;

int increment = 3;
int increment_delay = 1;
bool paused = true;

int m1_speed = 0;
int m2_speed = 0;
int m3_speed = 0;
int m4_speed = 0;

bool m1_forward = true;
bool m2_forward = true;
bool m3_forward = true;
bool m4_forward = true;

uint32_t time0 = millis();
uint32_t motor_command_delay = 0;
bool new_motor_command = false;

void setup() {
    AFMS.begin();  // create with the default frequency 1.6KHz
    //AFMS.begin(1000);  // OR with a different frequency, say 1KHz

    // Attach a servo to pin #10
    // servo1.attach(10);
    // servo2.attach(9);

    hard_stop_motors();
    release_motors();

    buggy.begin();
}

void set_turret(int servo1_angle, int servo2_angle)
{
    if (!servo1.attached()) {
        servo1.attach(10);
    }
    if (!servo2.attached()) {
        servo2.attach(9);
    }
    servo1.write(map(servo1_angle, 0, 255, 0, 180));
    servo2.write(map(servo2_angle, 0, 255, 0, 180));
}

// top left, top right, bottom left, bottom right
void set_motors(int speed2, int speed1, int speed3, int speed4)
{
    set_motor(speed1, m1_speed, m1_forward, motor_1);
    set_motor(speed2, m2_speed, m2_forward, motor_2);
    set_motor(speed3, m3_speed, m3_forward, motor_3);
    set_motor(speed4, m4_speed, m4_forward, motor_4);
}

void set_motor(int speed, int &recorded_speed, bool &recorded_direction, Adafruit_DCMotor *motor)
{
    if (speed >= 0) {
        if (!recorded_direction && speed > 50) {
            motor->setSpeed(0);
            motor->run(RELEASE);
            delay(100);
        }
        motor->run(FORWARD);
        recorded_direction = true;
    }
    else {
        motor->run(BACKWARD);
        recorded_direction = false;
    }
    recorded_speed = abs(speed);
    motor->setSpeed(recorded_speed);
}

void drive(int angle, int speed)
{
    angle %= 360;

    if (0 <= angle && angle < 90) {
        int fraction_speed = -2 * speed / 90 * angle + speed;
        set_motors(speed, fraction_speed, fraction_speed, speed);
    }
    else if (90 <= angle && angle < 180) {
        int fraction_speed = -2 * speed / 90 * (angle - 90) + speed;
        set_motors(fraction_speed, -speed, -speed, fraction_speed);
    }
    else if (180 <= angle && angle < 270) {
        int fraction_speed = 2 * speed / 90 * (angle - 180) - speed;
        set_motors(-speed, fraction_speed, fraction_speed, -speed);
    }
    else if (270 <= angle && angle < 360) {
        int fraction_speed = 2 * speed / 90 * (angle - 270) - speed;
        set_motors(fraction_speed, speed, speed, fraction_speed);
    }
}

void spin(int speed) {
    set_motors(speed, -speed, speed, -speed);
}

void stop_motors()
{
    while (m1_speed > 0 || m2_speed > 0 || m3_speed > 0 || m4_speed > 0)
    {
        if (m1_speed > 0) {
            motor_1->setSpeed(m1_speed);
            m1_speed -= increment;
        }
        if (m2_speed > 0) {
            motor_2->setSpeed(m2_speed);
            m2_speed -= increment;
        }
        if (m3_speed > 0) {
            motor_3->setSpeed(m3_speed);
            m3_speed -= increment;
        }
        if (m4_speed > 0) {
            motor_4->setSpeed(m4_speed);
            m4_speed -= increment;
        }
        delay(increment_delay);
    }
    motor_1->setSpeed(m1_speed);
    motor_2->setSpeed(m2_speed);
    motor_3->setSpeed(m3_speed);
    motor_4->setSpeed(m4_speed);
}

void hard_stop_motors() {
    set_motors(0, 0, 0, 0);
}

void release_motors()
{
    motor_1->run(RELEASE);
    motor_2->run(RELEASE);
    motor_3->run(RELEASE);
    motor_4->run(RELEASE);
    if (servo1.attached()) {
        servo1.detach();
    }
    if (servo2.attached()) {
        servo2.detach();
    }
}

void update_motors()
{
    if (time0 > millis())  time0 = millis();
    if (new_motor_command && (millis() - time0) > motor_command_delay) {
        hard_stop_motors();
        new_motor_command = false;
    }
}

void loop()
{
    while (buggy.available())
    {
        int status = buggy.readSerial();
        if (status == 0) {  // user command
            String command = buggy.getCommand();
            if (command.charAt(0) == 'p') {  // drive command
                int angle = command.substring(2, 5).toInt();
                int speed = command.substring(5, 8).toInt();
                if (command.charAt(1) == '1') {
                    speed *= -1;
                }
                drive(angle, speed);

                if (command.length() > 8) {
                    motor_command_delay = command.substring(8).toInt();
                    new_motor_command = true;
                    time0 = millis();
                }
            }
            else if (command.charAt(0) == 'r') {  // spin command
                int speed = command.substring(2, 5).toInt();
                if (command.charAt(1) == '1') {
                    speed *= -1;
                }
                spin(speed);

                if (command.length() > 5) {
                    motor_command_delay = command.substring(5).toInt();
                    new_motor_command = true;
                    time0 = millis();
                }
            }
            else if (command.charAt(0) == 'h') {  // stop command
                hard_stop_motors();
            }
            else if (command.charAt(0) == 'd') {  // release command
                release_motors();
            }
            else if (command.charAt(0) == 'c') {  // camera command
                int yaw = command.substring(1, 4).toInt();
                int azimuth = command.substring(4, 7).toInt();
                set_turret(yaw, azimuth);
            }
        }
        else if (status == 1) {  // stop event
            hard_stop_motors();
            release_motors();
        }
        else if (status == 2) {  // start event
            set_motors(0, 0, 0, 0);
            set_turret(0, 0);
        }
    }

    if (!buggy.isPaused()) {
        update_motors();
    }
}
