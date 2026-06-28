#!/usr/bin/env python3
"""
Hardware Interface for Adaptive Dexterous Hand
Supports: Allegro Hand, Shadow Hand, ESP32, CAN, I2C, PWM
"""

import numpy as np
from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum

class HandType(Enum):
    ALLEGRO = "allegro"
    SHADOW = "shadow"
    ESP32 = "esp32"
    CUSTOM = "custom"

@dataclass
class FingerConfig:
    """Configuration for a single finger."""
    name: str
    joint_ids: List[int]
    tactile_sensor_id: int
    min_force: float = 0.5
    max_force: float = 5.0
    home_position: List[float] = None

class HardwareInterface:
    """Base class for hardware communication."""
    
    def __init__(self, hand_type: HandType):
        self.hand_type = hand_type
        self.connected = False
        self.fingers = self._init_fingers()
    
    def _init_fingers(self) -> Dict[str, FingerConfig]:
        """Initialize finger configurations."""
        if self.hand_type == HandType.ALLEGRO:
            return {
                "thumb": FingerConfig("thumb", [0, 1, 2, 3], 0),
                "index": FingerConfig("index", [4, 5, 6, 7], 1),
                "middle": FingerConfig("middle", [8, 9, 10, 11], 2),
                "ring": FingerConfig("ring", [12, 13, 14, 15], 3),
                "pinky": FingerConfig("pinky", [16, 17, 18, 19], 4),
            }
        elif self.hand_type == HandType.SHADOW:
            return {
                "thumb": FingerConfig("thumb", [0, 1, 2, 3, 4], 0),
                "index": FingerConfig("index", [5, 6, 7, 8], 1),
                "middle": FingerConfig("middle", [9, 10, 11, 12], 2),
                "ring": FingerConfig("ring", [13, 14, 15, 16], 3),
                "pinky": FingerConfig("pinky", [17, 18, 19, 20], 4),
            }
        else:
            return {
                "thumb": FingerConfig("thumb", [0, 1, 2], 0),
                "index": FingerConfig("index", [3, 4, 5], 1),
                "middle": FingerConfig("middle", [6, 7, 8], 2),
                "ring": FingerConfig("ring", [9, 10, 11], 3),
                "pinky": FingerConfig("pinky", [12, 13, 14], 4),
            }
    
    def connect(self) -> bool:
        """Establish connection to hardware."""
        # Override in subclass for actual hardware communication
        self.connected = True
        return True
    
    def disconnect(self):
        """Close hardware connection."""
        self.connected = False
    
    def read_tactile(self) -> Dict[str, float]:
        """Read tactile sensor values."""
        # Override in subclass
        return {name: 0.0 for name in self.fingers}
    
    def read_joint_positions(self) -> Dict[str, List[float]]:
        """Read current joint positions."""
        # Override in subclass
        return {name: [0.0] * len(f.joint_ids) for name, f in self.fingers.items()}
    
    def set_joint_positions(self, positions: Dict[str, List[float]]):
        """Set target joint positions."""
        # Override in subclass
        pass
    
    def grasp(self, target_force: float = 2.0, timeout: float = 5.0) -> bool:
        """Execute grasp with force control."""
        if not self.connected:
            return False
        
        # Read initial tactile values
        tactile = self.read_tactile()
        
        # Close fingers until contact detected
        for finger_name, finger in self.fingers.items():
            if tactile[finger_name] < 0.1:  # No contact
                # Move finger to contact position
                positions = self.read_joint_positions()
                positions[finger_name] = [0.5] * len(finger.joint_ids)
                self.set_joint_positions(positions)
        
        # Apply force control
        start_time = time.time()
        while time.time() - start_time < timeout:
            tactile = self.read_tactile()
            
            # Check if all fingers have contact
            if all(v > 0.1 for v in tactile.values()):
                # Adjust force to target
                for finger_name, force in tactile.items():
                    if force < target_force * 0.9:
                        # Increase grip
                        pass
                    elif force > target_force * 1.1:
                        # Decrease grip
                        pass
            
            time.sleep(0.004)  # 4ms control loop
        
        return True
    
    def release(self):
        """Release grasp."""
        if not self.connected:
            return
        
        # Open all fingers
        positions = {name: [0.0] * len(f.joint_ids) for name, f in self.fingers.items()}
        self.set_joint_positions(positions)

class ROS2Interface(HardwareInterface):
    """ROS2-based hardware interface."""
    
    def __init__(self, hand_type: HandType = HandType.ALLEGRO):
        super().__init__(hand_type)
        self.node = None
        self.publishers = {}
        self.subscribers = {}
    
    def connect(self) -> bool:
        """Initialize ROS2 node and topics."""
        try:
            import rclpy
            from rclpy.node import Node
            
            rclpy.init()
            self.node = Node('dexhand_controller')
            
            # Create publishers for each finger
            for finger_name in self.fingers:
                topic = f'/hand/{finger_name}/command'
                self.publishers[finger_name] = self.node.create_publisher(
                    Float64MultiArray, topic, 10
                )
            
            # Create subscribers for tactile feedback
            for finger_name in self.fingers:
                topic = f'/hand/{finger_name}/tactile'
                self.subscribers[finger_name] = self.node.create_subscription(
                    Float64, topic, self._tactile_callback, 10
                )
            
            self.connected = True
            return True
        except Exception as e:
            print(f"ROS2 connection failed: {e}")
            return False
    
    def _tactile_callback(self, msg, finger_name):
        """Handle tactile sensor data."""
        self._tactile_values[finger_name] = msg.data
    
    def set_joint_positions(self, positions: Dict[str, List[float]]):
        """Publish joint commands via ROS2."""
        for finger_name, pos in positions.items():
            if finger_name in self.publishers:
                msg = Float64MultiArray()
                msg.data = pos
                self.publishers[finger_name].publish(msg)

class ESP32Interface(HardwareInterface):
    """ESP32-based hardware interface via Serial/CAN."""
    
    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 115200):
        super().__init__(HandType.ESP32)
        self.port = port
        self.baudrate = baudrate
        self.serial = None
    
    def connect(self) -> bool:
        """Establish serial connection to ESP32."""
        try:
            import serial
            self.serial = serial.Serial(self.port, self.baudrate, timeout=1)
            self.connected = True
            return True
        except Exception as e:
            print(f"ESP32 connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close serial connection."""
        if self.serial:
            self.serial.close()
        super().disconnect()
    
    def set_joint_positions(self, positions: Dict[str, List[float]]):
        """Send joint commands via serial."""
        if not self.connected:
            return
        
        # Format: "J<finger_id> <pos1> <pos2> ...\n"
        for finger_name, pos in positions.items():
            finger = self.fingers[finger_name]
            cmd = f"J{finger.joint_ids[0]} {' '.join(f'{p:.3f}' for p in pos)}\n"
            self.serial.write(cmd.encode())
    
    def read_tactile(self) -> Dict[str, float]:
        """Read tactile values from ESP32."""
        if not self.connected:
            return {}
        
        self.serial.write(b"T\n")
        response = self.serial.readline().decode().strip()
        
        # Parse: "T<value1> <value2> ...\n"
        values = response[1:].split()
        tactile = {}
        for i, (name, finger) in enumerate(self.fingers.items()):
            if i < len(values):
                tactile[name] = float(values[i])
        
        return tactile

# Example usage
if __name__ == "__main__":
    # ROS2 example
    robot = ROS2Interface(HandType.ALLEGRO)
    if robot.connect():
        print("Connected to Allegro Hand via ROS2")
        robot.grasp(target_force=2.0)
        robot.release()
        robot.disconnect()
    
    # ESP32 example
    esp = ESP32Interface(port="/dev/ttyUSB0")
    if esp.connect():
        print("Connected to ESP32")
        esp.grasp(target_force=2.0)
        esp.release()
        esp.disconnect()
