import os
import json
import numpy as np
from typing import Dict, Any

def load_config(config_path: str) -> Dict[str, Any]:
    with open(config_path, 'r') as f:
        return json.load(f)

def save_config(config: Dict[str, Any], config_path: str):
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def quat_to_euler(quat: np.ndarray) -> np.ndarray:
    w, x, y, z = quat
    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + y * y)
    roll = np.arctan2(t0, t1)
    
    t2 = +2.0 * (w * y - z * x)
    t2 = np.clip(t2, -1.0, 1.0)
    pitch = np.arcsin(t2)
    
    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    yaw = np.arctan2(t3, t4)
    
    return np.array([roll, pitch, yaw])

def euler_to_quat(euler: np.ndarray) -> np.ndarray:
    roll, pitch, yaw = euler
    cy = np.cos(yaw * 0.5)
    sy = np.sin(yaw * 0.5)
    cp = np.cos(pitch * 0.5)
    sp = np.sin(pitch * 0.5)
    cr = np.cos(roll * 0.5)
    sr = np.sin(roll * 0.5)
    
    w = cr * cp * cy + sr * sp * sy
    x = sr * cp * cy - cr * sp * sy
    y = cr * sp * cy + sr * cp * sy
    z = cr * cp * sy - sr * sp * cy
    
    return np.array([w, x, y, z])

def normalize_angle(angle: float) -> float:
    return np.mod(angle + np.pi, 2 * np.pi) - np.pi

def compute_distance(pos1: np.ndarray, pos2: np.ndarray) -> float:
    return np.linalg.norm(pos1 - pos2)

def sample_sphere(radius: float = 1.0) -> np.ndarray:
    theta = np.random.uniform(0, 2 * np.pi)
    phi = np.arccos(2 * np.random.uniform(0, 1) - 1)
    return np.array([
        radius * np.sin(phi) * np.cos(theta),
        radius * np.sin(phi) * np.sin(theta),
        radius * np.cos(phi)
    ])

def sample_cube(min_val: float = -1.0, max_val: float = 1.0) -> np.ndarray:
    return np.random.uniform(min_val, max_val, 3)

def generate_random_pose(workspace_center: np.ndarray = np.zeros(3), 
                        workspace_radius: float = 0.5) -> np.ndarray:
    position = workspace_center + sample_sphere(workspace_radius)
    orientation = euler_to_quat(sample_cube(-np.pi, np.pi))
    return np.concatenate([position, orientation])

def print_stats(data: Dict[str, np.ndarray], prefix: str = ""):
    for key, value in data.items():
        if isinstance(value, np.ndarray):
            print(f"{prefix}{key}: shape={value.shape}, mean={np.mean(value):.3f}, std={np.std(value):.3f}")

def interpolate(a: float, b: float, t: float) -> float:
    return a + (b - a) * t

def clamp(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(value, max_val))