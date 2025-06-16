import PyInstaller.__main__
import os
import shutil

# Create a temporary directory for the build
if os.path.exists('build'):
    shutil.rmtree('build')
if os.path.exists('dist'):
    shutil.rmtree('dist')

# Define the files to include
datas = [
    ('data', 'data'),
    ('config/settings.template.json', 'config'),
]

# Create the spec file content
spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas={datas},
    hiddenimports=[],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PostcardLister',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico'  # Optional: Add this if you have an icon
)
"""

# Write the spec file
with open('PostcardLister.spec', 'w') as f:
    f.write(spec_content)

# Run PyInstaller
PyInstaller.__main__.run([
    'PostcardLister.spec',
    '--clean',
    '--noconfirm'
])

# Clean up
if os.path.exists('PostcardLister.spec'):
    os.remove('PostcardLister.spec') 