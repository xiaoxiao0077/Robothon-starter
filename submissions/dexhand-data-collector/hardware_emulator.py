"""
Hardware Emulator Module
Simulates real-world hardware characteristics including:
- Communication delay
- Sensor noise
- Motor saturation
- Dead zones
- Temperature drift

This module helps bridge the sim-to-real gap by adding realistic hardware characteristics.
"""

import numpy as np
from typing import Dict, Tuple, Optional
import time

class HardwareEmulator:
    """
    Simulates real DexterousHand hardware characteristics.
    """
    
    def __init__(
        self,
        sensor_noise_std: float = 0.01,
        communication_delay: float = 0.005,  # 5ms delay
        motor_saturation: float = 1.5,
        dead_zone: float = 0.02,
        temperature_drift: float = 0.001,
        quantization_bits: int = 12,
        motor_time_constant: float = 0.01,
        sensor_bias: float = 0.001,
        friction_compensation: float = 0.05
    ):
        # Sensor characteristics
        self.sensor_noise_std = sensor_noise_std
        self.quantization_bits = quantization_bits
        self.quantization_step = 2 * np.pi / (2 ** quantization_bits)
        self.sensor_bias = sensor_bias
        self.bias_drift = 0.0
        
        # Communication characteristics
        self.communication_delay = communication_delay
        self.delayed_sensor_buffer = []
        self.buffer_size = 10
        
        # Motor characteristics
        self.motor_saturation = motor_saturation
        self.dead_zone = dead_zone
        self.motor_time_constant = motor_time_constant
        self.motor_state = np.zeros(19)  # Motor velocity state
        
        # Environmental characteristics
        self.temperature_drift = temperature_drift
        self.temperature = 25.0  # Room temperature in Celsius
        self.friction_compensation = friction_compensation
        
        # State tracking
        self.step_count = 0
        self.last_update_time = time.time()
        
        # Calibration parameters
        self.sensor_offsets = np.zeros(19)
        self.motor_gains = np.ones(19) * 0.95  # 5% gain error typical
        
    def calibrate(self, calibration_data: np.ndarray):
        """
        Perform hardware calibration using reference measurements.
        """
        self.sensor_offsets = np.mean(calibration_data, axis=0)
        return self
        
    def apply_dead_zone(self, command: np.ndarray) -> np.ndarray:
        """
        Apply motor dead zone to command signals.
        """
        result = np.sign(command) * np.maximum(
            np.abs(command) - self.dead_zone, 
            0
        )
        return result
        
    def apply_motor_dynamics(
        self, 
        command: np.ndarray, 
        dt: float
    ) -> np.ndarray:
        """
        Apply first-order motor dynamics with saturation.
        """
        # Saturate command
        saturated = np.clip(command, -self.motor_saturation, self.motor_saturation)
        
        # First-order dynamics
        alpha = dt / self.motor_time_constant
        self.motor_state = (1 - alpha) * self.motor_state + alpha * saturated
        
        return self.motor_state
        
    def add_sensor_noise(self, sensor_data: np.ndarray) -> np.ndarray:
        """
        Add realistic sensor noise based on hardware specifications.
        """
        # Gaussian noise
        noise = np.random.normal(0, self.sensor_noise_std, len(sensor_data))
        
        # Quantization noise
        quantized = np.round(sensor_data / self.quantization_step) * self.quantization_step
        quant_noise = quantized - sensor_data
        
        # Temperature-dependent drift
        temp_drift = self.bias_drift * (self.temperature - 25.0)
        
        # Apply all effects
        noisy_data = sensor_data + noise + quant_noise + self.sensor_bias + temp_drift
        
        return noisy_data
        
    def add_communication_delay(self, sensor_data: np.ndarray) -> np.ndarray:
        """
        Simulate communication delay by buffering sensor data.
        """
        self.delayed_sensor_buffer.append(sensor_data.copy())
        
        # Keep buffer at correct size
        while len(self.delayed_sensor_buffer) > self.buffer_size:
            self.delayed_sensor_buffer.pop(0)
            
        # Return oldest data (delayed by buffer_size steps)
        if len(self.delayed_sensor_buffer) >= self.buffer_size:
            return self.delayed_sensor_buffer[0]
        else:
            return sensor_data
            
    def apply_friction_compensation(
        self, 
        velocity: np.ndarray, 
        friction_model: str = "coulomb"
    ) -> np.ndarray:
        """
        Apply friction compensation to velocity commands.
        
        Args:
            velocity: Joint velocities
            friction_model: 'coulomb', 'viscous', or 'combined'
        """
        if friction_model == "coulomb":
            friction_torque = np.sign(velocity) * self.friction_compensation
        elif friction_model == "viscous":
            friction_torque = velocity * self.friction_compensation
        else:  # combined
            friction_torque = (
                np.sign(velocity) * self.friction_compensation + 
                velocity * self.friction_compensation * 0.5
            )
            
        return friction_torque
        
    def update_temperature(self, power_consumption: float, dt: float):
        """
        Update temperature based on power consumption (simplified thermal model).
        """
        # Heating from power consumption
        heat_generation = power_consumption * 0.1  # Simplified
        
        # Cooling (natural convection)
        cooling = (self.temperature - 25.0) * 0.01  # Thermal resistance
        
        self.temperature += (heat_generation - cooling) * dt
        self.temperature = np.clip(self.temperature, 20.0, 80.0)  # Operating range
        
        # Update bias drift based on temperature
        self.bias_drift = self.temperature_drift * (self.temperature - 25.0)
        
    def simulate_wear(
        self, 
        cumulative_usage_hours: float
    ) -> Dict[str, float]:
        """
        Simulate hardware degradation over time.
        
        Args:
            cumulative_usage_hours: Total hours of operation
            
        Returns:
            Dictionary of degradation factors
        """
        # Exponential wear model
        wear_factor = np.exp(-cumulative_usage_hours / 10000)  # 10000 hour MTBF
        
        degradation = {
            "motor_efficiency": 0.9 + 0.1 * wear_factor,
            "sensor_accuracy": 0.95 + 0.05 * wear_factor,
            "backlash": 0.02 + 0.03 * (1 - wear_factor),
            "friction_coefficient": 0.05 + 0.05 * (1 - wear_factor)
        }
        
        return degradation
        
    def process_sensor_data(
        self, 
        raw_data: np.ndarray, 
        timestamp: float
    ) -> np.ndarray:
        """
        Complete sensor data processing pipeline.
        
        Args:
            raw_data: Raw sensor readings from simulation
            timestamp: Current simulation timestamp
            
        Returns:
            Processed sensor data with hardware effects
        """
        # Apply sensor offsets (calibration)
        calibrated = raw_data + self.sensor_offsets
        
        # Apply gain errors
        calibrated *= self.motor_gains
        
        # Add sensor noise and quantization
        processed = self.add_sensor_noise(calibrated)
        
        # Apply communication delay
        delayed = self.add_communication_delay(processed)
        
        self.step_count += 1
        
        return delayed
        
    def process_motor_command(
        self, 
        command: np.ndarray, 
        current_velocity: np.ndarray,
        dt: float
    ) -> np.ndarray:
        """
        Complete motor command processing pipeline.
        
        Args:
            command: Desired motor commands
            current_velocity: Current joint velocities
            dt: Time step
            
        Returns:
            Processed motor commands with hardware effects
        """
        # Apply dead zone
        with_deadzone = self.apply_dead_zone(command)
        
        # Apply friction compensation
        friction_comp = self.apply_friction_compensation(current_velocity)
        compensated = with_deadzone - friction_comp
        
        # Apply motor dynamics
        processed = self.apply_motor_dynamics(compensated, dt)
        
        # Update temperature based on power
        power = np.sum(np.abs(processed))
        self.update_temperature(power, dt)
        
        return processed
        
    def get_characteristics_report(self) -> Dict:
        """
        Generate a report of current hardware characteristics.
        """
        return {
            "sensor_noise_std": self.sensor_noise_std,
            "communication_delay_ms": self.communication_delay * 1000,
            "motor_saturation": self.motor_saturation,
            "dead_zone": self.dead_zone,
            "current_temperature_C": self.temperature,
            "quantization_resolution_deg": np.degrees(self.quantization_step),
            "step_count": self.step_count,
            "buffer_fill_level": len(self.delayed_sensor_buffer) / self.buffer_size
        }
        
    def reset(self):
        """
        Reset hardware emulator state.
        """
        self.step_count = 0
        self.delayed_sensor_buffer = []
        self.motor_state = np.zeros(19)
        self.temperature = 25.0
        self.bias_drift = 0.0


class SimToRealBridge:
    """
    Bridge between simulation and real hardware.
    Implements domain randomization and adaptation techniques.
    """
    
    def __init__(self, emulator: HardwareEmulator):
        self.emulator = emulator
        self.domain_randomization = True
        self.adaptation_enabled = True
        
        # Randomization parameters
        self.randomization_ranges = {
            "mass_range": (0.9, 1.1),
            "friction_range": (0.5, 1.5),
            "delay_range": (0.003, 0.01),
            "noise_range": (0.005, 0.02)
        }
        
        # Adaptation state
        self.error_history = []
        self.performance_baseline = None
        
    def randomize_parameters(self):
        """
        Apply domain randomization to simulation parameters.
        """
        randomization = {
            "mass_scale": np.random.uniform(*self.randomization_ranges["mass_range"]),
            "friction_scale": np.random.uniform(*self.randomization_ranges["friction_range"]),
            "delay_scale": np.random.uniform(*self.randomization_ranges["delay_range"]),
            "noise_scale": np.random.uniform(*self.randomization_ranges["noise_range"])
        }
        return randomization
        
    def adapt_to_real(
        self, 
        sim_state: np.ndarray, 
        real_state: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Adapt simulation to match real hardware behavior.
        
        Args:
            sim_state: Simulation state
            real_state: Real hardware state (if available)
            
        Returns:
            Adapted state estimate
        """
        # Process through hardware emulator
        adapted = self.emulator.process_sensor_data(sim_state, time.time())
        
        if real_state is not None and self.adaptation_enabled:
            # Calculate adaptation error
            error = real_state - adapted
            self.error_history.append(error)
            
            # Simple adaptive correction
            if len(self.error_history) > 100:
                mean_error = np.mean(self.error_history[-100:], axis=0)
                adapted += 0.1 * mean_error  # Gradual correction
                
        return adapted
        
    def get_domain_randomization_config(self) -> Dict:
        """
        Get current domain randomization configuration.
        """
        return {
            "enabled": self.domain_randomization,
            "ranges": self.randomization_ranges
        }


def create_hardware_emulator(config: Optional[Dict] = None) -> HardwareEmulator:
    """
    Factory function to create hardware emulator with configuration.
    """
    if config is None:
        config = {}
        
    return HardwareEmulator(
        sensor_noise_std=config.get("sensor_noise_std", 0.01),
        communication_delay=config.get("communication_delay", 0.005),
        motor_saturation=config.get("motor_saturation", 1.5),
        dead_zone=config.get("dead_zone", 0.02),
        temperature_drift=config.get("temperature_drift", 0.001),
        quantization_bits=config.get("quantization_bits", 12),
        motor_time_constant=config.get("motor_time_constant", 0.01),
        sensor_bias=config.get("sensor_bias", 0.001),
        friction_compensation=config.get("friction_compensation", 0.05)
    )


if __name__ == "__main__":
    # Test hardware emulator
    emulator = create_hardware_emulator()
    
    # Simulate 100 steps
    for i in range(100):
        # Simulate sensor data
        raw_sensor = np.random.randn(19) * 0.5
        
        # Process through emulator
        processed = emulator.process_sensor_data(raw_sensor, time.time())
        
        # Simulate motor command
        motor_cmd = np.sin(i * 0.1) * np.ones(19)
        velocity = np.random.randn(19) * 0.1
        
        processed_cmd = emulator.process_motor_command(motor_cmd, velocity, 0.001)
        
    # Print characteristics
    print("Hardware Emulator Characteristics:")
    report = emulator.get_characteristics_report()
    for key, value in report.items():
        print(f"  {key}: {value}")
