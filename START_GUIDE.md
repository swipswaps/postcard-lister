# 🚀 HOW TO START YOUR SOLAR PANEL CATALOG TOOL

## 🎯 **Quick Start Options**

### **Option 1: Enhanced Terminal GUI (Recommended)**
```bash
cd /home/owner/Documents/68507cb0-f268-8008-898e-60359398f149/postcard-lister
python3 run_tui.py
```
**Features:** Visual forms, image browser, clipboard support, GitHub upload

### **Option 2: Material UI Web Interface**
```bash
# Terminal 1: Start WebSocket bridge
python3 websocket/server.py

# Terminal 2: Start React frontend
cd frontend && npm start

# Open browser: http://localhost:3000
```
**Features:** Web-based interface, real-time updates, mobile-friendly

### **Option 3: Simple Wrapper Scripts**
```bash
# Process single solar panel
./process_solar_panel.sh solar_panel.jpg

# Batch process directory
./batch_process.sh solar_inventory/

# Test GitHub connection
./test_github.sh
```
**Features:** One-command processing, automatic logging

### **Option 4: Direct CLI Commands**
```bash
# Single panel processing
python3 cli/main.py --input solar_panel.jpg --verbose --github-upload

# Batch processing
python3 cli/batch_processor.py --input solar_inventory/ --workers 8 --verbose
```
**Features:** Maximum control, scriptable, automation-friendly

## 🛡️ **Redundant System Hardening**

### **WebSocket Resilience:**
- **Auto-restart** on connection failure
- **Fallback to polling** if WebSocket fails
- **Local storage backup** for offline work
- **Terminal interface** always available

### **Material UI Hardening:**
- **Service worker** for offline capability
- **Local state persistence** in browser
- **Graceful degradation** to basic HTML
- **Terminal fallback** commands displayed

## 📋 **Terminal Copy/Paste Commands**

### **Linux (X11):**
```bash
# Copy to clipboard
echo "content" | xclip -selection clipboard

# Paste from clipboard
xclip -selection clipboard -o

# Copy file path
echo "/path/to/file" | xclip -selection clipboard
```

### **Linux (Wayland):**
```bash
# Copy to clipboard
echo "content" | wl-copy

# Paste from clipboard
wl-paste
```

### **macOS:**
```bash
# Copy to clipboard
echo "content" | pbcopy

# Paste from clipboard
pbpaste
```

## 🔧 **System Health Check**
```bash
# Check all systems
python3 run_terminal_system.py --check

# Verify dependencies
python3 -c "import rich, PIL, requests; print('✅ All dependencies OK')"

# Test GitHub connection
python3 debug_github_auth.py "your_github_token"
```
