#!/usr/bin/env python3
"""
FFAI Robothon Summer 2026 - Auto Submission Script
Automates the submission process for the competition.
"""

import os
import subprocess
import json
import argparse

def run_command(cmd, cwd=None):
    """Run a command and return the result."""
    print(f"Executing: {cmd}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Output: {result.stdout}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return None

def load_registration(uuid_file="registration.json"):
    """Load registration information."""
    with open(uuid_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_gitignore():
    """Create .gitignore file if not exists."""
    gitignore_content = """# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Data
data/
*.h5
*.mp4
*.png

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Build
build/
dist/
*.egg-info/

# Logs
logs/
*.log
"""
    with open('.gitignore', 'w') as f:
        f.write(gitignore_content)
    print("Created .gitignore")

def setup_git(repo_dir, github_username, email):
    """Setup git configuration."""
    run_command(f'git config user.name "{github_username}"', cwd=repo_dir)
    run_command(f'git config user.email "{email}"', cwd=repo_dir)
    print("Git configuration set")

def create_submission_zip(output_file="submission.zip"):
    """Create submission zip file."""
    if os.name == 'nt':
        # Windows
        run_command(f'powershell Compress-Archive -Path * -DestinationPath {output_file} -Force')
    else:
        # Unix
        run_command(f'zip -r {output_file} . -x "*.git*" -x "__pycache__" -x "*.pyc"')
    print(f"Created submission zip: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='FFAI Robothon Auto Submission')
    parser.add_argument('--github-username', required=True, help='GitHub username')
    parser.add_argument('--email', required=True, help='GitHub email')
    parser.add_argument('--repo-url', default='https://github.com/Faraday-Future-AI/Robothon-starter',
                        help='Official repository URL')
    args = parser.parse_args()

    # Load registration info
    registration = load_registration()
    uuid = registration['uuid']
    project_title = registration['project_title']
    
    print("=" * 60)
    print(f"FFAI Robothon Summer 2026 - Auto Submission")
    print(f"UUID: {uuid}")
    print(f"Project: {project_title}")
    print("=" * 60)

    # Create gitignore if not exists
    if not os.path.exists('.gitignore'):
        create_gitignore()

    # Get current directory
    current_dir = os.getcwd()
    print(f"\nCurrent directory: {current_dir}")

    # Instructions for manual steps
    print("\n" + "=" * 60)
    print("📋 STEP 1: Fork the official repository")
    print(f"Visit: {args.repo_url}")
    print("Click 'Fork' button to fork to your GitHub account")
    print("=" * 60)

    fork_url = f"https://github.com/{args.github_username}/Robothon-starter"
    print(f"\n📋 STEP 2: Clone your forked repository")
    print(f"Run: git clone {fork_url}.git")
    print(f"Then copy all files from {current_dir} to the cloned repo")
    print("=" * 60)

    print("\n📋 STEP 3: Commit and push")
    print("Run these commands in your forked repo directory:")
    print(f'  git add .')
    print(f'  git config user.name "{args.github_username}"')
    print(f'  git config user.email "{args.email}"')
    print(f'  git commit -m "Submission: {project_title} - UUID: {uuid}"')
    print(f'  git push origin main')
    print("=" * 60)

    print("\n📋 STEP 4: Create Pull Request")
    print(f"Visit: {fork_url}/compare")
    print("Click 'Compare & pull request'")
    print(f"Title: {project_title}")
    print(f"Description should include: UUID: {uuid}")
    print("=" * 60)

    # Create submission zip as backup
    print("\n📦 Creating submission zip as backup...")
    create_submission_zip()

    print("\n✅ Submission preparation complete!")
    print("Follow the steps above to complete your submission.")
    print(f"Your UUID: {uuid}")

if __name__ == '__main__':
    main()