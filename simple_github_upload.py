#!/usr/bin/env python3
"""
Simple GitHub Upload Tool
Direct command-line interface for uploading solar panel catalog
"""

import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path

def run_command(cmd, capture_output=True):
    """Run command and return result"""
    print(f"🔧 Running: {' '.join(cmd)}")
    try:
        if capture_output:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.stdout:
                print(f"📤 Output: {result.stdout.strip()}")
            if result.stderr:
                print(f"📥 Error: {result.stderr.strip()}")
            return result.returncode == 0, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd)
            return result.returncode == 0, "", ""
    except Exception as e:
        print(f"❌ Command failed: {e}")
        return False, "", str(e)

def check_git_status():
    """Check git repository status"""
    print("🔍 Checking git repository status...")
    
    # Check if we're in a git repo
    success, _, _ = run_command(['git', 'rev-parse', '--git-dir'])
    if not success:
        print("❌ Not a git repository")
        return False
    
    print("✅ Git repository detected")
    
    # Check current branch
    success, branch, _ = run_command(['git', 'branch', '--show-current'])
    if success:
        print(f"📍 Current branch: {branch.strip()}")
    
    # Check for remote
    success, remote, _ = run_command(['git', 'remote', 'get-url', 'origin'])
    if success:
        print(f"🌐 Remote URL: {remote.strip()}")
    else:
        print("❌ No remote repository configured")
        return False
    
    # Check for uncommitted changes
    success, status, _ = run_command(['git', 'status', '--porcelain'])
    if success and status.strip():
        files = status.strip().split('\n')
        print(f"📝 Uncommitted changes: {len(files)} files")
        for file_line in files[:5]:  # Show first 5
            print(f"   📄 {file_line}")
        if len(files) > 5:
            print(f"   ... and {len(files) - 5} more files")
    else:
        print("ℹ️ No uncommitted changes")
    
    return True

def upload_to_github():
    """Upload current changes to GitHub"""
    print("🚀 Starting GitHub upload...")
    
    if not check_git_status():
        return False
    
    # Create commit message
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    commit_message = f"Solar panel catalog update - {timestamp}"
    
    print(f"💾 Commit message: {commit_message}")
    
    # Stage all changes
    print("📦 Staging all changes...")
    success, _, _ = run_command(['git', 'add', '.'])
    if not success:
        print("❌ Failed to stage changes")
        return False
    
    # Check if there are changes to commit
    success, status, _ = run_command(['git', 'status', '--porcelain'])
    if not success or not status.strip():
        print("ℹ️ No changes to commit")
        return True
    
    # Commit changes
    print("💾 Committing changes...")
    success, _, _ = run_command(['git', 'commit', '-m', commit_message])
    if not success:
        print("❌ Failed to commit changes")
        return False
    
    # Get commit hash
    success, commit_hash, _ = run_command(['git', 'rev-parse', 'HEAD'])
    if success:
        short_hash = commit_hash.strip()[:8]
        print(f"📝 Commit hash: {short_hash}")
    
    # Push to remote
    print("📤 Pushing to GitHub...")
    success, _, error = run_command(['git', 'push', 'origin', 'HEAD'], capture_output=False)
    
    if success:
        print("✅ Successfully uploaded to GitHub!")
        return True
    else:
        print(f"❌ Push failed: {error}")
        return False

def main():
    """Main function"""
    print("🌞 Solar Panel Catalog - GitHub Upload Tool")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path('.git').exists():
        print("❌ Not in a git repository directory")
        print("Please run this from your solar panel catalog directory")
        return 1
    
    try:
        success = upload_to_github()
        if success:
            print("\n🎉 GitHub upload completed successfully!")
            return 0
        else:
            print("\n❌ GitHub upload failed")
            return 1
    except KeyboardInterrupt:
        print("\n🛑 Upload cancelled by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
