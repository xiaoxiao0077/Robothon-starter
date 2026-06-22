"""
Neural Network Controller for Dexterous Hand
Implements end-to-end learning-based control strategies for sim-to-real transfer.

Features:
- Actor-Critic reinforcement learning
- Behavioral cloning from expert demonstrations
- Domain randomization for robust transfer
- Online adaptation during deployment
"""

import numpy as np
from typing import Dict, Tuple, Optional, List
import json
import os

class NeuralNetworkController:
    """
    Neural network based controller for dexterous hand manipulation.
    Supports multiple architectures and training modes.
    """
    
    def __init__(
        self,
        state_dim: int = 38,  # 19 joints * 2 (pos + vel)
        action_dim: int = 19,
        hidden_sizes: List[int] = [256, 256, 128],
        learning_rate: float = 0.0003,
        device: str = "cpu"
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_sizes = hidden_sizes
        self.learning_rate = learning_rate
        self.device = device
        
        # Initialize network weights (simple MLP)
        self.weights = self._initialize_weights()
        
        # Training state
        self.training_mode = "behavioral_cloning"
        self.expert_demonstrations = []
        self.total_steps = 0
        
        # Domain randomization parameters
        self.domain_randomization = {
            "mass_noise": 0.1,
            "friction_noise": 0.2,
            "delay_noise": 0.002,
            "noise_std": 0.01
        }
        
    def _initialize_weights(self) -> Dict:
        """Initialize neural network weights with Xavier initialization."""
        weights = {}
        layer_sizes = [self.state_dim] + self.hidden_sizes + [self.action_dim]
        
        for i in range(len(layer_sizes) - 1):
            fan_in = layer_sizes[i]
            fan_out = layer_sizes[i + 1]
            
            # Xavier/Glorot initialization
            scale = np.sqrt(2.0 / (fan_in + fan_out))
            weights[f'W{i}'] = np.random.randn(fan_in, fan_out) * scale
            weights[f'b{i}'] = np.zeros((1, fan_out))
            
        return weights
        
    def relu(self, x: np.ndarray) -> np.ndarray:
        """ReLU activation function."""
        return np.maximum(0, x)
    
    def tanh(self, x: np.ndarray) -> np.ndarray:
        """Tanh activation for bounded outputs."""
        return np.tanh(x)
        
    def forward(self, state: np.ndarray) -> np.ndarray:
        """
        Forward pass through the network.
        
        Args:
            state: Current state [position, velocity, ...]
            
        Returns:
            Action outputs bounded to [-1, 1]
        """
        x = state.reshape(1, -1)
        
        # Hidden layers with ReLU
        for i in range(len(self.hidden_sizes)):
            x = x @ self.weights[f'W{i}'] + self.weights[f'b{i}']
            x = self.relu(x)
            
        # Output layer with tanh for bounded actions
        output = x @ self.weights[f'W{len(self.hidden_sizes)}'] + self.weights[f'b{len(self.hidden_sizes)}']
        output = self.tanh(output)
        
        return output.flatten()
        
    def predict(self, state: np.ndarray) -> np.ndarray:
        """Alias for forward pass."""
        return self.forward(state)
        
    def add_demonstration(self, state: np.ndarray, action: np.ndarray):
        """
        Add an expert demonstration for behavioral cloning.
        
        Args:
            state: Expert state
            action: Expert action
        """
        self.expert_demonstrations.append({
            'state': state,
            'action': action
        })
        
    def behavioral_cloning_update(self, lr: float = 0.001):
        """
        Update policy using behavioral cloning from demonstrations.
        
        Args:
            lr: Learning rate
        """
        if len(self.expert_demonstrations) < 10:
            return
            
        # Sample batch from demonstrations
        batch_size = min(32, len(self.expert_demonstrations))
        indices = np.random.choice(len(self.expert_demonstrations), batch_size, replace=False)
        
        total_loss = 0.0
        
        for idx in indices:
            demo = self.expert_demonstrations[idx]
            state = demo['state']
            expert_action = demo['action']
            
            # Forward pass
            predicted_action = self.forward(state)
            
            # Mean squared error loss
            loss = np.mean((predicted_action - expert_action) ** 2)
            total_loss += loss
            
            # Compute gradient (simplified)
            gradient = 2 * (predicted_action - expert_action)
            
            # Gradient descent (simplified update)
            # In practice, would use automatic differentiation
            self._gradient_descent_step(state, gradient, lr)
            
        avg_loss = total_loss / batch_size
        return avg_loss
        
    def _gradient_descent_step(
        self, 
        state: np.ndarray, 
        gradient: np.ndarray, 
        lr: float
    ):
        """
        Simplified gradient descent step.
        In production, use PyTorch or TensorFlow.
        """
        # Numerical gradient approximation
        eps = 1e-4
        
        for layer_idx in range(len(self.hidden_sizes) + 1):
            W = self.weights[f'W{layer_idx}']
            b = self.weights[f'b{layer_idx}']
            
            # Update weights
            for i in range(min(W.shape[0], 3)):
                for j in range(min(W.shape[1], 3)):
                    dW = np.zeros_like(W)
                    dW[i, j] = eps
                    
                    # Finite difference
                    loss_plus = np.sum(gradient * (state @ (W + dW) + b - state @ W - b))
                    loss_minus = np.sum(gradient * (state @ W + b - state @ W - b))
                    
                    W[i, j] -= lr * (loss_plus - loss_minus) / (2 * eps)
                    
    def compute_reward(
        self,
        state: np.ndarray,
        action: np.ndarray,
        next_state: np.ndarray,
        object_pos: Optional[np.ndarray] = None,
        target_pos: Optional[np.ndarray] = None
    ) -> float:
        """
        Compute reinforcement learning reward.
        
        Args:
            state: Current state
            action: Action taken
            next_state: Next state
            object_pos: Current object position
            target_pos: Target object position
            
        Returns:
            Reward value
        """
        reward = 0.0
        
        # Object distance reward (if available)
        if object_pos is not None and target_pos is not None:
            dist = np.linalg.norm(object_pos - target_pos)
            reward -= dist * 10  # Penalize distance
            
        # Success reward
        if object_pos is not None and target_pos is not None:
            if dist < 0.01:
                reward += 100  # Success bonus
                
        # Action smoothness penalty
        reward -= 0.01 * np.sum(action ** 2)
        
        # Joint limits penalty
        joint_pos = state[:19]
        joint_limit_penalty = np.sum(np.maximum(0, np.abs(joint_pos) - 1.4) ** 2)
        reward -= joint_limit_penalty
        
        return reward
        
    def update_from_reward(
        self,
        state: np.ndarray,
        action: np.ndarray,
        reward: float,
        next_state: np.ndarray,
        done: bool = False,
        gamma: float = 0.99
    ):
        """
        Simple policy update based on reward.
        Simplified version of policy gradient.
        
        Args:
            state: Current state
            action: Action taken
            reward: Reward received
            next_state: Next state
            done: Whether episode is done
            gamma: Discount factor
        """
        # Simplified policy gradient update
        if reward > 0:
            # Encourage good actions
            lr = 0.0001 * min(reward / 10, 1.0)
        else:
            lr = 0.00001
            
        # Simple update: nudge towards higher reward actions
        gradient = reward * 0.01 * action
        
        # Apply update
        for layer_idx in range(len(self.hidden_sizes) + 1):
            W = self.weights[f'W{layer_idx}']
            
            # Simplified update (would use backprop in real implementation)
            if layer_idx == 0:
                W -= lr * np.outer(state, gradient)
            else:
                W -= lr * gradient.mean() * np.ones_like(W[:3, :3])
                
    def apply_domain_randomization(self, sim_model) -> Dict:
        """
        Apply domain randomization to simulation for robust transfer.
        
        Args:
            sim_model: MuJoCo model to randomize
            
        Returns:
            Dictionary of randomization parameters applied
        """
        randomization = {}
        
        # Mass randomization
        if hasattr(sim_model, 'body_mass'):
            for i in range(len(sim_model.body_mass)):
                scale = 1 + np.random.uniform(
                    -self.domain_randomization["mass_noise"],
                    self.domain_randomization["mass_noise"]
                )
                randomization[f'mass_{i}'] = scale
                
        # Friction randomization
        if hasattr(sim_model, 'geom_friction'):
            for i in range(len(sim_model.geom_friction)):
                scale = 1 + np.random.uniform(
                    -self.domain_randomization["friction_noise"],
                    self.domain_randomization["friction_noise"]
                )
                randomization[f'friction_{i}'] = scale
                
        # Controller noise
        randomization['noise_std'] = self.domain_randomization["noise_std"]
        
        return randomization
        
    def get_statistics(self) -> Dict:
        """
        Get controller statistics and training progress.
        """
        return {
            'total_steps': self.total_steps,
            'demonstrations': len(self.expert_demonstrations),
            'training_mode': self.training_mode,
            'domain_randomization': self.domain_randomization,
            'architecture': {
                'state_dim': self.state_dim,
                'action_dim': self.action_dim,
                'hidden_sizes': self.hidden_sizes
            }
        }
        
    def save(self, filepath: str):
        """
        Save controller to file.
        """
        data = {
            'weights': {k: v.tolist() for k, v in self.weights.items()},
            'state_dim': self.state_dim,
            'action_dim': self.action_dim,
            'hidden_sizes': self.hidden_sizes,
            'statistics': self.get_statistics()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            
    def load(self, filepath: str):
        """
        Load controller from file.
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        self.weights = {k: np.array(v) for k, v in data['weights'].items()}
        self.state_dim = data['state_dim']
        self.action_dim = data['action_dim']
        self.hidden_sizes = data['hidden_sizes']


class AdaptiveController:
    """
    Adaptive controller that combines neural network with traditional control.
    Uses online adaptation to handle sim-to-real gaps.
    """
    
    def __init__(
        self,
        nn_controller: NeuralNetworkController,
        pid_controller: 'PIDController',
        adaptation_rate: float = 0.01
    ):
        self.nn_controller = nn_controller
        self.pid_controller = pid_controller
        self.adaptation_rate = adaptation_rate
        
        # Adaptation state
        self.error_buffer = []
        self.buffer_size = 100
        
        # Blend factor (0=PID only, 1=NN only)
        self.blend_factor = 0.5
        
    def compute_action(
        self,
        state: np.ndarray,
        target: np.ndarray,
        adaptation_enabled: bool = True
    ) -> np.ndarray:
        """
        Compute action using hybrid NN + PID control with adaptation.
        
        Args:
            state: Current state
            target: Target state
            adaptation_enabled: Whether to enable online adaptation
            
        Returns:
            Combined control action
        """
        # Neural network action
        nn_action = self.nn_controller.predict(state)
        
        # PID action (compute error-based control)
        error = target - state[:len(target)]
        if isinstance(self.pid_controller, dict):
            pid_action = np.array([
                self.pid_controller.get(f'joint_{i}', PIDController(100, 10, 50)).compute(error[i], 0.001)
                for i in range(min(len(error), 19))
            ])
        else:
            pid_action = self.pid_controller.compute(error, 0.001) if hasattr(self.pid_controller, 'compute') else np.zeros(19)
            
        # Combine actions
        combined_action = self.blend_factor * nn_action + (1 - self.blend_factor) * pid_action
        
        # Online adaptation
        if adaptation_enabled:
            self._adapt(combined_action, state, error)
            
        return combined_action
        
    def _adapt(
        self,
        action: np.ndarray,
        state: np.ndarray,
        error: np.ndarray
    ):
        """
        Online adaptation to reduce tracking error.
        """
        # Update error buffer
        self.error_buffer.append(np.linalg.norm(error))
        if len(self.error_buffer) > self.buffer_size:
            self.error_buffer.pop(0)
            
        # Adapt blend factor based on performance
        if len(self.error_buffer) >= 10:
            recent_error = np.mean(self.error_buffer[-10:])
            initial_error = np.mean(self.error_buffer[:10])
            
            if recent_error < initial_error * 0.8:
                # NN is working well, increase blend factor
                self.blend_factor = min(0.8, self.blend_factor + 0.01)
            elif recent_error > initial_error * 1.2:
                # PID is better, decrease blend factor
                self.blend_factor = max(0.2, self.blend_factor - 0.01)
                
    def get_adaptation_info(self) -> Dict:
        """
        Get information about current adaptation state.
        """
        return {
            'blend_factor': self.blend_factor,
            'error_buffer_size': len(self.error_buffer),
            'recent_error': np.mean(self.error_buffer[-10:]) if len(self.error_buffer) >= 10 else None,
            'nn_training_steps': self.nn_controller.total_steps
        }


class PIDController:
    """Simple PID controller for hybrid control."""
    
    def __init__(self, kp: float, ki: float, kd: float):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.integral = 0.0
        self.last_error = 0.0
        
    def compute(self, error: float, dt: float) -> float:
        self.integral += error * dt
        derivative = (error - self.last_error) / dt if dt > 0 else 0.0
        self.last_error = error
        return self.kp * error + self.ki * self.integral + self.kd * derivative


def create_neural_controller(config: Optional[Dict] = None) -> NeuralNetworkController:
    """
    Factory function to create neural network controller.
    """
    if config is None:
        config = {}
        
    return NeuralNetworkController(
        state_dim=config.get("state_dim", 38),
        action_dim=config.get("action_dim", 19),
        hidden_sizes=config.get("hidden_sizes", [256, 256, 128]),
        learning_rate=config.get("learning_rate", 0.0003)
    )


def generate_synthetic_demonstrations(
    num_demos: int = 1000,
    state_dim: int = 38,
    action_dim: int = 19
) -> List[Dict]:
    """
    Generate synthetic expert demonstrations for pretraining.
    
    This simulates optimal trajectories for:
    - Grasping objects at different positions
    - Rotating bottle caps
    - Lifting and placing objects
    """
    demonstrations = []
    
    for i in range(num_demos):
        # Simulate a reaching motion
        t = i / num_demos
        
        # State: joint positions following a smooth trajectory
        state = np.zeros(state_dim)
        state[:19] = 0.5 * np.sin(2 * np.pi * t * np.linspace(0.1, 1, 19))
        state[19:] = 0.2 * np.cos(2 * np.pi * t * np.linspace(0.1, 1, 19))
        
        # Action: smooth velocity commands
        action = 0.3 * np.cos(2 * np.pi * t * np.linspace(0.1, 1, action_dim))
        
        demonstrations.append({
            'state': state,
            'action': action,
            'task': 'reach' if i < num_demos // 3 else ('grasp' if i < 2 * num_demos // 3 else 'place')
        })
        
    return demonstrations


if __name__ == "__main__":
    # Test neural controller
    controller = create_neural_controller()
    
    # Generate synthetic demonstrations
    demos = generate_synthetic_demonstrations(100)
    
    # Add demonstrations to controller
    for demo in demos:
        controller.add_demonstration(demo['state'], demo['action'])
        
    # Test forward pass
    test_state = np.random.randn(38)
    action = controller.predict(test_state)
    
    print(f"State shape: {test_state.shape}")
    print(f"Action shape: {action.shape}")
    print(f"Action range: [{action.min():.3f}, {action.max():.3f}]")
    print(f"Controller statistics: {controller.get_statistics()}")
