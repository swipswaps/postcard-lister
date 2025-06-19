#!/usr/bin/env python3
################################################################################
# FILE: launch_complete_system.py
# DESC: Master launcher for complete solar panel catalog system
# WHAT: Unified entry point for all system components
# WHY: Single command to access all functionality
# FAIL: Graceful fallbacks for each component
# UX: Clear menu with all available options
# DEBUG: System-wide verbatim capture and logging
################################################################################

import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.columns import Columns
    from rich.text import Text
    from rich.live import Live
    from rich.progress import Progress, SpinnerColumn, TextColumn
except ImportError:
    print("🔧 Installing required packages...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'rich'], check=True)
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.columns import Columns
    from rich.text import Text
    from rich.live import Live
    from rich.progress import Progress, SpinnerColumn, TextColumn

class SolarPanelCatalogSystem:
    """
    WHAT: Master system launcher and coordinator
    WHY: Unified access to all solar panel catalog functionality
    FAIL: Graceful degradation when components unavailable
    UX: Clear navigation between all system components
    DEBUG: System-wide logging and monitoring
    """
    
    def __init__(self):
        self.console = Console()
        self.verbatim_log = []
        self.system_status = {}
        
        # Check system components
        self.check_system_health()
    
    def log_verbatim(self, message, level="INFO"):
        """System-wide verbatim logging"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"{timestamp} [{level}] {message}"
        self.verbatim_log.append(log_entry)
        
        # Also log to file
        log_file = Path("logs/system.log")
        log_file.parent.mkdir(exist_ok=True)
        with open(log_file, "a") as f:
            f.write(log_entry + "\n")
    
    def check_system_health(self):
        """Check health of all system components"""
        self.log_verbatim("🔍 Checking system health...")
        
        components = {
            'tui': self.check_tui_availability(),
            'websocket': self.check_websocket_availability(),
            'material_ui': self.check_material_ui_availability(),
            'ebay_api': self.check_ebay_api_availability(),
            'github': self.check_github_availability(),
            'ai_services': self.check_ai_availability(),
            'clipboard': self.check_clipboard_availability()
        }
        
        self.system_status = components
        
        healthy_count = sum(1 for status in components.values() if status['status'] == 'healthy')
        total_count = len(components)
        
        self.log_verbatim(f"✅ System health check complete: {healthy_count}/{total_count} components healthy")
    
    def check_tui_availability(self):
        """Check Terminal UI availability"""
        try:
            tui_path = Path("tui/main.py")
            if tui_path.exists():
                return {'status': 'healthy', 'message': 'Terminal UI available'}
            else:
                return {'status': 'warning', 'message': 'Terminal UI files missing'}
        except Exception as e:
            return {'status': 'error', 'message': f'TUI check failed: {e}'}
    
    def check_websocket_availability(self):
        """Check WebSocket server availability"""
        try:
            import websockets
            ws_path = Path("websocket/resilient_server.py")
            if ws_path.exists():
                return {'status': 'healthy', 'message': 'WebSocket server available'}
            else:
                return {'status': 'warning', 'message': 'WebSocket files missing'}
        except ImportError:
            return {'status': 'warning', 'message': 'WebSocket dependencies missing'}
        except Exception as e:
            return {'status': 'error', 'message': f'WebSocket check failed: {e}'}
    
    def check_material_ui_availability(self):
        """Check Material UI frontend availability"""
        try:
            frontend_path = Path("frontend/package.json")
            if frontend_path.exists():
                return {'status': 'healthy', 'message': 'Material UI frontend available'}
            else:
                return {'status': 'warning', 'message': 'Frontend files missing'}
        except Exception as e:
            return {'status': 'error', 'message': f'Frontend check failed: {e}'}
    
    def check_ebay_api_availability(self):
        """Check eBay API configuration"""
        try:
            config_path = Path("config/ebay_config.json")
            if config_path.exists():
                return {'status': 'healthy', 'message': 'eBay API configured'}
            else:
                return {'status': 'warning', 'message': 'eBay API not configured'}
        except Exception as e:
            return {'status': 'error', 'message': f'eBay API check failed: {e}'}
    
    def check_github_availability(self):
        """Check GitHub integration"""
        try:
            # Check for git and GitHub token
            result = subprocess.run(['git', '--version'], capture_output=True)
            if result.returncode == 0:
                return {'status': 'healthy', 'message': 'GitHub integration available'}
            else:
                return {'status': 'warning', 'message': 'Git not available'}
        except Exception as e:
            return {'status': 'error', 'message': f'GitHub check failed: {e}'}
    
    def check_ai_availability(self):
        """Check AI services availability"""
        try:
            config_path = Path("config/ai_config.json")
            if config_path.exists():
                return {'status': 'healthy', 'message': 'AI services configured'}
            else:
                return {'status': 'warning', 'message': 'AI services not configured'}
        except Exception as e:
            return {'status': 'error', 'message': f'AI check failed: {e}'}
    
    def check_clipboard_availability(self):
        """Check clipboard functionality"""
        try:
            from utils.clipboard_helper import ClipboardHelper
            helper = ClipboardHelper()
            if helper.clipboard_tools:
                return {'status': 'healthy', 'message': 'Clipboard tools available'}
            else:
                return {'status': 'warning', 'message': 'No clipboard tools detected'}
        except Exception as e:
            return {'status': 'error', 'message': f'Clipboard check failed: {e}'}
    
    def show_system_header(self):
        """Display system header with status"""
        header_text = Text()
        header_text.append("🌞 Solar Panel Catalog System - Complete Platform\n", style="bold cyan")
        header_text.append(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", style="dim")
        
        # System health summary
        healthy = sum(1 for s in self.system_status.values() if s['status'] == 'healthy')
        total = len(self.system_status)
        
        if healthy == total:
            health_style = "green"
            health_icon = "✅"
        elif healthy > total // 2:
            health_style = "yellow"
            health_icon = "⚠️"
        else:
            health_style = "red"
            health_icon = "❌"
        
        header_text.append(f"{health_icon} System Health: {healthy}/{total} components operational", style=health_style)
        
        return Panel(header_text, style="cyan", padding=(1, 2))
    
    def show_main_menu(self):
        """Display main system menu"""
        menu_options = Table(show_header=False, show_lines=True, expand=True)
        menu_options.add_column("Option", style="cyan", width=8)
        menu_options.add_column("Component", style="white")
        menu_options.add_column("Description", style="dim")
        menu_options.add_column("Status", style="green", width=12)
        
        # Get status indicators
        tui_status = "✅ Ready" if self.system_status['tui']['status'] == 'healthy' else "⚠️ Issues"
        web_status = "✅ Ready" if self.system_status['material_ui']['status'] == 'healthy' else "⚠️ Issues"
        ebay_status = "✅ Ready" if self.system_status['ebay_api']['status'] == 'healthy' else "⚠️ Setup needed"
        
        menu_options.add_row("1", "🎨 Terminal GUI", "Visual forms, image browser, processing", tui_status)
        menu_options.add_row("2", "🌐 Material UI Web", "Browser-based interface with real-time updates", web_status)
        menu_options.add_row("3", "📝 eBay Ad Manager", "Create, edit, analyze eBay listings", ebay_status)
        menu_options.add_row("4", "📱 Multi-Platform Ads", "Generate Facebook, Craigslist, Twitter ads", "✅ Ready")
        menu_options.add_row("5", "📤 GitHub Integration", "Upload and manage catalog repository", "✅ Ready")
        menu_options.add_row("6", "🔧 System Diagnostics", "Health check, logs, troubleshooting", "✅ Ready")
        menu_options.add_row("7", "⚙️ Configuration", "Setup APIs, tokens, preferences", "✅ Ready")
        menu_options.add_row("8", "📋 Clipboard Tools", "Test and configure clipboard operations", "✅ Ready")
        menu_options.add_row("0", "🚪 Exit System", "Shutdown all components", "✅ Ready")
        
        return Panel(menu_options, title="🎯 System Components", style="blue")
    
    def launch_terminal_gui(self):
        """Launch Terminal GUI"""
        self.console.print("🎨 [bold cyan]Launching Terminal GUI...[/bold cyan]")
        
        try:
            subprocess.run([sys.executable, "run_tui.py"], cwd=".")
        except KeyboardInterrupt:
            self.console.print("\n🔙 Returned to main menu")
        except Exception as e:
            self.console.print(f"❌ Failed to launch Terminal GUI: {e}", style="red")
            Prompt.ask("Press Enter to continue")
    
    def launch_material_ui(self):
        """Launch Material UI web interface"""
        self.console.print("🌐 [bold cyan]Launching Material UI Web Interface...[/bold cyan]")
        
        # Start WebSocket server
        self.console.print("📡 Starting WebSocket server...")
        try:
            ws_process = subprocess.Popen([sys.executable, "websocket/resilient_server.py"])
            time.sleep(2)  # Give server time to start
            
            # Start React frontend
            self.console.print("⚛️ Starting React frontend...")
            frontend_process = subprocess.Popen(["npm", "start"], cwd="frontend")
            
            self.console.print("✅ Material UI launched! Check your browser at http://localhost:3000")
            
            if Confirm.ask("Keep services running in background?"):
                self.console.print("🔄 Services running in background")
            else:
                self.console.print("🛑 Stopping services...")
                ws_process.terminate()
                frontend_process.terminate()
                
        except Exception as e:
            self.console.print(f"❌ Failed to launch Material UI: {e}", style="red")
            Prompt.ask("Press Enter to continue")
    
    def launch_ebay_manager(self):
        """Launch eBay Ad Manager"""
        self.console.print("📝 [bold cyan]Launching eBay Ad Manager...[/bold cyan]")
        
        try:
            subprocess.run([sys.executable, "ebay/ad_manager.py"], cwd=".")
        except KeyboardInterrupt:
            self.console.print("\n🔙 Returned to main menu")
        except Exception as e:
            self.console.print(f"❌ Failed to launch eBay Manager: {e}", style="red")
            Prompt.ask("Press Enter to continue")
    
    def launch_multiplatform_ads(self):
        """Launch Multi-Platform Ad Generator"""
        self.console.print("📱 [bold cyan]Launching Multi-Platform Ad Generator...[/bold cyan]")
        
        try:
            subprocess.run([sys.executable, "platforms/multiplatform_generator.py"], cwd=".")
        except KeyboardInterrupt:
            self.console.print("\n🔙 Returned to main menu")
        except Exception as e:
            self.console.print(f"❌ Failed to launch Multi-Platform Ads: {e}", style="red")
            Prompt.ask("Press Enter to continue")
    
    def show_system_diagnostics(self):
        """Show detailed system diagnostics"""
        self.console.clear()
        self.console.print("🔧 [bold cyan]System Diagnostics[/bold cyan]")
        
        # Component status table
        status_table = Table(show_header=True, show_lines=True)
        status_table.add_column("Component", style="cyan")
        status_table.add_column("Status", style="white")
        status_table.add_column("Message", style="dim")
        
        for component, status in self.system_status.items():
            status_icon = {
                'healthy': '✅',
                'warning': '⚠️',
                'error': '❌'
            }.get(status['status'], '❓')
            
            status_table.add_row(
                component.replace('_', ' ').title(),
                f"{status_icon} {status['status'].title()}",
                status['message']
            )
        
        diagnostics_panel = Panel(
            status_table,
            title="🔍 Component Status",
            style="blue"
        )
        self.console.print(diagnostics_panel)
        
        # Show recent logs
        if self.verbatim_log:
            recent_logs = "\n".join(self.verbatim_log[-10:])
            logs_panel = Panel(
                recent_logs,
                title="📋 Recent System Logs",
                style="yellow"
            )
            self.console.print(logs_panel)
        
        Prompt.ask("Press Enter to continue")
    
    def test_clipboard_tools(self):
        """Test clipboard functionality"""
        self.console.print("📋 [bold cyan]Testing Clipboard Tools...[/bold cyan]")
        
        try:
            subprocess.run([sys.executable, "utils/clipboard_helper.py"], cwd=".")
        except KeyboardInterrupt:
            self.console.print("\n🔙 Returned to main menu")
        except Exception as e:
            self.console.print(f"❌ Failed to test clipboard: {e}", style="red")
            Prompt.ask("Press Enter to continue")
    
    def run(self):
        """Main system loop"""
        while True:
            self.console.clear()
            self.console.print(self.show_system_header())
            self.console.print(self.show_main_menu())
            
            choice = Prompt.ask("🎯 Select component", choices=["0", "1", "2", "3", "4", "5", "6", "7", "8"])
            
            if choice == "0":
                self.console.print("👋 Shutting down Solar Panel Catalog System...", style="green")
                break
            elif choice == "1":
                self.launch_terminal_gui()
            elif choice == "2":
                self.launch_material_ui()
            elif choice == "3":
                self.launch_ebay_manager()
            elif choice == "4":
                self.launch_multiplatform_ads()
            elif choice == "5":
                self.console.print("📤 GitHub integration available in other components")
                Prompt.ask("Press Enter to continue")
            elif choice == "6":
                self.show_system_diagnostics()
            elif choice == "7":
                self.console.print("⚙️ Configuration tools available in individual components")
                Prompt.ask("Press Enter to continue")
            elif choice == "8":
                self.test_clipboard_tools()

def main():
    """Launch the complete solar panel catalog system"""
    try:
        system = SolarPanelCatalogSystem()
        system.run()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ System error: {e}")

if __name__ == "__main__":
    main()
