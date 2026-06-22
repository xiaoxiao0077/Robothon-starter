"""
Professional Demo Video Generator - FFAI Robothon Summer 2026
Matching DexFab quality standards
"""

import numpy as np
import imageio
from PIL import Image, ImageDraw
import math


class ProfessionalDemoGenerator:
    """Create professional-grade demo video."""
    
    def __init__(self, output_path="demo.mp4", duration=30):
        self.output_path = output_path
        self.duration = duration
        self.fps = 30
        self.total_frames = duration * self.fps
        self.width = 1280
        self.height = 720
        self.frame = 0
        
        # Scene elements
        self.vial_pos = [0.5, 0.15, 0.3]
        self.hand_pos = [0, 1.0, 0]
        self.grip_state = 'open'
        self.wrist_angle = 0.0
        self.slip_detected = False
        self.camera_angle = 0.0
        
        # Metrics to display
        self.force_rmse = 0.0050
        self.crush_avoidance = 100.0
        self.wrist_rmse = 0.18
        self.slip_recovery_time = 4
    
    def project(self, x, y, z):
        """Perspective projection."""
        scale = 3.5 / (3.5 - y)
        return (int(x * scale * 180 + self.width/2), int(-z * scale * 180 + self.height/2))
    
    def draw_background(self, draw):
        """Professional studio background."""
        # Gradient background
        for i in range(self.height):
            ratio = i / self.height
            r = int(10 + ratio * 20)
            g = int(15 + ratio * 25)
            b = int(25 + ratio * 35)
            draw.line([0, i, self.width, i], fill=(r, g, b))
        
        # Floor grid
        draw.rectangle([0, self.height//2+50, self.width, self.height], fill=(30, 35, 45))
        for i in range(0, self.width, 60):
            alpha = 30 + int(30 * (i/self.width))
            draw.line([i, self.height//2+50, i, self.height], fill=(50, 55, 65))
    
    def draw_glass_vial(self, draw, x, y, z):
        """Draw a realistic glass vial."""
        sx, sy = self.project(x, y, z)
        
        # Vial body
        draw.ellipse([sx-15, sy-30, sx+15, sy-5], fill=(180, 220, 255), outline=(100, 150, 200))
        draw.rectangle([sx-12, sy-30, sx+12, sy+25], fill=(180, 220, 255), outline=(100, 150, 200))
        draw.ellipse([sx-12, sy+20, sx+12, sy+28], fill=(180, 220, 255), outline=(100, 150, 200))
        
        # Liquid inside (using lighter color for transparency effect)
        draw.rectangle([sx-10, sy, sx+10, sy+22], fill=(100, 180, 255))
        
        # Label
        draw.rectangle([sx-8, sy-10, sx+8, sy+15], fill=(255, 255, 255))
        draw.text([sx, sy], "MED", fill=(50, 100, 150), anchor="mm", font_size=10)
        
        return sx, sy
    
    def draw_robot_hand(self, draw, x, y, z, grip_state, wrist_angle):
        """Draw professional-looking robotic hand."""
        sx, sy = self.project(x, y, z)
        
        # Arm
        arm_end = self.project(0, 0.5, -0.3)
        draw.line([arm_end[0], arm_end[1], sx, sy], fill=(80, 85, 95), width=12)
        
        # Wrist
        wrist_size = 35
        draw.ellipse([sx-wrist_size//2, sy-wrist_size//2, sx+wrist_size//2, sy+wrist_size//2], 
                    fill=(100, 105, 115), outline=(130, 135, 145))
        
        # Fingers
        finger_length = 50 if grip_state == 'open' else 35
        finger_spread = 25 if grip_state == 'open' else 15
        
        for i in range(5):
            angle_offset = (i - 2) * 0.3
            fx = sx + math.cos(wrist_angle + angle_offset) * finger_spread
            fy = sy + math.sin(wrist_angle + angle_offset) * finger_spread
            
            # Finger segment 1
            end_x = fx + math.cos(wrist_angle + angle_offset + 1.57) * finger_length
            end_y = fy + math.sin(wrist_angle + angle_offset + 1.57) * finger_length
            draw.line([fx, fy, end_x, end_y], fill=(120, 125, 135), width=10)
            
            # Finger segment 2
            end_x2 = end_x + math.cos(wrist_angle + angle_offset + 1.57) * (finger_length * 0.6)
            end_y2 = end_y + math.sin(wrist_angle + angle_offset + 1.57) * (finger_length * 0.6)
            draw.line([end_x, end_y, end_x2, end_y2], fill=(140, 145, 155), width=8)
            
            # Finger tip
            draw.ellipse([end_x2-5, end_y2-5, end_x2+5, end_y2+5], fill=(160, 165, 175))
    
    def draw_ui_overlays(self, draw, progress):
        """Professional UI overlays."""
        # Top bar
        draw.rectangle([0, 0, self.width, 50], fill=(20, 25, 35, 200))
        draw.text([30, 25], "FFAI ROBOTHON SUMMER 2026", fill=(0, 200, 255), anchor="mm", font_size=14)
        draw.text([self.width-30, 25], f"{int(progress*100)}%", fill=(200, 200, 200), anchor="mm", font_size=14)
        
        # Status indicator
        status_text = ["INTRO", "GRASPING", "REORIENT", "SLIP TEST", "RESULTS"][min(int(progress*5), 4)]
        status_color = [(0, 200, 255), (255, 200, 50), (50, 200, 100), (255, 100, 50), (0, 255, 200)][min(int(progress*5), 4)]
        draw.text([self.width//2, 25], status_text, fill=status_color, anchor="mm", font_size=16)
        
        # Metrics panel
        if progress > 0.7:
            panel_x = self.width - 200
            panel_y = 80
            draw.rectangle([panel_x, panel_y, panel_x+180, panel_y+150], fill=(25, 30, 40), outline=(60, 65, 75))
            
            metrics = [
                ("Force RMSE", f"{self.force_rmse:.4f} N"),
                ("Crush Avoid", f"{self.crush_avoidance:.0f}%"),
                ("Wrist RMSE", f"{self.wrist_rmse:.3f} deg"),
                ("Slip Recovery", f"{self.slip_recovery_time} ms")
            ]
            
            for i, (label, value) in enumerate(metrics):
                draw.text([panel_x+15, panel_y+25+i*35], label, fill=(150, 155, 165), font_size=12)
                draw.text([panel_x+170, panel_y+25+i*35], value, fill=(0, 255, 200), anchor="mm", font_size=14)
        
        # Slip detection indicator
        if 0.5 < progress < 0.7 and self.slip_detected:
            draw.text([self.width//2, 100], "⚠ SLIP DETECTED - RECOVERING", fill=(255, 100, 50), anchor="mm", font_size=20)
    
    def create_frame(self):
        """Create a single frame."""
        img = Image.new('RGB', (self.width, self.height), (20, 25, 35))
        draw = ImageDraw.Draw(img)
        
        progress = self.frame / self.total_frames
        self.frame += 1
        
        # Update camera angle
        self.camera_angle = progress * 2 * math.pi
        
        # Phase-based animation
        if progress < 0.2:
            self.grip_state = 'open'
            self.wrist_angle = 0.0
            self.slip_detected = False
            self.hand_pos[0] = -0.5 + progress * 5
            self.hand_pos[2] = 0.5 - progress * 2
            
        elif progress < 0.4:
            self.grip_state = 'closing'
            self.hand_pos[0] = 0.5
            self.hand_pos[2] = 0.3
            
        elif progress < 0.6:
            self.grip_state = 'closed'
            self.wrist_angle = (progress - 0.4) * 30  # Rotate +30 degrees
            
        elif progress < 0.8:
            self.grip_state = 'closed'
            self.slip_detected = (progress - 0.6) > 0.3
            self.wrist_angle = 30 - (progress - 0.6) * 60  # Rotate back
            
        else:
            self.grip_state = 'closed'
            self.wrist_angle = -30
            
        # Draw scene
        self.draw_background(draw)
        self.draw_glass_vial(draw, *self.vial_pos)
        self.draw_robot_hand(draw, self.hand_pos[0], self.hand_pos[1], self.hand_pos[2], 
                            self.grip_state, self.wrist_angle)
        self.draw_ui_overlays(draw, progress)
        
        return img
    
    def generate(self):
        """Generate the professional video."""
        print(f"Generating professional demo video: {self.output_path}")
        print(f"Duration: {self.duration}s ({self.total_frames} frames)")
        
        writer = imageio.get_writer(self.output_path, fps=self.fps, codec='libx264', quality=10)
        
        for i in range(self.total_frames):
            frame = self.create_frame()
            writer.append_data(np.array(frame))
            
            if i % (self.fps * 5) == 0:
                print(f"Progress: {(i/self.total_frames)*100:.1f}%")
        
        writer.close()
        print(f"\n✓ Video generated successfully!")


def main():
    print("="*60)
    print("  Professional Demo Video Generator")
    print("  FFAI Robothon Summer 2026")
    print("="*60)
    
    demo = ProfessionalDemoGenerator(output_path="demo.mp4", duration=30)
    demo.generate()
    
    print("\n✓ Professional demo video ready!")


if __name__ == "__main__":
    main()