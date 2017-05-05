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

Adafruit_NeoPixel strip = Adafruit_NeoPixel(24, 6, NEO_GRB + NEO_KHZ800);

#define SIGNAL_DELAY 1
#define SIGNAL_INCREMENT 3
#define SIGNAL_CYCLES 2

int signal_r, signal_g, signal_b = 0;


// We'll also test out the built in Arduino Servo library
Servo servo1;
Servo servo2;

int increment = 3;
int increment_delay = 1;
bool paused = true;

#define MAX_SPEED 200

int m1_speed = 0;
int m2_speed = 0;
int m3_speed = 0;
int m4_speed = 0;

bool m1_forward = true;
bool m2_forward = true;
bool m3_forward = true;
bool m4_forward = true;

uint32_t time0 = millis();
uint32_t time1 = millis();
uint32_t motor_command_delay = 0;
bool new_motor_command = false;

void setup() {
    AFMS.begin();  // create with the default frequency 1.6KHz
    //AFMS.begin(1000);  // OR with a different frequency, say 1KHz

    // Attach a servo to pin #10
    // servo1.attach(10);
    // servo2.attach(9);

    release_motors();

    strip.begin();
    strip.show();

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
    bool status_1 = verify_speed(speed1, m1_speed, m1_forward, motor_1);
    bool status_2 = verify_speed(speed2, m2_speed, m2_forward, motor_2);
    bool status_3 = verify_speed(speed3, m3_speed, m3_forward, motor_3);
    bool status_4 = verify_speed(speed4, m4_speed, m4_forward, motor_4);
    if (status_1 || status_2 || status_3 || status_4) {
        stop_motors();
        delay(100);
    }

    set_motor(speed1, m1_speed, m1_forward, motor_1);
    set_motor(speed2, m2_speed, m2_forward, motor_2);
    set_motor(speed3, m3_speed, m3_forward, motor_3);
    set_motor(speed4, m4_speed, m4_forward, motor_4);
}

bool verify_speed(int speed, int &recorded_speed, bool &recorded_direction, Adafruit_DCMotor *motor)
{
    recorded_speed = abs(speed);
    if (recorded_speed > 0) {
        if (speed > 0 && recorded_speed > 50) {
            if (!recorded_direction) {
                return true;
            }
        }
        else {
            if (recorded_direction) {
                return true;
            }
        }
    }

    return false;
}

void set_motor(int speed, int &recorded_speed, bool &recorded_direction, Adafruit_DCMotor *motor)
{
    recorded_speed = abs(speed);
    if (recorded_speed > MAX_SPEED) {
        recorded_speed = MAX_SPEED;
    }
    if (speed > 0) {
        motor->run(FORWARD);
        recorded_direction = true;
    }
    else if (speed == 0) {
        motor->setSpeed(0);
        motor->run(BRAKE);
    }
    else {
        motor->run(BACKWARD);
        recorded_direction = false;
    }

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

    m1_speed = 0;
    m2_speed = 0;
    m3_speed = 0;
    m4_speed = 0;

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
                int angle = 360 - command.substring(2, 5).toInt();
                int speed = -command.substring(5, 8).toInt();
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
            else if (command.charAt(0) == 'x') {  // circle demo
                for (int angle = 0; angle < 360; angle += 5) {
                    drive(angle, 255);
                    delay(1);
                }
                hard_stop_motors();
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

            fadeColors(255, 0, 0, SIGNAL_CYCLES * 2, SIGNAL_DELAY, SIGNAL_INCREMENT);
            fadeColors(255, 255, 255, 0, 0, 0, 1, SIGNAL_DELAY, SIGNAL_INCREMENT);
        }
        else if (status == 2) {  // start event
            set_motors(0, 0, 0, 0);

            fadeColors(255, 255, 255, 1, SIGNAL_DELAY, SIGNAL_INCREMENT);
            fadeColors(255, 255, 255, 0, 0, 255, SIGNAL_CYCLES, SIGNAL_DELAY, SIGNAL_INCREMENT);
            fadeColors(0, 0, 0, 1, SIGNAL_DELAY, SIGNAL_INCREMENT);
        }
    }

    if (!buggy.isPaused()) {
        update_motors();
    }
}



void fadeColors(int r, int g, int b, uint16_t cycles, uint8_t wait, int increment) {
    fadeColors(signal_r, signal_g, signal_b, r, g, b, cycles, wait, increment);
}

void fadeColors(int r1, int g1, int b1, int r2, int g2, int b2, uint16_t cycles, uint8_t wait, int increment)
{
    // Serial.print(r1); Serial.print('\t');
    // Serial.print(g1); Serial.print('\t');
    // Serial.print(b1); Serial.print('\n');
    // Serial.print(r2); Serial.print('\t');
    // Serial.print(g2); Serial.print('\t');
    // Serial.print(b2); Serial.print('\n');

    if (cycles % 2 == 0) {
        signal_r = r1;
        signal_g = g1;
        signal_b = b1;
    }
    else {
        signal_r = r2;
        signal_g = g2;
        signal_b = b2;
    }
    int red_diff = abs(r2 - r1);
    int green_diff = abs(g2 - g1);
    int blue_diff = abs(b2 - b1);

    char max_channel = 'r';
    int max_diff = red_diff;

    if (green_diff > max_diff) {
        max_diff = green_diff;
        max_channel = 'g';
    }
    if (blue_diff > max_diff) {
        max_diff = blue_diff;
        max_channel = 'b';
    }
    // Serial.println(max_channel);

    float red_slope = 0.0;
    float green_slope = 0.0;
    float blue_slope = 0.0;

    int start = 0;
    int end = 0;

    bool condition = true;

    switch (max_channel) {
        case 'r':
            if (r2 < r1) {
                increment *= -1;
            }
            break;
        case 'g':
            if (g2 < g1) {
                increment *= -1;
            }
            break;
        case 'b':
            if (b2 < b1) {
                increment *= -1;
            }
            break;
    }

    // Serial.println(cycles);
    for (uint16_t cycle = 0; cycle < cycles; cycle++)
    {
        switch (max_channel) {
            case 'r':
                condition = r1 < r2;
                if (increment < 0) {
                    condition = !condition;
                }
                if (condition) {
                    start = r1;
                    end = r2;
                }
                else {
                    start = r2;
                    end = r1;
                }
                green_slope = (float)(g2 - g1) / (r2 - r1);
                blue_slope = (float)(b2 - b1) / (r2 - r1);

                if (start < end) {
                    for (int value = start; value <= end; value += increment) {
                        setColor(strip.Color(
                                value,
                                green_slope * (value - r1) + g1,
                                blue_slope * (value - r1) + b1
                            )
                        );
                        delay(wait);
                    }
                }
                else if (start > end) {
                    for (int value = start; value >= end; value += increment) {
                        setColor(strip.Color(
                                value,
                                green_slope * (value - r1) + g1,
                                blue_slope * (value - r1) + b1
                            )
                        );
                        delay(wait);
                    }
                }
                break;

            case 'g':
                condition = g1 < g2;
                if (increment < 0) {
                    condition = !condition;
                }
                if (condition) {
                    start = g1;
                    end = g2;
                }
                else {
                    start = g2;
                    end = g1;
                }


                red_slope = (float)(r2 - r1) / (g2 - g1);
                blue_slope = (float)(b2 - b1) / (g2 - g1);
                if (start < end) {
                    for (int value = start; value <= end; value += increment) {
                        setColor(strip.Color(
                                red_slope * (value - g1) + r1,
                                value,
                                blue_slope * (value - g1) + b1
                            )
                        );
                        delay(wait);
                    }
                }
                else {
                    for (int value = start; value >= end; value += increment) {
                        setColor(strip.Color(
                                red_slope * (value - g1) + r1,
                                value,
                                blue_slope * (value - g1) + b1
                            )
                        );
                        delay(wait);
                    }
                }
                break;
            case 'b':
                condition = b1 < b2;
                if (increment < 0) {
                    condition = !condition;
                }
                if (condition) {
                    start = b1;
                    end = b2;
                }
                else {
                    start = b2;
                    end = b1;
                }
                red_slope = (float)(r2 - r1) / (b2 - b1);
                green_slope = (float)(g2 - g1) / (b2 - b1);

                if (start < end) {
                    for (int value = start; value <= end; value += increment) {
                        setColor(strip.Color(
                                red_slope * (value - b1) + r1,
                                green_slope * (value - b1) + g1,
                                value
                            )
                        );
                        delay(wait);
                    }
                }
                else {
                    for (int value = start; value >= end; value += increment) {
                        setColor(strip.Color(
                                red_slope * (value - b1) + r1,
                                green_slope * (value - b1) + g1,
                                value
                            )
                        );
                        delay(wait);
                    }
                }

                break;
        }
        increment *= -1;

    }
}

void setColor(uint32_t c)
{
    for(uint16_t i = 0; i < strip.numPixels(); i++) {
        strip.setPixelColor(i, c);
    }
    strip.show();
}
