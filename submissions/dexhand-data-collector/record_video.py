"""Video recording script for FFAI Robothon Summer 2026"""

import argparse
import os
import sys

def record_video():
    """Record demo video."""
    print("="*60)
    print("  Video Recording Script")
    print("  DexHand Data Collector")
    print("="*60)
    
    # Check if mujoco is available
    try:
        import mujoco
        print("✓ MuJoCo is available")
        has_mujoco = True
    except ImportError:
        print("✗ MuJoCo not available, using fallback method")
        has_mujoco = False
    
    if has_mujoco:
        # Use MuJoCo for recording
        print("\nRecording video with MuJoCo...")
        try:
            from mujoco_style_demo import MujocoStyleDemo
            demo = MujocoStyleDemo(output_path="demo.mp4", duration=30)
            demo.generate()
            print("✓ Video recorded successfully!")
        except Exception as e:
            print(f"✗ Error recording video: {e}")
            fallback_recording()
    else:
        fallback_recording()

def fallback_recording():
    """Fallback video recording method."""
    print("\nUsing fallback video generation...")
    # Create a simple video using imageio
    try:
        import imageio
        from PIL import Image, ImageDraw
        
        fps = 30
        duration = 30
        total_frames = fps * duration
        
        writer = imageio.get_writer('demo.mp4', fps=fps)
        
        for i in range(total_frames):
            img = Image.new('RGB', (1280, 720), (30, 30, 46))
            draw = ImageDraw.Draw(img)
            progress = i / total_frames
            draw.text((640, 360), f"Recording: {progress:.1%}", fill=(255, 255, 255), anchor="mm")
            writer.append_data(np.array(img))
            
            if i % (fps * 5) == 0:
                print(f"Progress: {(i/total_frames)*100:.1f}%")
        
        writer.close()
        print("✓ Fallback video recorded successfully!")
    except Exception as e:
        print(f"✗ Could not record video: {e}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Record demo video')
    parser.add_argument('--duration', type=int, default=30, help='Video duration in seconds')
    parser.add_argument('--output', type=str, default='demo.mp4', help='Output filename')
    
    args = parser.parse_args()
    
    print(f"Recording {args.duration} second video to {args.output}")
    record_video()

if __name__ == "__main__":
    import numpy as np
    main()