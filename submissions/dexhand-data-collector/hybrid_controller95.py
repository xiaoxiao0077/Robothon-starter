"""Hybrid Controller 95+ - Advanced Control Architecture"""

import numpy as np
from enum import Enum
import time


# =========================
# MODE DEFINITION
# =========================
class ControlMode(Enum):
    SAFE = 0
    PERFORMANCE = 1
    RECOVERY = 2


# =========================
# MAIN CONTROLLER
# =========================
class HybridController95:

    def __init__(self):
        # base gains
        self.kp_base = 1.0
        self.kd_base = 0.2

        # state memory
        self.prev_error = 0.0
        self.prev_action = 0.0
        self.prev_acc = 0.0

        self.mode = ControlMode.SAFE

        # smoothing
        self.alpha = 0.75  # position smoothing
        self.smoothed_error = 0.0

        # jerk limit
        self.j_max = 0.05

        # confidence
        self.confidence = 1.0

        # oscillation detector
        self.osc_window = []

    # =========================
    # PUBLIC API
    # =========================
    def step(self, observation):
        """
        observation = {
            'error': float,
            'tracking_score': float,
            'velocity': float,
            'lost_flag': bool
        }
        """

        error = observation['error']
        tracking = observation['tracking_score']
        lost = observation['lost_flag']

        # 1. state estimation
        self.confidence = self._compute_confidence(error, tracking, lost)

        # 2. mode selection (FSM)
        self.mode = self._select_mode(self.confidence, lost)

        # 3. smooth error
        self.smoothed_error = self._smooth(error)

        # 4. adaptive control
        action = self._control(self.smoothed_error)

        # 5. safety constraint (jerk limit)
        action = self._apply_jerk_limit(action)

        # 6. store state
        self.prev_error = error
        self.prev_action = action

        return action, self.mode, self.confidence

    # =========================
    # CONFIDENCE MODEL
    # =========================
    def _compute_confidence(self, error, tracking, lost):

        if lost:
            return 0.0

        stability = np.exp(-abs(error))  # error越小越稳定
        confidence = 0.6 * tracking + 0.4 * stability

        # oscillation penalty
        self.osc_window.append(error)
        if len(self.osc_window) > 5:
            self.osc_window.pop(0)

        if len(self.osc_window) == 5:
            osc = np.std(self.osc_window)
            confidence -= min(0.3, osc)

        return np.clip(confidence, 0.0, 1.0)

    # =========================
    # FSM MODE SELECTOR
    # =========================
    def _select_mode(self, confidence, lost):

        if lost or confidence < 0.4:
            return ControlMode.RECOVERY

        if confidence < 0.75:
            return ControlMode.SAFE

        return ControlMode.PERFORMANCE

    # =========================
    # SMOOTHING
    # =========================
    def _smooth(self, error):
        return self.alpha * self.smoothed_error + (1 - self.alpha) * error

    # =========================
    # CONTROL CORE
    # =========================
    def _control(self, error):

        kp, kd = self._adaptive_gains()

        derivative = error - self.prev_error

        # PD control
        action = kp * error + kd * derivative

        # recovery override
        if self.mode == ControlMode.RECOVERY:
            action = self._recovery_action()

        return action

    # =========================
    # ADAPTIVE GAINS
    # =========================
    def _adaptive_gains(self):

        speed_factor = min(1.0, abs(self.prev_action))

        kp = self.kp_base * (1.0 + 0.8 * speed_factor)
        kd = self.kd_base * (1.0 + 1.2 * speed_factor)

        if self.mode == ControlMode.SAFE:
            kp *= 0.7
            kd *= 1.3

        if self.mode == ControlMode.RECOVERY:
            kp *= 0.4
            kd *= 2.0

        return kp, kd

    # =========================
    # RECOVERY POLICY
    # =========================
    def _recovery_action(self):
        # slow search oscillation
        return 0.2 * np.sin(time.time() * 2.0)

    # =========================
    # JERK LIMITER
    # =========================
    def _apply_jerk_limit(self, action):

        acc = action - self.prev_action
        acc = np.clip(acc,
                      -self.j_max,
                      self.j_max)

        return self.prev_action + acc


# =========================
# MULTI-FINGER EXTENSION
# =========================
class MultiFingerHybridController:
    """Hybrid controller for multi-finger dexterous hand"""
    
    def __init__(self, num_fingers=5):
        self.controllers = [HybridController95() for _ in range(num_fingers)]
        self.num_fingers = num_fingers
        
    def step(self, observations):
        """
        observations: list of observation dicts for each finger
        """
        actions = []
        modes = []
        confidences = []
        
        for i in range(self.num_fingers):
            action, mode, conf = self.controllers[i].step(observations[i])
            actions.append(action)
            modes.append(mode)
            confidences.append(conf)
        
        # Coordination: adjust based on average confidence
        avg_conf = np.mean(confidences)
        if avg_conf < 0.5:
            actions = [a * 0.5 for a in actions]
        
        return actions, modes, confidences


# =========================
# WRIST CONTROLLER
# =========================
class WristHybridController(HybridController95):
    """Specialized hybrid controller for wrist reorientation"""
    
    def __init__(self):
        super().__init__()
        self.kp_base = 100.0
        self.kd_base = 20.0
        self.j_max = 2.0  # higher jerk limit for wrist
        self.target_angle = 0.0
    
    def set_target(self, angle):
        self.target_angle = angle
    
    def step(self, current_angle):
        error = self.target_angle - current_angle
        observation = {
            'error': error,
            'tracking_score': np.exp(-abs(error) * 0.1),
            'velocity': 0.0,
            'lost_flag': abs(error) > 45.0  # lost if >45 degrees
        }
        return super().step(observation)


# =========================
# FORCE CONTROL EXTENSION
# =========================
class ForceHybridController(HybridController95):
    """Hybrid controller with force feedback"""
    
    def __init__(self):
        super().__init__()
        self.kp_base = 0.5
        self.kd_base = 0.1
        self.target_force = 5.0
        self.crush_limit = 6.0
        self.force_error_integral = 0.0
    
    def set_target_force(self, force):
        self.target_force = force
    
    def step(self, current_force):
        error = self.target_force - current_force
        
        # Anti-windup
        self.force_error_integral += error * 0.01
        self.force_error_integral = np.clip(self.force_error_integral, -1.0, 1.0)
        
        # Tracking score based on force error
        tracking_score = np.exp(-abs(error))
        
        # Lost flag if crush limit exceeded
        lost = current_force >= self.crush_limit
        
        observation = {
            'error': error,
            'tracking_score': tracking_score,
            'velocity': 0.0,
            'lost_flag': lost
        }
        
        action, mode, conf = super().step(observation)
        
        # Crush protection override
        if current_force >= self.crush_limit:
            action = -0.5  # Release grip immediately
        
        return action, mode, conf, self.force_error_integral