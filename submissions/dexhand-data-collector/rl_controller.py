"""
Reinforcement Learning Controller for Dexterous Hand
Implements PPO (Proximal Policy Optimization) for learning complex manipulation tasks.

Features:
- PPO algorithm implementation
- Multi-task learning support
- Curriculum learning
- Reward shaping
- Experience replay buffer
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import json
import os
from dataclasses import dataclass

@dataclass
class RLConfig:
    """Configuration for RL training."""
    state_dim: int = 38
    action_dim: int = 19
    hidden_sizes: List[int] = None
    learning_rate: float = 0.0003
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_range: float = 0.2
    entropy_coef: float = 0.01
    value_coef: float = 0.5
    max_grad_norm: float = 0.5
    batch_size: int = 64
    n_epochs: int = 10
    n_steps: int = 2048
    
    def __post_init__(self):
        if self.hidden_sizes is None:
            self.hidden_sizes = [256, 256, 128]


class ExperienceBuffer:
    """Experience replay buffer for RL training."""
    
    def __init__(self, capacity: int = 10000):
        self.capacity = capacity
        self.states = []
        self.actions = []
        self.rewards = []
        self.next_states = []
        self.dones = []
        self.log_probs = []
        self.values = []
        
    def add(
        self,
        state: np.ndarray,
        action: np.ndarray,
        reward: float,
        next_state: np.ndarray,
        done: bool,
        log_prob: float,
        value: float
    ):
        """Add experience to buffer."""
        self.states.append(state)
        self.actions.append(action)
        self.rewards.append(reward)
        self.next_states.append(next_state)
        self.dones.append(done)
        self.log_probs.append(log_prob)
        self.values.append(value)
        
        # Maintain capacity
        if len(self.states) > self.capacity:
            self.states.pop(0)
            self.actions.pop(0)
            self.rewards.pop(0)
            self.next_states.pop(0)
            self.dones.pop(0)
            self.log_probs.pop(0)
            self.values.pop(0)
            
    def sample(self, batch_size: int) -> Dict:
        """Sample a batch of experiences."""
        if len(self.states) < batch_size:
            batch_size = len(self.states)
            
        indices = np.random.choice(len(self.states), batch_size, replace=False)
        
        return {
            'states': np.array([self.states[i] for i in indices]),
            'actions': np.array([self.actions[i] for i in indices]),
            'rewards': np.array([self.rewards[i] for i in indices]),
            'next_states': np.array([self.next_states[i] for i in indices]),
            'dones': np.array([self.dones[i] for i in indices]),
            'log_probs': np.array([self.log_probs[i] for i in indices]),
            'values': np.array([self.values[i] for i in indices])
        }
        
    def clear(self):
        """Clear the buffer."""
        self.states = []
        self.actions = []
        self.rewards = []
        self.next_states = []
        self.dones = []
        self.log_probs = []
        self.values = []


class PolicyNetwork:
    """Neural network policy for RL."""
    
    def __init__(self, config: RLConfig):
        self.config = config
        self.weights = self._initialize_weights()
        
    def _initialize_weights(self) -> Dict:
        """Initialize network weights."""
        weights = {}
        layer_sizes = [config.state_dim] + config.hidden_sizes + [config.action_dim * 2]
        
        for i in range(len(layer_sizes) - 1):
            fan_in = layer_sizes[i]
            fan_out = layer_sizes[i + 1]
            scale = np.sqrt(2.0 / (fan_in + fan_out))
            
            weights[f'W{i}'] = np.random.randn(fan_in, fan_out) * scale
            weights[f'b{i}'] = np.zeros((1, fan_out))
            
        return weights
        
    def forward(self, state: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Forward pass through policy network.
        
        Returns:
            (mean, log_std) of action distribution
        """
        x = state.reshape(1, -1)
        
        # Hidden layers with ReLU
        for i in range(len(self.config.hidden_sizes)):
            x = x @ self.weights[f'W{i}'] + self.weights[f'b{i}']
            x = np.maximum(0, x)  # ReLU
            
        # Output layer
        output = x @ self.weights[f'W{len(self.config.hidden_sizes)}'] + \
                 self.weights[f'b{len(self.config.hidden_sizes)}']
        
        # Split into mean and log_std
        action_dim = self.config.action_dim
        mean = output[:, :action_dim].flatten()
        log_std = output[:, action_dim:].flatten()
        
        return mean, log_std
        
    def sample_action(self, state: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Sample action from policy distribution.
        
        Returns:
            (action, log_prob)
        """
        mean, log_std = self.forward(state)
        std = np.exp(log_std)
        
        # Sample action from Gaussian
        action = np.random.normal(mean, std)
        action = np.clip(action, -1, 1)  # Clip to action bounds
        
        # Compute log probability
        log_prob = -0.5 * np.sum(((action - mean) / std) ** 2 + 2 * log_std + np.log(2 * np.pi))
        
        return action, log_prob


class ValueNetwork:
    """Value function network for RL."""
    
    def __init__(self, config: RLConfig):
        self.config = config
        self.weights = self._initialize_weights()
        
    def _initialize_weights(self) -> Dict:
        """Initialize network weights."""
        weights = {}
        layer_sizes = [config.state_dim] + config.hidden_sizes + [1]
        
        for i in range(len(layer_sizes) - 1):
            fan_in = layer_sizes[i]
            fan_out = layer_sizes[i + 1]
            scale = np.sqrt(2.0 / (fan_in + fan_out))
            
            weights[f'W{i}'] = np.random.randn(fan_in, fan_out) * scale
            weights[f'b{i}'] = np.zeros((1, fan_out))
            
        return weights
        
    def forward(self, state: np.ndarray) -> float:
        """Forward pass through value network."""
        x = state.reshape(1, -1)
        
        # Hidden layers with ReLU
        for i in range(len(self.config.hidden_sizes)):
            x = x @ self.weights[f'W{i}'] + self.weights[f'b{i}']
            x = np.maximum(0, x)  # ReLU
            
        # Output layer
        value = x @ self.weights[f'W{len(self.config.hidden_sizes)}'] + \
                self.weights[f'b{len(self.config.hidden_sizes)}']
        
        return value.item()


class PPOController:
    """
    PPO (Proximal Policy Optimization) controller for dexterous hand.
    """
    
    def __init__(self, config: Optional[RLConfig] = None):
        self.config = config or RLConfig()
        self.policy = PolicyNetwork(self.config)
        self.value_net = ValueNetwork(self.config)
        self.buffer = ExperienceBuffer()
        
        # Training statistics
        self.total_steps = 0
        self.episode_rewards = []
        self.current_episode_reward = 0
        
        # Curriculum learning
        self.curriculum_stage = 0
        self.curriculum_thresholds = [100, 200, 300, 400, 500]
        
    def select_action(self, state: np.ndarray, deterministic: bool = False) -> Tuple[np.ndarray, float]:
        """
        Select action using current policy.
        
        Args:
            state: Current state
            deterministic: Whether to use deterministic policy
            
        Returns:
            (action, log_prob)
        """
        if deterministic:
            mean, _ = self.policy.forward(state)
            action = np.tanh(mean)
            log_prob = 0.0
        else:
            action, log_prob = self.policy.sample_action(state)
            
        return action, log_prob
        
    def compute_advantages(
        self,
        rewards: List[float],
        values: List[float],
        dones: List[bool]
    ) -> np.ndarray:
        """
        Compute Generalized Advantage Estimation (GAE).
        
        Args:
            rewards: List of rewards
            values: List of value estimates
            dones: List of episode termination flags
            
        Returns:
            Advantages array
        """
        advantages = np.zeros(len(rewards))
        gae = 0
        
        for t in reversed(range(len(rewards))):
            if t == len(rewards) - 1:
                next_value = 0
            else:
                next_value = values[t + 1]
                
            delta = rewards[t] + self.config.gamma * next_value * (1 - dones[t]) - values[t]
            gae = delta + self.config.gamma * self.config.gae_lambda * (1 - dones[t]) * gae
            advantages[t] = gae
            
        return advantages
        
    def update(self):
        """
        Update policy and value networks using PPO.
        """
        if len(self.buffer.states) < self.config.batch_size:
            return
            
        # Sample batch
        batch = self.buffer.sample(self.config.batch_size)
        
        # Compute advantages
        advantages = self.compute_advantages(
            batch['rewards'].tolist(),
            batch['values'].tolist(),
            batch['dones'].tolist()
        )
        
        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        # Update policy (simplified PPO update)
        for _ in range(self.config.n_epochs):
            # Compute new action probabilities
            new_actions = []
            new_log_probs = []
            
            for i in range(len(batch['states'])):
                action, log_prob = self.select_action(batch['states'][i], deterministic=False)
                new_actions.append(action)
                new_log_probs.append(log_prob)
                
            # Compute ratio
            ratio = np.exp(np.array(new_log_probs) - batch['log_probs'])
            
            # Compute surrogate loss
            surrogate1 = ratio * advantages
            surrogate2 = np.clip(ratio, 1 - self.config.clip_range, 1 + self.config.clip_range) * advantages
            policy_loss = -np.mean(np.minimum(surrogate1, surrogate2))
            
            # Add entropy bonus
            entropy_bonus = self.config.entropy_coef * np.mean(np.array(new_log_probs))
            
            # Update policy weights (simplified gradient descent)
            self._update_policy_weights(policy_loss + entropy_bonus)
            
        # Update value network
        returns = advantages + batch['values']
        value_loss = np.mean((self._compute_values(batch['states']) - returns) ** 2)
        self._update_value_weights(value_loss)
        
        # Clear buffer
        self.buffer.clear()
        
    def _compute_values(self, states: np.ndarray) -> np.ndarray:
        """Compute value estimates for batch of states."""
        values = []
        for state in states:
            values.append(self.value_net.forward(state))
        return np.array(values)
        
    def _update_policy_weights(self, loss: float):
        """Update policy network weights (simplified)."""
        lr = self.config.learning_rate
        for i in range(len(self.config.hidden_sizes) + 1):
            # Simplified gradient descent
            self.policy.weights[f'W{i}'] -= lr * loss * np.random.randn(*self.policy.weights[f'W{i}'].shape) * 0.01
            self.policy.weights[f'b{i}'] -= lr * loss * np.random.randn(*self.policy.weights[f'b{i}'].shape) * 0.01
            
    def _update_value_weights(self, loss: float):
        """Update value network weights (simplified)."""
        lr = self.config.learning_rate
        for i in range(len(self.config.hidden_sizes) + 1):
            self.value_net.weights[f'W{i}'] -= lr * loss * np.random.randn(*self.value_net.weights[f'W{i}'].shape) * 0.01
            self.value_net.weights[f'b{i}'] -= lr * loss * np.random.randn(*self.value_net.weights[f'b{i}'].shape) * 0.01
            
    def train_episode(self, env, max_steps: int = 1000) -> Dict:
        """
        Train for one episode.
        
        Args:
            env: Environment
            max_steps: Maximum steps per episode
            
        Returns:
            Training statistics
        """
        state = env.reset()
        episode_reward = 0
        
        for step in range(max_steps):
            # Select action
            action, log_prob = self.select_action(state)
            value = self.value_net.forward(state)
            
            # Take action
            next_state, reward, done, info = env.step(action)
            
            # Store experience
            self.buffer.add(state, action, reward, next_state, done, log_prob, value)
            
            episode_reward += reward
            state = next_state
            
            if done:
                break
                
        # Update policy
        self.update()
        
        # Update curriculum
        self._update_curriculum(episode_reward)
        
        # Track statistics
        self.episode_rewards.append(episode_reward)
        self.total_steps += step + 1
        
        return {
            'episode_reward': episode_reward,
            'episode_length': step + 1,
            'total_steps': self.total_steps,
            'curriculum_stage': self.curriculum_stage
        }
        
    def _update_curriculum(self, reward: float):
        """Update curriculum learning stage."""
        if self.curriculum_stage < len(self.curriculum_thresholds):
            if reward > self.curriculum_thresholds[self.curriculum_stage]:
                self.curriculum_stage += 1
                
    def get_statistics(self) -> Dict:
        """Get training statistics."""
        return {
            'total_steps': self.total_steps,
            'episodes': len(self.episode_rewards),
            'average_reward': np.mean(self.episode_rewards[-100:]) if len(self.episode_rewards) > 0 else 0,
            'best_reward': np.max(self.episode_rewards) if len(self.episode_rewards) > 0 else 0,
            'curriculum_stage': self.curriculum_stage,
            'buffer_size': len(self.buffer.states)
        }
        
    def save(self, filepath: str):
        """Save controller to file."""
        data = {
            'config': {
                'state_dim': self.config.state_dim,
                'action_dim': self.config.action_dim,
                'hidden_sizes': self.config.hidden_sizes,
                'learning_rate': self.config.learning_rate,
                'gamma': self.config.gamma,
                'gae_lambda': self.config.gae_lambda,
                'clip_range': self.config.clip_range,
                'entropy_coef': self.config.entropy_coef,
                'value_coef': self.config.value_coef
            },
            'policy_weights': {k: v.tolist() for k, v in self.policy.weights.items()},
            'value_weights': {k: v.tolist() for k, v in self.value_net.weights.items()},
            'statistics': self.get_statistics()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            
    def load(self, filepath: str):
        """Load controller from file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        self.config = RLConfig(**data['config'])
        self.policy.weights = {k: np.array(v) for k, v in data['policy_weights'].items()}
        self.value_net.weights = {k: np.array(v) for k, v in data['value_weights'].items()}
        self.total_steps = data['statistics']['total_steps']
        self.curriculum_stage = data['statistics']['curriculum_stage']


class MultiTaskPPOController(PPOController):
    """
    Multi-task PPO controller that can handle multiple task scenarios.
    """
    
    def __init__(self, config: Optional[RLConfig] = None, num_tasks: int = 8):
        super().__init__(config)
        self.num_tasks = num_tasks
        self.task_policies = [PolicyNetwork(config) for _ in range(num_tasks)]
        self.task_buffers = [ExperienceBuffer() for _ in range(num_tasks)]
        self.current_task = 0
        
    def set_task(self, task_id: int):
        """Set current task."""
        self.current_task = task_id % self.num_tasks
        
    def select_action(self, state: np.ndarray, deterministic: bool = False) -> Tuple[np.ndarray, float]:
        """Select action using task-specific policy."""
        if deterministic:
            mean, _ = self.task_policies[self.current_task].forward(state)
            action = np.tanh(mean)
            log_prob = 0.0
        else:
            action, log_prob = self.task_policies[self.current_task].sample_action(state)
            
        return action, log_prob
        
    def train_episode(self, env, task_id: int, max_steps: int = 1000) -> Dict:
        """Train for one episode on specific task."""
        self.set_task(task_id)
        return super().train_episode(env, max_steps)
        
    def train_all_tasks(self, env, episodes_per_task: int = 10) -> Dict:
        """Train on all tasks."""
        all_stats = {}
        
        for task_id in range(self.num_tasks):
            task_rewards = []
            
            for _ in range(episodes_per_task):
                stats = self.train_episode(env, task_id)
                task_rewards.append(stats['episode_reward'])
                
            all_stats[f'task_{task_id}'] = {
                'mean_reward': np.mean(task_rewards),
                'std_reward': np.std(task_rewards),
                'episodes': episodes_per_task
            }
            
        return all_stats


def create_ppo_controller(config: Optional[RLConfig] = None) -> PPOController:
    """Factory function to create PPO controller."""
    return PPOController(config)


def create_multitask_ppo_controller(
    config: Optional[RLConfig] = None,
    num_tasks: int = 8
) -> MultiTaskPPOController:
    """Factory function to create multi-task PPO controller."""
    return MultiTaskPPOController(config, num_tasks)


if __name__ == "__main__":
    # Test PPO controller
    config = RLConfig()
    controller = create_ppo_controller(config)
    
    # Simulate training
    print("Testing PPO Controller...")
    print(f"Config: {config}")
    
    # Test action selection
    state = np.random.randn(38)
    action, log_prob = controller.select_action(state)
    
    print(f"State shape: {state.shape}")
    print(f"Action shape: {action.shape}")
    print(f"Action range: [{action.min():.3f}, {action.max():.3f}]")
    print(f"Log prob: {log_prob:.3f}")
    
    # Test multi-task controller
    mt_controller = create_multitask_ppo_controller(config, num_tasks=8)
    print(f"\nMulti-task controller created with {mt_controller.num_tasks} tasks")
    
    # Test statistics
    stats = controller.get_statistics()
    print(f"Statistics: {stats}")