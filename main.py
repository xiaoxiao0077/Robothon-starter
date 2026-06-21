import argparse
import os
import json
import numpy as np

try:
    import mujoco
    try:
        from mujoco import viewer
        MUJOCO_VERSION = 'new'
    except ImportError:
        MUJOCO_VERSION = 'old'
        import mujoco_py
except ImportError:
    import mujoco_py
    MUJOCO_VERSION = 'old'

from src.data_collector import MultiTaskDataCollector
from src.controller import (
    TeleoperationController, AutoGraspController, 
    AdaptiveGraspController, ForceControlController
)
from src.triage_controller import TriageController, FiveFingerGraspController
from src.utils import ensure_dir

try:
    from hardware_emulator import HardwareEmulator, SimToRealBridge, create_hardware_emulator
    from neural_controller import NeuralNetworkController, AdaptiveController, create_neural_controller
    from task_scenarios import TaskScenarioLibrary, PerformanceBenchmark, SimToRealAnalyzer
    NEW_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some advanced modules not available: {e}")
    NEW_MODULES_AVAILABLE = False

try:
    from hardware_validation import HardwareValidationSuite, validate_all, run_hardware_validation
    VALIDATION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Hardware validation module not available: {e}")
    VALIDATION_AVAILABLE = False

def load_model_and_data(scene_path):
    if MUJOCO_VERSION == 'new':
        model = mujoco.MjModel.from_xml_path(scene_path)
        data = mujoco.MjData(model)
        return model, data, None
    else:
        model = mujoco_py.load_model_from_path(scene_path)
        sim = mujoco_py.MjSim(model)
        return model, sim.data, sim

def run_teleop(args):
    model, data, sim = load_model_and_data(args.scene)
    
    if MUJOCO_VERSION == 'new':
        from mujoco import viewer
        viewer = viewer.launch(model, data)
    else:
        viewer = mujoco_py.MjViewer(sim)
    
    controller = TeleoperationController(model, data)
    collector = MultiTaskDataCollector(output_dir=args.output)
    collector.setup_from_model(model, data)
    collector.set_augmentation(args.augment, ['noise', 'scale'])
    collector.add_task_config('teleop', {'mode': 'manual', 'duration': args.duration})
    
    recording = False
    start_time = 0.0
    key_states = {}
    
    def keyboard_callback(keycode, action, mods):
        key = chr(keycode).lower() if keycode >= 32 and keycode <= 126 else str(keycode)
        is_pressed = action == 0
        
        if key == 'v' and is_pressed:
            nonlocal recording
            recording = not recording
            if recording:
                print("Recording started")
                collector.clear()
                collector.setup_from_model(model, data)
            else:
                print("Recording stopped")
                filepath = collector.save_sequence('teleop_grasping')
                stats = collector.get_statistics()
                print(f"Data saved: {filepath}")
                print(f"Stats: {stats}")
        
        if key == 'r' and is_pressed:
            if MUJOCO_VERSION == 'new':
                mujoco.mj_resetData(model, data)
            else:
                sim.reset()
            controller.open_hand()
            print("Reset simulation")
            
        if key == ' ':
            key_states[' '] = is_pressed
        elif keycode == 340:
            key_states['shift'] = is_pressed
        else:
            key_states[key] = is_pressed
    
    if MUJOCO_VERSION == 'new':
        viewer.callback_keyboard = keyboard_callback
    
    while True:
        controller.update_key_states(key_states)
        if MUJOCO_VERSION == 'new':
            mujoco.mj_step(model, data)
        else:
            sim.step()
        
        if recording:
            collector.collect(model, data, data.time)
        
        if MUJOCO_VERSION == 'new':
            viewer.sync()
            if not viewer.is_running():
                break
        else:
            viewer.render()
        
        if data.time - start_time > args.duration:
            if recording:
                collector.save_sequence('teleop_grasping')
            break

def run_auto_collect(args):
    model, data, sim = load_model_and_data(args.scene)
    
    tasks = [
        {'name': 'random_exploration', 'controller': AutoGraspController},
        {'name': 'adaptive_grasping', 'controller': AdaptiveGraspController},
        {'name': 'force_control', 'controller': ForceControlController},
        {'name': 'five_finger_grasp', 'controller': FiveFingerGraspController}
    ]
    
    collector = MultiTaskDataCollector(output_dir=args.output)
    collector.set_augmentation(args.augment, ['noise', 'scale', 'warp'])
    
    for task_config in tasks:
        task_name = task_config['name']
        controller_class = task_config['controller']
        
        collector.add_task_config(task_name, {'type': task_name, 'samples': args.num_samples})
        
        for sample_idx in range(args.num_samples):
            if MUJOCO_VERSION == 'new':
                mujoco.mj_resetData(model, data)
            else:
                sim.reset()
            controller = controller_class(model, data)
            
            collector.clear()
            collector.setup_from_model(model, data)
            collector.set_task(task_name)
            
            for step_idx in range(args.steps_per_sample):
                if isinstance(controller, AdaptiveGraspController):
                    controller.update(data.sensordata)
                elif isinstance(controller, ForceControlController):
                    controller.update(model.opt.timestep)
                elif isinstance(controller, FiveFingerGraspController):
                    controller.update()
                else:
                    controller.update()
                
                if MUJOCO_VERSION == 'new':
                    mujoco.mj_step(model, data)
                else:
                    sim.step()
                collector.collect_with_task(model, data, data.time, {'sample_idx': sample_idx})
            
            collector.save_sequence(task_name, sample_idx)
            
            if (sample_idx + 1) % args.log_interval == 0:
                progress = ((sample_idx + 1) / args.num_samples) * 100
                print(f"Task: {task_name} - Progress: {progress:.1f}%")
        
        print(f"Completed task: {task_name}")

def run_triage(args):
    model, data, sim = load_model_and_data(args.scene)
    
    if MUJOCO_VERSION == 'new':
        from mujoco import viewer
        viewer = viewer.launch(model, data)
    else:
        viewer = mujoco_py.MjViewer(sim)
    
    controller = TriageController(model, data)
    collector = MultiTaskDataCollector(output_dir=args.output)
    collector.setup_from_model(model, data)
    collector.add_task_config('triage', {'mode': 'autonomous', 'task': 'vial_handling'})
    
    frames = []
    frame_count = 0
    target_frames = int(args.duration / model.opt.timestep)
    
    while True:
        phase, completed = controller.update(data)
        if MUJOCO_VERSION == 'new':
            mujoco.mj_step(model, data)
        else:
            sim.step()
        collector.collect(model, data, data.time)
        
        if frame_count % 2 == 0:
            if MUJOCO_VERSION == 'new':
                frame = viewer.read_pixels()
                frames.append(frame)
            else:
                frame = sim.render(width=640, height=480, camera_name='main_camera')
                frames.append(frame)
        
        if frame_count % 50 == 0:
            status = controller.get_task_status()
            print(f"Frame {frame_count}: Phase: {status['phase']} | Rotation: {status['rotation_angle']:.2f} rad")
        
        if MUJOCO_VERSION == 'new':
            viewer.sync()
            if not viewer.is_running():
                break
        else:
            viewer.render()
        
        frame_count += 1
        
        if completed or frame_count >= target_frames:
            print("Task completed!")
            break
    
    collector.save_sequence('triage_demo')
    
    import imageio
    video_path = os.path.join(args.output, 'triage_demo.mp4')
    imageio.mimsave(video_path, frames, fps=30)
    print(f"Triage demo saved to {video_path}")

def run_visualize(args):
    import h5py
    import matplotlib.pyplot as plt
    
    with h5py.File(args.input, 'r') as f:
        timestamps = f['timestamps'][:]
        joint_positions = f['joint_positions'][:]
        sensor_data = f['sensor_data'][:]
        
        metadata = json.loads(f.attrs.get('metadata', '{}'))
    
    fig, axes = plt.subplots(3, 1, figsize=(12, 12))
    
    axes[0].plot(timestamps, joint_positions[:, :6])
    axes[0].set_title('Joint Positions (Thumb & Index)')
    axes[0].set_xlabel('Time (s)')
    axes[0].set_ylabel('Position (rad)')
    axes[0].legend(['Thumb ABD', 'Thumb Flex1', 'Thumb Flex2', 'Index ABD', 'Index Flex1', 'Index Flex2'])
    
    axes[1].plot(timestamps, sensor_data[:, :5])
    axes[1].set_title('Touch Sensor Data')
    axes[1].set_xlabel('Time (s)')
    axes[1].set_ylabel('Value')
    axes[1].legend(['Thumb', 'Index', 'Middle', 'Ring', 'Pinky'])
    
    if 'system_energy' in f:
        energy = f['system_energy'][:]
        axes[2].plot(timestamps, energy[:, 0], label='Kinetic')
        axes[2].plot(timestamps, energy[:, 1], label='Potential')
        axes[2].set_title('System Energy')
        axes[2].set_xlabel('Time (s)')
        axes[2].set_ylabel('Energy (J)')
        axes[2].legend()
    
    plt.tight_layout()
    
    output_dir = os.path.dirname(args.input) or '.'
    plot_path = os.path.join(output_dir, 'data_visualization.png')
    plt.savefig(plot_path)
    print(f"Visualization saved to {plot_path}")

def run_demo(args):
    model, data, sim = load_model_and_data(args.scene)
    
    if MUJOCO_VERSION == 'new':
        from mujoco import viewer
        viewer = viewer.launch(model, data)
    else:
        viewer = mujoco_py.MjViewer(sim)
    
    controller = FiveFingerGraspController(model, data)
    controller.set_grasp_pattern('precision')
    
    collector = MultiTaskDataCollector(output_dir=args.output)
    collector.setup_from_model(model, data)
    
    frames = []
    frame_count = 0
    target_frames = int(args.duration / model.opt.timestep)
    
    print(f"Generating demo...")
    
    for frame_count in range(target_frames):
        controller.update()
        
        if frame_count > 100 and frame_count < 300:
            controller.set_grasp_pattern('power')
        elif frame_count >= 300:
            controller.set_grasp_pattern('tripod')
            
        if MUJOCO_VERSION == 'new':
            mujoco.mj_step(model, data)
            if frame_count % 2 == 0:
                viewer.sync()
        else:
            sim.step()
            viewer.render()
        
        collector.collect(model, data, data.time)
        
        if frame_count % 100 == 0:
            progress = (frame_count / target_frames) * 100
            print(f"Progress: {progress:.1f}%")
    
    collector.save_sequence('demo')
    print(f"Demo completed!")

def run_validate(args):
    if not VALIDATION_AVAILABLE:
        print("Error: Hardware validation module not available")
        print("Please install dependencies: pip install -r requirements.txt")
        return
    
    print("="*60)
    print("  Hardware Validation Suite")
    print("="*60)
    
    suite = HardwareValidationSuite(scene_path=args.scene)
    results = suite.run_all_tests()
    
    print("\n" + "="*60)
    print("  Validation Results")
    print("="*60)
    
    passed = sum(1 for r in results.values() if r.get('pass', False))
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result.get('pass', False) else "FAIL"
        msg = result.get('message', result.get('description', ''))
        print(f"  {status} - {test_name}: {msg}")
    
    print(f"\n  Summary: {passed}/{total} tests passed")
    print(f"  Score: {(passed/total)*100:.1f}%")
    
    report_path = os.path.join(args.output, 'validation_report.json')
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2, default=lambda x: float(x) if isinstance(x, (np.integer, np.floating)) else bool(x) if isinstance(x, (np.bool_)) else x)
    print(f"\n  Report saved to: {report_path}")

def run_train(args):
    try:
        from train_controllers import ControllerTrainingPipeline
    except ImportError as e:
        print(f"Error: Training module not available: {e}")
        return
    
    print("="*60)
    print("  Controller Training Pipeline")
    print("="*60)
    
    pipeline = ControllerTrainingPipeline(scene_path=args.scene)
    
    print("\n[1/3] Training Neural Network Controller...")
    neural_losses = pipeline.train_neural_controller(
        n_epochs=args.neural_epochs, 
        batch_size=args.batch_size
    )
    print(f"  Final loss: {neural_losses[-1]:.6f}")
    
    print("\n[2/3] Training RL Controller...")
    rl_rewards = pipeline.train_rl_controller(
        n_iterations=args.rl_iterations,
        n_epochs=args.rl_epochs
    )
    print(f"  Final reward: {rl_rewards[-1]:.2f}")
    
    print("\n[3/3] Evaluating trained controllers...")
    metrics = pipeline.evaluate_controllers()
    
    print("\n" + "="*60)
    print("  Training Results")
    print("="*60)
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    model_path = os.path.join(args.output, 'trained_controllers.json')
    pipeline.save_models(model_path)
    print(f"\n  Models saved to: {model_path}")

def main():
    parser = argparse.ArgumentParser(description='Dexterous Hand Data Collection System')
    parser.add_argument('--mode', type=str, default='teleop', 
                        choices=['teleop', 'collect', 'visualize', 'demo', 'triage', 'validate', 'train'],
                        help='Operation mode')
    parser.add_argument('--scene', type=str, default='assets/scenes/data_collection_arena.xml',
                        help='Path to MuJoCo scene XML')
    parser.add_argument('--output', type=str, default='data',
                        help='Output directory for collected data')
    parser.add_argument('--input', type=str, default=None,
                        help='Input file for visualization')
    parser.add_argument('--num_samples', type=int, default=50,
                        help='Number of samples to collect')
    parser.add_argument('--steps_per_sample', type=int, default=500,
                        help='Simulation steps per sample')
    parser.add_argument('--duration', type=float, default=60.0,
                        help='Duration in seconds for teleop/demo mode')
    parser.add_argument('--log_interval', type=int, default=10,
                        help='Log progress every N samples')
    parser.add_argument('--augment', action='store_true', default=False,
                        help='Enable data augmentation')
    
    parser.add_argument('--neural_epochs', type=int, default=50,
                        help='Number of epochs for neural network training')
    parser.add_argument('--batch_size', type=int, default=32,
                        help='Batch size for training')
    parser.add_argument('--rl_iterations', type=int, default=20,
                        help='Number of RL iterations')
    parser.add_argument('--rl_epochs', type=int, default=10,
                        help='Number of epochs per RL iteration')
    
    args = parser.parse_args()
    
    ensure_dir(args.output)
    
    if args.mode == 'teleop':
        run_teleop(args)
    elif args.mode == 'collect':
        run_auto_collect(args)
    elif args.mode == 'visualize':
        if args.input is None:
            print("Please provide --input for visualization mode")
            return
        run_visualize(args)
    elif args.mode == 'demo':
        run_demo(args)
    elif args.mode == 'triage':
        run_triage(args)
    elif args.mode == 'validate':
        run_validate(args)
    elif args.mode == 'train':
        run_train(args)

if __name__ == '__main__':
    main()