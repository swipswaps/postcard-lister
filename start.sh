#!/bin/bash

# Solar Panel Catalog - Material UI Edition
# Automated startup script

echo "🌞 Solar Panel Catalog - Material UI Edition"
echo "=============================================="
echo ""

# Check if ports are in use
if lsof -Pi :8081 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  WARNING: Port 8081 is already in use (WebSocket server)"
    echo "   You may need to kill existing processes:"
    echo "   pkill -f github_cli_server"
    echo ""
fi

if lsof -Pi :3001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  WARNING: Port 3001 is already in use (React frontend)"
    echo "   The React app will ask to use a different port"
    echo ""
fi

echo "🚀 Starting Material UI Solar Panel Catalog..."
echo ""
echo "📋 INSTRUCTIONS:"
echo "   1. This script will open TWO terminal windows"
echo "   2. Keep BOTH terminals running"
echo "   3. Your browser will open automatically to http://localhost:3001"
echo "   4. Use Ctrl+C in each terminal to stop the servers"
echo ""

# Check if we're in a desktop environment
if [ -n "$DISPLAY" ] || [ -n "$WAYLAND_DISPLAY" ]; then
    echo "🖥️  Desktop environment detected - opening terminal windows..."
    
    # Start WebSocket server in new terminal
    if command -v gnome-terminal >/dev/null 2>&1; then
        gnome-terminal --title="🔧 WebSocket Server" -- bash -c "
            echo '🔧 Starting WebSocket Server...'
            echo '🌞 Solar Panel Catalog - GitHub CLI WebSocket Server'
            echo '============================================================'
            echo '🔧 Features: GitHub CLI primary, git fallback, verbatim logging'
            echo '📊 Provides: Real gh CLI output, tee pattern capture, evidence'
            echo '============================================================'
            cd websocket && python3 github_cli_server.py
            echo 'Press Enter to close this terminal...'
            read
        " &
        
        # Start React frontend in new terminal
        gnome-terminal --title="⚛️  React Frontend" -- bash -c "
            echo '⚛️  Starting React Frontend...'
            echo '🌞 Solar Panel Catalog - Material UI Frontend'
            echo '============================================='
            echo '🎨 Features: Material UI, WebSocket integration, GitHub upload'
            echo '🌐 Will be available at: http://localhost:3001'
            echo '============================================='
            cd frontend && PORT=3001 npm start
            echo 'Press Enter to close this terminal...'
            read
        " &
        
    elif command -v konsole >/dev/null 2>&1; then
        konsole --title "🔧 WebSocket Server" -e bash -c "
            echo '🔧 Starting WebSocket Server...'
            cd websocket && python3 github_cli_server.py
            echo 'Press Enter to close this terminal...'
            read
        " &
        
        konsole --title "⚛️  React Frontend" -e bash -c "
            echo '⚛️  Starting React Frontend...'
            cd frontend && PORT=3001 npm start
            echo 'Press Enter to close this terminal...'
            read
        " &
        
    elif command -v xterm >/dev/null 2>&1; then
        xterm -title "🔧 WebSocket Server" -e bash -c "
            echo '🔧 Starting WebSocket Server...'
            cd websocket && python3 github_cli_server.py
            echo 'Press Enter to close this terminal...'
            read
        " &
        
        xterm -title "⚛️  React Frontend" -e bash -c "
            echo '⚛️  Starting React Frontend...'
            cd frontend && PORT=3001 npm start
            echo 'Press Enter to close this terminal...'
            read
        " &
    else
        echo "❌ No supported terminal emulator found"
        echo "   Please install gnome-terminal, konsole, or xterm"
        exit 1
    fi
    
    echo "✅ Terminal windows opened!"
    
    # Wait a moment for servers to start
    sleep 3
    
    # Open browser
    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open http://localhost:3001 >/dev/null 2>&1 &
    elif command -v firefox >/dev/null 2>&1; then
        firefox http://localhost:3001 >/dev/null 2>&1 &
    elif command -v google-chrome >/dev/null 2>&1; then
        google-chrome http://localhost:3001 >/dev/null 2>&1 &
    fi
    
else
    echo "🖥️  No desktop environment detected - manual startup required"
    echo ""
    echo "📋 Manual startup instructions:"
    echo "   1. Open terminal 1: cd websocket && python3 github_cli_server.py"
    echo "   2. Open terminal 2: cd frontend && PORT=3001 npm start"
    echo "   3. Open browser to: http://localhost:3001"
    exit 0
fi

echo ""
echo "🌐 Your application will be available at:"
echo "   Frontend: http://localhost:3001"
echo "   WebSocket: ws://localhost:8081"
echo ""
echo "🎯 GitHub upload functionality is ready to use!"
echo ""
echo "📚 For more information, see README.md"
echo "🆘 For troubleshooting, check the README.md troubleshooting section"
echo ""
echo "🎉 Material UI Solar Panel Catalog setup complete!"
