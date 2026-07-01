"""
Recovery Module
Slip detection and recovery strategies
"""

import numpy as np

class SlipRecovery:
    """Slip detection and recovery."""
    
    def __init__(self, detection_threshold=0.5, recovery_factor=1.5):
        self.detection_threshold = detection_threshold
        self.recovery_factor = recovery_factor
        self.slip_history = []
        
    def detect_slip(self, force_history):
        """Detect slip from force history."""
        if len(force_history) < 2:
            return False
        
        forces = np.array(force_history)
        gradient = np.gradient(forces)
        
        slip_detected = np.any(np.abs(gradient) > self.detection_threshold)
        self.slip_history.append(slip_detected)
        
        return slip_detected
    
    def compute_recovery_force(self, current_force, slip_detected):
        """Compute recovery force if slip detected."""
        if slip_detected:
            return current_force * self.recovery_factor
        return current_force
    
    def adaptive_recovery(self, force_history, tactile_data):
        """Adaptive recovery strategy."""
        slip_detected = self.detect_slip(force_history)
        
        if slip_detected:
            recovery_force = np.mean(force_history) * self.recovery_factor
            return {
                "action": "increase_force",
                "force": recovery_force,
                "grip_adjustment": "tighten"
            }
        else:
            return {
                "action": "maintain",
                "force": np.mean(force_history),
                "grip_adjustment": "none"
            }
