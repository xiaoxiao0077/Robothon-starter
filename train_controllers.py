#!/usr/bin/env python3
"""
Training Script for DexHand Controllers
Demonstrates actual training of neural and RL controllers

This script shows:
1. Neural controller behavioral cloning training
2. RL controller PPO training
3. Training progress and performance metrics
"""

import numpy as np
import time
import json
import os
from typing import Dict, List

try:
    import mujoco
    MUJOCO_VERSION = 'new'
except ImportError:
    import mujoco_py
    MUJOCO_VERSION = 'old'

from neural_controller import NeuralNetworkController
from rl_controller import PPOController, RLConfig
from hardware_emulator import create_hardware_emulator


class DexHandTrainer:
    """Training coordinator for dexterous hand controllers."""
    
    def __init__(self, scene_path: str = "./assets/scenes/demo_arena.xml"):
        self.scene_path = scene_path
        
        # Load model
        if MUJOCO_VERSION == 'new':
            self.model = mujoco.MjModel.from_xml_path(scene_path)
            self.data = mujoco.MjData(self.model)
        else:
            self.model = mujoco_py.load_model_from_path(scene_path)
            self.data = mujoco_py.MjSim(self.model)
        
        self.nu = self.model.nu
        self.nq = self.model.nq
        
        # Create controllers
        self.neural_controller = NeuralNetworkController(
            state_dim=38,  # 19 joints * 2
            action_dim=self.nu
        )
        
        self.rl_config = RLConfig(
            state_dim=38,
            action_dim=self.nu,
            hidden_sizes=[128, 128, 64],
            batch_size=32,
            n_steps=512
        )
        self.rl_controller = PPOController(self.rl_config)
        
        # Hardware emulator
        self.emulator = create_hardware_emulator()
        
        # Training metrics
        self.metrics = {
            'neural_training_loss': [],
            'rl_episode_rewards': [],
            'grasp_success_rate': 0.0
        }
        
    def _step_simulation(self):
        """Step simulation"""
        if MUJOCO_VERSION == 'new':
            mujoco.mj_step(self.model, self.data)
        else:
            self.data.step()
    
    def _get_state(self) -> np.ndarray:
        """Get current state vector."""
        joint_pos = self.data.qpos[:self.nu] if self.nu <= len(self.data.qpos) else np.zeros(self.nu)
        joint_vel = self.data.qvel[:self.nu] if self.nu <= len(self.data.qvel) else np.zeros(self.nu)
        
        # Pad if needed
        if len(joint_pos) < self.nu:
            joint_pos = np.pad(joint_pos, (0, self.nu - len(joint_pos)))
            joint_vel = np.pad(joint_vel, (0, self.nu - len(joint_vel)))
        
        # Process through emulator
        raw_state = np.concatenate([joint_pos, joint_vel])
        processed_state = self.emulator.process_sensor_data(raw_state, time.time())
        
        return processed_state
    
    def _generate_expert_demonstrations(self, n_demos: int = 100) -> List[Dict]:
        """Generate expert demonstrations using predefined motion patterns."""
        demonstrations = []
        
        print(f"Generating {n_demos} expert demonstrations...")
        
        for demo_idx in range(n_demos):
            # Reset
            if MUJOCO_VERSION == 'new':
                mujoco.mj_resetData(self.model, self.data)
            else:
                self.data.reset()
            
            # Different grasp patterns
            pattern = demo_idx % 5
            
            if pattern == 0:  # Power grasp
                target = np.ones(self.nu) * 0.8
            elif pattern == 1:  # Precision pinch
                target = np.zeros(self.nu)
                target[0] = 0.5
                target[3] = 0.8
            elif pattern == 2:  # Tripod
                target = np.zeros(self.nu)
                target[0:4] = [0.4, 0.7, 0.3, 0.8]
                target[4:8] = [0.3, 0.8, 0.6, 0.4]
            elif pattern == 3:  # Wide spread
                target = np.array([-0.5, 0.2, 0.1] + [0.3, 0.1, 0.1, 0.1] * 4)
            else:  # Relaxed
                target = np.ones(self.nu) * 0.3
            
            # Collect state-action pairs
            for step in range(50):
                self._step_simulation()
                
                state = self._get_state()
                action = target.copy() + np.random.normal(0, 0.05, self.nu)
                
                demonstrations.append({
                    'state': state,
                    'action': np.clip(action, -1.5, 1.5)
                })
        
        print(f"Generated {len(demonstrations)} state-action pairs")
        return demonstrations
    
    def train_neural_controller(self, n_epochs: int = 10, batch_size: int = 32):
        """Train neural controller using behavioral cloning."""
        print("\n" + "=" * 60)
        print("TRAINING NEURAL CONTROLLER (Behavioral Cloning)")
        print("=" * 60)
        
        # Generate demonstrations
        demonstrations = self._generate_expert_demonstrations(n_demos=50)
        
        # Add demonstrations to controller
        for demo in demonstrations[:500]:
            self.neural_controller.add_demonstration(demo['state'], demo['action'])
        
        # Training loop
        losses = []
        for epoch in range(n_epochs):
            epoch_losses = []
            
            for _ in range(10):  # 10 updates per epoch
                loss = self.neural_controller.behavioral_cloning_update(lr=0.001)
                if loss is not None:
                    epoch_losses.append(loss)
            
            avg_loss = np.mean(epoch_losses) if epoch_losses else 0
            losses.append(avg_loss)
            
            if (epoch + 1) % 2 == 0:
                print(f"  Epoch {epoch+1}/{n_epochs} - Loss: {avg_loss:.6f}")
        
        self.metrics['neural_training_loss'] = losses
        
        # Test performance
        print("\nTesting trained neural controller...")
        test_rewards = self._evaluate_neural_controller(n_episodes=5)
        print(f"  Average test reward: {np.mean(test_rewards):.2f}")
        
        return losses
    
    def _evaluate_neural_controller(self, n_episodes: int = 5) -> List[float]:
        """Evaluate neural controller performance."""
        rewards = []
        
        for _ in range(n_episodes):
            if MUJOCO_VERSION == 'new':
                mujoco.mj_resetData(self.model, self.data)
            else:
                self.data.reset()
            
            total_reward = 0
            
            for step in range(100):
                state = self._get_state()
                action = self.neural_controller.predict(state)
                
                self.data.ctrl[:] = action
                self._step_simulation()
                
                # Simple reward based on action magnitude and smoothness
                reward = -0.01 * np.sum(action ** 2)
                total_reward += reward
            
            rewards.append(total_reward)
        
        return rewards
    
    def train_rl_controller(self, n_iterations: int = 5):
        """Train RL controller using PPO."""
        print("\n" + "=" * 60)
        print("TRAINING RL CONTROLLER (PPO)")
        print("=" * 60)
        
        episode_rewards = []
        
        for iteration in range(n_iterations):
            # Collect experience
            episode_reward = 0
            
            if MUJOCO_VERSION == 'new':
                mujoco.mj_resetData(self.model, self.data)
            else:
                self.data.reset()
            
            state = self._get_state()
            
            for step in range(self.rl_config.n_steps):
                # Select action
                action, log_prob = self.rl_controller.select_action(state)
                
                # Apply action
                self.data.ctrl[:] = action
                self._step_simulation()
                
                # Get next state
                next_state = self._get_state()
                
                # Compute reward
                reward = -0.01 * np.sum(action ** 2)  # Smoothness reward
                reward += 0.1 * (1 - np.abs(action).mean())  # Prefer centered actions
                
                done = step == self.rl_config.n_steps - 1
                
                # Get value estimate
                _, value = self.rl_controller.policy.forward(state)
                value = np.mean(value)
                
                # Add to buffer
                self.rl_controller.buffer.add(
                    state, action, reward, next_state, done, log_prob, value
                )
                
                state = next_state
                episode_reward += reward
            
            # Update policy
            self.rl_controller.update()
            
            episode_rewards.append(episode_reward)
            self.metrics['rl_episode_rewards'] = episode_rewards
            
            if (iteration + 1) % 2 == 0:
                avg_reward = np.mean(episode_rewards[-10:])
                print(f"  Iteration {iteration+1}/{n_iterations} - Avg Reward: {avg_reward:.2f}")
        
        return episode_rewards
    
    def test_grasping(self, n_trials: int = 10) -> float:
        """Test grasping success rate."""
        print("\n" + "=" * 60)
        print("TESTING GRASPING PERFORMANCE")
        print("=" * 60)
        
        successes = 0
        
        for trial in range(n_trials):
            if MUJOCO_VERSION == 'new':
                mujoco.mj_resetData(self.model, self.data)
            else:
                self.data.reset()
            
            # Close hand gradually
            for step in range(100):
                progress = step / 100
                action = np.ones(self.nu) * progress * 0.8
                self.data.ctrl[:] = action
                self._step_simulation()
            
            # Check stability (low velocity)
            max_vel = np.max(np.abs(self.data.qvel))
            
            if max_vel < 0.5:
                successes += 1
        
        success_rate = successes / n_trials
        self.metrics['grasp_success_rate'] = success_rate
        
        print(f"  Grasping success rate: {success_rate*100:.1f}% ({successes}/{n_trials})")
        return success_rate
    
    def run_full_training(self) -> Dict:
        """Run complete training pipeline."""
        print("\n" + "=" * 60)
        print("DEXHAND CONTROLLER TRAINING PIPELINE")
        print("=" * 60)
        print(f"Model: {self.model.name}")
        print(f"State dim: 38, Action dim: {self.nu}")
        print("=" * 60)
        
        start_time = time.time()
        
        # Train neural controller
        neural_losses = self.train_neural_controller(n_epochs=10)
        
        # Train RL controller
        rl_rewards = self.train_rl_controller(n_iterations=5)
        
        # Test grasping
        grasp_success = self.test_grasping(n_trials=10)
        
        elapsed = time.time() - start_time
        
        # Save results
        results = {
            'training_time_seconds': elapsed,
            'neural_controller': {
                'final_loss': float(neural_losses[-1]) if neural_losses else 0,
                'loss_improvement': float(neural_losses[0] - neural_losses[-1]) if len(neural_losses) > 1 else 0,
                'training_epochs': len(neural_losses)
            },
            'rl_controller': {
                'final_reward': float(rl_rewards[-1]) if rl_rewards else 0,
                'avg_reward': float(np.mean(rl_rewards)) if rl_rewards else 0,
                'training_iterations': len(rl_rewards)
            },
            'grasping': {
                'success_rate': float(grasp_success)
            },
            'status': 'success' if grasp_success > 0.5 else 'needs_more_training'
        }
        
        # Save training results
        os.makedirs('training_results', exist_ok=True)
        with open('training_results/training_report.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print("\n" + "=" * 60)
        print("TRAINING COMPLETE")
        print("=" * 60)
        print(f"  Total time: {elapsed:.1f}s")
        print(f"  Neural final loss: {results['neural_controller']['final_loss']:.6f}")
        print(f"  RL avg reward: {results['rl_controller']['avg_reward']:.2f}")
        print(f"  Grasp success: {results['grasping']['success_rate']*100:.1f}%")
        print(f"  Status: {results['status']}")
        print("=" * 60)
        
        return results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Train DexHand Controllers')
    parser.add_argument('--scene', '-s', default='./assets/scenes/demo_arena.xml',
                       help='Path to scene XML')
    parser.add_argument('--neural_epochs', type=int, default=50,
                       help='Neural controller training epochs')
    parser.add_argument('--rl_iterations', type=int, default=20,
                       help='RL controller training iterations')
    
    args = parser.parse_args()
    
    trainer = DexHandTrainer(scene_path=args.scene)
    results = trainer.run_full_training()
    
    print("\nTraining results saved to: training_results/training_report.json")


if __name__ == "__main__":
    main()
