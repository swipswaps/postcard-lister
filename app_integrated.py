#!/usr/bin/env python3
################################################################################
# FILE: app_integrated.py
# DESC: Fully integrated postcard lister using all core modules
# SPEC: Phase 1 - Core Integration Complete
################################################################################

import os
import sys
import json
import traceback
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QWidget, QTabWidget, QFormLayout, QLineEdit,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QTextEdit, QProgressBar, QGroupBox, QCheckBox, QSpinBox,
    QComboBox, QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QFont

# Import our sophisticated core modules
from core.vision_handler import get_postcard_metadata
from core.enhanced_vision_handler import get_enhanced_metadata
from core.image_processor import process_image_set
from core.github_catalog import GitHubCatalog, upload_product_to_github
from core.csv_generator import generate_csv, fill_row
from core.utils import is_image_file

################################################################################
# CONFIGURATION MANAGEMENT
################################################################################

class ConfigManager:
    """Handles loading and saving configuration from JSON files"""
    
    def __init__(self):
        self.config_path = "config/settings.json"
        self.template_path = "config/settings.template.json"
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from settings.json, create from template if needed"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                print(f"✅ Loaded configuration from {self.config_path}")
            else:
                # Create from template
                if os.path.exists(self.template_path):
                    with open(self.template_path, 'r') as f:
                        self.config = json.load(f)
                    print(f"⚠️  Created config from template. Please edit {self.config_path}")
                else:
                    # Create minimal config
                    self.config = {
                        "aws_access_key": "",
                        "aws_secret_key": "",
                        "s3_bucket": "",
                        "aws_region": "us-east-1",
                        "openai_api_key": "",
                        "background_color": "#000000",
                        "custom_html": "",
                        "store_category_id": ""
                    }
                    print("⚠️  Created minimal configuration")
                
                self.save_config()
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            self.config = {}
    
    def save_config(self):
        """Save current configuration to settings.json"""
        try:
            os.makedirs("config", exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            print(f"✅ Configuration saved to {self.config_path}")
        except Exception as e:
            print(f"❌ Error saving config: {e}")
    
    def get(self, key, default=""):
        """Get configuration value with default"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set configuration value"""
        self.config[key] = value
    
    def update_from_gui(self, gui_values):
        """Update config from GUI form values"""
        for key, value in gui_values.items():
            self.config[key] = value
        self.save_config()

################################################################################
# WORKER THREADS
################################################################################

class GitHubUploadWorker(QThread):
    """Background thread for GitHub uploads without blocking GUI"""

    # Signals for communicating with GUI
    progress_updated = pyqtSignal(str)  # status message
    upload_complete = pyqtSignal(bool, str)  # success, message

    def __init__(self, commit_message):
        super().__init__()
        self.commit_message = commit_message

    def run(self):
        """Run GitHub upload with verbatim system/error/application message capture"""
        try:
            import subprocess
            import os
            import tempfile
            from datetime import datetime

            self.progress_updated.emit("🔍 Checking upload script...")

            # Check if upload script exists
            upload_script = "github_upload_clean.sh"
            if not os.path.exists(upload_script):
                self.upload_complete.emit(False, f"❌ Upload script not found: {upload_script}")
                return

            # Create timestamped log files for verbatim capture
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            stdout_log = f"{log_dir}/github_upload_stdout_{timestamp}.log"
            stderr_log = f"{log_dir}/github_upload_stderr_{timestamp}.log"
            combined_log = f"{log_dir}/github_upload_combined_{timestamp}.log"

            self.progress_updated.emit(f"📝 Logging to: {combined_log}")
            self.progress_updated.emit("📤 Executing GitHub upload script with verbatim capture...")

            # Create enhanced script that captures ALL output with tee pattern
            enhanced_script = f"""#!/bin/bash
# Enhanced GitHub upload with verbatim message capture
# Based on PRF pattern: exec 2> >(stdbuf -oL ts | tee "$LOG_MASKED" | tee >(cat >&4))

set -euo pipefail

# Setup logging with tee pattern for verbatim capture
exec 1> >(stdbuf -oL ts | tee "{stdout_log}" | tee >(cat >&1))
exec 2> >(stdbuf -oL ts | tee "{stderr_log}" | tee >(cat >&2))

# Also create combined log
exec 3> >(stdbuf -oL ts | tee "{combined_log}")

echo "🔧 VERBATIM SYSTEM MESSAGE CAPTURE ACTIVE" >&3
echo "📅 Timestamp: $(date)" >&3
echo "📁 Working Directory: $(pwd)" >&3
echo "🔧 Git Status:" >&3
git status --porcelain >&3 2>&3 || echo "Git status failed" >&3

echo "📤 Executing original upload script..." >&3

# Execute the original upload script with full output capture
bash "{upload_script}" "{self.commit_message}" 2>&3 1>&3

echo "✅ Upload script execution completed" >&3
echo "📊 Final git status:" >&3
git status --porcelain >&3 2>&3 || echo "Final git status failed" >&3
"""

            # Write enhanced script to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(enhanced_script)
                enhanced_script_path = f.name

            try:
                # Make enhanced script executable
                os.chmod(enhanced_script_path, 0o755)

                # Run enhanced script with REAL-TIME verbatim capture (Fedora Linux)
                self.progress_updated.emit("🔄 Starting real-time output capture on Fedora...")

                import threading
                import queue
                import time

                # Create queues for real-time output
                stdout_queue = queue.Queue()
                stderr_queue = queue.Queue()

                def read_output(pipe, output_queue, prefix):
                    """Read output from pipe and put in queue with real-time emission"""
                    try:
                        for line in iter(pipe.readline, ''):
                            if line:
                                line = line.rstrip()
                                output_queue.put(line)
                                # Emit immediately for real-time display
                                self.progress_updated.emit(f"{prefix} {line}")
                        pipe.close()
                    except Exception as e:
                        self.progress_updated.emit(f"⚠️ Error reading {prefix}: {e}")

                # Start process with separate pipes
                process = subprocess.Popen(
                    ["/bin/bash", enhanced_script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=os.getcwd(),
                    bufsize=1,  # Line buffered
                    universal_newlines=True
                )

                # Start reader threads for real-time output
                stdout_thread = threading.Thread(
                    target=read_output,
                    args=(process.stdout, stdout_queue, "📤 STDOUT:")
                )
                stderr_thread = threading.Thread(
                    target=read_output,
                    args=(process.stderr, stderr_queue, "🚨 STDERR:")
                )

                stdout_thread.daemon = True
                stderr_thread.daemon = True
                stdout_thread.start()
                stderr_thread.start()

                # Wait for process to complete
                self.progress_updated.emit("⏳ Waiting for upload script to complete...")
                process.wait()

                # Wait for reader threads to finish
                stdout_thread.join(timeout=5)
                stderr_thread.join(timeout=5)

                # Collect all output from queues
                stdout_lines = []
                stderr_lines = []

                # Get all stdout
                while not stdout_queue.empty():
                    try:
                        line = stdout_queue.get_nowait()
                        stdout_lines.append(line)
                    except queue.Empty:
                        break

                # Get all stderr
                while not stderr_queue.empty():
                    try:
                        line = stderr_queue.get_nowait()
                        stderr_lines.append(line)
                    except queue.Empty:
                        break

                # Create result object for compatibility
                class ProcessResult:
                    def __init__(self, returncode, stdout, stderr):
                        self.returncode = returncode
                        self.stdout = stdout
                        self.stderr = stderr

                result = ProcessResult(
                    process.returncode,
                    '\n'.join(stdout_lines),
                    '\n'.join(stderr_lines)
                )

                # Read verbatim logs
                stdout_content = ""
                stderr_content = ""
                combined_content = ""

                try:
                    if os.path.exists(stdout_log):
                        with open(stdout_log, 'r') as f:
                            stdout_content = f.read().strip()
                    if os.path.exists(stderr_log):
                        with open(stderr_log, 'r') as f:
                            stderr_content = f.read().strip()
                    if os.path.exists(combined_log):
                        with open(combined_log, 'r') as f:
                            combined_content = f.read().strip()
                except Exception as e:
                    self.progress_updated.emit(f"⚠️ Log read error: {e}")

                # Emit verbatim system messages
                if result.returncode == 0:
                    success_msg = "✅ GitHub upload successful!"

                    if combined_content:
                        success_msg += f"\n\n📋 VERBATIM SYSTEM MESSAGES:\n{combined_content}"
                    if stdout_content:
                        success_msg += f"\n\n📤 STDOUT CAPTURE:\n{stdout_content}"
                    if stderr_content:
                        success_msg += f"\n\n🚨 STDERR CAPTURE:\n{stderr_content}"
                    if result.stdout.strip():
                        success_msg += f"\n\n🔧 SUBPROCESS STDOUT:\n{result.stdout.strip()}"
                    if result.stderr.strip():
                        success_msg += f"\n\n⚠️ SUBPROCESS STDERR:\n{result.stderr.strip()}"

                    self.upload_complete.emit(True, success_msg)
                else:
                    error_msg = f"❌ GitHub upload failed (exit code: {result.returncode})"

                    if combined_content:
                        error_msg += f"\n\n📋 VERBATIM SYSTEM MESSAGES:\n{combined_content}"
                    if stderr_content:
                        error_msg += f"\n\n🚨 STDERR CAPTURE:\n{stderr_content}"
                    if stdout_content:
                        error_msg += f"\n\n📤 STDOUT CAPTURE:\n{stdout_content}"
                    if result.stderr.strip():
                        error_msg += f"\n\n⚠️ SUBPROCESS STDERR:\n{result.stderr.strip()}"
                    if result.stdout.strip():
                        error_msg += f"\n\n🔧 SUBPROCESS STDOUT:\n{result.stdout.strip()}"

                    self.upload_complete.emit(False, error_msg)

            finally:
                # Cleanup temp script
                try:
                    os.unlink(enhanced_script_path)
                except:
                    pass

        except subprocess.TimeoutExpired:
            self.upload_complete.emit(False, "⏰ Upload timed out after 2 minutes")
        except Exception as e:
            self.upload_complete.emit(False, f"❌ Upload error: {str(e)}")

class PostcardProcessor(QThread):
    """Background thread for processing postcards without blocking GUI"""
    
    # Signals for communicating with GUI
    progress_updated = pyqtSignal(int, str)  # progress percentage, status message
    processing_complete = pyqtSignal(dict)   # results dictionary
    error_occurred = pyqtSignal(str)         # error message
    
    def __init__(self, front_path, back_path, config, product_type="auto"):
        super().__init__()
        self.front_path = front_path
        self.back_path = back_path
        self.config = config
        self.product_type = product_type
        self.results = {}
    
    def run(self):
        """Main processing pipeline - runs in background thread"""
        try:
            self.progress_updated.emit(10, "Starting image processing...")
            
            # Step 1: Process images (create multiple variants)
            output_dir = "output"
            processed_images = process_image_set(
                self.front_path, 
                self.back_path, 
                output_dir, 
                index=1,  # Could be made dynamic for batch processing
                bg_color=self.config.get("background_color", "#000000")
            )
            
            if not processed_images:
                raise Exception("Image processing failed")
            
            self.progress_updated.emit(30, "Images processed successfully")
            
            # Step 2: Extract metadata using enhanced AI vision
            vision_image_path = processed_images.get("vision")
            if not vision_image_path or not os.path.exists(vision_image_path):
                raise Exception("Vision image not created")

            # Determine product hint
            product_hint = None
            if self.product_type != "auto":
                product_hint = self.product_type

            self.progress_updated.emit(40, f"Analyzing {product_hint or 'product'} with enhanced AI...")

            # Use enhanced multi-LLM analysis
            metadata = get_enhanced_metadata(
                vision_image_path,
                self.config,
                product_hint
            )

            if not metadata:
                raise Exception("AI metadata extraction failed")

            # Log analysis results
            analysis_method = metadata.get("analysis_method", "unknown")
            confidence = metadata.get("confidence", 0.0)
            product_type = metadata.get("product_type", "Unknown")

            self.progress_updated.emit(70, f"Analysis complete: {product_type} ({confidence:.1%} confidence)")
            
            # Step 3: Upload to GitHub Catalog (if configured)
            catalog_urls = {}
            product_id = ""

            if self.config.get("use_github_catalog", True):
                self.progress_updated.emit(80, "Uploading to GitHub catalog...")

                try:
                    # Create GitHub catalog instance
                    github_catalog = GitHubCatalog(self.config)

                    # Prepare images for upload
                    images_to_upload = {}
                    for img_type in ["front", "back", "final"]:
                        if img_type in processed_images and os.path.exists(processed_images[img_type]):
                            images_to_upload[img_type] = processed_images[img_type]

                    # Upload product to GitHub catalog
                    product_id = github_catalog.create_product(metadata, images_to_upload)

                    # Get the uploaded image URLs
                    if product_id:
                        product_data = github_catalog.read_product(product_id)
                        if product_data:
                            catalog_urls = product_data.get("images", {})

                    self.progress_updated.emit(90, f"GitHub catalog upload complete: {product_id}")

                except Exception as e:
                    print(f"GitHub catalog upload failed: {e}")
                    self.progress_updated.emit(85, f"GitHub upload failed: {str(e)}")
                    catalog_urls = {}
            else:
                self.progress_updated.emit(80, "GitHub catalog disabled")
            
            # Step 4: Compile results
            self.results = {
                "metadata": metadata,
                "processed_images": processed_images,
                "catalog_urls": catalog_urls,
                "product_id": product_id,
                "front_path": self.front_path,
                "back_path": self.back_path
            }
            
            self.progress_updated.emit(100, "Processing complete!")
            self.processing_complete.emit(self.results)
            
        except Exception as e:
            error_msg = f"Processing failed: {str(e)}\n{traceback.format_exc()}"
            self.error_occurred.emit(error_msg)

################################################################################
# MAIN APPLICATION CLASS
################################################################################

class IntegratedPostcardLister(QWidget):
    """Main application window with full integration"""
    
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.processor = None
        self.results_data = []
        
        self.init_ui()
        self.load_config_to_gui()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Postcard Lister - Integrated Version")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Create tabs
        self.settings_tab = self.create_settings_tab()
        self.process_tab = self.create_process_tab()
        self.results_tab = self.create_results_tab()
        
        self.tabs.addTab(self.settings_tab, "⚙️ Settings")
        self.tabs.addTab(self.process_tab, "🔄 Process")
        self.tabs.addTab(self.results_tab, "📊 Results")
        
        # Main layout
        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)
    
    def create_settings_tab(self):
        """Create the settings configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Configuration form
        form_group = QGroupBox("Configuration")
        form_layout = QFormLayout()
        
        # Create form fields
        self.openai_key_field = QLineEdit()
        self.openai_key_field.setEchoMode(QLineEdit.Password)

        self.github_token_field = QLineEdit()
        self.github_token_field.setEchoMode(QLineEdit.Password)

        self.github_owner_field = QLineEdit()
        self.github_repo_field = QLineEdit()
        self.store_category_field = QLineEdit()
        self.background_color_field = QLineEdit()

        # Feature options
        self.use_multi_llm_checkbox = QCheckBox("Enable Multi-LLM Analysis (Enhanced Accuracy)")
        self.use_multi_llm_checkbox.setChecked(True)
        self.use_multi_llm_checkbox.setToolTip("Use multiple AI models for improved accuracy and consensus")

        self.use_github_catalog_checkbox = QCheckBox("Enable GitHub Catalog (Recommended)")
        self.use_github_catalog_checkbox.setChecked(True)
        self.use_github_catalog_checkbox.setToolTip("Store products in GitHub repository with version control")

        # Add fields to form
        form_layout.addRow("OpenAI API Key:", self.openai_key_field)
        form_layout.addRow("GitHub Token:", self.github_token_field)
        form_layout.addRow("GitHub Owner:", self.github_owner_field)
        form_layout.addRow("GitHub Repo:", self.github_repo_field)
        form_layout.addRow("Store Category ID:", self.store_category_field)
        form_layout.addRow("Background Color:", self.background_color_field)
        form_layout.addRow("", self.use_multi_llm_checkbox)
        form_layout.addRow("", self.use_github_catalog_checkbox)
        
        form_group.setLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()

        save_button = QPushButton("💾 Save Configuration")
        save_button.clicked.connect(self.save_config_from_gui)

        github_upload_button = QPushButton("🚀 Upload to GitHub")
        github_upload_button.clicked.connect(self.upload_to_github)
        github_upload_button.setToolTip("Upload current changes to GitHub repository")

        button_layout.addWidget(save_button)
        button_layout.addWidget(github_upload_button)
        button_layout.addStretch()

        # Status display
        self.config_status = QTextEdit()
        self.config_status.setMaximumHeight(100)
        self.config_status.setReadOnly(True)

        layout.addWidget(form_group)
        layout.addLayout(button_layout)
        layout.addWidget(QLabel("Configuration Status:"))
        layout.addWidget(self.config_status)
        
        tab.setLayout(layout)
        return tab

    def create_process_tab(self):
        """Create the main processing tab"""
        tab = QWidget()
        layout = QVBoxLayout()

        # Product type selection
        product_group = QGroupBox("Product Type")
        product_layout = QVBoxLayout()

        self.product_type_combo = QComboBox()
        self.product_type_combo.addItems([
            "Auto-detect",
            "Solar Panel",
            "Postcard",
            "Electronics",
            "Generic Product"
        ])
        self.product_type_combo.setCurrentText("Auto-detect")

        product_layout.addWidget(QLabel("Select product type for optimized analysis:"))
        product_layout.addWidget(self.product_type_combo)
        product_group.setLayout(product_layout)

        # File selection group
        file_group = QGroupBox("Select Product Images")
        file_layout = QVBoxLayout()

        # Front image selection
        front_layout = QHBoxLayout()
        self.front_path_label = QLabel("No front image selected")
        self.front_select_btn = QPushButton("📁 Select Front Image")
        self.front_select_btn.clicked.connect(self.select_front_image)
        front_layout.addWidget(QLabel("Front:"))
        front_layout.addWidget(self.front_path_label)
        front_layout.addWidget(self.front_select_btn)

        # Back image selection
        back_layout = QHBoxLayout()
        self.back_path_label = QLabel("No back image selected")
        self.back_select_btn = QPushButton("📁 Select Back Image")
        self.back_select_btn.clicked.connect(self.select_back_image)
        back_layout.addWidget(QLabel("Back:"))
        back_layout.addWidget(self.back_path_label)
        back_layout.addWidget(self.back_select_btn)

        file_layout.addLayout(front_layout)
        file_layout.addLayout(back_layout)
        file_group.setLayout(file_layout)

        # Processing controls
        process_group = QGroupBox("Processing")
        process_layout = QVBoxLayout()

        # Process button
        self.process_btn = QPushButton("🚀 Process Postcard")
        self.process_btn.clicked.connect(self.start_processing)
        self.process_btn.setEnabled(False)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_label = QLabel("Ready to process")

        process_layout.addWidget(self.process_btn)
        process_layout.addWidget(self.progress_label)
        process_layout.addWidget(self.progress_bar)
        process_group.setLayout(process_layout)

        # Output log
        log_group = QGroupBox("Processing Log")
        log_layout = QVBoxLayout()

        self.process_log = QTextEdit()
        self.process_log.setReadOnly(True)
        self.process_log.setMaximumHeight(200)

        log_layout.addWidget(self.process_log)
        log_group.setLayout(log_layout)

        # Add all groups to main layout
        layout.addWidget(product_group)
        layout.addWidget(file_group)
        layout.addWidget(process_group)
        layout.addWidget(log_group)
        layout.addStretch()

        tab.setLayout(layout)
        return tab

    def create_results_tab(self):
        """Create the results display tab"""
        tab = QWidget()
        layout = QVBoxLayout()

        # Results display
        results_group = QGroupBox("Processing Results")
        results_layout = QVBoxLayout()

        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)

        results_layout.addWidget(self.results_display)
        results_group.setLayout(results_layout)

        # Export controls
        export_group = QGroupBox("Export")
        export_layout = QHBoxLayout()

        self.export_csv_btn = QPushButton("📄 Export to CSV")
        self.export_csv_btn.clicked.connect(self.export_to_csv)
        self.export_csv_btn.setEnabled(False)

        self.view_images_btn = QPushButton("🖼️ View Processed Images")
        self.view_images_btn.clicked.connect(self.view_processed_images)
        self.view_images_btn.setEnabled(False)

        self.upload_results_btn = QPushButton("🚀 Upload to GitHub")
        self.upload_results_btn.clicked.connect(self.upload_to_github)
        self.upload_results_btn.setToolTip("Upload processing results and catalog to GitHub")
        self.upload_results_btn.setEnabled(False)

        export_layout.addWidget(self.export_csv_btn)
        export_layout.addWidget(self.view_images_btn)
        export_layout.addWidget(self.upload_results_btn)
        export_layout.addStretch()

        export_group.setLayout(export_layout)

        layout.addWidget(results_group)
        layout.addWidget(export_group)

        tab.setLayout(layout)
        return tab

    def load_config_to_gui(self):
        """Load configuration values into GUI fields"""
        self.openai_key_field.setText(self.config_manager.get("openai_api_key"))
        self.github_token_field.setText(self.config_manager.get("github_token"))
        self.github_owner_field.setText(self.config_manager.get("github_owner"))
        self.github_repo_field.setText(self.config_manager.get("github_repo", "postcard-lister"))
        self.store_category_field.setText(self.config_manager.get("store_category_id"))
        self.background_color_field.setText(self.config_manager.get("background_color", "#000000"))
        self.use_multi_llm_checkbox.setChecked(self.config_manager.get("use_multi_llm", True))
        self.use_github_catalog_checkbox.setChecked(self.config_manager.get("use_github_catalog", True))

        self.update_config_status()

    def save_config_from_gui(self):
        """Save GUI values to configuration"""
        gui_values = {
            "openai_api_key": self.openai_key_field.text(),
            "github_token": self.github_token_field.text(),
            "github_owner": self.github_owner_field.text(),
            "github_repo": self.github_repo_field.text(),
            "store_category_id": self.store_category_field.text(),
            "background_color": self.background_color_field.text(),
            "use_multi_llm": self.use_multi_llm_checkbox.isChecked(),
            "use_github_catalog": self.use_github_catalog_checkbox.isChecked()
        }

        self.config_manager.update_from_gui(gui_values)
        self.update_config_status()
        self.log_message("✅ Configuration saved successfully")

    def update_config_status(self):
        """Update the configuration status display"""
        status_lines = []

        # Helper function to check if value is real (not placeholder)
        def is_real_value(value):
            if not value:
                return False
            placeholder_patterns = ["YOUR_", "ENTER_", "ADD_", "REPLACE_"]
            return not any(pattern in value.upper() for pattern in placeholder_patterns)

        # Check OpenAI API key
        openai_key = self.config_manager.get("openai_api_key")
        if is_real_value(openai_key):
            status_lines.append("✅ OpenAI API key configured")
        else:
            status_lines.append("❌ OpenAI API key missing (required)")

        # Check GitHub configuration
        github_token = self.config_manager.get("github_token")
        github_owner = self.config_manager.get("github_owner")
        github_repo = self.config_manager.get("github_repo")

        if (is_real_value(github_token) and
            is_real_value(github_owner) and
            is_real_value(github_repo)):
            status_lines.append("✅ GitHub catalog configured")
        else:
            status_lines.append("⚠️ GitHub catalog not configured (will use gh CLI)")

        # Check store category
        store_category = self.config_manager.get("store_category_id")
        if is_real_value(store_category):
            status_lines.append("✅ Store category configured")
        else:
            status_lines.append("⚠️ Store category not set (optional)")

        # Check multi-LLM status
        if self.config_manager.get("use_multi_llm", True):
            status_lines.append("✅ Multi-LLM analysis enabled")
        else:
            status_lines.append("⚠️ Multi-LLM analysis disabled")

        self.config_status.setText("\n".join(status_lines))

    def select_front_image(self):
        """Select front image file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Front Image",
            "",
            "Images (*.jpg *.jpeg *.png)"
        )
        if file_path:
            self.front_path = file_path
            self.front_path_label.setText(os.path.basename(file_path))
            self.log_message(f"✅ Front image selected: {os.path.basename(file_path)}")
            self.check_ready_to_process()

    def select_back_image(self):
        """Select back image file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Back Image",
            "",
            "Images (*.jpg *.jpeg *.png)"
        )
        if file_path:
            self.back_path = file_path
            self.back_path_label.setText(os.path.basename(file_path))
            self.log_message(f"✅ Back image selected: {os.path.basename(file_path)}")
            self.check_ready_to_process()

    def check_ready_to_process(self):
        """Check if we have everything needed to start processing"""
        has_images = hasattr(self, 'front_path') and hasattr(self, 'back_path')

        # Check if OpenAI key is real (not placeholder)
        openai_key = self.config_manager.get("openai_api_key")
        has_real_openai_key = self.is_real_value(openai_key)

        ready = has_images and has_real_openai_key
        self.process_btn.setEnabled(ready)

        if ready:
            self.progress_label.setText("Ready to process postcard")
        elif not has_images:
            self.progress_label.setText("Please select both front and back images")
        elif not has_real_openai_key:
            self.progress_label.setText("Please configure OpenAI API key in Settings")

    def is_real_value(self, value):
        """Helper function to check if value is real (not placeholder)"""
        if not value:
            return False
        placeholder_patterns = ["YOUR_", "ENTER_", "ADD_", "REPLACE_"]
        return not any(pattern in value.upper() for pattern in placeholder_patterns)

    def start_processing(self):
        """Start the postcard processing in background thread"""
        if not hasattr(self, 'front_path') or not hasattr(self, 'back_path'):
            self.log_message("❌ Please select both front and back images")
            return

        if not self.config_manager.get("openai_api_key"):
            self.log_message("❌ Please configure OpenAI API key in Settings tab")
            return

        # Disable process button during processing
        self.process_btn.setEnabled(False)
        self.progress_bar.setValue(0)

        # Get selected product type
        product_type = self.product_type_combo.currentText()
        if product_type == "Auto-detect":
            product_type = "auto"

        # Create and start processor thread
        self.processor = PostcardProcessor(
            self.front_path,
            self.back_path,
            self.config_manager.config,
            product_type
        )

        # Connect signals
        self.processor.progress_updated.connect(self.update_progress)
        self.processor.processing_complete.connect(self.processing_finished)
        self.processor.error_occurred.connect(self.processing_error)

        # Start processing
        self.processor.start()
        self.log_message("🚀 Starting postcard processing...")

    def update_progress(self, percentage, message):
        """Update progress bar and status message"""
        self.progress_bar.setValue(percentage)
        self.progress_label.setText(message)
        self.log_message(f"[{percentage}%] {message}")

    def processing_finished(self, results):
        """Handle successful processing completion"""
        self.results_data.append(results)

        # Re-enable process button
        self.process_btn.setEnabled(True)
        self.export_csv_btn.setEnabled(True)
        self.view_images_btn.setEnabled(True)
        self.upload_results_btn.setEnabled(True)

        # Display results
        self.display_results(results)

        # Switch to results tab
        self.tabs.setCurrentIndex(2)

        self.log_message("🎉 Processing completed successfully!")

    def processing_error(self, error_message):
        """Handle processing errors"""
        self.process_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Processing failed")

        self.log_message(f"❌ Processing failed: {error_message}")

    def display_results(self, results):
        """Display processing results in the results tab"""
        metadata = results.get("metadata", {})
        catalog_urls = results.get("catalog_urls", {})
        product_id = results.get("product_id", "")

        # Format results for display
        product_type = metadata.get("product_type", "Product")
        display_text = f"🎯 {product_type.upper()} ANALYSIS RESULTS\n"
        display_text += "=" * 50 + "\n\n"

        # Product ID and catalog info
        if product_id:
            display_text += f"🆔 PRODUCT ID: {product_id}\n"
            display_text += f"📂 CATALOG: GitHub Repository\n\n"

        # Basic metadata
        display_text += "📋 METADATA:\n"
        for key, value in metadata.items():
            if value:  # Only show non-empty values
                display_text += f"  {key}: {value}\n"

        display_text += "\n"

        # Image processing results
        processed_images = results.get("processed_images", {})
        display_text += "🖼️ PROCESSED IMAGES:\n"
        for img_type, path in processed_images.items():
            display_text += f"  {img_type.title()}: {os.path.basename(path)}\n"

        display_text += "\n"

        # GitHub catalog URLs if available
        if catalog_urls:
            display_text += "🌐 GITHUB CATALOG URLS:\n"
            for img_type, url in catalog_urls.items():
                display_text += f"  {img_type.title()}: {url}\n"
        else:
            display_text += "⚠️ GitHub catalog upload not configured or failed\n"

        display_text += "\n"

        # Analysis method info
        analysis_method = metadata.get("analysis_method", "single_llm")
        confidence = metadata.get("confidence", 0.0)
        if confidence:
            display_text += f"🧠 ANALYSIS: {analysis_method} (confidence: {confidence:.1%})\n"

        display_text += "\n✅ Ready for CSV export!"

        self.results_display.setText(display_text)

    def export_to_csv(self):
        """Export results to eBay-compatible CSV"""
        if not self.results_data:
            self.log_message("❌ No results to export")
            return

        try:
            # Get save location
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save CSV File",
                "postcard_listings.csv",
                "CSV Files (*.csv)"
            )

            if not file_path:
                return

            # Prepare data for CSV generation
            csv_rows = []
            for result in self.results_data:
                metadata = result.get("metadata", {})
                s3_urls = result.get("s3_urls", {})

                # Create row data (metadata, s3_urls, settings)
                row_data = (metadata, s3_urls, self.config_manager.config)
                csv_rows.append(row_data)

            # Generate CSV using our core module
            template_path = "data/postcard-ebay-template-csv-version.csv"
            if os.path.exists(template_path):
                generate_csv(file_path, template_path, csv_rows)
                self.log_message(f"✅ CSV exported successfully: {file_path}")
            else:
                self.log_message(f"❌ Template file not found: {template_path}")

        except Exception as e:
            self.log_message(f"❌ CSV export failed: {str(e)}")

    def view_processed_images(self):
        """Open the output directory to view processed images"""
        output_dir = "output"
        if os.path.exists(output_dir):
            if sys.platform == "win32":
                os.startfile(output_dir)
            elif sys.platform == "darwin":
                os.system(f"open {output_dir}")
            else:
                os.system(f"xdg-open {output_dir}")

            self.log_message(f"📁 Opened output directory: {output_dir}")
        else:
            self.log_message("❌ Output directory not found")

    def upload_to_github(self):
        """Upload current changes to GitHub repository with comprehensive feedback"""
        try:
            self.log_message("🚀 Starting GitHub upload...")
            self.log_message("⏱️ This may take 30-60 seconds, please wait...")

            # Save current configuration first
            self.log_message("💾 Saving current configuration...")
            self.save_config_from_gui()
            self.log_message("✅ Configuration saved")

            # Create commit message with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_message = f"GUI Upload: Configuration and catalog updates - {timestamp}"
            self.log_message(f"📝 Commit message: {commit_message}")

            # Disable upload buttons during upload
            sender = self.sender()
            if sender:
                sender.setEnabled(False)
                sender.setText("⏳ Uploading...")

            # Start upload worker thread
            self.upload_worker = GitHubUploadWorker(commit_message)
            self.upload_worker.progress_updated.connect(self.log_message)
            self.upload_worker.upload_complete.connect(self.upload_finished)
            self.upload_worker.start()

            # Start progress timer for user feedback
            self.upload_progress_timer = QTimer()
            self.upload_progress_timer.timeout.connect(self.update_upload_progress)
            self.upload_progress_dots = 0
            self.upload_progress_timer.start(1000)  # Update every second

        except Exception as e:
            self.log_message(f"❌ GitHub upload error: {str(e)}")
            import traceback
            self.log_message(f"📋 Details: {traceback.format_exc()}")
            self.log_message("🔧 Check that git and GitHub CLI are properly configured")

            # Re-enable button on error
            sender = self.sender()
            if sender:
                sender.setEnabled(True)
                sender.setText("🚀 Upload to GitHub")

    def update_upload_progress(self):
        """Update upload progress indicator"""
        self.upload_progress_dots = (self.upload_progress_dots + 1) % 4
        progress_msg = f"⏳ Upload in progress{'.' * self.upload_progress_dots}{' ' * (3 - self.upload_progress_dots)}"
        # Don't log this as it would spam the log, just update status

    def upload_finished(self, success, message):
        """Handle upload completion"""
        # Stop progress timer
        if hasattr(self, 'upload_progress_timer'):
            self.upload_progress_timer.stop()

        # Log final result
        self.log_message(message)

        if success:
            self.log_message("🌐 Changes pushed to repository")
            self.log_message("✅ Upload completed successfully!")
        else:
            self.log_message("🔧 Check git configuration and network connection")
            self.log_message("💡 Try again or check the upload script manually")

        # Re-enable upload buttons
        for button_text in ["🚀 Upload to GitHub"]:
            # Find and re-enable upload buttons
            for widget in self.findChildren(QPushButton):
                if "Upload to GitHub" in widget.text():
                    widget.setEnabled(True)
                    widget.setText("🚀 Upload to GitHub")

    def log_message(self, message):
        """Add message to process log"""
        self.process_log.append(message)
        print(message)  # Also print to console

################################################################################
# MAIN ENTRY POINT
################################################################################

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("Postcard Lister - Integrated")
    app.setApplicationVersion("1.0")

    # Create and show main window
    window = IntegratedPostcardLister()
    window.show()

    # Start event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
