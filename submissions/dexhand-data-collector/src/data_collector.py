import os
import h5py
import json
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

class DataCollector:
    def __init__(self, output_dir: str = "data"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.data: Dict[str, List[np.ndarray]] = {}
        self.metadata: Dict[str, Any] = {}
        self.timestamps: List[float] = []
        self.sequence_count = 0
        
    def init_data_structure(self, keys: List[str]):
        for key in keys:
            self.data[key] = []
            
    def add_metadata(self, key: str, value: Any):
        self.metadata[key] = value
        
    def record(self, data_dict: Dict[str, np.ndarray], timestamp: float):
        for key, value in data_dict.items():
            if key not in self.data:
                self.data[key] = []
            self.data[key].append(np.asarray(value))
        self.timestamps.append(timestamp)
        
    def save(self, filename: str = None) -> str:
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_{timestamp}.h5"
        
        filepath = os.path.join(self.output_dir, filename)
        
        with h5py.File(filepath, 'w') as f:
            for key, values in self.data.items():
                if len(values) > 0:
                    f.create_dataset(key, data=np.array(values), compression='gzip')
            
            f.create_dataset('timestamps', data=np.array(self.timestamps))
            
            metadata_str = json.dumps(self.metadata)
            f.attrs['metadata'] = metadata_str
        
        print(f"Data saved to {filepath}")
        return filepath
    
    def get_statistics(self) -> Dict[str, Any]:
        stats = {
            'num_samples': len(self.timestamps),
            'duration': self.timestamps[-1] - self.timestamps[0] if self.timestamps else 0,
            'channels': list(self.data.keys())
        }
        
        for key, values in self.data.items():
            if len(values) > 0:
                arr = np.array(values)
                stats[f'{key}_shape'] = arr.shape
                stats[f'{key}_mean'] = float(np.mean(arr))
                stats[f'{key}_std'] = float(np.std(arr))
        
        return stats
    
    def clear(self):
        self.data = {}
        self.metadata = {}
        self.timestamps = []

class DataAugmenter:
    @staticmethod
    def add_gaussian_noise(data: np.ndarray, mean: float = 0.0, std: float = 0.01) -> np.ndarray:
        noise = np.random.normal(mean, std, data.shape)
        return data + noise
    
    @staticmethod
    def time_warp(data: np.ndarray, factor_range: Tuple[float, float] = (0.8, 1.2)) -> np.ndarray:
        factor = np.random.uniform(*factor_range)
        num_samples = int(len(data) * factor)
        if num_samples == len(data):
            return data
        indices = np.linspace(0, len(data) - 1, num_samples).astype(int)
        return data[indices]
    
    @staticmethod
    def amplitude_scale(data: np.ndarray, factor_range: Tuple[float, float] = (0.9, 1.1)) -> np.ndarray:
        factor = np.random.uniform(*factor_range)
        return data * factor
    
    @staticmethod
    def time_shift(data: np.ndarray, max_shift: int = 10) -> np.ndarray:
        shift = np.random.randint(-max_shift, max_shift)
        if shift == 0:
            return data
        return np.roll(data, shift, axis=0)
    
    @staticmethod
    def augment(data: np.ndarray, augmentations: List[str] = None) -> np.ndarray:
        if augmentations is None:
            augmentations = ['noise', 'scale']
        
        augmented = data.copy()
        
        if 'noise' in augmentations:
            augmented = DataAugmenter.add_gaussian_noise(augmented)
        if 'warp' in augmentations:
            augmented = DataAugmenter.time_warp(augmented)
        if 'scale' in augmentations:
            augmented = DataAugmenter.amplitude_scale(augmented)
        if 'shift' in augmentations:
            augmented = DataAugmenter.time_shift(augmented)
        
        return augmented

class MujocoDataCollector(DataCollector):
    def __init__(self, output_dir: str = "data"):
        super().__init__(output_dir)
        self.sensor_names = []
        self.joint_names = []
        self.actuator_names = []
        self.augmenter = DataAugmenter()
        self.enable_augmentation = False
        self.augmentation_types = ['noise', 'scale']
        
    def setup_from_model(self, model, data):
        self.sensor_names = [model.sensor(i).name for i in range(model.nsensor)]
        self.joint_names = [model.joint(i).name for i in range(model.njoint)]
        self.actuator_names = [model.actuator(i).name for i in range(model.nu)]
        
        self.init_data_structure([
            'joint_positions',
            'joint_velocities',
            'joint_torques',
            'sensor_data',
            'actuator_forces',
            'actuator_targets',
            'body_positions',
            'body_quaternions',
            'body_velocities',
            'contact_info',
            'system_energy',
            'control_signals'
        ])
        
        self.add_metadata('sensor_names', self.sensor_names)
        self.add_metadata('joint_names', self.joint_names)
        self.add_metadata('actuator_names', self.actuator_names)
        self.add_metadata('num_sensors', model.nsensor)
        self.add_metadata('num_joints', model.njoint)
        self.add_metadata('num_actuators', model.nu)
        self.add_metadata('timestep', float(model.opt.timestep))
        self.add_metadata('augmentation_enabled', self.enable_augmentation)
        self.add_metadata('augmentation_types', self.augmentation_types)
    
    def set_augmentation(self, enable: bool, types: List[str] = None):
        self.enable_augmentation = enable
        if types is not None:
            self.augmentation_types = types
        self.add_metadata('augmentation_enabled', enable)
        self.add_metadata('augmentation_types', self.augmentation_types)
    
    def collect(self, model, data, timestamp: float):
        data_dict = {}
        
        data_dict['joint_positions'] = np.copy(data.qpos)
        data_dict['joint_velocities'] = np.copy(data.qvel)
        data_dict['joint_torques'] = np.copy(data.qfrc_actuator)
        data_dict['sensor_data'] = np.copy(data.sensordata)
        data_dict['actuator_forces'] = np.copy(data.actuator_force)
        data_dict['actuator_targets'] = np.copy(data.ctrl)
        data_dict['control_signals'] = np.copy(data.ctrl)
        
        body_positions = []
        body_quaternions = []
        body_velocities = []
        for i in range(model.nbody):
            body_positions.append(np.copy(data.xpos[i]))
            body_quaternions.append(np.copy(data.xquat[i]))
            body_velocities.append(np.copy(data.cvel[i]))
        data_dict['body_positions'] = np.array(body_positions)
        data_dict['body_quaternions'] = np.array(body_quaternions)
        data_dict['body_velocities'] = np.array(body_velocities)
        
        contact_info = []
        for i in range(data.ncon):
            con = data.contact[i]
            info = [
                con.geom1, con.geom2,
                con.pos[0], con.pos[1], con.pos[2],
                con.frame[0], con.frame[1], con.frame[2],
                con.dist, con.eforce[0], con.eforce[1], con.eforce[2],
                con.eforce[3], con.eforce[4], con.eforce[5]
            ]
            contact_info.append(info)
        data_dict['contact_info'] = np.array(contact_info) if contact_info else np.zeros((0, 15))
        
        data_dict['system_energy'] = np.array([data.energy[0], data.energy[1]])
        
        if self.enable_augmentation:
            for key in ['sensor_data', 'joint_velocities', 'joint_torques']:
                data_dict[key] = self.augmenter.augment(data_dict[key], self.augmentation_types)
        
        self.record(data_dict, timestamp)
    
    def save_sequence(self, task_name: str, sequence_id: int = None) -> str:
        if sequence_id is None:
            sequence_id = self.sequence_count
            self.sequence_count += 1
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{task_name}_seq_{sequence_id:04d}_{timestamp}.h5"
        
        self.add_metadata('task_name', task_name)
        self.add_metadata('sequence_id', sequence_id)
        
        return self.save(filename)

class MultiTaskDataCollector(MujocoDataCollector):
    def __init__(self, output_dir: str = "data"):
        super().__init__(output_dir)
        self.current_task = None
        self.task_configs = {}
        
    def add_task_config(self, task_name: str, config: Dict[str, Any]):
        self.task_configs[task_name] = config
        
    def set_task(self, task_name: str):
        self.current_task = task_name
        self.add_metadata('current_task', task_name)
        if task_name in self.task_configs:
            self.add_metadata('task_config', self.task_configs[task_name])
        
    def collect_with_task(self, model, data, timestamp: float, task_info: Dict[str, Any] = None):
        self.collect(model, data, timestamp)
        
        if task_info:
            for key, value in task_info.items():
                if key not in self.data:
                    self.data[key] = []
                self.data[key].append(np.array([value]))