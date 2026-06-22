import argparse
import os
import numpy as np
import mujoco
from src.data_collector import MujocoDataCollector
from src.controller import AutoGraspController
from src.utils import ensure_dir

def run_experiment(args):
    model = mujoco.MjModel.from_xml_path(args.scene)
    data = mujoco.MjData(model)
    
    controller = AutoGraspController(model, data)
    collector = MujocoDataCollector(output_dir=args.output)
    
    print(f"Running experiment: {args.experiment_name}")
    print(f"Number of samples: {args.num_samples}")
    print(f"Steps per sample: {args.steps_per_sample}")
    
    collector.add_metadata('experiment_name', args.experiment_name)
    collector.add_metadata('num_samples', args.num_samples)
    collector.add_metadata('steps_per_sample', args.steps_per_sample)
    collector.add_metadata('timestamp', np.datetime64('now'))
    
    for sample_idx in range(args.num_samples):
        mujoco.mj_resetData(model, data)
        
        collector.setup_from_model(model, data)
        
        for step_idx in range(args.steps_per_sample):
            controller.update()
            mujoco.mj_step(model, data)
            collector.collect(model, data, data.time)
        
        sample_filename = f"{args.experiment_name}_sample_{sample_idx:04d}.h5"
        collector.save(sample_filename)
        collector.clear()
        
        if (sample_idx + 1) % args.log_interval == 0:
            progress = ((sample_idx + 1) / args.num_samples) * 100
            print(f"Progress: {progress:.1f}% - Sample {sample_idx + 1}/{args.num_samples}")
    
    print("Experiment completed successfully!")

def main():
    parser = argparse.ArgumentParser(description='Run data collection experiment')
    parser.add_argument('--experiment_name', type=str, default='grasping_experiment',
                        help='Name of the experiment')
    parser.add_argument('--scene', type=str, default='assets/scenes/data_collection_arena.xml',
                        help='Path to MuJoCo scene XML')
    parser.add_argument('--output', type=str, default='data',
                        help='Output directory for collected data')
    parser.add_argument('--num_samples', type=int, default=100,
                        help='Number of samples to collect')
    parser.add_argument('--steps_per_sample', type=int, default=500,
                        help='Simulation steps per sample')
    parser.add_argument('--log_interval', type=int, default=10,
                        help='Log progress every N samples')
    
    args = parser.parse_args()
    
    ensure_dir(args.output)
    
    run_experiment(args)

if __name__ == '__main__':
    main()