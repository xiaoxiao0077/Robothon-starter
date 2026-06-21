#!/usr/bin/env python3
"""
Robot Controller - High-level interface for DexHand
Wraps src/controller.py with simplified API for competition demo.
"""

from src.controller import SlipZeroController, AdaptiveImpedanceController
from src.force_control_utils import ForceFeedback
from src.data_collector import DataCollector

class RobotController:
    """Main controller class for Dexterous Hand operations."""
    
    def __init__(self):
        self.slip_ctrl = SlipZeroController(target_force=5.0, recovery_time_ms=4.0)
        self.impedance_ctrl = AdaptiveImpedanceController()
        self.force_feedback = ForceFeedback()
        self.data_collector = DataCollector()
    
    def grasp(self, obj_type="default"):
        """Execute grasp with automatic slip recovery."""
        self.slip_ctrl.lock(obj_type)
        return {"status": "grasped", "slip_detected": False}
    
    def release(self):
        """Release object."""
        self.slip_ctrl.unlock()
        return {"status": "released"}
    
    def apply_force(self, direction, magnitude):
        """Apply force with impedance control."""
        return self.impedance_ctrl.apply(direction, magnitude)
    
    def get_sensor_data(self):
        """Get current sensor readings."""
        return self.force_feedback.read_all()

if __name__ == "__main__":
    ctrl = RobotController()
    print("RobotController initialized successfully")
