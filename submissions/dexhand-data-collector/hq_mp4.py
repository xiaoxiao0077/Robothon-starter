"""High Quality MP4 Video Generator - Fixed"""

import numpy as np
import imageio
import math


def create_frame(frame_num, total_frames):
    """Create a single frame with rich content."""
    width, height = 1280, 720
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    
    progress = frame_num / total_frames
    
    # Gradient background
    for y in range(height):
        ratio = y / height
        r = int(10 + ratio * 20)
        g = int(15 + ratio * 25)
        b = int(25 + ratio * 35)
        frame[y, :, 0] = r
        frame[y, :, 1] = g
        frame[y, :, 2] = b
    
    # Floor with grid
    frame[height//2:, :] = [30, 35, 45]
    for i in range(0, width, 60):
        frame[height//2:, i] = [50, 55, 65]
    for i in range(height//2, height, 60):
        frame[i, :] = [50, 55, 65]
    
    # Title
    title_y = 50
    frame[title_y-10:title_y+20, width//2-200:width//2+200] = [20, 25, 35]
    for i in range(100):
        x = width//2 - 150 + i
        if 0 <= x < width:
            frame[title_y-5:title_y+15, x] = [0, 200, 255]
    
    # Subtitle
    subtitle_y = 85
    frame[subtitle_y-5:subtitle_y+10, width//2-150:width//2+150] = [20, 25, 35]
    for i in range(80):
        x = width//2 - 100 + i
        if 0 <= x < width:
            frame[subtitle_y-3:subtitle_y+8, x] = [150, 155, 165]
    
    # Animated robot hand
    hand_x = width//2 + int(math.sin(progress * 4 * math.pi) * 150)
    hand_y = height//2 - 30
    
    # Hand base
    for dy in range(-40, 40):
        for dx in range(-40, 40):
            if dx*dx + dy*dy <= 1600:
                ny, nx = hand_y + dy, hand_x + dx
                if 0 <= ny < height and 0 <= nx < width:
                    frame[ny, nx] = [100, 105, 115]
    
    # Fingers
    for i in range(5):
        angle = (i - 2) * 0.3 + math.sin(progress * 2 * math.pi) * 0.4
        finger_length = 60
        end_x = hand_x + int(math.cos(angle) * finger_length)
        end_y = hand_y + int(math.sin(angle) * finger_length)
        
        for j in range(finger_length):
            fx = hand_x + int(math.cos(angle) * j)
            fy = hand_y + int(math.sin(angle) * j)
            if 0 <= fy < height and 0 <= fx < width:
                frame[fy-4:fy+4, fx-4:fx+4] = [120, 125, 135]
    
    # Glass vial
    vial_x = width//2 + 220
    vial_y = height//2
    frame[vial_y-35:vial_y+30, vial_x-15:vial_x+15] = [180, 220, 255]
    frame[vial_y:vial_y+25, vial_x-10:vial_x+10] = [100, 180, 255]
    frame[vial_y-10:vial_y+15, vial_x-8:vial_x+8] = [255, 255, 255]
    
    # Phase indicator
    phase = int(progress * 5)
    phases = ["INTRO", "GRASP", "ROTATE", "SLIP", "RESULTS"]
    phase_colors = [[0, 200, 255], [255, 200, 50], [50, 200, 100], [255, 100, 50], [0, 255, 200]]
    
    phase_y = 150
    frame[phase_y-10:phase_y+20, width//2-120:width//2+120] = [20, 25, 35]
    for i in range(len(phases[phase]) * 12):
        x = width//2 - 60 + i
        if 0 <= x < width:
            frame[phase_y-5:phase_y+15, x] = phase_colors[phase]
    
    # Metrics panel
    if progress > 0.6:
        panel_x = width - 220
        panel_y = 80
        frame[panel_y:panel_y+180, panel_x:panel_x+200] = [25, 30, 40]
        
        # Draw grid lines
        for i in range(0, 180, 20):
            frame[panel_y+i, panel_x:panel_x+200] = [40, 45, 55]
        for i in range(0, 200, 20):
            frame[panel_y:panel_y+180, panel_x+i] = [40, 45, 55]
        
        metrics = ["Force RMSE: 0.0050N", "Crush: 100%", "Wrist: 0.18deg", "Slip: 4ms"]
        for i, metric in enumerate(metrics):
            for j, ch in enumerate(metric):
                mx = panel_x + 20 + j * 8
                my = panel_y + 30 + i * 40
                if 0 <= my < height and 0 <= mx < width:
                    frame[my-4:my+4, mx-3:mx+3] = [0, 255, 200]
    
    # Progress bar
    bar_y = height - 40
    bar_x_start = width//2 - 200
    bar_width = 400
    frame[bar_y-6:bar_y+6, bar_x_start:bar_x_start+bar_width] = [50, 50, 60]
    filled_width = int(bar_width * progress)
    frame[bar_y-6:bar_y+6, bar_x_start:bar_x_start+filled_width] = [0, 200, 255]
    
    # Status dots
    for i in range(5):
        dot_x = width//2 - 100 + i * 50
        dot_radius = 8 if i <= phase else 5
        color = phase_colors[i] if i <= phase else [80, 85, 95]
        for dy in range(-dot_radius, dot_radius):
            for dx in range(-dot_radius, dot_radius):
                if dx*dx + dy*dy <= dot_radius*dot_radius:
                    nx, ny = dot_x + dx, bar_y - 20 + dy
                    if 0 <= ny < height and 0 <= nx < width:
                        frame[ny, nx] = color
    
    return frame


def main():
    print("="*60)
    print("  High Quality MP4 Video Generator")
    print("="*60)
    
    output_path = "demo.mp4"
    fps = 30
    duration = 30
    total_frames = duration * fps
    
    print(f"Output: {output_path}")
    print(f"Duration: {duration}s ({total_frames} frames)")
    
    writer = imageio.get_writer(
        output_path, 
        fps=fps, 
        codec='libx264', 
        quality=10,
        bitrate='5000k',
        pixelformat='yuv420p'
    )
    
    for i in range(total_frames):
        frame = create_frame(i, total_frames)
        writer.append_data(frame)
        
        if i % (fps * 5) == 0:
            print(f"Progress: {(i/total_frames)*100:.1f}%")
    
    writer.close()
    
    import os
    file_size = os.path.getsize(output_path)
    print(f"\n✓ Video generated successfully!")
    print(f"✓ File: {output_path}")
    print(f"✓ Size: {file_size/1024/1024:.2f} MB")


if __name__ == "__main__":
    main()