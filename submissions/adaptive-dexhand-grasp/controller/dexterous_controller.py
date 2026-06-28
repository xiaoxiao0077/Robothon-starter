#!/usr/bin/env python3
"""
Dexterous Hand Controller - Core control logic
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class GraspPhase(Enum):
    APPROACH = "approach"
    GRASP = "grasp"
    LIFT = "lift"
    TRANSPORT = "transport"
    PLACE = "place"
    RELEASE = "release"
    RECOVER = "recover"

@dataclass
class FingerState:
    """State of a single finger."""
    name: str
    joint_positions: List[float]
    tactile_value: float
    force: float
    contact: bool

@dataclass
class GraspResult:
    """Result of a grasp attempt."""
    success: bool
    force: float
    recovery_attempts: int
    phase: GraspPhase
    error: Optional[str] = None

class DexterousHandController:
    """Main controller for 5-finger dexterous hand."""
    
    def __init__(self, n_fingers: int = 5, n_joints_per_finger: int = 3):
        self.n_fingers = n_fingers
        self.n_joints_per_finger = n_joints_per_finger
        self.fingers = self._init_fingers()
        self.current_phase = GraspPhase.APPROACH
        self.recovery_attempts = 0
        self.max_recovery_attempts = 3
        
    def _init_fingers(self) -> Dict[str, FingerState]:
        """Initialize finger states."""
        finger_names = ["thumb", "index", "middle", "ring", "pinky"]
        fingers = {}
        for name in finger_names:
            fingers[name] = FingerState(
                name=name,
                joint_positions=[0.0] * self.n_joints_per_finger,
                tactile_value=0.0,
                force=0.0,
                contact=False
            )
        return fingers
    
    def reset(self):
        """Reset controller to initial state."""
        for finger in self.fingers.values():
            finger.joint_positions = [0.0] * self.n_joints_per_finger
            finger.tactile_value = 0.0
            finger.force = 0.0
            finger.contact = False
        self.current_phase = GraspPhase.APPROACH
        self.recovery_attempts = 0
    
    def update_tactile(self, tactile_values: Dict[str, float]):
        """Update tactile sensor readings."""
        for name, value in tactile_values.items():
            if name in self.fingers:
                self.fingers[name].tactile_value = value
                self.fingers[name].contact = value > 0.1
    
    def check_all_contact(self) -> bool:
        """Check if all fingers have contact."""
        return all(f.contact for f in self.fingers.values())
    
    def calculate_adaptive_force(self, target_force: float) -> float:
        """Calculate adaptive force based on tactile feedback."""
        if not self.check_all_contact():
            return target_force * 1.2  # Increase if not all contact
        
        # Adjust based on force distribution
        forces = [f.force for f in self.fingers.values()]
        force_std = np.std(forces)
        
        if force_std > 0.5:  # Uneven force distribution
            return target_force * 0.9  # Reduce to prevent damage
        
        return target_force
    
    def detect_slip(self) -> bool:
        """Detect slip event from tactile sensors."""
        for finger in self.fingers.values():
            # Slip detected if tactile value drops suddenly
            if finger.tactile_value < 0.05 and finger.contact:
                return True
        return False
    
    def execute_recovery(self) -> bool:
        """Execute slip recovery procedure."""
        if self.recovery_attempts >= self.max_recovery_attempts:
            return False
        
        self.recovery_attempts += 1
        self.current_phase = GraspPhase.RECOVER
        
        # Increase grip force
        for finger in self.fingers.values():
            finger.force *= 1.2
        
        return True
    
    def grasp(self, target_force: float = 2.0, timeout: float = 5.0) -> GraspResult:
        """Execute complete grasp sequence with fault recovery."""
        self.reset()
        self.current_phase = GraspPhase.APPROACH
        
        # Phase 1: Approach
        # (Simulated - move fingers to object)
        
        # Phase 2: Grasp
        self.current_phase = GraspPhase.GRASP
        
        # Phase 3: Check contact and apply force
        adaptive_force = self.calculate_adaptive_force(target_force)
        
        # Phase 4: Check for slip
        if self.detect_slip():
            if self.execute_recovery():
                # Recovery successful, continue
                pass
            else:
                return GraspResult(
                    success=False,
                    force=adaptive_force,
                    recovery_attempts=self.recovery_attempts,
                    phase=GraspPhase.RECOVER,
                    error="Max recovery attempts exceeded"
                )
        
        # Phase 5: Lift
        self.current_phase = GraspPhase.LIFT
        
        # Phase 6: Transport
        self.current_phase = GraspPhase.TRANSPORT
        
        # Phase 7: Place
        self.current_phase = GraspPhase.PLACE
        
        # Phase 8: Release
        self.current_phase = GraspPhase.RELEASE
        
        return GraspResult(
            success=True,
            force=adaptive_force,
            recovery_attempts=self.recovery_attempts,
            phase=GraspPhase.RELEASE
        )
    
    def multi_step_task(self, n_steps: int = 15) -> List[GraspResult]:
        """Execute multi-step task sequence."""
        results = []
        
        for step in range(n_steps):
            # Simulate different objects and targets
            target_force = 2.0 + np.random.normal(0, 0.3)
            
            result = self.grasp(target_force=target_force)
            results.append(result)
            
            if not result.success:
                # Task failed, attempt recovery
                if self.recovery_attempts < self.max_recovery_attempts:
                    self.execute_recovery()
                    # Retry step
                    result = self.grasp(target_force=target_force)
                    results[-1] = result
        
        return results

class MultiStepTaskPlanner:
    """Plans and executes multi-step manipulation tasks."""
    
    def __init__(self, controller: DexterousHandController):
        self.controller = controller
        self.task_sequence = self._define_task_sequence()
    
    def _define_task_sequence(self) -> List[Dict]:
        """Define 15-step task sequence."""
        return [
            {"step": 1, "action": "scan_workspace", "description": "Scan workspace for objects"},
            {"step": 2, "action": "approach_object_1", "description": "Approach first object"},
            {"step": 3, "action": "grasp_object_1", "description": "Grasp first object"},
            {"step": 4, "action": "lift_object_1", "description": "Lift first object"},
            {"step": 5, "action": "transport_object_1", "description": "Transport to target A"},
            {"step": 6, "action": "place_object_1", "description": "Place at target A"},
            {"step": 7, "action": "release_object_1", "description": "Release first object"},
            {"step": 8, "action": "approach_object_2", "description": "Approach second object"},
            {"step": 9, "action": "grasp_object_2", "description": "Grasp second object"},
            {"step": 10, "action": "lift_object_2", "description": "Lift second object"},
            {"step": 11, "action": "transport_object_2", "description": "Transport to target B"},
            {"step": 12, "action": "place_object_2", "description": "Place at target B (stack)"},
            {"step": 13, "action": "release_object_2", "description": "Release second object"},
            {"step": 14, "action": "verify_stack", "description": "Verify stack stability"},
            {"step": 15, "action": "retreat", "description": "Retreat to home position"},
        ]
    
    def execute_task(self) -> List[Dict]:
        """Execute complete task sequence."""
        results = []
        
        for task in self.task_sequence:
            step = task["step"]
            action = task["action"]
            
            # Execute grasp for manipulation steps
            if "grasp" in action or "lift" in action:
                result = self.controller.grasp(target_force=2.0)
                task_result = {
                    "step": step,
                    "action": action,
                    "success": result.success,
                    "force": result.force,
                    "recovery_attempts": result.recovery_attempts
                }
            else:
                # Non-manipulation steps (scan, approach, etc.)
                task_result = {
                    "step": step,
                    "action": action,
                    "success": True,
                    "force": 0.0,
                    "recovery_attempts": 0
                }
            
            results.append(task_result)
        
        return results

# Example usage
if __name__ == "__main__":
    controller = DexterousHandController()
    planner = MultiStepTaskPlanner(controller)
    
    results = planner.execute_task()
    
    # Print results
    print("\n" + "="*60)
    print("MULTI-TASK EXECUTION RESULTS")
    print("="*60)
    
    successes = sum(1 for r in results if r["success"])
    print(f"\nTotal Steps: {len(results)}")
    print(f"Successful: {successes}/{len(results)} ({successes/len(results)*100:.1f}%)")
    
    print("\nStep-by-Step Results:")
    print("-"*60)
    for r in results:
        status = "✓" if r["success"] else "✗"
        print(f"  Step {r['step']:2d}: {status} {r['action']:<25} Force={r['force']:.2f}N")
