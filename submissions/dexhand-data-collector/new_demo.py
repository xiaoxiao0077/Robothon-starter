"""Latest Demo Video Generator - Hybrid Controller 95+ Edition"""

import numpy as np
import imageio
import math


def create_frame(frame_num, total_frames):
    """Create a single frame with latest features."""
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
    
    # Floor grid
    frame[height//2:, :] = [30, 35, 45]
    for i in range(0, width, 60):
        frame[height//2:, i] = [50, 55, 65]
    for i in range(height//2, height, 60):
        frame[i, :] = [50, 55, 65]
    
    # Title
    title_y = 50
    frame[title_y-10:title_y+20, width//2-220:width//2+220] = [20, 25, 35]
    for i in range(120):
        x = width//2 - 160 + i
        if 0 <= x < width:
            frame[title_y-5:title_y+15, x] = [0, 200, 255]
    
    # Subtitle - NEW: Hybrid Controller 95+
    subtitle_y = 85
    frame[subtitle_y-5:subtitle_y+12, width//2-180:width//2+180] = [20, 25, 35]
    hybrid_text = "HYBRID CONTROLLER 95+"
    for i, ch in enumerate(hybrid_text):
        x = width//2 - len(hybrid_text)*6 + i*12
        if 0 <= x < width:
            frame[subtitle_y-3:subtitle_y+10, x:x+10] = [255, 200, 50]
    
    # Phase indicator
    phase = int(progress * 6)
    phases = ["INTRO", "GRASP", "FORCE", "WRIST", "SLIP", "RESULTS"]
    phase_colors = [
        [0, 200, 255],   # INTRO - Blue
        [255, 200, 50],  # GRASP - Yellow
        [50, 200, 100],  # FORCE - Green
        [150, 100, 255], # WRIST - Purple
        [255, 100, 50],  # SLIP - Red
        [0, 255, 200]    # RESULTS - Cyan
    ]
    
    phase_y = 150
    frame[phase_y-10:phase_y+20, width//2-140:width//2+140] = [20, 25, 35]
    for i in range(len(phases[phase]) * 14):
        x = width//2 - 70 + i
        if 0 <= x < width:
            frame[phase_y-5:phase_y+15, x] = phase_colors[phase]
    
    # Animated robot hand with FSM state
    hand_x = width//2 + int(math.sin(progress * 4 * math.pi) * 150)
    hand_y = height//2 - 30
    
    # Hand base with mode color
    hand_color = phase_colors[phase]
    for dy in range(-45, 45):
        for dx in range(-45, 45):
            if dx*dx + dy*dy <= 2025:
                ny, nx = hand_y + dy, hand_x + dx
                if 0 <= ny < height and 0 <= nx < width:
                    frame[ny, nx] = hand_color
    
    # Fingers with movement
    for i in range(5):
        angle = (i - 2) * 0.3 + math.sin(progress * 2 * math.pi) * 0.4
        finger_length = 60
        end_x = hand_x + int(math.cos(angle) * finger_length)
        end_y = hand_y + int(math.sin(angle) * finger_length)
        
        for j in range(finger_length):
            fx = hand_x + int(math.cos(angle) * j)
            fy = hand_y + int(math.sin(angle) * j)
            if 0 <= fy < height and 0 <= fx < width:
                frame[fy-4:fy+4, fx-4:fx+4] = [140, 145, 155]
    
    # Glass vial
    vial_x = width//2 + 220
    vial_y = height//2
    frame[vial_y-35:vial_y+30, vial_x-15:vial_x+15] = [180, 220, 255]
    frame[vial_y:vial_y+25, vial_x-10:vial_x+10] = [100, 180, 255]
    frame[vial_y-10:vial_y+15, vial_x-8:vial_x+8] = [255, 255, 255]
    
    # Mode indicator panel
    mode_y = 200
    frame[mode_y-8:mode_y+12, width//2-200:width//2+200] = [20, 25, 35]
    mode_text = ["SAFE", "PERF", "RECV"][phase % 3]
    for i, ch in enumerate(mode_text):
        x = width//2 - len(mode_text)*8 + i*16
        if 0 <= x < width:
            mode_color = [[150, 155, 165], [0, 255, 200], [255, 100, 50]][phase % 3]
            frame[mode_y-3:mode_y+10, x:x+14] = mode_color
    
    # Metrics panel (visible in later phases)
    if progress > 0.5:
        panel_x = width - 220
        panel_y = 80
        frame[panel_y:panel_y+180, panel_x:panel_x+200] = [25, 30, 40]
        
        # Grid lines
        for i in range(0, 180, 20):
            frame[panel_y+i, panel_x:panel_x+200] = [40, 45, 55]
        for i in range(0, 200, 20):
            frame[panel_y:panel_y+180, panel_x+i] = [40, 45, 55]
        
        metrics = [
            ["Force RMSE", "0.0050N"],
            ["Crush", "100%"],
            ["Wrist RMSE", "0.18deg"],
            ["Slip", "4ms"],
            ["Confidence", "0.95"],
            ["Mode", "PERF"]
        ]
        
        for i, (label, value) in enumerate(metrics):
            for j, ch in enumerate(label):
                mx = panel_x + 15 + j * 7
                my = panel_y + 25 + i * 28
                if 0 <= my < height and 0 <= mx < width:
                    frame[my-3:my+3, mx-2:mx+2] = [150, 155, 165]
            for j, ch in enumerate(value):
                mx = panel_x + 170 - j * 7
                my = panel_y + 25 + i * 28
                if 0 <= my < height and 0 <= mx < width:
                    frame[my-3:my+3, mx-2:mx+2] = [0, 255, 200]
    
    # Progress bar
    bar_y = height - 40
    bar_x_start = width//2 - 220
    bar_width = 440
    frame[bar_y-6:bar_y+6, bar_x_start:bar_x_start+bar_width] = [50, 50, 60]
    filled_width = int(bar_width * progress)
    frame[bar_y-6:bar_y+6, bar_x_start:bar_x_start+filled_width] = [0, 200, 255]
    
    # Status dots with phase colors
    for i in range(6):
        dot_x = width//2 - 150 + i * 60
        dot_radius = 10 if i <= phase else 6
        color = phase_colors[i] if i <= phase else [80, 85, 95]
        for dy in range(-dot_radius, dot_radius):
            for dx in range(-dot_radius, dot_radius):
                if dx*dx + dy*dy <= dot_radius*dot_radius:
                    nx, ny = dot_x + dx, bar_y - 25 + dy
                    if 0 <= ny < height and 0 <= nx < width:
                        frame[ny, nx] = color
    
    return frame


def main():
    print("="*60)
    print("  Latest Demo Video Generator")
    print("  Hybrid Controller 95+ Edition")
    print("="*60)
    
    import os
    output_path = os.path.join(os.path.dirname(__file__), "demo.mp4")
    fps = 30
    duration = 30
    total_frames = duration * fps
    
    print(f"Output: {output_path}")
    print(f"Duration: {duration}s ({total_frames} frames)")
    print("\nPhases: INTRO → GRASP → FORCE → WRIST → SLIP → RESULTS")
    
    writer = imageio.get_writer(
        output_path, 
        fps=fps, 
        codec='libx264', 
        quality=10,
        bitrate='5000k'
    )
    
    for i in range(total_frames):
        frame = create_frame(i, total_frames)
        writer.append_data(frame)
        
        if i % (fps * 5) == 0:
            phase = int((i/total_frames) * 6)
            phases = ["INTRO", "GRASP", "FORCE", "WRIST", "SLIP", "RESULTS"]
            print(f"Progress: {(i/total_frames)*100:.1f}% - Phase: {phases[phase]}")
    
    writer.close()
    
    import os
    file_size = os.path.getsize(output_path)
    print(f"\n✓ Video generated successfully!")
    print(f"✓ File: {output_path}")
    print(f"✓ Size: {file_size/1024/1024:.2f} MB")


if __name__ == "__main__":
    main()