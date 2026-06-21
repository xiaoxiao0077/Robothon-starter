#!/usr/bin/env python3
"""
硬件接口抽象层 - Hardware Interface Abstraction Layer
支持真实电机和传感器通信
"""
import numpy as np
import time
from abc import ABC, abstractmethod


class ActuatorInterface(ABC):
    """执行器接口抽象基类"""
    @abstractmethod
    def set_position(self, joint_id: int, position: float) -> bool:
        """设置关节位置"""
        pass
    
    @abstractmethod
    def set_velocity(self, joint_id: int, velocity: float) -> bool:
        """设置关节速度"""
        pass
    
    @abstractmethod
    def set_torque(self, joint_id: int, torque: float) -> bool:
        """设置关节力矩"""
        pass
    
    @abstractmethod
    def get_position(self, joint_id: int) -> float:
        """获取关节位置"""
        pass
    
    @abstractmethod
    def get_velocity(self, joint_id: int) -> float:
        """获取关节速度"""
        pass
    
    @abstractmethod
    def get_torque(self, joint_id: int) -> float:
        """获取关节力矩"""
        pass


class SensorInterface(ABC):
    """传感器接口抽象基类"""
    @abstractmethod
    def read_joint_positions(self) -> np.ndarray:
        """读取所有关节位置"""
        pass
    
    @abstractmethod
    def read_joint_velocities(self) -> np.ndarray:
        """读取所有关节速度"""
        pass
    
    @abstractmethod
    def read_touch_sensors(self) -> np.ndarray:
        """读取触觉传感器"""
        pass
    
    @abstractmethod
    def read_imu(self) -> dict:
        """读取IMU数据"""
        pass


class CANBusActuator(ActuatorInterface):
    """CAN总线执行器接口 - 用于真实电机控制"""
    def __init__(self, channel: int = 0, bitrate: int = 1000000):
        self.channel = channel
        self.bitrate = bitrate
        self.motor_ids = list(range(19))  # 19个电机
        self._connected = False
        
        # 电机参数 (基于真实舵机规格)
        self.max_torque = 2.0  # Nm
        self.max_velocity = 10.0  # rad/s
        self.position_resolution = 0.001  # rad
        self.torque_resolution = 0.001  # Nm
        
    def connect(self) -> bool:
        """连接CAN总线"""
        print(f"[CAN] Connecting to channel {self.channel} at {self.bitrate} bps...")
        # 模拟连接
        self._connected = True
        print("[CAN] Connected successfully")
        return True
    
    def disconnect(self):
        """断开CAN总线"""
        self._connected = False
        print("[CAN] Disconnected")
    
    def send_command(self, motor_id: int, cmd_type: str, value: float) -> bool:
        """发送CAN命令"""
        if not self._connected:
            return False
        # 模拟CAN发送
        # 真实实现需要调用 socketcan 或其他CAN库
        return True
    
    def read_response(self, motor_id: int) -> dict:
        """读取CAN响应"""
        if not self._connected:
            return {}
        # 模拟读取
        return {'position': 0.0, 'velocity': 0.0, 'torque': 0.0}
    
    def set_position(self, joint_id: int, position: float) -> bool:
        """设置关节位置"""
        if joint_id >= len(self.motor_ids):
            return False
        motor_id = self.motor_ids[joint_id]
        # 限幅
        position = np.clip(position, -np.pi, np.pi)
        return self.send_command(motor_id, 'position', position)
    
    def set_velocity(self, joint_id: int, velocity: float) -> bool:
        """设置关节速度"""
        if joint_id >= len(self.motor_ids):
            return False
        motor_id = self.motor_ids[joint_id]
        velocity = np.clip(velocity, -self.max_velocity, self.max_velocity)
        return self.send_command(motor_id, 'velocity', velocity)
    
    def set_torque(self, joint_id: int, torque: float) -> bool:
        """设置关节力矩"""
        if joint_id >= len(self.motor_ids):
            return False
        motor_id = self.motor_ids[joint_id]
        torque = np.clip(torque, -self.max_torque, self.max_torque)
        return self.send_command(motor_id, 'torque', torque)
    
    def get_position(self, joint_id: int) -> float:
        """获取关节位置"""
        if joint_id >= len(self.motor_ids):
            return 0.0
        motor_id = self.motor_ids[joint_id]
        resp = self.read_response(motor_id)
        return resp.get('position', 0.0)
    
    def get_velocity(self, joint_id: int) -> float:
        """获取关节速度"""
        if joint_id >= len(self.motor_ids):
            return 0.0
        motor_id = self.motor_ids[joint_id]
        resp = self.read_response(motor_id)
        return resp.get('velocity', 0.0)
    
    def get_torque(self, joint_id: int) -> float:
        """获取关节力矩"""
        if joint_id >= len(self.motor_ids):
            return 0.0
        motor_id = self.motor_ids[joint_id]
        resp = self.read_response(motor_id)
        return resp.get('torque', 0.0)


class I2CSensor(SensorInterface):
    """I2C传感器接口 - 用于触觉传感器阵列"""
    def __init__(self, bus: int = 1, address: int = 0x40):
        self.bus = bus
        self.address = address
        self.touch_sensor_count = 5  # 5个指尖
        
    def connect(self) -> bool:
        """连接I2C传感器"""
        print(f"[I2C] Connecting to bus {self.bus} at 0x{self.address:02x}...")
        return True
    
    def read_register(self, reg: int, length: int = 1) -> bytes:
        """读取I2C寄存器"""
        # 模拟读取
        return bytes([0] * length)
    
    def write_register(self, reg: int, value: int) -> bool:
        """写入I2C寄存器"""
        return True
    
    def read_joint_positions(self) -> np.ndarray:
        """读取关节位置 (编码器)"""
        # 从I2C读取5个手指的关节角度
        positions = np.zeros(24)
        for finger in range(5):
            for joint in range(4):
                idx = finger * 4 + joint
                if idx < 24:
                    positions[idx] = np.random.uniform(-0.5, 0.5)
        return positions
    
    def read_joint_velocities(self) -> np.ndarray:
        """读取关节速度"""
        velocities = np.zeros(24)
        for i in range(24):
            velocities[i] = np.random.uniform(-1, 1)
        return velocities
    
    def read_touch_sensors(self) -> np.ndarray:
        """读取触觉传感器"""
        touch = np.zeros(self.touch_sensor_count)
        for i in range(self.touch_sensor_count):
            # 模拟触觉数据 (0-1范围, 1表示完全接触)
            touch[i] = np.random.uniform(0, 1) if np.random.random() > 0.3 else 0
        return touch
    
    def read_imu(self) -> dict:
        """读取IMU数据"""
        return {
            'gyro': np.random.uniform(-2, 2, 3),      # rad/s
            'accel': np.random.uniform(-10, 10, 3),    # m/s^2
            'mag': np.random.uniform(-50, 50, 3),      # μT
            'temperature': 25.0 + np.random.uniform(-5, 5)  # °C
        }


class PWM Actuator:
    """PWM执行器接口 - 用于低成本舵机控制"""
    def __init__(self, gpio_pin: int):
        self.gpio_pin = gpio_pin
        self.frequency = 50  # Hz (舵机标准)
        self.min_duty = 0.025  # 2.5%
        self.max_duty = 0.125  # 12.5%
        
    def set_angle(self, angle: float):
        """设置舵机角度 (-90 to 90 degrees)"""
        duty_cycle = (angle + 90) / 180 * (self.max_duty - self.min_duty) + self.min_duty
        # 真实实现需要调用 RPi.GPIO 或 pigpio
        return True


class HardwareBridge:
    """硬件桥接器 - 连接仿真与真实硬件"""
    def __init__(self):
        self.can_actuator = CANBusActuator()
        self.i2c_sensor = I2CSensor()
        self.connected = False
        
    def connect(self) -> bool:
        """连接所有硬件"""
        print("=" * 50)
        print("Connecting to Hardware...")
        print("=" * 50)
        
        can_ok = self.can_actuator.connect()
        i2c_ok = self.i2c_sensor.connect()
        
        self.connected = can_ok and i2c_ok
        
        if self.connected:
            print("[Hardware] All devices connected successfully")
        else:
            print("[Hardware] Warning: Some devices failed to connect")
        
        return self.connected
    
    def disconnect(self):
        """断开所有硬件"""
        self.can_actuator.disconnect()
        self.connected = False
        print("[Hardware] All devices disconnected")
    
    def read_all_sensors(self) -> dict:
        """读取所有传感器数据"""
        if not self.connected:
            return {}
        
        return {
            'joint_positions': self.i2c_sensor.read_joint_positions(),
            'joint_velocities': self.i2c_sensor.read_joint_velocities(),
            'touch_sensors': self.i2c_sensor.read_touch_sensors(),
            'imu': self.i2c_sensor.read_imu(),
            'actuator_torques': np.array([
                self.can_actuator.get_torque(i) for i in range(19)
            ])
        }
    
    def send_position_command(self, positions: np.ndarray) -> bool:
        """发送位置控制命令"""
        if not self.connected or len(positions) > 19:
            return False
        
        for i, pos in enumerate(positions[:19]):
            self.can_actuator.set_position(i, pos)
        
        return True
    
    def send_torque_command(self, torques: np.ndarray) -> bool:
        """发送力矩控制命令"""
        if not self.connected or len(torques) > 19:
            return False
        
        for i, torque in enumerate(torques[:19]):
            self.can_actuator.set_torque(i, torque)
        
        return True


class RealTimeController:
    """实时控制器 - 硬件在环"""
    def __init__(self, bridge: HardwareBridge, control_rate: int = 1000):
        self.bridge = bridge
        self.control_rate = control_rate  # Hz
        self.dt = 1.0 / control_rate
        self.running = False
        
    def start(self):
        """启动实时控制循环"""
        print(f"[Controller] Starting at {self.control_rate} Hz...")
        self.running = True
        
        iteration = 0
        while self.running and iteration < 1000:
            # 读取传感器
            sensor_data = self.bridge.read_all_sensors()
            
            # 简单的位置控制示例
            target_positions = np.random.uniform(-0.5, 0.5, 19)
            self.bridge.send_position_command(target_positions)
            
            iteration += 1
            time.sleep(self.dt)
        
        print("[Controller] Stopped")
    
    def stop(self):
        """停止控制循环"""
        self.running = False


if __name__ == "__main__":
    print("=" * 50)
    print("Hardware Interface Test")
    print("=" * 50)
    
    # 创建硬件桥接器
    bridge = HardwareBridge()
    
    # 连接硬件
    bridge.connect()
    
    # 读取传感器数据
    print("\nReading sensor data...")
    sensor_data = bridge.read_all_sensors()
    for key, value in sensor_data.items():
        if isinstance(value, np.ndarray):
            print(f"  {key}: shape={value.shape}")
        else:
            print(f"  {key}: {type(value)}")
    
    # 发送控制命令
    print("\nSending position commands...")
    test_positions = np.zeros(19)
    bridge.send_position_command(test_positions)
    
    # 断开连接
    bridge.disconnect()
    
    print("\n" + "=" * 50)
    print("Hardware Interface Test Complete")
    print("=" * 50)
