#!/usr/bin/env python3
################################################################################
# FILE: debug_github_auth.py
# DESC: Debug GitHub authentication issues
# WHAT: Test GitHub token and diagnose authentication problems
# WHY: Troubleshoot GitHub API access issues
################################################################################

import requests
import json
import sys

def test_github_token(token):
    """
    WHAT: Test GitHub token authentication and permissions
    WHY: Diagnose authentication issues with verbatim API responses
    """
    print("🔍 GITHUB TOKEN AUTHENTICATION DEBUG")
    print("=" * 50)
    
    # Test basic authentication
    print("1. Testing basic authentication...")
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Solar-Panel-Catalog-System'
    }
    
    try:
        response = requests.get('https://api.github.com/user', headers=headers)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"   ✅ Authentication successful!")
            print(f"   👤 Username: {user_data.get('login')}")
            print(f"   📧 Email: {user_data.get('email', 'Not public')}")
            print(f"   🏢 Company: {user_data.get('company', 'None')}")
        else:
            print(f"   ❌ Authentication failed!")
            print(f"   📋 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return False
    
    # Test token scopes (handle both classic and fine-grained PATs)
    print("\n2. Checking token scopes/permissions...")
    scopes = response.headers.get('X-OAuth-Scopes', '')
    print(f"   📋 Current scopes: {scopes}")

    if scopes == '':
        print("   🔎 Fine-grained PAT detected – scopes header empty")
        print("   📋 Checking repository-level permissions instead...")

        # For fine-grained PATs, we need to check repository permissions
        # This is done by testing actual repository operations
        print("   💡 Fine-grained PATs use repository-level permissions:")
        print("      • Contents: Read & Write (for push/pull)")
        print("      • Actions: Write (for workflows)")
        print("   ✅ Will test actual repository access below...")

    else:
        print("   🔎 Classic PAT detected – checking global scopes...")
        required_scopes = ['repo', 'workflow']
        missing_scopes = []

        for scope in required_scopes:
            if scope in scopes:
                print(f"   ✅ {scope} - Available")
            else:
                print(f"   ❌ {scope} - Missing")
                missing_scopes.append(scope)

        if missing_scopes:
            print(f"\n   ⚠️ Missing required scopes: {missing_scopes}")
            print("   💡 Go to https://github.com/settings/tokens")
            print("   💡 Edit your token and add missing scopes")
            return False
    
    # Test repository access
    print("\n3. Testing repository access...")
    
    # Get user's repositories
    try:
        repos_response = requests.get('https://api.github.com/user/repos', headers=headers)
        if repos_response.status_code == 200:
            repos = repos_response.json()
            print(f"   ✅ Can access repositories ({len(repos)} found)")
            
            # Show first few repos
            for repo in repos[:3]:
                print(f"   📁 {repo['full_name']} - {repo['permissions']}")
        else:
            print(f"   ❌ Cannot access repositories: {repos_response.status_code}")
            print(f"   📋 Response: {repos_response.text}")
            
    except Exception as e:
        print(f"   ❌ Repository access test failed: {e}")
    
    # Test specific repository (if provided)
    print("\n4. Testing postcard-lister repository access...")
    try:
        repo_url = 'https://api.github.com/repos/swipswaps/postcard-lister'
        repo_response = requests.get(repo_url, headers=headers)

        print(f"   Status Code: {repo_response.status_code}")

        if repo_response.status_code == 200:
            repo_data = repo_response.json()
            print(f"   ✅ Repository accessible!")
            print(f"   📁 Name: {repo_data['full_name']}")
            print(f"   🔒 Private: {repo_data['private']}")

            permissions = repo_data.get('permissions', {})
            print(f"   📝 Permissions:")
            print(f"      • Read: {permissions.get('pull', False)}")
            print(f"      • Write: {permissions.get('push', False)}")
            print(f"      • Admin: {permissions.get('admin', False)}")

            # Check if we have the required permissions for fine-grained PATs
            if not permissions.get('push', False):
                print(f"   ⚠️ Missing 'push' permission - needed for uploads")
                print(f"   💡 For fine-grained PATs: Set 'Contents' to 'Read & Write'")

        elif repo_response.status_code == 404:
            print(f"   ❌ Repository not found or no access")
            print(f"   💡 Check repository name and permissions")
        else:
            print(f"   ❌ Repository access failed")
            print(f"   📋 Response: {repo_response.text}")

    except Exception as e:
        print(f"   ❌ Repository test failed: {e}")

    # Test repository contents access (for fine-grained PATs)
    print("\n5. Testing repository contents access...")
    try:
        contents_url = 'https://api.github.com/repos/swipswaps/postcard-lister/contents'
        contents_response = requests.get(contents_url, headers=headers)

        print(f"   Status Code: {contents_response.status_code}")

        if contents_response.status_code == 200:
            print(f"   ✅ Can read repository contents")
            contents = contents_response.json()
            print(f"   📁 Files/folders found: {len(contents)}")
        elif contents_response.status_code == 403:
            print(f"   ❌ Forbidden - insufficient permissions")
            print(f"   💡 For fine-grained PATs: Set 'Contents' to 'Read & Write'")
        else:
            print(f"   ❌ Contents access failed: {contents_response.status_code}")

    except Exception as e:
        print(f"   ❌ Contents test failed: {e}")
    
    return True

def test_git_authentication(token):
    """Test git command line authentication"""
    print("\n6. Testing git command line authentication...")
    
    import subprocess
    import os
    
    # Set up git credentials
    env = os.environ.copy()
    env['GH_TOKEN'] = token
    
    try:
        # Test git ls-remote
        result = subprocess.run([
            'git', 'ls-remote', 'https://github.com/swipswaps/postcard-lister.git'
        ], capture_output=True, text=True, env=env, timeout=10)
        
        print(f"   Git ls-remote exit code: {result.returncode}")
        
        if result.returncode == 0:
            print(f"   ✅ Git authentication successful!")
            print(f"   📋 Remote refs found: {len(result.stdout.split())//2}")
        else:
            print(f"   ❌ Git authentication failed!")
            print(f"   📋 Error: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print(f"   ⏰ Git command timed out")
    except Exception as e:
        print(f"   ❌ Git test failed: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 debug_github_auth.py <github_token>")
        print("Example: python3 debug_github_auth.py github_pat_11ADTE7IQ0...")
        sys.exit(1)
    
    token = sys.argv[1]
    
    # Remove any quotes or prefixes
    token = token.strip().strip('"').strip("'")
    
    print(f"🔧 Testing token: {token[:20]}...")
    print()
    
    if test_github_token(token):
        test_git_authentication(token)
        print("\n🎉 GitHub authentication debugging complete!")
    else:
        print("\n❌ GitHub authentication failed!")
        print("\n💡 Common solutions:")
        print("   1. Check token scopes at https://github.com/settings/tokens")
        print("   2. Ensure 'repo' and 'workflow' scopes are enabled")
        print("   3. Check if token has expired")
        print("   4. Verify repository access permissions")

if __name__ == "__main__":
    main()
