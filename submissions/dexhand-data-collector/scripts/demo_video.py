#!/usr/bin/env python3
"""
DexHand Data Collector Demo Video
Uses imageio_ffmpeg to create MP4 video
"""

import numpy as np
from imageio_ffmpeg import write_frames
from PIL import Image, ImageDraw

def create_demo_video():
    """Create a demonstration video showing dexterous hand data collection"""
    
    # Video parameters
    width = 1280
    height = 720
    fps = 30
    duration = 90  # 90秒视频
    total_frames = int(duration * fps)
    
    # Create output video
    output_file = "triage_demo.mp4"
    
    print(f"Creating MP4 video: {output_file}")
    print(f"Resolution: {width}x{height}, FPS: {fps}, Duration: {duration}s (90 seconds)")
    print(f"Total frames: {total_frames}")
    
    # Precompute animation data
    np.random.seed(42)
    
    # Generate sensor data
    time_steps = np.arange(total_frames)
    joint_pos_data = np.sin(time_steps * 0.15) * 50
    force_data = np.cos(time_steps * 0.1) * 30
    torque_data = np.random.normal(0, 20, total_frames)
    force_data2 = np.sin(time_steps * 0.12) * 40
    
    # Initialize video writer
    writer = write_frames(output_file, (width, height), fps=fps)
    writer.send(None)  # Initialize
    
    for frame_idx in range(total_frames):
        progress = frame_idx / total_frames
        
        # Create blank frame
        img = Image.new('RGB', (width, height), color=(30, 30, 35))
        draw = ImageDraw.Draw(img)
        
        # Calculate animation phases
        phase = progress * 4  # Multiple phases
        phase_mod = phase % 4  # 0: approach, 1: grasp, 2: lift, 3: place
        
        # ----------------------
        # Left panel: Scene visualization
        # ----------------------
        panel_x = 20
        panel_y = 20
        panel_w = 580
        panel_h = 680
        
        # Panel background
        draw.rectangle([panel_x, panel_y, panel_x+panel_w, panel_y+panel_h], 
                      fill=(45, 45, 50), outline=(100, 100, 100))
        
        # Title
        draw.text((panel_x + 20, panel_y + 15), "DexHand Data Collector", 
                  fill=(255, 255, 255))
        
        # Ground line
        draw.line([(panel_x + 50, panel_y + 580), (panel_x + panel_w - 50, panel_y + 580)], 
                  fill=(150, 150, 150), width=2)
        
        # Table
        table_x = panel_x + 100
        table_y = panel_y + 480
        draw.rectangle([table_x, table_y, table_x + 400, table_y + 20], fill=(180, 160, 140))
        
        # Calculate object positions with slight oscillation
        oscillation = np.sin(frame_idx * 0.02) * 2
        
        # Medical vial (blue) - positioned at table
        vial_x = panel_x + 220 + oscillation
        vial_y = panel_y + 440
        
        # Check if hand is near vial (for grasp animation)
        vial_grabbed = 0.25 < progress < 0.4
        if vial_grabbed:
            vial_y -= 50  # Lift vial
            vial_x += 20
        
        draw.ellipse([vial_x-15, vial_y-15, vial_x+15, vial_y+15], fill=(50, 100, 255))
        draw.text((vial_x-12, vial_y+20), "Vial (Critical)", fill=(150, 150, 150))
        
        # Pill bottle (green)
        pill_x = panel_x + 380 - oscillation
        pill_y = panel_y + 440
        pill_grabbed = 0.55 < progress < 0.7
        if pill_grabbed:
            pill_y -= 50
            pill_x += 20
        draw.ellipse([pill_x-12, pill_y-12, pill_x+12, pill_y+12], fill=(50, 200, 50))
        draw.text((pill_x-15, pill_y+18), "Pills", fill=(150, 150, 150))
        
        # Syringe (cyan)
        syringe_x = panel_x + 300
        syringe_y = panel_y + 460
        syringe_grabbed = 0.8 < progress < 0.95
        if syringe_grabbed:
            syringe_y -= 50
        draw.rectangle([syringe_x-5, syringe_y-20, syringe_x+5, syringe_y+20], fill=(50, 200, 200))
        draw.text((syringe_x-12, syringe_y+25), "Syringe", fill=(150, 150, 150))
        
        # Additional object: Bandage (yellow)
        bandage_x = panel_x + 450
        bandage_y = panel_y + 470
        draw.rectangle([bandage_x-15, bandage_y-8, bandage_x+15, bandage_y+8], fill=(255, 220, 50))
        draw.text((bandage_x-20, bandage_y+12), "Bandage", fill=(150, 150, 150))
        
        # Calculate hand position based on phase
        if progress < 0.15:
            # Start position
            hand_x = panel_x + 550
            hand_y = panel_y + 150
        elif progress < 0.25:
            # Move to vial
            t = (progress - 0.15) / 0.1
            hand_x = panel_x + 550 - t * 330
            hand_y = panel_y + 150 + t * 290
        elif progress < 0.4:
            # Grasp and lift vial
            t = (progress - 0.25) / 0.15
            hand_x = panel_x + 220
            hand_y = panel_y + 440 - t * 80
        elif progress < 0.55:
            # Move to center
            t = (progress - 0.4) / 0.15
            hand_x = panel_x + 220 - t * 60
            hand_y = panel_y + 360 - t * 100
        elif progress < 0.7:
            # Grasp pills
            t = (progress - 0.55) / 0.15
            hand_x = panel_x + 160 - t * 20
            hand_y = panel_y + 260 + t * 180
        elif progress < 0.8:
            # Move to syringe
            t = (progress - 0.7) / 0.1
            hand_x = panel_x + 140 + t * 160
            hand_y = panel_y + 440 + t * 20
        elif progress < 0.95:
            # Grasp syringe
            t = (progress - 0.8) / 0.15
            hand_x = panel_x + 300
            hand_y = panel_y + 460 - t * 60
        else:
            # Return to start
            hand_x = panel_x + 550
            hand_y = panel_y + 150
        
        # Draw arm with multiple segments
        arm_base_x = panel_x + 550
        arm_base_y = panel_y + 100
        
        # Draw multiple arm segments
        mid_x = (arm_base_x + hand_x) / 2
        mid_y = (arm_base_y + hand_y) / 2
        elbow_x = mid_x + np.sin(frame_idx * 0.03) * 20
        elbow_y = mid_y
        
        # Arm segments
        draw.line([(arm_base_x, arm_base_y), (elbow_x, elbow_y)], 
                  fill=(120, 140, 180), width=10)
        draw.line([(elbow_x, elbow_y), (hand_x, hand_y)], 
                  fill=(100, 120, 160), width=8)
        
        # Draw hand (red circle) with fingers
        draw.ellipse([hand_x-20, hand_y-20, hand_x+20, hand_y+20], fill=(255, 80, 80))
        
        # Draw finger positions
        finger_angles = [0, 0.5, 1.0, 1.5, 2.0]
        for i, angle in enumerate(finger_angles):
            fx = hand_x + np.cos(angle + frame_idx * 0.05) * 25
            fy = hand_y + np.sin(angle + frame_idx * 0.05) * 25
            draw.line([(hand_x, hand_y), (fx, fy)], fill=(200, 100, 100), width=4)
            draw.ellipse([fx-5, fy-5, fx+5, fy+5], fill=(200, 80, 80))
        
        draw.text((hand_x-25, hand_y+30), "Dexterous Hand (24-DOF)", fill=(200, 200, 200))
        
        # ----------------------
        # Right panel: Data visualization
        # ----------------------
        panel2_x = 620
        panel2_y = 20
        panel2_w = 640
        panel2_h = 680
        
        # Panel background
        draw.rectangle([panel2_x, panel2_y, panel2_x+panel2_w, panel2_y+panel2_h], 
                      fill=(45, 45, 50), outline=(100, 100, 100))
        
        # Title
        draw.text((panel2_x + 20, panel2_y + 15), "Real-time Sensor Data Stream", 
                  fill=(255, 255, 255))
        
        # Draw 4 sensor charts
        chart_x_start = panel2_x + 50
        chart_width = panel2_w - 80
        chart_height = 150
        
        sensors = [
            ("Joint Position", joint_pos_data, (100, 150, 255), panel2_y + 80),
            ("Joint Velocity", force_data, (100, 255, 150), panel2_y + 250),
            ("Torque", torque_data, (255, 100, 150), panel2_y + 420),
            ("Force", force_data2, (255, 200, 100), panel2_y + 590)
        ]
        
        for name, data, color, y_offset in sensors:
            draw.text((chart_x_start + 5, y_offset - 5), name, fill=(150, 150, 150))
            points = []
            for i in range(min(frame_idx + 1, total_frames)):
                px = chart_x_start + (i / (total_frames - 1)) * chart_width
                py = y_offset + chart_height - (data[i] + 50) * (chart_height / 100)
                points.append((px, py))
            if len(points) > 1:
                draw.line(points, fill=color, width=2)
        
        # ----------------------
        # Bottom info panel
        # ----------------------
        # Mission status
        mission_text = "Mission: Dexterous Manipulation - Medical Triage"
        draw.text((40, height - 60), mission_text, fill=(200, 200, 255))
        
        # Current action based on progress
        if progress < 0.15:
            action = "Initializing... Approaching target"
        elif progress < 0.25:
            action = "Moving to critical vial"
        elif progress < 0.4:
            action = "Grasping critical medication"
        elif progress < 0.55:
            action = "Lifting and relocating"
        elif progress < 0.7:
            action = "Grasping pills container"
        elif progress < 0.8:
            action = "Preparing syringe"
        elif progress < 0.95:
            action = "Handling precision tool"
        else:
            action = "Task complete - Returning to home"
        
        draw.text((40, height - 40), f"Status: {action}", fill=(100, 255, 100))
        
        # UUID and frame info
        draw.text((40, height - 20), 
                  f"FFAI Robothon 2026 | UUID: 438a8329-a02c-4fdb-80b5-12bff9d9f69d", 
                  fill=(150, 150, 150))
        draw.text((width - 180, height - 20), 
                  f"Frame: {frame_idx}/{total_frames} | {int(progress*100)}%", 
                  fill=(150, 150, 150))
        
        # Convert to numpy array and send to writer
        frame = np.array(img)
        writer.send(frame)
        
        # Progress
        if (frame_idx + 1) % 30 == 0:
            elapsed = (frame_idx + 1) / fps
            print(f"Frame {frame_idx + 1}/{total_frames} ({elapsed:.1f}s / {duration}s) - {int((frame_idx + 1)/total_frames * 100)}%")
    
    # Close writer
    writer.close()
    
    print(f"✅ MP4 video saved successfully: {output_file}")
    return output_file

if __name__ == "__main__":
    try:
        create_demo_video()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()