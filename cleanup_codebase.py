#!/usr/bin/env python3
################################################################################
# FILE: cleanup_codebase.py
# DESC: Clean up redundant files and organize codebase for GitHub catalog
# USAGE: python3 cleanup_codebase.py
################################################################################

import os
import shutil
from pathlib import Path

def cleanup_redundant_files():
    """Remove redundant GitHub upload scripts and old versions"""
    print("🧹 Cleaning up redundant files...")
    
    # Files to remove (keep only the working ones)
    redundant_patterns = [
        "prf_github_one_shot_uploader_v*.sh",
        "app_gh_init_v*.py", 
        "fix_secrets*.sh",
        "force_*.sh",
        "push_to_*.sh",
        "resolve_*.sh",
        "remove_*.sh",
        "create_fresh_repo.sh",
        "restart_app.py"
    ]
    
    # Keep these essential files
    keep_files = {
        "github_upload_clean.sh",  # Working GitHub upload
        "run_integrated.py",       # Main launcher
        "app_integrated.py",       # Main application
        "test_integration.py",     # Integration tests
        "test_enhanced_system.py"  # Enhanced tests
    }
    
    removed_count = 0
    
    for pattern in redundant_patterns:
        if "*" in pattern:
            # Handle wildcard patterns
            base_pattern = pattern.replace("*", "")
            for file in os.listdir("."):
                if base_pattern in file and file not in keep_files:
                    try:
                        os.remove(file)
                        print(f"  ❌ Removed: {file}")
                        removed_count += 1
                    except Exception as e:
                        print(f"  ⚠️ Could not remove {file}: {e}")
        else:
            # Handle exact file names
            if os.path.exists(pattern) and pattern not in keep_files:
                try:
                    os.remove(pattern)
                    print(f"  ❌ Removed: {pattern}")
                    removed_count += 1
                except Exception as e:
                    print(f"  ⚠️ Could not remove {pattern}: {e}")
    
    print(f"✅ Removed {removed_count} redundant files")

def organize_logs():
    """Organize log files"""
    print("📁 Organizing log files...")
    
    # Move loose log files to logs directory
    log_files = [f for f in os.listdir(".") if f.endswith(".log")]
    
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    moved_count = 0
    for log_file in log_files:
        try:
            shutil.move(log_file, f"logs/{log_file}")
            print(f"  📄 Moved: {log_file} → logs/")
            moved_count += 1
        except Exception as e:
            print(f"  ⚠️ Could not move {log_file}: {e}")
    
    print(f"✅ Organized {moved_count} log files")

def create_archive_directory():
    """Create archive directory for old versions"""
    print("📦 Creating archive directory...")
    
    archive_dir = "archive"
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
        print(f"✅ Created {archive_dir}/ directory")
    
    # Move old app versions to archive
    old_apps = ["app.py", "app_v2.py", "build_exe.py", "PostcardLister.spec"]
    
    moved_count = 0
    for app_file in old_apps:
        if os.path.exists(app_file):
            try:
                shutil.move(app_file, f"{archive_dir}/{app_file}")
                print(f"  📦 Archived: {app_file}")
                moved_count += 1
            except Exception as e:
                print(f"  ⚠️ Could not archive {app_file}: {e}")
    
    print(f"✅ Archived {moved_count} old files")

def update_gitignore():
    """Update .gitignore for better security and organization"""
    print("🔒 Updating .gitignore...")
    
    gitignore_additions = """
# Security - API Keys and Tokens
*.env
*.env.local
.env.*
**/config/settings.json
**/*api_key*
**/*token*
**/*secret*

# GitHub Catalog
catalog/temp/
catalog/processing/

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
logs/
*.log

# Archive
archive/

# Chat logs (prevent future exposure)
68507cb0*.txt
**/68507cb0*.txt
"""
    
    try:
        with open(".gitignore", "a") as f:
            f.write(gitignore_additions)
        print("✅ Updated .gitignore with security and organization rules")
    except Exception as e:
        print(f"⚠️ Could not update .gitignore: {e}")

def create_clean_structure():
    """Create clean directory structure for GitHub catalog"""
    print("🏗️ Creating clean directory structure...")
    
    directories = [
        "catalog",
        "catalog/products", 
        "catalog/products/solar-panels",
        "catalog/products/postcards",
        "catalog/products/electronics",
        "catalog/exports",
        "catalog/templates",
        "docs"
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"  📁 Created: {directory}/")
    
    print("✅ Clean directory structure created")

def main():
    """Main cleanup function"""
    print("🚀 CODEBASE CLEANUP & GITHUB CATALOG PREPARATION")
    print("=" * 60)
    
    try:
        cleanup_redundant_files()
        print()
        
        organize_logs()
        print()
        
        create_archive_directory()
        print()
        
        update_gitignore()
        print()
        
        create_clean_structure()
        print()
        
        print("🎉 CLEANUP COMPLETE!")
        print("✅ Redundant files removed")
        print("✅ Logs organized")
        print("✅ Old versions archived")
        print("✅ Security improved")
        print("✅ GitHub catalog structure ready")
        print()
        print("🔒 SECURITY REMINDER:")
        print("  • Rotate your OpenAI API key (exposed key removed from config)")
        print("  • Add your new API key to config/settings.json")
        print("  • Never commit API keys to git again")
        print()
        print("🚀 Ready for GitHub catalog implementation!")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
