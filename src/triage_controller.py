import numpy as np
from src.controller import DexterousHandController, PIDController, TrajectoryPlanner

class TriageController(DexterousHandController):
    def __init__(self, model, data):
        super().__init__(model, data)
        self.task_phase = 0
        self.phases = ['approach', 'grasp', 'lift', 'rotate', 'place', 'release']
        self.current_phase = 'approach'
        
        self.vial_position = np.array([-0.2, 0.1, 0.75])
        self.goal_position = np.array([0.3, -0.2, 0.85])
        
        self.trajectory_planner = TrajectoryPlanner()
        self.wrist_controller = PIDController(200, 5, 20)
        self.rotation_angle = 0.0
        
        self.grasp_complete = False
        self.rotation_complete = False
        self.task_completed = False
        
    def set_target_object(self, position: np.ndarray):
        self.vial_position = position.copy()
        
    def set_goal_position(self, position: np.ndarray):
        self.goal_position = position.copy()
        
    def update(self, data):
        hand_pos = data.xpos[data.body('palm').id]
        
        if self.current_phase == 'approach':
            self._approach_vial(hand_pos)
        elif self.current_phase == 'grasp':
            self._grasp_vial(data)
        elif self.current_phase == 'lift':
            self._lift_vial(data)
        elif self.current_phase == 'rotate':
            self._rotate_cap(data)
        elif self.current_phase == 'place':
            self._place_vial(hand_pos)
        elif self.current_phase == 'release':
            self._release_vial()
            
        return self.current_phase, self.task_completed
    
    def _approach_vial(self, hand_pos):
        target_pos = self.vial_position + np.array([0, 0, 0.15])
        distance = np.linalg.norm(hand_pos - target_pos)
        
        if distance < 0.05:
            self.current_phase = 'grasp'
            self.open_hand()
        else:
            self._move_towards(target_pos)
            
    def _grasp_vial(self, data):
        touch_sensors = data.sensordata[-5:]
        num_contacts = np.sum(touch_sensors > 0.1)
        
        if num_contacts >= 3:
            self.current_phase = 'lift'
            self.grasp_complete = True
        else:
            progress = min(1.0, self.data.time * 2)
            self.set_grip(progress)
            
    def _lift_vial(self, data):
        if self.data.time > 1.0:
            self.current_phase = 'rotate'
            
    def _rotate_cap(self, data):
        self.rotation_angle += 0.02
        
        indices = self.finger_indices['index'] + self.finger_indices['middle']
        for idx in indices[1:]:
            self.data.ctrl[idx] = np.sin(self.rotation_angle) * 0.3 + 0.8
            
        if self.rotation_angle > 4 * np.pi:
            self.current_phase = 'place'
            self.rotation_complete = True
            
    def _place_vial(self, hand_pos):
        target_pos = self.goal_position
        distance = np.linalg.norm(hand_pos - target_pos)
        
        if distance < 0.05:
            self.current_phase = 'release'
        else:
            self._move_towards(target_pos)
            
    def _release_vial(self):
        self.open_hand()
        if self.data.time > 2.0:
            self.task_completed = True
            
    def _move_towards(self, target_pos):
        pass
    
    def get_task_status(self):
        return {
            'phase': self.current_phase,
            'phase_index': self.phases.index(self.current_phase),
            'grasp_complete': self.grasp_complete,
            'rotation_complete': self.rotation_complete,
            'task_completed': self.task_completed,
            'rotation_angle': self.rotation_angle
        }

class FiveFingerGraspController(DexterousHandController):
    def __init__(self, model, data):
        super().__init__(model, data)
        self.grasp_patterns = {
            'precision': {
                'thumb': [0.3, 0.8, 1.0],
                'index': [0.2, 1.0, 0.8, 0.6],
                'middle': [0.1, 0.9, 0.7, 0.5],
                'ring': [0.0, 0.5, 0.4, 0.3],
                'pinky': [-0.1, 0.4, 0.3, 0.2]
            },
            'power': {
                'thumb': [0.5, 1.2, 1.5],
                'index': [0.0, 1.5, 1.3, 1.0],
                'middle': [0.0, 1.5, 1.3, 1.0],
                'ring': [0.0, 1.4, 1.2, 0.9],
                'pinky': [-0.3, 1.3, 1.1, 0.8]
            },
            'tripod': {
                'thumb': [0.4, 0.9, 1.1],
                'index': [0.3, 1.1, 0.9, 0.7],
                'middle': [0.2, 1.0, 0.8, 0.6],
                'ring': [0.0, 0.3, 0.2, 0.1],
                'pinky': [-0.2, 0.2, 0.1, 0.0]
            }
        }
        self.current_pattern = 'precision'
        self.grasp_progress = 0.0
        
    def set_grasp_pattern(self, pattern_name: str):
        if pattern_name in self.grasp_patterns:
            self.current_pattern = pattern_name
            
    def update(self, target_grip: float = None):
        if target_grip is not None:
            self.grasp_progress = np.clip(target_grip, 0, 1)
        else:
            self.grasp_progress = min(1.0, self.grasp_progress + 0.02)
            
        pattern = self.grasp_patterns[self.current_pattern]
        
        for finger, angles in pattern.items():
            indices = self.finger_indices[finger]
            for i, idx in enumerate(indices):
                if i < len(angles):
                    self.data.ctrl[idx] = angles[i] * self.grasp_progress
                    
        return self.grasp_progress
    
    def get_finger_forces(self, data):
        forces = {}
        for finger, indices in self.finger_indices.items():
            forces[finger] = np.mean(np.abs(data.actuator_force[indices]))
        return forces