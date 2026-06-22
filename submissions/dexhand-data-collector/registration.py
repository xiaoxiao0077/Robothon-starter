"""Registration script for FFAI Robothon Summer 2026"""

import json
import os

def generate_registration():
    """Generate registration.json file."""
    registration = {
        "uuid": "438a8329-a02c-4fdb-80b5-12bff9d9f69d",
        "project_name": "DexHand Data Collector",
        "team_name": "DexHand Team",
        "description": "Advanced dexterous hand control system with closed-loop control and slip recovery",
        "description_zh": "高级灵巧手控制系统，具备闭环控制和滑移恢复功能",
        "category": "dexterous_manipulation",
        "submission_date": "2026-06-22",
        "version": "1.0.0",
        "contact_email": "team@dexhand.io",
        "features": [
            "24-DOF Dexterous Hand Control",
            "Closed-Loop Control System",
            "4ms Slip Detection & Recovery",
            "Multi-Modal Sensor Integration",
            "Multi-Task Learning Framework",
            "Sim-to-Real Transfer"
        ],
        "files": {
            "config": "config.json",
            "model": "robot.xml",
            "controller": "robot_controller.py",
            "evaluation": "evaluation_report.json",
            "demo": "demo.mp4",
            "requirements": "requirements.txt"
        }
    }
    
    with open('registration.json', 'w', encoding='utf-8') as f:
        json.dump(registration, f, indent=2, ensure_ascii=False)
    
    print("✓ registration.json generated")

def main():
    """Main function."""
    print("="*60)
    print("  Registration Script")
    print("  DexHand Data Collector")
    print("="*60)
    
    generate_registration()
    
    print("\n✓ Registration complete!")

if __name__ == "__main__":
    main()