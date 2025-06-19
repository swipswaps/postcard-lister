# 🌞 Solar Panel Catalog - Material UI Edition

A modern web application for processing and cataloging solar panels with automated GitHub integration. Features a Material UI interface with real-time WebSocket communication and proven GitHub upload functionality.

## 🚀 Quick Start

**One-command startup** (recommended):
```bash
./start.sh
```

This automatically:
- ✅ Opens two terminal windows (WebSocket server + React frontend)
- ✅ Starts both services with proper configuration
- ✅ Opens your browser to http://localhost:3001
- ✅ Provides full GitHub upload functionality

## 🔧 Manual Setup (if needed)

1. **Clone and setup**:
```bash
git clone https://github.com/swipswaps/postcard-lister.git
cd postcard-lister
```

2. **Install dependencies**:
```bash
# Frontend dependencies
cd frontend && npm install && cd ..

# Backend dependencies (if using Python features)
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Configure GitHub token** (for upload functionality):
```bash
# Create .env.local file with your GitHub token
echo "GH_TOKEN=your_github_token_here" > .env.local
```

## 🎯 Manual Startup (alternative)

If `./start.sh` doesn't work, start manually:

**Terminal 1 - WebSocket Server:**
```bash
cd websocket && python3 github_cli_server.py
```

**Terminal 2 - React Frontend:**
```bash
cd frontend && PORT=3001 npm start
```

**Then open:** http://localhost:3001

## ✨ Features

- 🎨 **Material UI Interface** - Modern, responsive web design
- 🔄 **Real-time WebSocket** - Live communication between frontend and backend
- 📤 **GitHub Integration** - Direct upload to GitHub with full network visibility
- 🌞 **Solar Panel Processing** - Specialized for solar panel catalog management
- 📱 **Android-style Layout** - Mobile-friendly interface design
- 🔍 **Verbatim Logging** - Complete system message capture for troubleshooting
- ⚡ **Simple GitHub Push** - Use `./simple_github_push.sh "message"` for direct uploads

## 🛠️ GitHub Upload

**Simple command-line upload:**
```bash
./simple_github_push.sh "Your commit message"
```

This script provides:
- ✅ Full network message visibility
- ✅ Proven git commands (no over-engineering)
- ✅ Complete success/failure feedback
- ✅ Automatic token management

## 📋 System Requirements

- **Node.js** 16+ (for React frontend)
- **Python** 3.8+ (for WebSocket server)
- **Git** (for GitHub integration)
- **Modern browser** (Chrome, Firefox, Safari, Edge)

## 🌐 Architecture

- **Frontend**: React with Material UI (port 3001)
- **Backend**: Python WebSocket server (port 8081)
- **GitHub**: Direct integration with proven git commands
- **Logging**: Complete verbatim system message capture

## 🆘 Troubleshooting

**Port conflicts:**
```bash
# Kill existing processes
pkill -f github_cli_server
pkill -f "react-scripts"
```

**GitHub upload issues:**
- Check `.env.local` has valid `GH_TOKEN`
- Use `./simple_github_push.sh` for direct upload with full error visibility
- All network messages are shown for easy debugging

**Browser connection issues:**
- Ensure both servers are running (check terminal outputs)
- Try refreshing browser or clearing cache
- Check http://localhost:3001 and ws://localhost:8081

## 📄 License

GNU GENERAL PUBLIC LICENSE v3.0

## 🎯 Status

✅ **Working System** - Material UI interface with proven GitHub integration
✅ **Simple Startup** - One command: `./start.sh`
✅ **Full Network Visibility** - All system messages displayed for troubleshooting
✅ **Proven Approach** - Uses standard git commands, no over-engineering
