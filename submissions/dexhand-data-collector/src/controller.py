import numpy as np
from typing import Dict, Tuple, Optional, List

class PIDController:
    def __init__(self, kp: float, ki: float, kd: float, 
                 min_output: float = -np.inf, max_output: float = np.inf):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.min_output = min_output
        self.max_output = max_output
        self.integral = 0.0
        self.last_error = 0.0
        
    def reset(self):
        self.integral = 0.0
        self.last_error = 0.0
        
    def compute(self, error: float, dt: float) -> float:
        self.integral += error * dt
        derivative = (error - self.last_error) / dt if dt > 0 else 0.0
        self.last_error = error
        
        output = self.kp * error + self.ki * self.integral + self.kd * derivative
        return np.clip(output, self.min_output, self.max_output)

class ImpedanceController:
    def __init__(self, kp: np.ndarray, kv: np.ndarray, 
                 desired_pos: np.ndarray, desired_vel: np.ndarray = None):
        self.kp = kp
        self.kv = kv
        self.desired_pos = desired_pos.copy()
        self.desired_vel = desired_vel.copy() if desired_vel is not None else np.zeros_like(desired_pos)
        
    def set_desired(self, pos: np.ndarray, vel: Optional[np.ndarray] = None):
        self.desired_pos = pos.copy()
        if vel is not None:
            self.desired_vel = vel.copy()
        
    def compute(self, current_pos: np.ndarray, current_vel: np.ndarray) -> np.ndarray:
        pos_error = self.desired_pos - current_pos
        vel_error = self.desired_vel - current_vel
        return self.kp * pos_error + self.kv * vel_error

class SlipDetector:
    """Detect slip using tactile and force sensors."""
    def __init__(self, slip_threshold: float = 0.1, window_size: int = 10):
        self.slip_threshold = slip_threshold
        self.window_size = window_size
        self.force_history = []
        self.touch_history = []
        self.slip_detected = False
        self.slip_magnitude = 0.0
        
    def update(self, forces: np.ndarray, touch: np.ndarray):
        """Update slip detector with new sensor data."""
        self.force_history.append(np.mean(np.abs(forces)))
        self.touch_history.append(np.mean(touch))
        
        # Maintain window
        if len(self.force_history) > self.window_size:
            self.force_history.pop(0)
            self.touch_history.pop(0)
        
        # Detect slip based on force/touch variations
        if len(self.force_history) >= self.window_size:
            force_std = np.std(self.force_history)
            touch_diff = np.diff(self.touch_history)
            
            if force_std > self.slip_threshold or np.any(np.abs(touch_diff) > 0.05):
                self.slip_detected = True
                self.slip_magnitude = force_std
            else:
                self.slip_detected = False
                self.slip_magnitude = 0.0
        
        return self.slip_detected, self.slip_magnitude

class SlipRecoveryController:
    """Fast slip recovery mechanism (4ms response time)."""
    def __init__(self, recovery_strength: float = 0.5, recovery_duration: float = 0.004):
        self.recovery_strength = recovery_strength
        self.recovery_duration = recovery_duration
        self.recovering = False
        self.recovery_timer = 0.0
        self.original_grip = 0.0
        
    def trigger_recovery(self, current_grip: float):
        """Trigger slip recovery."""
        self.recovering = True
        self.recovery_timer = 0.0
        self.original_grip = current_grip
        
    def update(self, dt: float) -> float:
        """Update recovery and return grip adjustment."""
        if not self.recovering:
            return 0.0
        
        self.recovery_timer += dt
        
        if self.recovery_timer >= self.recovery_duration:
            self.recovering = False
            return 0.0
        
        # Smooth recovery profile
        progress = self.recovery_timer / self.recovery_duration
        adjustment = self.recovery_strength * (1 - np.cos(progress * np.pi)) / 2
        
        return adjustment

class RobotController:
    def __init__(self, model, data):
        self.model = model
        self.data = data
        self.nu = model.nu
        self.nq = model.nq
        self.actuator_names = [model.actuator(i).name for i in range(model.nu)]
        
    def set_actuator_targets(self, targets: np.ndarray):
        if len(targets) == self.nu:
            self.data.ctrl[:] = targets
            
    def get_actuator_targets(self) -> np.ndarray:
        return np.copy(self.data.ctrl)
    
    def get_joint_positions(self) -> np.ndarray:
        return np.copy(self.data.qpos)
    
    def get_joint_velocities(self) -> np.ndarray:
        return np.copy(self.data.qvel)

class DexterousHandController(RobotController):
    def __init__(self, model, data):
        super().__init__(model, data)
        self.finger_indices = {
            'thumb': [0, 1, 2],
            'index': [3, 4, 5, 6],
            'middle': [7, 8, 9, 10],
            'ring': [11, 12, 13, 14],
            'pinky': [15, 16, 17, 18]
        }
        self.finger_pids = {
            finger: [PIDController(500, 10, 50, -1.5, 1.5) for _ in range(len(indices))]
            for finger, indices in self.finger_indices.items()
        }
        
    def set_finger_position(self, finger_name: str, angles: np.ndarray):
        if finger_name in self.finger_indices:
            indices = self.finger_indices[finger_name]
            for i, idx in enumerate(indices):
                if i < len(angles):
                    self.data.ctrl[idx] = angles[i]
    
    def set_all_fingers(self, angles_dict: Dict[str, np.ndarray]):
        for finger, angles in angles_dict.items():
            self.set_finger_position(finger, angles)
    
    def open_hand(self):
        self.data.ctrl[:] = 0.0
        
    def close_hand(self, grip_strength: float = 1.0):
        targets = np.zeros(self.nu)
        targets[self.finger_indices['thumb']] = [0.0, 1.0, 1.2]
        targets[self.finger_indices['index']] = [0.0, 1.2, 1.0, 0.8]
        targets[self.finger_indices['middle']] = [0.0, 1.2, 1.0, 0.8]
        targets[self.finger_indices['ring']] = [0.0, 1.0, 0.9, 0.7]
        targets[self.finger_indices['pinky']] = [-0.2, 0.9, 0.8, 0.6]
        self.data.ctrl[:] = targets * grip_strength
    
    def set_grip(self, grip_value: float):
        self.close_hand(grip_strength=np.clip(grip_value, 0, 1))
    
    def update_pid(self, desired_positions: np.ndarray, dt: float):
        current_pos = self.get_joint_positions()
        for finger, pids in self.finger_pids.items():
            indices = self.finger_indices[finger]
            for i, idx in enumerate(indices):
                if i < len(pids):
                    error = desired_positions[idx] - current_pos[idx + 6]
                    self.data.ctrl[idx] = pids[i].compute(error, dt)

class TrajectoryPlanner:
    def __init__(self):
        self.trajectory = []
        self.current_idx = 0
        
    def generate_joint_space_trajectory(self, start_pos: np.ndarray, end_pos: np.ndarray, 
                                        duration: float, timestep: float):
        num_steps = int(duration / timestep)
        self.trajectory = []
        
        for i in range(num_steps + 1):
            t = i / num_steps
            pos = start_pos + (end_pos - start_pos) * self.smooth_step(t)
            vel = (end_pos - start_pos) * self.smooth_step_derivative(t) / timestep
            self.trajectory.append((pos, vel))
        
        self.current_idx = 0
        
    def smooth_step(self, t: float) -> float:
        return t * t * (3 - 2 * t)
    
    def smooth_step_derivative(self, t: float) -> float:
        return 6 * t * (1 - t)
    
    def get_next_target(self) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        if self.current_idx < len(self.trajectory):
            target = self.trajectory[self.current_idx]
            self.current_idx += 1
            return target
        return None
    
    def is_complete(self) -> bool:
        return self.current_idx >= len(self.trajectory)

class AdaptiveGraspController(DexterousHandController):
    """Advanced adaptive grasping with closed-loop control and slip recovery."""
    def __init__(self, model, data):
        super().__init__(model, data)
        self.contact_threshold = 0.1
        self.adaptation_rate = 0.01
        self.target_grip_force = 5.0
        self.current_grip_force = 0.0
        self.grasp_state = 'opening'
        
        # Slip detection and recovery
        self.slip_detector = SlipDetector(slip_threshold=0.1, window_size=5)
        self.slip_recovery = SlipRecoveryController(recovery_strength=0.3, recovery_duration=0.004)
        
        # Closed-loop parameters
        self.force_error_integral = 0.0
        self.max_adjustment = 0.1
        self.slip_recovery_count = 0
        
    def update(self, sensor_data: np.ndarray, dt: float = 0.001):
        touch_sensors = sensor_data[-5:]
        current_forces = self.data.actuator_force
        
        # Update slip detector
        slip_detected, slip_magnitude = self.slip_detector.update(current_forces, touch_sensors)
        
        # Handle slip recovery
        if slip_detected and self.grasp_state == 'holding':
            self.slip_recovery.trigger_recovery(self.current_grip_force)
            self.slip_recovery_count += 1
        
        # Get recovery adjustment
        recovery_adjustment = self.slip_recovery.update(dt)
        
        if self.grasp_state == 'opening':
            self.open_hand()
            if np.sum(touch_sensors > self.contact_threshold) > 0:
                self.grasp_state = 'grasping'
                
        elif self.grasp_state == 'grasping':
            avg_torque = np.mean(np.abs(current_forces))
            
            if avg_torque < self.target_grip_force:
                self.current_grip_force = min(1.0, self.current_grip_force + self.adaptation_rate + recovery_adjustment)
                self.set_grip(self.current_grip_force)
            else:
                self.grasp_state = 'holding'
                
        elif self.grasp_state == 'holding':
            # Closed-loop force control
            force_error = self.target_grip_force - np.mean(np.abs(current_forces))
            self.force_error_integral += force_error * dt
            
            # PI control for grip adjustment
            adjustment = 0.01 * force_error + 0.001 * self.force_error_integral
            adjustment = np.clip(adjustment, -self.max_adjustment, self.max_adjustment)
            
            self.current_grip_force = min(1.0, max(0.2, self.current_grip_force + adjustment))
            self.set_grip(self.current_grip_force)
            
            # Apply slip recovery adjustment
            if recovery_adjustment > 0:
                self.current_grip_force = min(1.0, self.current_grip_force + recovery_adjustment)
                self.set_grip(self.current_grip_force)
            
        return {
            'state': self.grasp_state,
            'num_contacts': np.sum(touch_sensors > self.contact_threshold),
            'grip_force': self.current_grip_force,
            'slip_detected': slip_detected,
            'slip_magnitude': slip_magnitude,
            'slip_recovery_count': self.slip_recovery_count
        }

class TeleoperationController(DexterousHandController):
    def __init__(self, model, data):
        super().__init__(model, data)
        self.key_state = {}
        self.grip_value = 0.0
        self.grip_speed = 0.1
        self.move_speed = 0.05
        
    def update_key_state(self, key: str, pressed: bool):
        self.key_state[key] = pressed
        
    def update_key_states(self, key_states: dict):
        self.key_state = key_states.copy()
        
    def update(self):
        grip_delta = 0.0
        
        if ' ' in self.key_state and self.key_state[' ']:
            grip_delta = self.grip_speed
        elif 'shift' in self.key_state and self.key_state['shift']:
            grip_delta = -self.grip_speed
            
        self.grip_value = np.clip(self.grip_value + grip_delta, 0.0, 1.0)
        self.set_grip(self.grip_value)
        
        for finger in ['index', 'middle', 'ring', 'pinky']:
            idx_char = finger[0]
            if idx_char in self.key_state and self.key_state[idx_char]:
                indices = self.finger_indices[finger]
                for idx in indices[1:]:
                    self.data.ctrl[idx] = min(self.data.ctrl[idx] + 0.05, 1.8)
            elif idx_char.upper() in self.key_state and self.key_state[idx_char.upper()]:
                indices = self.finger_indices[finger]
                for idx in indices[1:]:
                    self.data.ctrl[idx] = max(self.data.ctrl[idx] - 0.05, 0.0)
        
        if 't' in self.key_state and self.key_state['t']:
            indices = self.finger_indices['thumb']
            self.data.ctrl[indices[1]] = min(self.data.ctrl[indices[1]] + 0.05, 1.5)
        if 'T' in self.key_state and self.key_state['T']:
            indices = self.finger_indices['thumb']
            self.data.ctrl[indices[1]] = max(self.data.ctrl[indices[1]] - 0.05, 0.0)
            
        return self.grip_value

class AutoGraspController(DexterousHandController):
    def __init__(self, model, data):
        super().__init__(model, data)
        self.phase = 0
        self.max_phases = 200
        self.trajectory_planner = TrajectoryPlanner()
        
    def update(self):
        self.phase = (self.phase + 1) % self.max_phases
        
        if self.phase < 50:
            self.open_hand()
        elif self.phase < 150:
            progress = (self.phase - 50) / 100
            self.set_grip(progress)
        else:
            self.close_hand()
            
        return self.phase / self.max_phases

class ForceControlController(DexterousHandController):
    def __init__(self, model, data):
        super().__init__(model, data)
        self.target_forces = np.ones(self.nu) * 5.0
        self.force_pids = [PIDController(10, 1, 2, -10, 10) for _ in range(self.nu)]
        self.force_sensor_indices = {}
        
    def set_target_force(self, finger_name: str, force: float):
        if finger_name in self.finger_indices:
            indices = self.finger_indices[finger_name]
            for idx in indices:
                self.target_forces[idx] = force
                
    def update(self, dt: float):
        current_forces = self.data.actuator_force
        
        for i in range(self.nu):
            error = self.target_forces[i] - current_forces[i]
            correction = self.force_pids[i].compute(error, dt)
            self.data.ctrl[i] = np.clip(self.data.ctrl[i] + correction, 0, 1.8)
            
        return current_forces

class ClosedLoopController(DexterousHandController):
    """Advanced closed-loop controller integrating vision, tactile, and force feedback."""
    def __init__(self, model, data):
        super().__init__(model, data)
        self.slip_detector = SlipDetector(slip_threshold=0.08, window_size=8)
        self.slip_recovery = SlipRecoveryController(recovery_strength=0.4, recovery_duration=0.004)
        
        # Vision integration weights
        self.vision_weight = 0.3
        self.tactile_weight = 0.5
        self.force_weight = 0.2
        
        # Target tracking
        self.target_position = None
        self.target_velocity = None
        
        # Control gains
        self.position_gain = 500.0
        self.velocity_gain = 50.0
        self.force_gain = 10.0
        
        # State tracking
        self.state = 'idle'
        self.slip_events = []
        self.total_recovery_time = 0.0
        
    def set_target(self, position: np.ndarray, velocity: Optional[np.ndarray] = None):
        """Set target position for visual servoing."""
        self.target_position = position.copy()
        self.target_velocity = velocity.copy() if velocity is not None else np.zeros_like(position)
        self.state = 'tracking'
        
    def update(self, sensor_data: np.ndarray, vision_data: Optional[Dict] = None, dt: float = 0.001):
        """Update closed-loop controller with multi-modal feedback."""
        # Extract sensor data
        joint_pos = self.get_joint_positions()
        joint_vel = self.get_joint_velocities()
        current_forces = self.data.actuator_force
        touch_sensors = sensor_data[-5:] if len(sensor_data) >= 5 else np.zeros(5)
        
        # Update slip detection
        slip_detected, slip_magnitude = self.slip_detector.update(current_forces, touch_sensors)
        
        # Handle slip recovery
        recovery_adjustment = 0.0
        if slip_detected and self.state == 'holding':
            self.slip_recovery.trigger_recovery(np.mean(self.data.ctrl))
            self.slip_events.append({'time': self.total_recovery_time, 'magnitude': slip_magnitude})
            
        if self.slip_recovery.recovering:
            recovery_adjustment = self.slip_recovery.update(dt)
            self.total_recovery_time += dt
        
        # Vision-based control
        control_signal = np.zeros(self.nu)
        if vision_data and self.target_position is not None:
            # Visual error
            visual_error = self.target_position - vision_data.get('end_effector_pos', joint_pos[:3])
            control_signal[:3] += self.vision_weight * self.position_gain * visual_error
            
        # Tactile-based control
        contact_points = np.where(touch_sensors > self.slip_detector.slip_threshold)[0]
        if len(contact_points) > 0:
            avg_touch = np.mean(touch_sensors[contact_points])
            tactile_adjustment = (avg_touch - 0.5) * self.tactile_weight * 10
            control_signal[:] += tactile_adjustment
            
        # Force-based control
        force_error = self.force_weight * (5.0 - np.mean(np.abs(current_forces)))
        control_signal[:] += self.force_gain * force_error
        
        # Slip recovery adjustment
        control_signal[:] += recovery_adjustment * 100
        
        # Apply control
        self.data.ctrl[:] = np.clip(self.data.ctrl + control_signal * dt, -1.5, 1.5)
        
        # Update state
        if self.state == 'tracking':
            if self.target_position is not None:
                error_norm = np.linalg.norm(joint_pos[:3] - self.target_position)
                if error_norm < 0.05:
                    self.state = 'holding'
        
        return {
            'state': self.state,
            'slip_detected': slip_detected,
            'slip_magnitude': slip_magnitude,
            'recovery_adjustment': recovery_adjustment,
            'num_slip_events': len(self.slip_events),
            'total_recovery_time': self.total_recovery_time
        }
