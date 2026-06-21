#!/usr/bin/env python3
"""
Task Scenarios for DexHand - 11 Comprehensive Task Definitions
11个综合任务场景定义
"""
import numpy as np


class TaskScenario:
    """Base class for task scenarios"""
    def __init__(self, name, description, difficulty, timeout_s=10.0):
        self.name = name
        self.description = description
        self.difficulty = difficulty
        self.timeout_s = timeout_s
        self.success_criteria = {}
    
    def get_initial_state(self):
        """Get initial joint positions"""
        return np.zeros(24)
    
    def get_target_state(self):
        """Get target joint positions"""
        return np.zeros(24)
    
    def check_success(self, state, target):
        """Check if task is successful"""
        error = np.abs(state - target).mean()
        return error < 0.05


class TriFingerGrasp(TaskScenario):
    """Task 1: Three-finger precision grasp - Thumb + Index + Middle"""
    def __init__(self):
        super().__init__(
            name="tri_finger_grasp",
            description="Precision grasp using thumb, index, and middle fingers to pick up a small sphere",
            difficulty="MEDIUM",
            timeout_s=8.0
        )
        self.success_criteria = {
            'contact_detected': True,
            'object_lifted': 0.05,  # meters
            'stability_score': 0.8
        }
    
    def get_initial_state(self):
        """Spread fingers to prepare for grasp"""
        state = np.zeros(24)
        state[0:4] = [0.5, 0.3, 0.2, 0.1]  # Thumb spread
        state[4:8] = [0.0, 0.5, 0.4, 0.3]  # Index
        state[8:12] = [0.0, 0.5, 0.4, 0.3]  # Middle
        return state
    
    def get_target_state(self):
        """Closed grasp position"""
        state = np.zeros(24)
        state[0:4] = [0.8, 0.8, 0.7, 0.6]  # Thumb closed
        state[4:8] = [0.3, 0.9, 0.8, 0.7]  # Index closed
        state[8:12] = [0.3, 0.9, 0.8, 0.7]  # Middle closed
        return state


class FiveFingerEnvelope(TaskScenario):
    """Task 2: Five-finger envelope grasp - Full hand wrap around cylinder"""
    def __init__(self):
        super().__init__(
            name="five_finger_envelope",
            description="Full hand envelope grasp around a cylindrical object",
            difficulty="HIGH",
            timeout_s=10.0
        )
        self.success_criteria = {
            'all_fingers_contact': True,
            'grip_force': 5.0,  # Newtons
            'stability_score': 0.85
        }
    
    def get_initial_state(self):
        """Wide spread open hand"""
        state = np.zeros(24)
        state[:] = [0.3, 0.2, 0.1, 0.0] * 6  # All spread
        return state
    
    def get_target_state(self):
        """Full envelope closure"""
        state = np.zeros(24)
        state[:] = [0.9, 0.8, 0.7, 0.6] * 6  # All closed
        return state


class CapRotation(TaskScenario):
    """Task 3: Bottle cap rotation - Five-finger coordinated rotation"""
    def __init__(self):
        super().__init__(
            name="cap_rotation",
            description="Five-finger coordinated rotation to open a bottle cap",
            difficulty="HIGH",
            timeout_s=15.0
        )
        self.success_criteria = {
            'rotation_angle': 2 * np.pi,  # Full rotation
            'grip_maintained': True,
            'time_efficiency': 0.7
        }
    
    def get_initial_state(self):
        """Gripping position"""
        state = np.zeros(24)
        state[0:4] = [0.6, 0.5, 0.4, 0.3]  # Thumb
        state[4:8] = [0.5, 0.6, 0.5, 0.4]  # Index
        state[8:12] = [0.5, 0.6, 0.5, 0.4]  # Middle
        state[12:16] = [0.5, 0.6, 0.5, 0.4]  # Ring
        state[16:20] = [0.5, 0.6, 0.5, 0.4]  # Pinky
        return state
    
    def get_target_state(self):
        """Rotated grip position"""
        state = self.get_initial_state()
        state[0:4] = [0.7, 0.6, 0.5, 0.4]  # Thumb rotated
        return state


class PrecisePlacement(TaskScenario):
    """Task 4: Precise object placement into target zone"""
    def __init__(self):
        super().__init__(
            name="precise_placement",
            description="Place object precisely into a designated target zone",
            difficulty="MEDIUM",
            timeout_s=10.0
        )
        self.success_criteria = {
            'position_error': 0.01,  # meters
            'orientation_error': 0.1,  # radians
            'settling_time': 1.0  # seconds
        }
    
    def get_initial_state(self):
        """Holding object above target"""
        state = np.zeros(24)
        state[0:4] = [0.7, 0.6, 0.5, 0.4]
        state[4:8] = [0.6, 0.5, 0.4, 0.3]
        state[8:12] = [0.6, 0.5, 0.4, 0.3]
        return state
    
    def get_target_state(self):
        """Release position over target"""
        state = np.zeros(24)
        state[0:4] = [0.4, 0.3, 0.2, 0.1]
        state[4:8] = [0.3, 0.2, 0.1, 0.0]
        state[8:12] = [0.3, 0.2, 0.1, 0.0]
        return state


class HandoffTransfer(TaskScenario):
    """Task 5: Object handoff transfer between grippers"""
    def __init__(self):
        super().__init__(
            name="handoff_transfer",
            description="Transfer object from one gripper to another",
            difficulty="HIGH",
            timeout_s=12.0
        )
        self.success_criteria = {
            'transfer_complete': True,
            'object_stable': True,
            'time_efficiency': 0.75
        }


class ToolManipulation(TaskScenario):
    """Task 6: Tool use manipulation - Screwdriver rotation"""
    def __init__(self):
        super().__init__(
            name="tool_manipulation",
            description="Use tool (screwdriver) to perform rotation task",
            difficulty="HIGH",
            timeout_s=15.0
        )
        self.success_criteria = {
            'tool_grasped': True,
            'rotation_complete': True,
            'force_applied': 3.0
        }


class GravityPlacement(TaskScenario):
    """Task 7: Place object under gravity influence"""
    def __init__(self):
        super().__init__(
            name="gravity_placement",
            description="Carefully place object accounting for gravity",
            difficulty="MEDIUM",
            timeout_s=8.0
        )
        self.success_criteria = {
            'position_accuracy': 0.02,
            'no_collision': True,
            'settling_time': 1.5
        }


class SoftManipulation(TaskScenario):
    """Task 8: Soft object manipulation - Cloth/fabric"""
    def __init__(self):
        super().__init__(
            name="soft_manipulation",
            description="Manipulate soft deformable object",
            difficulty="MEDIUM",
            timeout_s=10.0
        )
        self.success_criteria = {
            'deformation_controlled': True,
            'shape_maintained': True
        }


class MultiObjectSort(TaskScenario):
    """Task 9: Sort multiple objects by type"""
    def __init__(self):
        super().__init__(
            name="multi_object_sort",
            description="Sort 3 objects into designated zones",
            difficulty="HIGH",
            timeout_s=20.0
        )
        self.success_criteria = {
            'objects_sorted': 3,
            'sorting_accuracy': 1.0,
            'time_efficiency': 0.8
        }


class AdaptiveGrasp(TaskScenario):
    """Task 10: Adaptive grasp based on object properties"""
    def __init__(self):
        super().__init__(
            name="adaptive_grasp",
            description="Adapt grasp strategy based on sensed object properties",
            difficulty="HIGH",
            timeout_s=10.0
        )
        self.success_criteria = {
            'object_detected': True,
            'grasp_adapted': True,
            'grasp_success': True
        }


class TriageOperation(TaskScenario):
    """Task 11: Medical triage operation - Sort by priority"""
    def __init__(self):
        super().__init__(
            name="triage_operation",
            description="Medical triage: sort patients by priority level",
            difficulty="MEDIUM",
            timeout_s=15.0
        )
        self.success_criteria = {
            'patients_sorted': 5,
            'priority_correct': 0.95,
            'time_efficiency': 0.85
        }


# Factory function to get all scenarios
def get_all_scenarios():
    """Return list of all 11 task scenarios"""
    return [
        TriFingerGrasp(),
        FiveFingerEnvelope(),
        CapRotation(),
        PrecisePlacement(),
        HandoffTransfer(),
        ToolManipulation(),
        GravityPlacement(),
        SoftManipulation(),
        MultiObjectSort(),
        AdaptiveGrasp(),
        TriageOperation(),
    ]


def get_scenario_by_name(name):
    """Get scenario by name"""
    scenarios = get_all_scenarios()
    for scenario in scenarios:
        if scenario.name == name:
            return scenario
    return None


if __name__ == "__main__":
    # Test all scenarios
    print("=" * 60)
    print("DexHand Task Scenarios - All 11 Tasks")
    print("=" * 60)
    
    scenarios = get_all_scenarios()
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario.name}")
        print(f"   Difficulty: {scenario.difficulty}")
        print(f"   Timeout: {scenario.timeout_s}s")
        print(f"   Description: {scenario.description}")
        print(f"   Criteria: {list(scenario.success_criteria.keys())}")
    
    print(f"\n{'=' * 60}")
    print(f"Total: {len(scenarios)} task scenarios")
    print("=" * 60)
