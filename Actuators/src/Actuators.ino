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
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>

#define ENCODER_OPTIMIZE_INTERRUPTS
#include <Encoder.h>

#include <Atlasbuggy.h>


Atlasbuggy robot("naboris actuators");

/* ----------------------- *
 * BNO055 global variables *
 * ----------------------- */

#define INCLUDE_FILTERED_DATA
// #define INCLUDE_MAG_DATA
// #define INCLUDE_GYRO_DATA
// #define INCLUDE_ACCEL_DATA
// #define INCLUDE_LINACCEL_DATA

Adafruit_BNO055 bno = Adafruit_BNO055();

int imu_buf_len = 25;

char *imu_print_buffer;
imu::Quaternion quat;
imu::Vector<3> euler;
imu::Vector<3> mag;
imu::Vector<3> gyro;
imu::Vector<3> accel;
imu::Vector<3> linaccel;

// Accelerometer & gyroscope only for getting relative orientation, subject to gyro drift
// Adafruit_BNO055 bno = Adafruit_BNO055(0x08); // OPERATION_MODE_IMUPLUS

// Accelerometer & magnetometer only for getting relative orientation
// Adafruit_BNO055 bno = Adafruit_BNO055(0x0a);  // OPERATION_MODE_M4G

// Gets heading only from compass
// Adafruit_BNO055 bno = Adafruit_BNO055(0x09); // OPERATION_MODE_COMPASS

// OPERATION_MODE_NDOF without fast magnetometer calibration
// Adafruit_BNO055 bno = Adafruit_BNO055(OPERATION_MODE_NDOF_FMC_OFF);

/* ----------------------------- *
 * Motor shield global variables *
 * ----------------------------- */

 // Create the motor shield object with the default I2C address
 Adafruit_MotorShield AFMS = Adafruit_MotorShield();
 // Or, create it with a different I2C address (say for stacking)
 // Adafruit_MotorShield AFMS = Adafruit_MotorShield(0x61);

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

#define NUM_MOTORS 4
MotorStruct* motors = new MotorStruct[NUM_MOTORS];

#define MOTOR_1 1
#define MOTOR_2 0
#define MOTOR_3 2
#define MOTOR_4 3

/* ------------------------ *
 * Encoder global variables *
 * ------------------------ */

#define TICKS_TO_MM 100.0

Encoder rightEncoder(2, 8);
Encoder leftEncoder(3, 12);

long oldLeftPosition = 0;
long newRightPosition = 0;
long oldRightPosition = 0;
long newLeftPosition = 0;
uint32_t prev_enc_time = 0;

#define R_ENC_BUF_LEN 16
#define L_ENC_BUF_LEN 16
char r_enc_print_buffer[R_ENC_BUF_LEN];
char l_enc_print_buffer[L_ENC_BUF_LEN];

/* ----------------------------- *
 * Servo turret global variables *
 * ----------------------------- */

#define AZIMUTH_PIN 9
#define YAW_PIN 10
Servo servo1;
Servo servo2;
bool attached = false;
uint32_t servo_ping_time = 0;

/* -------------------------- *
 * LED strip global variables *
 * -------------------------- */

#define NUM_LEDS 24
#define LED_SIGNAL_PIN 6
Adafruit_NeoPixel strip = Adafruit_NeoPixel(NUM_LEDS, LED_SIGNAL_PIN, NEO_GRB + NEO_KHZ800);

uint32_t ping_timer = millis();

#define INIT_DATA_BUF_SIZE 255

void setup() {
    robot.begin();

    #ifdef INCLUDE_FILTERED_DATA
    imu_buf_len += 51;
    #endif

    #ifdef INCLUDE_MAG_DATA
    imu_buf_len += 22;
    #endif

    #ifdef INCLUDE_GYRO_DATA
    imu_buf_len += 22;
    #endif

    #ifdef INCLUDE_ACCEL_DATA
    imu_buf_len += 22;
    #endif

    #ifdef INCLUDE_LINACCEL_DATA
    imu_buf_len += 22;
    #endif

    imu_print_buffer = (char *)malloc(sizeof(char) * imu_buf_len);

    AFMS.begin();
    strip.begin();

    if(!bno.begin())
    {
        /* There was a problem detecting the BNO055 ... check your connections */
        Serial.print("Oops, no BNO055 detected ... Check your wiring or I2C ADDR!");
        while(1);
    }
    delay(1000);
    bno.setExtCrystalUse(true);

    strip.show();

    for (int motor_num = 1; motor_num <= NUM_MOTORS; motor_num++) {
        motors[motor_num - 1] = init_motor(motor_num);
    }

    char init_data_buf[INIT_DATA_BUF_SIZE];
    snprintf(init_data_buf, INIT_DATA_BUF_SIZE, "%d\t%d\t%s", bno.getTemp(), NUM_LEDS, String(TICKS_TO_MM));
    robot.setInitData(init_data_buf);
}

float qw, qx, qy, qz;
float ex, ey, ez;
float mx, my, mz;
float gx, gy, gz;
float ax, ay, az;
float lx, ly, lz;
uint8_t sys_stat, gyro_stat, accel_stat, mag_stat = 0;

#ifdef INCLUDE_FILTERED_DATA
uint16_t imu_skip_counter = 0;
#endif

void updateIMU() {
    // Possible vector values can be:
    // - VECTOR_ACCELEROMETER - m/s^2
    // - VECTOR_MAGNETOMETER  - uT
    // - VECTOR_GYROSCOPE     - rad/s
    // - VECTOR_EULER         - degrees
    // - VECTOR_LINEARACCEL   - m/s^2
    // - VECTOR_GRAVITY       - m/s^2

    Serial.print("imu\tt");
    Serial.print(millis());

    #ifdef INCLUDE_FILTERED_DATA
    // Quaternion data
    imu::Quaternion quat = bno.getQuat();

    float new_qw = quat.w();
    float new_qx = quat.x();
    float new_qy = quat.y();
    float new_qz = quat.z();

    if (new_qw != qw) {
        Serial.print("\tqw");
        Serial.print(qw, 4);
        qw = new_qw;
    }

    if (new_qx != qx) {
        Serial.print("\tqx");
        Serial.print(qx, 4);
        qx = new_qx;
    }

    if (new_qy != qy) {
        Serial.print("\tqy");
        Serial.print(qy, 4);
        qy = new_qy;
    }

    if (new_qz != qz) {
        Serial.print("\tqz");
        Serial.print(qz, 4);
        qz = new_qz;
    }

    imu::Vector<3> euler = bno.getVector(Adafruit_BNO055::VECTOR_EULER);

    float new_ex = euler.x();
    float new_ey = euler.y();
    float new_ez = euler.z();

    // xyz is yaw pitch roll. switching roll pitch yaw
    if (new_ex != ex) {
        Serial.print("\tez");
        Serial.print(ex, 4);
        ex = new_ex;
    }

    if (new_ey != ey) {
        Serial.print("\tey");
        Serial.print(ey, 4);
        ey = new_ey;
    }

    if (new_ez != ez) {
        Serial.print("\tex");
        Serial.print(ez, 4);
        ez = new_ez;
    }
    #endif

    #ifdef INCLUDE_MAG_DATA
    imu::Vector<3> mag = bno.getVector(Adafruit_BNO055::VECTOR_MAGNETOMETER);

    float new_mx = mag.x();
    float new_my = mag.y();
    float new_mz = mag.z();

    if (new_mx != mx) {
        Serial.print("\tmx");
        Serial.print(mx, 4);
        mx = new_mx;
    }

    if (new_my != my) {
        Serial.print("\tmy");
        Serial.print(my, 4);
        my = new_my;
    }

    if (new_mz != mz) {
        Serial.print("\tmz");
        Serial.print(mz, 4);
        mz = new_mz;
    }
    #endif

    #ifdef INCLUDE_GYRO_DATA
    imu::Vector<3> gyro = bno.getVector(Adafruit_BNO055::VECTOR_GYROSCOPE);

    float new_gx = gyro.x();
    float new_gy = gyro.y();
    float new_gz = gyro.z();

    if (new_gx != gx) {
        Serial.print("\tgx");
        Serial.print(gx, 4);
        gx = new_gx;
    }

    if (new_gy != gy) {
        Serial.print("\tgy");
        Serial.print(gy, 4);
        gy = new_gy;
    }

    if (new_gz != gz) {
        Serial.print("\tgz");
        Serial.print(gz, 4);
        gz = new_gz;
    }
    #endif

    #ifdef INCLUDE_ACCEL_DATA
    imu::Vector<3> accel = bno.getVector(Adafruit_BNO055::VECTOR_ACCELEROMETER);

    float new_ax = accel.x();
    float new_ay = accel.y();
    float new_az = accel.z();

    if (new_ax != ax) {
        Serial.print("\tax");
        Serial.print(ax, 4);
        ax = new_ax;
    }

    if (new_ay != ay) {
        Serial.print("\tay");
        Serial.print(ay, 4);
        ay = new_ay;
    }

    if (new_az != az) {
        Serial.print("\taz");
        Serial.print(az, 4);
        az = new_az;
    }
    #endif

    #ifdef INCLUDE_LINACCEL_DATA
    imu::Vector<3> linaccel = bno.getVector(Adafruit_BNO055::VECTOR_LINEARACCEL);

    float new_lx = linaccel.x();
    float new_ly = linaccel.y();
    float new_lz = linaccel.z();

    if (new_lx != lx) {
        Serial.print("\tlx");
        Serial.print(lx, 4);
        lx = new_lx;
    }

    if (new_ly != ly) {
        Serial.print("\tly");
        Serial.print(ly, 4);
        ly = new_ly;
    }

    if (new_lz != lz) {
        Serial.print("\tlz");
        Serial.print(lz, 4);
        lz = new_lz;
    }
    #endif

    /* Display calibration status for each sensor. */
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

void set_motor_goal(int motor_num, int speed) {
    motors[motor_num].goal_speed = speed;
    if (motors[motor_num].goal_speed > 0) {
        if (motors[motor_num].goal_speed < 0) {
            motors[motor_num].goal_speed = 0;
        }
        if (motors[motor_num].goal_speed > 255) {
            motors[motor_num].goal_speed = 255;
        }
    }
    else {
        if (motors[motor_num].goal_speed > 0) {
            motors[motor_num].goal_speed = 0;
        }
        if (motors[motor_num].goal_speed < -255) {
            motors[motor_num].goal_speed = -255;
        }
    }
}

// top left, top right, bottom left, bottom right
void set_motor_goals(int speed1, int speed2, int speed3, int speed4)
{
    set_motor_goal(MOTOR1, speed1);  // top left
    set_motor_goal(MOTOR2, speed2);  // top right
    set_motor_goal(MOTOR3, speed3);  // bottom left
    set_motor_goal(MOTOR4, speed4);  // bottom right
}


void ping() {
    ping_timer = millis();
}

void ping_turret() {
    servo_ping_timer = millis();
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

void updateEncoders()
{
    uint32_t enc_time = millis();
    newRightPosition = rightEncoder.read();
    newLeftPosition = leftEncoder.read();

    if (newRightPosition != oldRightPosition) {
        snprintf(r_enc_print_buffer, R_ENC_BUF_LEN, "er%lu\t%li\n", enc_time, newRightPosition);

        oldRightPosition = newRightPosition;
        Serial.print(r_enc_print_buffer);
    }

    if (newLeftPosition != oldLeftPosition) {
        snprintf(l_enc_print_buffer, L_ENC_BUF_LEN, "el%lu\t%li\n", enc_time, newLeftPosition);

        oldLeftPosition = newLeftPosition;
        Serial.print(l_enc_print_buffer);
    }
}

void loop()
{
    while (robot.available())
    {
        int status = robot.readSerial();
        if (status == 0) {  // user command
            String command = robot.getCommand();
            if (command.charAt(0) == 'd') {  // drive command
                int m1 = command.substring(1, 5).toInt();
                int m2 = command.substring(6, 9).toInt();
                int m3 = command.substring(9, 13).toInt();
                int m4 = command.substring(13, 17).toInt();
                set_motor_goals(m1, m2, m3, m4);
                ping();
            }

            else if (command.charAt(0) == 'h') {  // stop command
                stop_motors();
            }
            else if (command.charAt(0) == 'r') {  // release command
                release_motors();
            }
            else if (command.charAt(0) == 'c') {  // turret command
                int yaw = command.substring(1, 4).toInt();
                int azimuth = command.substring(4, 7).toInt();

                set_yaw(yaw);
                set_azimuth(azimuth);
                ping_turret();
            }
            else if (command.charAt(0) == 'o') {  // pixel command
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
            else if (command.charAt(0) == 'x') {  // show command
                if (attached) {
                    detach_turret();
                    delay(50);
                }
                strip.show();
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
            rightEncoder.write(0);
            leftEncoder.write(0);
            oldLeftPosition = -1;
            oldRightPosition = -1;
        }
    }

    if (!robot.isPaused()) {
        if (ping_timer > millis())  ping_timer = millis();
        if ((millis() - ping_timer) > 500) {
            stop_motors();
            ping_timer = millis();
        }

        if (servo_ping_timer > millis())  servo_ping_timer = millis();
        if (attached && (millis() - servo_ping_timer) > 750) {
            detach_turret();
            servo_ping_timer = millis();
        }

        updateEncoders();
        updateIMU();

        // 100Hz update rate for imu
        delay(10);
    }
}
