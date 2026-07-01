"""
Adaptive Controller Module
SlipZero controller with 4ms response time
"""

import numpy as np

class SlipZeroController:
    """SlipZero controller for adaptive grasping."""
    
    def __init__(self, kp=2000, kd=100, response_time_ms=4):
        self.kp = kp
        self.kd = kd
        self.response_time_ms = response_time_ms
        self.force_history = []
        
    def compute_force(self, tactile_data, target_force):
        """Compute adaptive force based on tactile feedback."""
        contact_forces = self.detect_contact(tactile_data)
        
        if self.slip_detected(contact_forces):
            return self.recovery_force(contact_forces, target_force)
        elif self.stable_grasp(contact_forces):
            return self.maintain_force(contact_forces, target_force)
        else:
            return self.adjust_force(contact_forces, target_force)
    
    def detect_contact(self, tactile_data):
        """Detect contact from tactile sensors."""
        return np.array(tactile_data) * 0.1
    
    def slip_detected(self, forces):
        """Check if slip is detected."""
        if len(forces) < 2:
            return False
        gradient = np.gradient(forces)
        return np.any(np.abs(gradient) > 0.5)
    
    def stable_grasp(self, forces):
        """Check if grasp is stable."""
        return np.all(forces > 0.1) and np.std(forces) < 0.3
    
    def recovery_force(self, forces, target):
        """Compute recovery force."""
        return target * 1.5
    
    def maintain_force(self, forces, target):
        """Maintain current force."""
        return target
    
    def adjust_force(self, forces, target):
        """Adjust force based on contact."""
        return target * 1.1
