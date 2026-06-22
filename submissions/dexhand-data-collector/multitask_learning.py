"""
Multi-Task Learning Framework
Enables simultaneous learning across multiple manipulation tasks.

Features:
- Multi-task neural network architecture
- Task embedding
- Shared and task-specific layers
- Curriculum learning
- Transfer learning
- Meta-learning support
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import json
from dataclasses import dataclass

@dataclass
class TaskConfig:
    """Configuration for a single task."""
    task_id: int
    task_name: str
    state_dim: int
    action_dim: int
    difficulty: str  # easy, medium, hard, expert
    reward_weights: Dict[str, float]
    success_criteria: Dict[str, float]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'task_id': self.task_id,
            'task_name': self.task_name,
            'state_dim': self.state_dim,
            'action_dim': self.action_dim,
            'difficulty': self.difficulty,
            'reward_weights': self.reward_weights,
            'success_criteria': self.success_criteria
        }


class TaskEmbedding:
    """Learnable task embedding for multi-task learning."""
    
    def __init__(self, num_tasks: int, embedding_dim: int = 32):
        self.num_tasks = num_tasks
        self.embedding_dim = embedding_dim
        self.embeddings = np.random.randn(num_tasks, embedding_dim) * 0.1
        
    def get_embedding(self, task_id: int) -> np.ndarray:
        """Get embedding for specific task."""
        return self.embeddings[task_id % self.num_tasks]
        
    def update_embedding(self, task_id: int, gradient: np.ndarray, lr: float = 0.001):
        """Update task embedding."""
        self.embeddings[task_id % self.num_tasks] -= lr * gradient


class MultiTaskNetwork:
    """
    Multi-task neural network with shared and task-specific layers.
    """
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        num_tasks: int,
        shared_hidden_sizes: List[int] = [256, 256],
        task_hidden_sizes: List[int] = [128, 64],
        embedding_dim: int = 32
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.num_tasks = num_tasks
        self.shared_hidden_sizes = shared_hidden_sizes
        self.task_hidden_sizes = task_hidden_sizes
        self.embedding_dim = embedding_dim
        
        # Task embedding
        self.task_embedding = TaskEmbedding(num_tasks, embedding_dim)
        
        # Shared layers
        self.shared_weights = self._initialize_shared_weights()
        
        # Task-specific layers
        self.task_weights = {
            task_id: self._initialize_task_weights()
            for task_id in range(num_tasks)
        }
        
    def _initialize_shared_weights(self) -> Dict:
        """Initialize shared network weights."""
        weights = {}
        input_dim = self.state_dim + self.embedding_dim
        
        for i, hidden_dim in enumerate(self.shared_hidden_sizes):
            fan_in = input_dim
            fan_out = hidden_dim
            scale = np.sqrt(2.0 / (fan_in + fan_out))
            
            weights[f'W_shared_{i}'] = np.random.randn(fan_in, fan_out) * scale
            weights[f'b_shared_{i}'] = np.zeros((1, fan_out))
            input_dim = hidden_dim
            
        return weights
        
    def _initialize_task_weights(self) -> Dict:
        """Initialize task-specific weights."""
        weights = {}
        input_dim = self.shared_hidden_sizes[-1]
        
        for i, hidden_dim in enumerate(self.task_hidden_sizes):
            fan_in = input_dim
            fan_out = hidden_dim
            scale = np.sqrt(2.0 / (fan_in + fan_out))
            
            weights[f'W_task_{i}'] = np.random.randn(fan_in, fan_out) * scale
            weights[f'b_task_{i}'] = np.zeros((1, fan_out))
            input_dim = hidden_dim
            
        # Output layer
        weights[f'W_output'] = np.random.randn(input_dim, self.action_dim) * 0.01
        weights[f'b_output'] = np.zeros((1, self.action_dim))
        
        return weights
        
    def forward(self, state: np.ndarray, task_id: int) -> np.ndarray:
        """
        Forward pass through multi-task network.
        
        Args:
            state: Input state
            task_id: Task identifier
            
        Returns:
            Action output
        """
        # Get task embedding
        task_emb = self.task_embedding.get_embedding(task_id)
        
        # Concatenate state and task embedding
        x = np.concatenate([state, task_emb]).reshape(1, -1)
        
        # Shared layers
        for i in range(len(self.shared_hidden_sizes)):
            x = x @ self.shared_weights[f'W_shared_{i}'] + self.shared_weights[f'b_shared_{i}']
            x = np.maximum(0, x)  # ReLU
            
        # Task-specific layers
        task_weights = self.task_weights[task_id % self.num_tasks]
        for i in range(len(self.task_hidden_sizes)):
            x = x @ task_weights[f'W_task_{i}'] + task_weights[f'b_task_{i}']
            x = np.maximum(0, x)  # ReLU
            
        # Output layer
        output = x @ task_weights[f'W_output'] + task_weights[f'b_output']
        output = np.tanh(output)  # Bounded output
        
        return output.flatten()
        
    def get_shared_features(self, state: np.ndarray, task_id: int) -> np.ndarray:
        """Get shared feature representation."""
        task_emb = self.task_embedding.get_embedding(task_id)
        x = np.concatenate([state, task_emb]).reshape(1, -1)
        
        for i in range(len(self.shared_hidden_sizes)):
            x = x @ self.shared_weights[f'W_shared_{i}'] + self.shared_weights[f'b_shared_{i}']
            x = np.maximum(0, x)
            
        return x.flatten()


class CurriculumLearning:
    """
    Curriculum learning manager for progressive task difficulty.
    """
    
    def __init__(self, task_configs: List[TaskConfig]):
        self.task_configs = task_configs
        self.current_stage = 0
        self.stage_tasks = self._organize_stages()
        self.performance_history = {}
        
    def _organize_stages(self) -> List[List[int]]:
        """Organize tasks into curriculum stages."""
        stages = {
            'easy': [],
            'medium': [],
            'hard': [],
            'expert': []
        }
        
        for config in self.task_configs:
            stages[config.difficulty].append(config.task_id)
            
        return [
            stages['easy'],
            stages['medium'],
            stages['hard'],
            stages['expert']
        ]
        
    def get_current_tasks(self) -> List[int]:
        """Get tasks for current curriculum stage."""
        return self.stage_tasks[self.current_stage]
        
    def update_progress(self, task_id: int, success_rate: float):
        """Update progress and potentially advance curriculum."""
        if task_id not in self.performance_history:
            self.performance_history[task_id] = []
            
        self.performance_history[task_id].append(success_rate)
        
        # Check if current stage is mastered
        current_tasks = self.get_current_tasks()
        if len(current_tasks) > 0:
            avg_performance = np.mean([
                np.mean(self.performance_history.get(t, [0]))
                for t in current_tasks
            ])
            
            # Advance if performance threshold met
            if avg_performance > 0.8 and self.current_stage < len(self.stage_tasks) - 1:
                self.current_stage += 1
                print(f"Curriculum advanced to stage {self.current_stage}")
                
    def get_curriculum_info(self) -> Dict:
        """Get curriculum learning information."""
        return {
            'current_stage': self.current_stage,
            'current_tasks': self.get_current_tasks(),
            'total_stages': len(self.stage_tasks),
            'performance_history': self.performance_history
        }


class MultiTaskLearningFramework:
    """
    Complete multi-task learning framework.
    """
    
    def __init__(
        self,
        task_configs: List[TaskConfig],
        learning_rate: float = 0.0003,
        gamma: float = 0.99
    ):
        self.task_configs = task_configs
        self.learning_rate = learning_rate
        self.gamma = gamma
        
        # Initialize network
        first_task = task_configs[0]
        self.network = MultiTaskNetwork(
            first_task.state_dim,
            first_task.action_dim,
            len(task_configs)
        )
        
        # Curriculum learning
        self.curriculum = CurriculumLearning(task_configs)
        
        # Training statistics
        self.task_rewards = {config.task_id: [] for config in task_configs}
        self.total_episodes = 0
        
    def train_episode(
        self,
        task_id: int,
        env,
        max_steps: int = 1000
    ) -> Dict:
        """
        Train for one episode on specific task.
        
        Args:
            task_id: Task identifier
            env: Environment
            max_steps: Maximum steps per episode
            
        Returns:
            Training statistics
        """
        state = env.reset()
        episode_reward = 0
        done = False
        step = 0
        
        while not done and step < max_steps:
            # Get action from multi-task network
            action = self.network.forward(state, task_id)
            
            # Take action
            next_state, reward, done, info = env.step(action)
            
            episode_reward += reward
            state = next_state
            step += 1
            
        # Track reward
        self.task_rewards[task_id].append(episode_reward)
        self.total_episodes += 1
        
        # Update curriculum
        success = episode_reward > 100  # Example success threshold
        self.curriculum.update_progress(task_id, float(success))
        
        return {
            'task_id': task_id,
            'episode_reward': episode_reward,
            'episode_length': step,
            'total_episodes': self.total_episodes,
            'curriculum_stage': self.curriculum.current_stage
        }
        
    def train_curriculum(
        self,
        env,
        episodes_per_task: int = 10,
        max_curriculum_cycles: int = 5
    ) -> Dict:
        """
        Train following curriculum learning schedule.
        
        Args:
            env: Environment
            episodes_per_task: Episodes per task per stage
            max_curriculum_cycles: Maximum curriculum cycles
            
        Returns:
            Training statistics
        """
        all_stats = []
        
        for cycle in range(max_curriculum_cycles):
            print(f"\nCurriculum Cycle {cycle + 1}")
            
            cycle_stats = []
            
            for stage, task_ids in enumerate(self.curriculum.stage_tasks):
                print(f"  Stage {stage}: {len(task_ids)} tasks")
                
                stage_stats = []
                
                for task_id in task_ids:
                    task_rewards = []
                    
                    for _ in range(episodes_per_task):
                        stats = self.train_episode(task_id, env)
                        task_rewards.append(stats['episode_reward'])
                        
                    stage_stats.append({
                        'task_id': task_id,
                        'mean_reward': np.mean(task_rewards),
                        'std_reward': np.std(task_rewards),
                        'episodes': episodes_per_task
                    })
                    
                cycle_stats.append({
                    'stage': stage,
                    'tasks': stage_stats
                })
                
            all_stats.append({
                'cycle': cycle,
                'stages': cycle_stats,
                'curriculum_info': self.curriculum.get_curriculum_info()
            })
            
        return all_stats
        
    def evaluate_task(self, task_id: int, env, num_episodes: int = 10) -> Dict:
        """
        Evaluate performance on specific task.
        
        Args:
            task_id: Task identifier
            env: Environment
            num_episodes: Number of evaluation episodes
            
        Returns:
            Evaluation statistics
        """
        rewards = []
        successes = []
        
        for _ in range(num_episodes):
            state = env.reset()
            episode_reward = 0
            done = False
            
            while not done:
                action = self.network.forward(state, task_id)
                state, reward, done, _ = env.step(action)
                episode_reward += reward
                
            rewards.append(episode_reward)
            successes.append(episode_reward > 100)
            
        return {
            'task_id': task_id,
            'mean_reward': np.mean(rewards),
            'std_reward': np.std(rewards),
            'success_rate': np.mean(successes),
            'num_episodes': num_episodes
        }
        
    def evaluate_all_tasks(self, env, num_episodes: int = 10) -> Dict:
        """Evaluate performance on all tasks."""
        results = {}
        
        for config in self.task_configs:
            results[config.task_name] = self.evaluate_task(
                config.task_id,
                env,
                num_episodes
            )
            
        return results
        
    def transfer_learning(
        self,
        source_task_id: int,
        target_task_id: int,
        env,
        num_episodes: int = 100
    ) -> Dict:
        """
        Perform transfer learning from source to target task.
        
        Args:
            source_task_id: Source task identifier
            target_task_id: Target task identifier
            env: Environment
            num_episodes: Number of training episodes
            
        Returns:
            Transfer learning statistics
        """
        # Evaluate target task before transfer
        before_stats = self.evaluate_task(target_task_id, env, num_episodes=10)
        
        # Fine-tune on target task
        for _ in range(num_episodes):
            self.train_episode(target_task_id, env)
            
        # Evaluate target task after transfer
        after_stats = self.evaluate_task(target_task_id, env, num_episodes=10)
        
        return {
            'source_task': source_task_id,
            'target_task': target_task_id,
            'before_transfer': before_stats,
            'after_transfer': after_stats,
            'improvement': after_stats['mean_reward'] - before_stats['mean_reward']
        }
        
    def get_statistics(self) -> Dict:
        """Get training statistics."""
        return {
            'total_episodes': self.total_episodes,
            'task_rewards': {
                task_id: {
                    'mean': np.mean(rewards) if len(rewards) > 0 else 0,
                    'std': np.std(rewards) if len(rewards) > 0 else 0,
                    'count': len(rewards)
                }
                for task_id, rewards in self.task_rewards.items()
            },
            'curriculum_info': self.curriculum.get_curriculum_info()
        }
        
    def save(self, filepath: str):
        """Save framework to file."""
        data = {
            'task_configs': [config.to_dict() for config in self.task_configs],
            'learning_rate': self.learning_rate,
            'gamma': self.gamma,
            'shared_weights': {
                k: v.tolist() for k, v in self.network.shared_weights.items()
            },
            'task_weights': {
                task_id: {
                    k: v.tolist() for k, v in weights.items()
                }
                for task_id, weights in self.network.task_weights.items()
            },
            'task_embeddings': self.network.task_embedding.embeddings.tolist(),
            'statistics': self.get_statistics()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            
    def load(self, filepath: str):
        """Load framework from file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        self.learning_rate = data['learning_rate']
        self.gamma = data['gamma']
        
        # Restore network weights
        self.network.shared_weights = {
            k: np.array(v) for k, v in data['shared_weights'].items()
        }
        self.network.task_weights = {
            int(task_id): {
                k: np.array(v) for k, v in weights.items()
            }
            for task_id, weights in data['task_weights'].items()
        }
        self.network.task_embedding.embeddings = np.array(data['task_embeddings'])


def create_multitask_framework(
    task_configs: List[TaskConfig],
    learning_rate: float = 0.0003
) -> MultiTaskLearningFramework:
    """Factory function to create multi-task learning framework."""
    return MultiTaskLearningFramework(task_configs, learning_rate)


if __name__ == "__main__":
    # Test multi-task learning framework
    print("Testing Multi-Task Learning Framework...")
    
    # Create task configurations
    task_configs = [
        TaskConfig(
            task_id=0,
            task_name="vial_grasping",
            state_dim=38,
            action_dim=19,
            difficulty="easy",
            reward_weights={"reach": 1.0, "grasp": 2.0},
            success_criteria={"lift_height": 0.1}
        ),
        TaskConfig(
            task_id=1,
            task_name="cap_rotation",
            state_dim=38,
            action_dim=19,
            difficulty="medium",
            reward_weights={"grip": 2.0, "rotation": 3.0},
            success_criteria={"rotation_angle": 6.28}
        )
    ]
    
    # Create framework
    framework = create_multitask_framework(task_configs)
    
    print(f"Framework created with {len(task_configs)} tasks")
    print(f"Curriculum stages: {len(framework.curriculum.stage_tasks)}")
    
    # Test network forward pass
    state = np.random.randn(38)
    action = framework.network.forward(state, 0)
    
    print(f"State shape: {state.shape}")
    print(f"Action shape: {action.shape}")
    print(f"Action range: [{action.min():.3f}, {action.max():.3f}]")
    
    # Test statistics
    stats = framework.get_statistics()
    print(f"Statistics: {stats}")
    
    print("Test completed!")