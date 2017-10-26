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
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>

#include <Atlasbuggy.h>


/* Set the delay between fresh samples */
#define INCLUDE_FILTERED_DATA

#ifdef INCLUDE_FILTERED_DATA
int sample_rate_delay_ms = 10;
#else
int sample_rate_delay_ms = 100;
#endif

// Create the motor shield object with the default I2C address
Adafruit_MotorShield AFMS = Adafruit_MotorShield();
// Or, create it with a different I2C address (say for stacking)
// Adafruit_MotorShield AFMS = Adafruit_MotorShield(0x61);

Atlasbuggy robot("naboris actuators");


Adafruit_BNO055 bno = Adafruit_BNO055();


// Accelerometer & gyroscope only for getting relative orientation, subject to gyro drift
// Adafruit_BNO055 bno = Adafruit_BNO055(0x08); // OPERATION_MODE_IMUPLUS

// Accelerometer & magnetometer only for getting relative orientation
// Adafruit_BNO055 bno = Adafruit_BNO055(0x0a);  // OPERATION_MODE_M4G

// Gets heading only from compass
// Adafruit_BNO055 bno = Adafruit_BNO055(0x09); // OPERATION_MODE_COMPASS

// OPERATION_MODE_NDOF without fast magnetometer calibration
// Adafruit_BNO055 bno = Adafruit_BNO055(OPERATION_MODE_NDOF_FMC_OFF);

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
int speed_increment = 20;
int speed_delay = 1;
MotorStruct* motors = new MotorStruct[NUM_MOTORS];

Servo servo1;
Servo servo2;
int yaw = 0;
int azimuth = 0;
int goal_yaw = 0;
int goal_azimuth = 0;
bool attached = false;
bool goal_available = false;
uint32_t servo_timer = millis();

#define NUM_LEDS 24
#define LED_SIGNAL_PIN 6
Adafruit_NeoPixel strip = Adafruit_NeoPixel(NUM_LEDS, LED_SIGNAL_PIN, NEO_GRB + NEO_KHZ800);
uint32_t led_time = millis();
bool cycle_paused = true;

uint16_t lower_V = 4800;
uint16_t upper_V = 5000;
Battery battery(lower_V, upper_V, A0);

uint32_t ping_timer = millis();

void setup() {
    robot.begin();
    AFMS.begin();
    strip.begin();
    battery.begin();
    if(!bno.begin())
    {
        /* There was a problem detecting the BNO055 ... check your connections */
        Serial.print("Ooops, no BNO055 detected ... Check your wiring or I2C ADDR!");
        while(1);
    }
    delay(1000);
    bno.setExtCrystalUse(true);

    String temperature = String(bno.getTemp());
    String sample_rate_delay_ms_str = String(sample_rate_delay_ms);

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
        voltageValueStr + "\t" +
        temperature + "\t" +
        sample_rate_delay_ms_str
    );

}

void updateIMU() {
    // Possible vector values can be:
    // - VECTOR_ACCELEROMETER - m/s^2
    // - VECTOR_MAGNETOMETER  - uT
    // - VECTOR_GYROSCOPE     - rad/s
    // - VECTOR_EULER         - degrees
    // - VECTOR_LINEARACCEL   - m/s^2
    // - VECTOR_GRAVITY       - m/s^2

    Serial.print("t");
    Serial.print(millis());

    #ifdef INCLUDE_FILTERED_DATA
    // Quaternion data
    imu::Quaternion quat = bno.getQuat();

    float qw = quat.w();
    float qx = quat.x();
    float qy = quat.y();
    float qz = quat.z();

    Serial.print("\tqw");
    Serial.print(qw);
    Serial.print("\tqx");
    Serial.print(qx);
    Serial.print("\tqy");
    Serial.print(qy);
    Serial.print("\tqz");
    Serial.print(qz);

    imu::Vector<3> euler = bno.getVector(Adafruit_BNO055::VECTOR_EULER);

    // xyz is yaw pitch roll for some reason... switching roll pitch yaw
    Serial.print("\tex");
    Serial.print(euler.z(), 4);
    Serial.print("\tey");
    Serial.print(euler.y(), 4);
    Serial.print("\tez");
    Serial.print(euler.x(), 4);
    // float roll;
    // float pitch;
    // float yaw;
    // float singularity_check = qx * qy + qz * qw;
    // if (singularity_check == 0.5) {  // north pole
    //     yaw = 2 * atan2(qx, qw);
    //     pitch = PI / 2;
    //     roll = 0.0;
    // }
    // else if (singularity_check == -0.5) {  // south pole
    //     yaw = -2 * atan2(qx, qw);
    //     pitch = -PI / 2;
    //     roll = 0.0;
    // }
    // else {
    //     yaw = atan2(2 * qy * qw - 2 * qx * qz, 1 - 2 * qy * qy - 2 * qz * qz);
    //     pitch = asin(2 * qx * qy + 2 * qz * qw);
    //     roll = atan2(2 * qx * qw - 2 * qy * qz, 1 - 2 * qx * qx - 2 * qz * qz);
    // }
    // Serial.print("\tex");
    // Serial.print(roll);
    // Serial.print("\tey");
    // Serial.print(pitch);
    // Serial.print("\tez");
    // Serial.print(yaw);

    #endif

    imu::Vector<3> mag = bno.getVector(Adafruit_BNO055::VECTOR_MAGNETOMETER);

    Serial.print("\tmx");
    Serial.print(mag.x(), 4);
    Serial.print("\tmy");
    Serial.print(mag.y(), 4);
    Serial.print("\tmz");
    Serial.print(mag.z(), 4);

    imu::Vector<3> gyro = bno.getVector(Adafruit_BNO055::VECTOR_GYROSCOPE);

    Serial.print("\tgx");
    Serial.print(gyro.x(), 4);
    Serial.print("\tgy");
    Serial.print(gyro.y(), 4);
    Serial.print("\tgz");
    Serial.print(gyro.z(), 4);

    imu::Vector<3> accel = bno.getVector(Adafruit_BNO055::VECTOR_ACCELEROMETER);

    Serial.print("\tax");
    Serial.print(accel.x(), 4);
    Serial.print("\tay");
    Serial.print(accel.y(), 4);
    Serial.print("\taz");
    Serial.print(accel.z(), 4);

    imu::Vector<3> linaccel = bno.getVector(Adafruit_BNO055::VECTOR_LINEARACCEL);
    Serial.print("\tlx");
    Serial.print(linaccel.x(), 4);
    Serial.print("\tly");
    Serial.print(linaccel.y(), 4);
    Serial.print("\tlz");
    Serial.print(linaccel.z(), 4);


    /* Display calibration status for each sensor. */
    uint8_t sys_stat, gyro_stat, accel_stat, mag_stat = 0;
    bno.getCalibration(&sys_stat, &gyro_stat, &accel_stat, &mag_stat);
    Serial.print("\tss");
    Serial.print(sys_stat, DEC);
    Serial.print("\tsg");
    Serial.print(gyro_stat, DEC);
    Serial.print("\tsa");
    Serial.print(accel_stat, DEC);
    Serial.print("\tsm");
    Serial.print(mag_stat, DEC);

    Serial.print('\n');

    delay(sample_rate_delay_ms);
}

void attach_turret()
{
    if (!attached) {
        servo1.attach(YAW_PIN);
        servo2.attach(AZIMUTH_PIN);
        attached = true;
    }
}

void detach_turret()
{
    if (attached) {
        servo1.detach();
        servo2.detach();
        attached = false;
    }
}

void set_yaw(int yaw) {
    servo1.write(yaw);
}

void set_azimuth(int azimuth) {
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

void drive(int angle, int speed, int angular)
{
    angle %= 360;

    if (0 <= angle && angle < 90) {
        int fraction_speed = -2 * speed / 90 * angle + speed;
        set_motor_goals(speed + angular, fraction_speed - angular, fraction_speed + angular, speed - angular);
    }
    else if (90 <= angle && angle < 180) {
        int fraction_speed = -2 * speed / 90 * (angle - 90) + speed;
        set_motor_goals(fraction_speed + angular, -speed - angular, -speed + angular, fraction_speed - angular);
    }
    else if (180 <= angle && angle < 270) {
        int fraction_speed = 2 * speed / 90 * (angle - 180) - speed;
        set_motor_goals(-speed + angular, fraction_speed - angular, fraction_speed + angular, -speed - angular);
    }
    else if (270 <= angle && angle < 360) {
        int fraction_speed = 2 * speed / 90 * (angle - 270) - speed;
        set_motor_goals(fraction_speed + angular, speed - angular, speed + angular, fraction_speed - angular);
    }
}

void ping() {
    ping_timer = millis();
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
                int speed = command.substring(5, 8).toInt();
                int angular = command.substring(8, 11).toInt();
                if (command.charAt(1) == '1') {
                    speed *= -1;
                }
                else if (command.charAt(1) == '2') {
                    angular *= -1;
                }
                else if (command.charAt(1) == '3') {
                    speed *= -1;
                    angular *= -1;
                }
                drive(angle, speed, angular * 2);
                ping();
            }
            else if (command.charAt(0) == 'r') {  // spin command
                int speed = command.substring(2, 5).toInt();
                if (command.charAt(1) == '1') {
                    speed *= -1;
                }
                spin(speed);
                ping();
            }

            else if (command.charAt(0) == 'h') {  // stop command
                stop_motors();
            }
            else if (command.charAt(0) == 'r') {  // release command
                release_motors();
            }
            else if (command.charAt(0) == 'c') {  // turret command
                servo_timer = millis();
                attach_turret();

                goal_yaw = command.substring(1, 4).toInt();
                goal_azimuth = command.substring(4, 7).toInt();

                set_yaw(goal_yaw);
                set_azimuth(goal_azimuth);

                servo_timer = millis();
                goal_available = true;
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
        }
    }

    if (!robot.isPaused()) {
        update_motors();
        updateIMU();
        if (ping_timer > millis())  ping_timer = millis();
        if ((millis() - ping_timer) > 750) {
            stop_motors();
            detach_turret();
            ping_timer = millis();
        }

        // Sequence of turret events to run (avoids use of delay)
        if (servo_timer > millis())  servo_timer = millis();
        if (goal_available && (millis() - servo_timer) > 500)
        {
            detach_turret();
            goal_available = false;
            servo_timer = millis();
        }

        if (!cycle_paused) {
            if (led_time > millis()) led_time = millis();
            if ((millis() - led_time) > 50) {
                update_leds();
                led_time = millis();
            }
        }
    }
}
