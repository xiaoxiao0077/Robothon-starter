"""
Tactile Sensor Module
64 tactile sensors (16 per finger)
"""

import numpy as np

class TactileSensorArray:
    """Array of tactile sensors."""
    
    def __init__(self, n_sensors=64, n_fingers=4):
        self.n_sensors = n_sensors
        self.n_fingers = n_fingers
        self.sensors_per_finger = n_sensors // n_fingers
        
    def read(self):
        """Read all sensors."""
        return np.random.uniform(0, 1, self.n_sensors)
    
    def detect_contact(self, threshold=0.1):
        """Detect contact on each finger."""
        readings = self.read()
        contacts = []
        for i in range(self.n_fingers):
            start = i * self.sensors_per_finger
            end = start + self.sensors_per_finger
            finger_data = readings[start:end]
            contacts.append(np.any(finger_data > threshold))
        return contacts
    
    def compute_force(self):
        """Compute force from sensor readings."""
        readings = self.read()
        return np.sum(readings) * 0.1
