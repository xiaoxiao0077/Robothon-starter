/*
 * DexHand ESP32 Controller Firmware
 * ESP32-WROOM-32 / ESP32-S3
 * 
 * 功能：低层级电机控制和传感器读取
 * 通信：CAN Bus / UART / WiFi(BLE)
 */

#include <Arduino.h>
#include <Preferences.h>
#include <CAN.h>

// ============ 配置 ============
#define JOINT_COUNT 19
#define CONTROL_FREQ 1000  // Hz
#define CAN_TIMEOUT 1000   // μs

// ============ 引脚定义 ============
#define LED_STATUS 2
#define CAN_TX 5
#define CAN_RX 4
#define I2C_SDA 21
#define I2C_SCL 22

// ============ 全局变量 ============
Preferences preferences;

// 关节状态
float joint_positions[JOINT_COUNT] = {0};
float joint_velocities[JOINT_COUNT] = {0};
float joint_torques[JOINT_COUNT] = {0};
float target_positions[JOINT_COUNT] = {0};
float target_torques[JOINT_COUNT] = {0};

// 触觉传感器
float touch_sensors[5] = {0};

// 控制周期
unsigned long control_period_us = 1000;  // 1ms = 1000μs
unsigned long last_control_time = 0;

// 状态标志
bool calibrated = false;
bool emergency_stop = false;

// ============ 函数声明 ============
void init_can();
void init_i2c();
void init_serial();
void read_joint_states();
void read_touch_sensors();
void send_control_commands();
void update_motors();
float constrain_float(float value, float min_val, float max_val);
unsigned short crc16_modbus(uint8_t *data, uint16_t len);

// ============ 设置 ============
void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("===========================================");
    Serial.println("DexHand ESP32 Controller v1.0");
    Serial.println("===========================================");
    
    // 初始化引脚
    pinMode(LED_STATUS, OUTPUT);
    digitalWrite(LED_STATUS, LOW);
    
    // 初始化通信
    init_serial();
    init_i2c();
    init_can();
    
    // 从Flash加载校准数据
    preferences.begin("dexhand", false);
    calibrated = preferences.getBool("calibrated", false);
    if (calibrated) {
        Serial.println("Loading calibration data from Flash...");
        for (int i = 0; i < JOINT_COUNT; i++) {
            joint_positions[i] = preferences.getFloat(("pos_" + String(i)).c_str(), 0.0f);
        }
    } else {
        Serial.println("Warning: Not calibrated. Run calibration first.");
    }
    preferences.end();
    
    // 等待CAN总线就绪
    delay(100);
    
    Serial.println("===========================================");
    Serial.println("System initialized successfully!");
    Serial.println("===========================================");
}

// ============ 主循环 ============
void loop() {
    unsigned long current_time = micros();
    
    // 控制频率
    if (current_time - last_control_time >= control_period_us) {
        last_control_time = current_time;
        
        // 读取传感器
        read_joint_states();
        read_touch_sensors();
        
        // 处理命令 (CAN / Serial)
        process_commands();
        
        // 更新电机
        update_motors();
        
        // 发送状态
        send_status();
        
        // LED指示
        digitalWrite(LED_STATUS, !digitalRead(LED_STATUS));
    }
    
    // 处理串口命令
    if (Serial.available()) {
        process_serial_command();
    }
}

// ============ CAN初始化 ============
void init_can() {
    Serial.println("Initializing CAN Bus...");
    
    // 设置CAN引脚
    CAN.setPins(CAN_TX, CAN_RX);
    
    // 尝试初始化CAN (500kbps)
    if (!CAN.begin(500000)) {
        Serial.println("Warning: CAN failed to initialize. Running in simulation mode.");
    } else {
        Serial.println("CAN initialized successfully (500kbps).");
        // 添加滤波器接收所有报文
        CAN.filter(0);
    }
}

// ============ I2C初始化 ============
void init_i2c() {
    Serial.println("Initializing I2C...");
    Wire.begin(I2C_SDA, I2C_SCL);
    Wire.setClock(400000);  // 400kHz
    
    // 扫描I2C设备
    byte error, address;
    int nDevices = 0;
    
    for (address = 1; address < 127; address++) {
        Wire.beginTransmission(address);
        error = Wire.endTransmission();
        
        if (error == 0) {
            Serial.print("I2C device found at address 0x");
            Serial.println(address, HEX);
            nDevices++;
        }
    }
    
    if (nDevices == 0) {
        Serial.println("Warning: No I2C devices found.");
    }
}

// ============ 串口初始化 ============
void init_serial() {
    Serial.println("Serial interface ready.");
    Serial.println("Commands:");
    Serial.println("  POS <id> <value> - Set position");
    Serial.println("  STOP             - Emergency stop");
    Serial.println("  CAL              - Calibrate");
    Serial.println("  STAT             - Print status");
}

// ============ 读取关节状态 ============
void read_joint_states() {
    // 模拟读取 (真实需要CAN通信)
    for (int i = 0; i < JOINT_COUNT; i++) {
        // 添加噪声模拟真实传感器
        float noise = (random(-100, 100) / 10000.0f);
        joint_positions[i] = joint_positions[i] + noise;
        joint_velocities[i] = (target_positions[i] - joint_positions[i]) * 100;
    }
}

// ============ 读取触觉传感器 ============
void read_touch_sensors() {
    // 模拟触觉数据
    for (int i = 0; i < 5; i++) {
        touch_sensors[i] = random(0, 100) / 100.0f;
    }
}

// ============ 处理CAN命令 ============
void process_commands() {
    // 检查CAN报文
    if (CAN.parsePacket()) {
        int id = CAN.packetId();
        
        if (id >= 0x100 && id < 0x100 + JOINT_COUNT) {
            int joint_id = id - 0x100;
            
            // 读取数据
            uint8_t data[8];
            int i = 0;
            while (CAN.available() && i < 8) {
                data[i++] = CAN.read();
            }
            
            // 解析命令 (4字节位置 + 4字节力矩)
            if (i >= 8) {
                target_positions[joint_id] = *((float*)&data[0]);
                target_torques[joint_id] = *((float*)&data[4]);
            }
        }
    }
}

// ============ 更新电机 ============
void update_motors() {
    if (emergency_stop) return;
    
    for (int i = 0; i < JOINT_COUNT; i++) {
        // PID控制
        float error = target_positions[i] - joint_positions[i];
        float torque = error * 10.0f;  // 简化P控制
        
        // 限幅
        torque = constrain_float(torque, -2.0f, 2.0f);
        joint_torques[i] = torque;
        
        // 真实需要发送CAN命令
        // send_can_motor_command(i, target_positions[i], torque);
    }
}

// ============ 发送状态 ============
void send_status() {
    // 定期通过CAN发送状态
    static unsigned long last_status_time = 0;
    unsigned long now = millis();
    
    if (now - last_status_time >= 10) {  // 100Hz
        last_status_time = now;
        
        // 发送关节状态
        for (int i = 0; i < JOINT_COUNT; i++) {
            CAN.beginPacket(0x200 + i);
            uint8_t data[8];
            *((float*)&data[0]) = joint_positions[i];
            *((float*)&data[4]) = joint_torques[i];
            CAN.write(data, 8);
            CAN.endPacket();
        }
        
        // 通过USB发送状态
        if (Serial) {
            Serial.print("POS:");
            for (int i = 0; i < JOINT_COUNT; i++) {
                Serial.print(joint_positions[i], 4);
                if (i < JOINT_COUNT - 1) Serial.print(",");
            }
            Serial.println();
        }
    }
}

// ============ 处理串口命令 ============
void process_serial_command() {
    static String command = "";
    
    while (Serial.available()) {
        char c = Serial.read();
        if (c == '\n' || c == '\r') {
            command.trim();
            
            if (command.startsWith("POS")) {
                // POS <id> <value>
                int space1 = command.indexOf(' ');
                int space2 = command.indexOf(' ', space1 + 1);
                if (space2 > 0) {
                    int id = command.substring(space1 + 1, space2).toInt();
                    float value = command.substring(space2 + 1).toFloat();
                    if (id >= 0 && id < JOINT_COUNT) {
                        target_positions[id] = value;
                        Serial.print("Set joint ");
                        Serial.print(id);
                        Serial.print(" to ");
                        Serial.println(value);
                    }
                }
            }
            else if (command == "STOP") {
                emergency_stop = true;
                Serial.println("Emergency stop!");
            }
            else if (command == "RESUME") {
                emergency_stop = false;
                Serial.println("Resume.");
            }
            else if (command == "CAL") {
                Serial.println("Calibrating...");
                for (int i = 0; i < JOINT_COUNT; i++) {
                    joint_positions[i] = 0.0f;
                    target_positions[i] = 0.0f;
                }
                calibrated = true;
                
                // 保存校准数据
                preferences.begin("dexhand", false);
                preferences.putBool("calibrated", true);
                for (int i = 0; i < JOINT_COUNT; i++) {
                    preferences.putFloat(("pos_" + String(i)).c_str(), 0.0f);
                }
                preferences.end();
                
                Serial.println("Calibration saved!");
            }
            else if (command == "STAT") {
                Serial.println("=== Joint States ===");
                for (int i = 0; i < JOINT_COUNT; i++) {
                    Serial.print("Joint ");
                    Serial.print(i);
                    Serial.print(": pos=");
                    Serial.print(joint_positions[i], 4);
                    Serial.print(", vel=");
                    Serial.print(joint_velocities[i], 4);
                    Serial.print(", tor=");
                    Serial.println(joint_torques[i], 4);
                }
                Serial.println("=== Touch Sensors ===");
                for (int i = 0; i < 5; i++) {
                    Serial.print("Touch ");
                    Serial.print(i);
                    Serial.print(": ");
                    Serial.println(touch_sensors[i], 4);
                }
            }
            
            command = "";
        } else {
            command += c;
        }
    }
}

// ============ 工具函数 ============
float constrain_float(float value, float min_val, float max_val) {
    if (value < min_val) return min_val;
    if (value > max_val) return max_val;
    return value;
}

unsigned short crc16_modbus(uint8_t *data, uint16_t len) {
    unsigned short crc = 0xFFFF;
    
    for (uint16_t i = 0; i < len; i++) {
        crc ^= data[i];
        for (uint8_t j = 0; j < 8; j++) {
            if (crc & 0x0001) {
                crc = (crc >> 1) ^ 0xA001;
            } else {
                crc >>= 1;
            }
        }
    }
    
    return crc;
}
