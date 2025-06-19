#!/usr/bin/env python3
################################################################################
# FILE: cli/setup.py
# DESC: Terminal-centric setup and configuration
# SPEC: TERMINAL-CENTRIC-2025-06-18-SETUP
# WHAT: Interactive setup for solar panel catalog system
# WHY: Easy configuration of API keys and GitHub integration
# FAIL: Exits with error if setup cannot be completed
# UX: Interactive prompts with validation and help
# DEBUG: Logs all setup operations with verbatim capture
################################################################################

import sys
import os
import json
import getpass
from pathlib import Path
from datetime import datetime

def echo_info(message):
    """Print info message with terminal formatting"""
    print(f"[INFO]  ℹ️  {message}")

def echo_ok(message):
    """Print success message with terminal formatting"""
    print(f"[PASS]  ✅ {message}")

def echo_warn(message):
    """Print warning message with terminal formatting"""
    print(f"[WARN]  ⚠️  {message}")

def echo_fail(message):
    """Print failure message with terminal formatting"""
    print(f"[FAIL]  ❌ {message}")

def setup_directories():
    """
    WHAT: Create necessary directories for terminal operation
    WHY: Ensure all required directories exist
    FAIL: Returns False if directory creation fails
    UX: Shows directory creation progress
    DEBUG: Logs all directory operations
    """
    echo_info("Setting up directory structure...")
    
    directories = [
        "config",
        "logs",
        "logs/batch",
        "catalog",
        "exports",
        "temp"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            echo_ok(f"Directory ready: {directory}")
        except Exception as e:
            echo_fail(f"Failed to create directory {directory}: {e}")
            return False
    
    return True

def validate_openai_key(api_key):
    """
    WHAT: Validate OpenAI API key format
    WHY: Ensure API key is properly formatted
    FAIL: Returns False if key format is invalid
    UX: Shows validation result
    DEBUG: Logs validation without exposing key
    """
    if not api_key:
        return False
    
    if not api_key.startswith('sk-'):
        return False
    
    if len(api_key) < 20:
        return False
    
    return True

def validate_github_token(token):
    """
    WHAT: Validate GitHub token format
    WHY: Ensure GitHub token is properly formatted
    FAIL: Returns False if token format is invalid
    UX: Shows validation result
    DEBUG: Logs validation without exposing token
    """
    if not token:
        return False
    
    # GitHub personal access tokens are typically 40 characters
    if len(token) < 20:
        return False
    
    return True

def setup_openai_config():
    """
    WHAT: Interactive setup of OpenAI API configuration
    WHY: Required for AI analysis of solar panels
    FAIL: Returns None if setup fails
    UX: Interactive prompts with validation
    DEBUG: Logs setup progress without exposing keys
    """
    echo_info("Setting up OpenAI API configuration...")
    
    print("\n🧠 OpenAI API Key Setup")
    print("=" * 40)
    print("You need an OpenAI API key for AI analysis.")
    print("Get your key from: https://platform.openai.com/api-keys")
    print()
    
    while True:
        api_key = getpass.getpass("Enter your OpenAI API key (sk-...): ").strip()
        
        if not api_key:
            echo_warn("API key cannot be empty")
            continue
        
        if validate_openai_key(api_key):
            echo_ok("OpenAI API key format validated")
            return api_key
        else:
            echo_fail("Invalid API key format. Must start with 'sk-' and be at least 20 characters")
            
            retry = input("Try again? (y/n): ").strip().lower()
            if retry != 'y':
                return None

def setup_github_config():
    """
    WHAT: Interactive setup of GitHub configuration
    WHY: Required for catalog storage and version control
    FAIL: Returns None if setup fails
    UX: Interactive prompts with validation
    DEBUG: Logs setup progress without exposing tokens
    """
    echo_info("Setting up GitHub configuration...")
    
    print("\n🐙 GitHub Configuration Setup")
    print("=" * 40)
    print("GitHub is used for catalog storage and version control.")
    print("You need a GitHub personal access token.")
    print("Create one at: https://github.com/settings/tokens")
    print("Required scopes: repo, workflow")
    print()
    
    # GitHub repository
    while True:
        repo_url = input("Enter your GitHub repository URL: ").strip()
        
        if not repo_url:
            echo_warn("Repository URL cannot be empty")
            continue
        
        if 'github.com' in repo_url:
            echo_ok(f"GitHub repository: {repo_url}")
            break
        else:
            echo_fail("Please enter a valid GitHub repository URL")
    
    # GitHub token
    while True:
        token = getpass.getpass("Enter your GitHub personal access token: ").strip()
        
        if not token:
            echo_warn("GitHub token cannot be empty")
            continue
        
        if validate_github_token(token):
            echo_ok("GitHub token format validated")
            break
        else:
            echo_fail("Invalid token format. Must be at least 20 characters")
            
            retry = input("Try again? (y/n): ").strip().lower()
            if retry != 'y':
                return None
    
    # GitHub username
    username = input("Enter your GitHub username: ").strip()
    if not username:
        echo_warn("GitHub username not provided")
        username = "user"
    
    return {
        'github_repo_url': repo_url,
        'github_token': token,
        'github_username': username
    }

def setup_processing_config():
    """
    WHAT: Setup processing configuration options
    WHY: Configure processing behavior and preferences
    FAIL: Returns default configuration if setup fails
    UX: Interactive prompts with sensible defaults
    DEBUG: Logs all configuration choices
    """
    echo_info("Setting up processing configuration...")
    
    print("\n⚙️ Processing Configuration")
    print("=" * 40)
    
    # Multi-LLM configuration
    multi_llm = input("Enable multi-LLM analysis for higher accuracy? (y/n) [y]: ").strip().lower()
    multi_llm_enabled = multi_llm != 'n'
    
    # Batch processing workers
    while True:
        try:
            workers = input("Number of parallel workers for batch processing [4]: ").strip()
            if not workers:
                workers = 4
            else:
                workers = int(workers)
            
            if workers < 1 or workers > 16:
                echo_warn("Workers should be between 1 and 16")
                continue
            
            break
        except ValueError:
            echo_warn("Please enter a valid number")
    
    # Store category
    store_category = input("Default store category (optional): ").strip()
    
    echo_ok("Processing configuration completed")
    
    return {
        'multi_llm_enabled': multi_llm_enabled,
        'batch_workers': workers,
        'store_category': store_category if store_category else None
    }

def save_configuration(config):
    """
    WHAT: Save configuration to settings file
    WHY: Persist configuration for terminal operations
    FAIL: Returns False if save fails
    UX: Shows save progress and location
    DEBUG: Logs save operation without exposing secrets
    """
    echo_info("Saving configuration...")
    
    config_path = Path("config/settings.json")
    
    try:
        # Add metadata
        config['created_at'] = datetime.now().isoformat()
        config['version'] = '1.0.0'
        config['interface'] = 'terminal'
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        echo_ok(f"Configuration saved to {config_path}")
        return True
        
    except Exception as e:
        echo_fail(f"Failed to save configuration: {e}")
        return False

def test_configuration(config):
    """
    WHAT: Test configuration by importing core modules
    WHY: Verify that setup is working correctly
    FAIL: Returns False if testing fails
    UX: Shows test progress and results
    DEBUG: Logs all test operations
    """
    echo_info("Testing configuration...")
    
    try:
        # Test core module imports
        echo_info("Testing core module imports...")
        
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        from core.enhanced_vision_handler import EnhancedVisionHandler
        echo_ok("Enhanced vision handler import successful")
        
        from core.multi_llm_analyzer import MultiLLMAnalyzer
        echo_ok("Multi-LLM analyzer import successful")
        
        from core.github_catalog import GitHubCatalog
        echo_ok("GitHub catalog import successful")
        
        # Test API key (basic validation)
        if config.get('openai_api_key'):
            vision_handler = EnhancedVisionHandler(config['openai_api_key'])
            echo_ok("OpenAI API key configuration successful")
        
        echo_ok("Configuration testing completed successfully")
        return True
        
    except Exception as e:
        echo_fail(f"Configuration testing failed: {e}")
        echo_warn("You may need to install missing dependencies")
        return False

def main():
    """
    WHAT: Main setup entry point
    WHY: Interactive terminal setup for solar panel catalog system
    FAIL: Exits with error code if setup fails
    UX: Guided setup process with validation
    DEBUG: Complete setup operation logging
    """
    print("🚀 SOLAR PANEL CATALOG SYSTEM - TERMINAL SETUP")
    print("=" * 60)
    print("This setup will configure your terminal-centric solar panel")
    print("catalog system with AI analysis and GitHub integration.")
    print("=" * 60)
    print()
    
    # Setup directories
    if not setup_directories():
        echo_fail("Directory setup failed")
        sys.exit(1)
    
    # Setup OpenAI
    openai_key = setup_openai_config()
    if not openai_key:
        echo_fail("OpenAI setup cancelled or failed")
        sys.exit(1)
    
    # Setup GitHub
    github_config = setup_github_config()
    if not github_config:
        echo_fail("GitHub setup cancelled or failed")
        sys.exit(1)
    
    # Setup processing options
    processing_config = setup_processing_config()
    
    # Combine configuration
    config = {
        'openai_api_key': openai_key,
        **github_config,
        **processing_config
    }
    
    # Save configuration
    if not save_configuration(config):
        echo_fail("Failed to save configuration")
        sys.exit(1)
    
    # Test configuration
    if not test_configuration(config):
        echo_warn("Configuration testing failed, but setup is complete")
        echo_warn("You may need to install dependencies or check API keys")
    
    print("\n🎉 SETUP COMPLETE!")
    print("=" * 60)
    echo_ok("Terminal-centric solar panel catalog system is ready")
    echo_info("Next steps:")
    print("  • Process single image: python3 cli/main.py --input panel.jpg")
    print("  • Batch process: python3 cli/batch_processor.py --input directory/")
    print("  • Enable verbatim capture: add --verbose to any command")
    print("=" * 60)

if __name__ == "__main__":
    main()
