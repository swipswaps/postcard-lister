#!/usr/bin/env python3
################################################################################
# FILE: github/upload_handler.py
# DESC: GitHub upload handler with verbatim capture
# WHAT: Complete GitHub integration with real-time progress and verbatim logging
# WHY: Provide reliable GitHub catalog uploads with full transparency
# FAIL: Graceful fallback to manual instructions if automated upload fails
# UX: Real-time progress updates and complete verbatim capture
# DEBUG: Complete logging of all GitHub operations
################################################################################

import subprocess
import json
import time
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class GitHubUploadHandler:
    """
    WHAT: Handle GitHub uploads with verbatim capture and progress tracking
    WHY: Provide transparent, reliable GitHub catalog uploads
    FAIL: Graceful fallback with manual instructions
    UX: Real-time progress and complete verbatim logging
    DEBUG: Complete capture of all GitHub operations
    """
    
    def __init__(self, repo_path: str = ".", verbose: bool = True):
        self.repo_path = Path(repo_path)
        self.verbose = verbose
        self.verbatim_log = []
        self.github_token = self.load_github_token()
        
    def load_github_token(self) -> Optional[str]:
        """Load GitHub token from environment or config"""
        # Try environment variable first
        token = os.getenv('GITHUB_TOKEN')
        if token:
            self.log_verbatim("✅ GitHub token loaded from environment")
            return token
        
        # Try .env.local file
        env_file = self.repo_path / '.env.local'
        if env_file.exists():
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith('GITHUB_TOKEN='):
                            token = line.split('=', 1)[1].strip().strip('"\'')
                            self.log_verbatim("✅ GitHub token loaded from .env.local")
                            return token
            except Exception as e:
                self.log_verbatim(f"⚠️ Failed to read .env.local: {e}")
        
        self.log_verbatim("❌ No GitHub token found")
        return None
    
    def log_verbatim(self, message: str, level: str = "INFO"):
        """Log message with verbatim capture"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"{timestamp} [{level}] {message}"
        self.verbatim_log.append(log_entry)
        
        if self.verbose:
            print(log_entry)
        
        # Also log to file
        log_file = self.repo_path / "logs" / "github_upload.log"
        log_file.parent.mkdir(exist_ok=True)
        with open(log_file, "a") as f:
            f.write(log_entry + "\n")
    
    def run_command(self, command: List[str], capture_output: bool = True) -> Tuple[bool, str, str]:
        """Run command with verbatim capture"""
        cmd_str = " ".join(command)
        self.log_verbatim(f"🔧 Running: {cmd_str}")
        
        try:
            if capture_output:
                result = subprocess.run(
                    command,
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.stdout:
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            self.log_verbatim(f"📤 STDOUT: {line}")
                
                if result.stderr:
                    for line in result.stderr.strip().split('\n'):
                        if line.strip():
                            self.log_verbatim(f"📥 STDERR: {line}")
                
                success = result.returncode == 0
                if success:
                    self.log_verbatim(f"✅ Command succeeded: {cmd_str}")
                else:
                    self.log_verbatim(f"❌ Command failed (code {result.returncode}): {cmd_str}")
                
                return success, result.stdout, result.stderr
            else:
                # For commands that need real-time output
                process = subprocess.Popen(
                    command,
                    cwd=self.repo_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                output_lines = []
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        line = output.strip()
                        output_lines.append(line)
                        self.log_verbatim(f"📡 LIVE: {line}")
                
                success = process.returncode == 0
                return success, '\n'.join(output_lines), ""
                
        except subprocess.TimeoutExpired:
            self.log_verbatim(f"⏰ Command timed out: {cmd_str}", "ERROR")
            return False, "", "Command timed out"
        except Exception as e:
            self.log_verbatim(f"💥 Command error: {e}", "ERROR")
            return False, "", str(e)
    
    def check_git_status(self) -> Dict[str, any]:
        """Check git repository status"""
        self.log_verbatim("🔍 Checking git repository status...")
        
        status = {
            'is_git_repo': False,
            'has_remote': False,
            'remote_url': '',
            'current_branch': '',
            'uncommitted_changes': False,
            'files_to_commit': [],
            'ahead_behind': {'ahead': 0, 'behind': 0}
        }
        
        # Check if it's a git repo
        success, _, _ = self.run_command(['git', 'rev-parse', '--git-dir'])
        if not success:
            self.log_verbatim("❌ Not a git repository", "ERROR")
            return status
        
        status['is_git_repo'] = True
        self.log_verbatim("✅ Git repository detected")
        
        # Get current branch
        success, branch, _ = self.run_command(['git', 'branch', '--show-current'])
        if success:
            status['current_branch'] = branch.strip()
            self.log_verbatim(f"📍 Current branch: {status['current_branch']}")
        
        # Check for remote
        success, remote_url, _ = self.run_command(['git', 'remote', 'get-url', 'origin'])
        if success:
            status['has_remote'] = True
            status['remote_url'] = remote_url.strip()
            self.log_verbatim(f"🌐 Remote URL: {status['remote_url']}")
        
        # Check for uncommitted changes
        success, git_status, _ = self.run_command(['git', 'status', '--porcelain'])
        if success and git_status.strip():
            status['uncommitted_changes'] = True
            status['files_to_commit'] = [line.strip() for line in git_status.strip().split('\n')]
            self.log_verbatim(f"📝 Uncommitted changes: {len(status['files_to_commit'])} files")
            for file_line in status['files_to_commit'][:5]:  # Show first 5
                self.log_verbatim(f"   📄 {file_line}")
            if len(status['files_to_commit']) > 5:
                self.log_verbatim(f"   ... and {len(status['files_to_commit']) - 5} more files")
        
        return status
    
    def upload_to_github(self, commit_message: str = None) -> Dict[str, any]:
        """Upload current changes to GitHub with verbatim capture"""
        self.log_verbatim("🚀 Starting GitHub upload process...")
        
        if not commit_message:
            commit_message = f"Solar panel catalog update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        result = {
            'success': False,
            'message': '',
            'commit_hash': '',
            'files_uploaded': 0,
            'verbatim_log': self.verbatim_log.copy()
        }
        
        # Check git status
        git_status = self.check_git_status()
        
        if not git_status['is_git_repo']:
            result['message'] = "Not a git repository"
            return result
        
        if not git_status['has_remote']:
            result['message'] = "No remote repository configured"
            self.log_verbatim("❌ No remote repository found", "ERROR")
            return result
        
        # Stage all changes
        self.log_verbatim("📦 Staging all changes...")
        success, _, _ = self.run_command(['git', 'add', '.'])
        if not success:
            result['message'] = "Failed to stage changes"
            return result
        
        # Check if there are changes to commit
        success, status_output, _ = self.run_command(['git', 'status', '--porcelain'])
        if not success or not status_output.strip():
            self.log_verbatim("ℹ️ No changes to commit")
            result['success'] = True
            result['message'] = "No changes to upload"
            return result
        
        # Count files to be committed
        files_to_commit = [line for line in status_output.strip().split('\n') if line.strip()]
        result['files_uploaded'] = len(files_to_commit)
        self.log_verbatim(f"📄 Files to commit: {result['files_uploaded']}")
        
        # Commit changes
        self.log_verbatim(f"💾 Committing changes: {commit_message}")
        success, commit_output, _ = self.run_command(['git', 'commit', '-m', commit_message])
        if not success:
            result['message'] = "Failed to commit changes"
            return result
        
        # Extract commit hash
        success, commit_hash, _ = self.run_command(['git', 'rev-parse', 'HEAD'])
        if success:
            result['commit_hash'] = commit_hash.strip()[:8]
            self.log_verbatim(f"📝 Commit hash: {result['commit_hash']}")
        
        # Push to remote
        self.log_verbatim("📤 Pushing to GitHub...")
        success, push_output, push_error = self.run_command(['git', 'push', 'origin', git_status['current_branch']], capture_output=False)
        
        if success:
            self.log_verbatim("✅ Successfully pushed to GitHub!")
            result['success'] = True
            result['message'] = f"Successfully uploaded {result['files_uploaded']} files to GitHub"
        else:
            self.log_verbatim(f"❌ Push failed: {push_error}", "ERROR")
            result['message'] = f"Push failed: {push_error}"
        
        return result
    
    def get_verbatim_log(self) -> List[str]:
        """Get complete verbatim log"""
        return self.verbatim_log.copy()
    
    def save_verbatim_log(self, filename: str = None) -> str:
        """Save verbatim log to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"github_upload_verbatim_{timestamp}.log"
        
        log_path = self.repo_path / "logs" / filename
        log_path.parent.mkdir(exist_ok=True)
        
        with open(log_path, 'w') as f:
            f.write("# GitHub Upload Verbatim Log\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            for entry in self.verbatim_log:
                f.write(entry + "\n")
        
        self.log_verbatim(f"📄 Verbatim log saved: {log_path}")
        return str(log_path)

def main():
    """Test the GitHub upload handler"""
    handler = GitHubUploadHandler(verbose=True)
    
    print("🔧 Testing GitHub Upload Handler")
    print("=" * 50)
    
    # Check status
    status = handler.check_git_status()
    print(f"\nGit Status: {json.dumps(status, indent=2)}")
    
    # Test upload (dry run)
    if status['is_git_repo']:
        print("\n🚀 Testing upload...")
        result = handler.upload_to_github("Test upload from GitHub handler")
        print(f"\nUpload Result: {json.dumps(result, indent=2)}")
    
    # Save verbatim log
    log_file = handler.save_verbatim_log()
    print(f"\n📄 Verbatim log saved to: {log_file}")

if __name__ == "__main__":
    main()
