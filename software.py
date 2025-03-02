import gi
import subprocess
import os
import tempfile
import threading
from pathlib import Path
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

from popular_apps import PopularAppsPage
from download_manager import DownloadManagerPage

class SoftwarePage(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        # Create stack for different pages
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        
        # Create and add main software page
        self.main_software_page = self.create_main_software_page()
        self.stack.add_named(self.main_software_page, "main")
        
        self.append(self.stack)

    def create_main_software_page(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Create title
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        title_box.set_margin_top(20)
        title_box.set_margin_bottom(20)
        title_box.set_margin_start(20)
        title_box.set_margin_end(20)
        
        title_label = Gtk.Label()
        title_label.set_markup("<span size='large'>Software</span>")
        title_label.set_justify(Gtk.Justification.CENTER)
        title_box.append(title_label)
        
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        
        main_box.append(title_box)
        main_box.append(separator)
        
        # Create grid for options
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(10)
        grid.set_margin_top(20)
        grid.set_margin_bottom(20)
        grid.set_margin_start(20)
        grid.set_margin_end(20)
        
        # Add options
        row = 0
        col = 0
        
        options = [
            ("Install & Remove Software", "system-software-install-symbolic", "Install and remove software using Yumex", "yumex"),
            ("Update your system", "software-update-available-symbolic", "Update your system", "mandriva-updater"),
            ("Configure updates frequency", "preferences-system-time-symbolic", "Configure how often to check for updates", "mandriva-update-freq"),
            ("Configure media sources", "drive-harddisk-symbolic", "Configure media sources for install and updates", None),
            ("Install popular apps", "system-software-install-symbolic", "Install popular applications", None),
            ("Install external apps", "folder-download-symbolic", "Install applications from outside the repository", None),
            ("Install Codecs", "audio-x-generic-symbolic", "Install multimedia codecs for audio and video playback", None),
            ("Drivers", "preferences-system-symbolic", "Configure system drivers", None)
        ]
        
        for title, icon_name, description, command in options:
            button = self.create_option_button(title, icon_name, description)
            grid.attach(button, col, row, 1, 1)
            col = (col + 1) % 2
            if col == 0:
                row += 1
        
        main_box.append(grid)
        return main_box

    def create_option_button(self, title, icon_name, description):
        button = Gtk.Button()
        button.add_css_class("flat")
        button.set_hexpand(True)
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        
        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.set_pixel_size(48)
        box.append(icon)
        
        label = Gtk.Label(label=title)
        label.set_markup(f"<b>{title}</b>")
        box.append(label)
        
        desc_label = Gtk.Label(label=description)
        desc_label.set_markup(f"<small>{description}</small>")
        box.append(desc_label)
        
        button.set_child(box)
        button.connect("clicked", self.on_option_clicked, title)
        
        return button

    def on_option_clicked(self, button, title):
        if title == "Update your system":
            try:
                # First check if the system updater is installed
                updater_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                          "system_updater/update_manager_launcher.py")
                if not os.path.exists(updater_path):
                    dialog = Adw.MessageDialog.new(
                        self.get_root(),
                        "System Updater Not Available",
                        "The enhanced system updater is not installed. You can use 'dnf update' "
                        "from the terminal or install the system-updater package when available."
                    )
                    dialog.add_response("ok", "OK")
                    dialog.present()
                    return

                subprocess.Popen(
                    ["python3", updater_path],
                    cwd=os.path.dirname(os.path.abspath(__file__))
                )
            except Exception as e:
                dialog = Adw.MessageDialog.new(
                    self.get_root(),
                    "Error",
                    f"Failed to launch Update Manager: {str(e)}"
                )
                dialog.add_response("ok", "OK")
                dialog.present()
        elif title == "Install & Remove Software":
            self.check_and_run_yumex()
        elif title == "Configure updates frequency":
            if not hasattr(self, 'update_freq_page'):
                self.update_freq_page = UpdateFrequencyPage()
                self.stack.add_named(self.update_freq_page, "update_freq")
            self.stack.set_visible_child_name("update_freq")
        elif title == "Configure media sources":
            try:
                subprocess.Popen(
                    ["python3", "repo-test.py"],
                    cwd=os.path.dirname(os.path.abspath(__file__))
                )
            except Exception as e:
                dialog = Adw.MessageDialog.new(
                    self.get_root(),
                    "Error",
                    f"Failed to launch Repository Test: {str(e)}"
                )
                dialog.add_response("ok", "OK")
                dialog.present()
        elif title == "Install popular apps":
            if not hasattr(self, 'popular_apps_page'):
                self.popular_apps_page = PopularAppsPage()
                self.stack.add_named(self.popular_apps_page, "popular_apps")
            self.stack.set_visible_child_name("popular_apps")
        elif title == "Install external apps":
            if not hasattr(self, 'download_manager_page'):
                self.download_manager_page = DownloadManagerPage()
                self.stack.add_named(self.download_manager_page, "download_manager")
            self.stack.set_visible_child_name("download_manager")
        elif title == "Install Codecs":
            if not hasattr(self, 'codecs_page'):
                self.codecs_page = CodecsPage()
                self.stack.add_named(self.codecs_page, "codecs")
            self.stack.set_visible_child_name("codecs")
        elif title == "Drivers":
            if not hasattr(self, 'drivers_page'):
                self.drivers_page = DriversPage()
                self.stack.add_named(self.drivers_page, "drivers")
            self.stack.set_visible_child_name("drivers")

    def check_and_run_yumex(self):
        try:
            subprocess.run(['which', 'yumex'], check=True)
            subprocess.Popen(['yumex'])
        except subprocess.CalledProcessError:
            dialog = Adw.MessageDialog.new(
                self.get_root(),
                "Install Yumex",
                "Yumex is not installed. Would you like to install it now?"
            )
            dialog.add_response("cancel", "Cancel")
            dialog.add_response("install", "Install")
            dialog.set_default_response("install")
            dialog.connect("response", self.on_yumex_install_response)
            dialog.present()

    def on_yumex_install_response(self, dialog, response):
        if response == "install":
            # Create progress dialog
            progress_dialog = Adw.MessageDialog.new(
                self.get_root(),
                "Installing Yumex",
                "Please wait while Yumex is being installed..."
            )
            progress_dialog.add_response("cancel", "Cancel")
            
            # Create progress box
            progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            progress_box.set_margin_top(10)
            progress_box.set_margin_bottom(10)
            progress_box.set_margin_start(10)
            progress_box.set_margin_end(10)
            
            # Add progress bar
            progress_bar = Gtk.ProgressBar()
            progress_bar.set_show_text(True)
            progress_box.append(progress_bar)
            
            # Add status label
            status_label = Gtk.Label()
            status_label.set_wrap(True)
            status_label.set_halign(Gtk.Align.START)
            progress_box.append(status_label)
            
            # Set the extra child
            progress_dialog.set_extra_child(progress_box)
            progress_dialog.present()
            
            def update_progress(fraction, text):
                if fraction is not None:
                    progress_bar.set_fraction(fraction)
                status_label.set_markup(f"<span size='small'>{text}</span>")

            def install_thread():
                try:
                    # Create temporary script file
                    script_content = """#!/bin/bash
set -e

# Function to handle dnf output
handle_output() {
    while IFS= read -r line; do
        if [[ $line == *"Downloading"* ]]; then
            echo "PROGRESS:30:$line"
        elif [[ $line == *"Installing"* ]] || [[ $line == *"Upgrading"* ]]; then
            echo "PROGRESS:60:$line"
        elif [[ $line == *"Verifying"* ]]; then
            echo "PROGRESS:80:$line"
        elif [[ $line == *"Complete!"* ]]; then
            echo "PROGRESS:100:Installation complete!"
        else
            echo "INFO:$line"
        fi
    done
}

# Update package cache
echo "PROGRESS:10:Refreshing package cache..."
dnf makecache 2>&1 | handle_output

# Install package
echo "PROGRESS:20:Starting installation..."
dnf install -y yumex 2>&1 | handle_output
"""
                    
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as script_file:
                        script_file.write(script_content)
                        script_path = script_file.name
                    
                    # Make script executable
                    os.chmod(script_path, 0o755)
                    
                    # Execute script with pkexec and capture output
                    process = subprocess.Popen(
                        ["pkexec", script_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        universal_newlines=True,
                        bufsize=1
                    )

                    # Process output in real-time
                    while True:
                        line = process.stdout.readline()
                        if not line and process.poll() is not None:
                            break
                            
                        if line.startswith("PROGRESS:"):
                            _, percent, message = line.strip().split(":", 2)
                            GLib.idle_add(update_progress, float(percent)/100, message)
                        elif line.startswith("INFO:"):
                            _, message = line.strip().split(":", 1)
                            GLib.idle_add(update_progress, None, message)
                    
                    # Check if process was successful
                    if process.returncode != 0:
                        raise subprocess.CalledProcessError(process.returncode, "pkexec")
                    
                    # Remove temporary script
                    os.unlink(script_path)
                    
                    # Launch yumex
                    GLib.idle_add(lambda: subprocess.Popen(['yumex']))
                    GLib.idle_add(progress_dialog.close)
                    
                except Exception as e:
                    GLib.idle_add(progress_dialog.close)
                    GLib.idle_add(lambda: self.show_error_dialog(
                        "Installation Error",
                        f"Failed to install Yumex.\nError: {str(e)}"
                    ))
            
            thread = threading.Thread(target=install_thread)
            thread.daemon = True
            thread.start()

    def show_error_dialog(self, title, message):
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            title,
            message
        )
        dialog.add_response("ok", "OK")
        dialog.present()

    def show_main(self):
        self.stack.set_visible_child_name("main")

class UpdateFrequencyPage(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        # Create main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        
        # Add title
        title_label = Gtk.Label()
        title_label.set_markup("<span size='large'>Configure Update Settings</span>")
        title_label.set_halign(Gtk.Align.START)
        main_box.append(title_label)
        
        # Add description
        desc_label = Gtk.Label()
        desc_label.set_markup("Choose how DNF should handle system updates:")
        desc_label.set_halign(Gtk.Align.START)
        desc_label.set_margin_bottom(10)
        main_box.append(desc_label)
        
        # Create radio buttons for options
        self.option1 = Gtk.CheckButton()
        self.option1.set_label("Download updates automatically but let me choose when to install them")
        main_box.append(self.option1)
        
        self.option2 = Gtk.CheckButton.new_with_label("Download and install updates automatically")
        self.option2.set_group(self.option1)
        main_box.append(self.option2)
        
        self.option3 = Gtk.CheckButton.new_with_label("Never download or install updates automatically")
        self.option3.set_group(self.option1)
        main_box.append(self.option3)
        
        # Add apply button
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(20)
        
        apply_button = Gtk.Button(label="Apply Changes")
        apply_button.add_css_class("suggested-action")
        apply_button.connect("clicked", self._on_apply_clicked)
        button_box.append(apply_button)
        
        main_box.append(button_box)
        
        # Read current settings
        self._load_current_settings()
        
        self.append(main_box)
    
    def _load_current_settings(self):
        try:
            download_updates = "yes"
            apply_updates = "yes"
            
            if os.path.exists("/etc/dnf/automatic.conf"):
                with open("/etc/dnf/automatic.conf", "r") as f:
                    for line in f:
                        if line.strip().startswith("download_updates ="):
                            download_updates = line.split("=")[1].strip()
                        elif line.strip().startswith("apply_updates ="):
                            apply_updates = line.split("=")[1].strip()
            
            if download_updates == "yes" and apply_updates == "yes":
                self.option2.set_active(True)
            elif download_updates == "yes" and apply_updates == "no":
                self.option1.set_active(True)
            else:
                self.option3.set_active(True)
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.option3.set_active(True)
    
    def _on_apply_clicked(self, button):
        # Prepare the new values based on selection
        if self.option1.get_active():
            download_updates = "yes"
            apply_updates = "no"
        elif self.option2.get_active():
            download_updates = "yes"
            apply_updates = "yes"
        else:
            download_updates = "no"
            apply_updates = "no"
        
        try:
            # Read the current config file
            config_lines = []
            if os.path.exists("/etc/dnf/automatic.conf"):
                with open("/etc/dnf/automatic.conf", "r") as f:
                    config_lines = f.readlines()
            
            # If file doesn't exist or is empty, create default content
            if not config_lines:
                config_lines = [
                    "[commands]\n",
                    "download_updates = yes\n",
                    "apply_updates = yes\n",
                    "\n",
                    "[emitters]\n",
                    "system_name = None\n",
                    "emit_via = None\n",
                    "\n",
                    "[base]\n",
                    "debuglevel = 1\n"
                ]
            
            # Update the values in the existing content
            download_updated = False
            apply_updated = False
            new_config_lines = []
            
            for line in config_lines:
                if line.strip().startswith("download_updates ="):
                    new_config_lines.append(f"download_updates = {download_updates}\n")
                    download_updated = True
                elif line.strip().startswith("apply_updates ="):
                    new_config_lines.append(f"apply_updates = {apply_updates}\n")
                    apply_updated = True
                else:
                    new_config_lines.append(line)
            
            # Add missing settings if they weren't found
            if not download_updated:
                new_config_lines.insert(1, f"download_updates = {download_updates}\n")
            if not apply_updated:
                new_config_lines.insert(2, f"apply_updates = {apply_updates}\n")
            
            # Write to temporary file
            with open("/tmp/dnf_automatic.conf", "w") as f:
                f.writelines(new_config_lines)
            
            # Use pkexec to copy the file as root
            subprocess.run(["pkexec", "cp", "/tmp/dnf_automatic.conf", "/etc/dnf/automatic.conf"], check=True)
            
            dialog = Adw.MessageDialog.new(
                self.get_root(),
                "Success",
                "Update settings have been changed successfully."
            )
            dialog.add_response("ok", "OK")
            dialog.present()
        except Exception as e:
            dialog = Adw.MessageDialog.new(
                self.get_root(),
                "Error",
                f"Failed to apply changes: {str(e)}"
            )
            dialog.add_response("ok", "OK")
            dialog.present()
        finally:
            # Clean up temporary file
            if os.path.exists("/tmp/dnf_automatic.conf"):
                os.remove("/tmp/dnf_automatic.conf")

class CodecsPage(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        # Create main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        
        # Add title
        title_label = Gtk.Label()
        title_label.set_markup("<span size='large'>Install Media Codecs</span>")
        title_label.set_halign(Gtk.Align.START)
        main_box.append(title_label)
        
        # Add description
        desc_label = Gtk.Label()
        desc_label.set_markup(
            "Select the media codecs you want to install. These codecs enable playback "
            "of various audio and video formats."
        )
        desc_label.set_wrap(True)
        desc_label.set_halign(Gtk.Align.START)
        desc_label.set_margin_bottom(10)
        main_box.append(desc_label)
        
        # Create scrolled window for codecs list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(300)
        
        # Create list box for codecs
        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        list_box.add_css_class("boxed-list")
        
        # Define available codecs with descriptions
        self.codecs = {
            "lib64dvdcss2": "DVD decryption library",
            "faac": "AAC audio encoder",
            "flac": "Free Lossless Audio Codec",
            "faad2": "AAC audio decoder",
            "gpac": "Multimedia framework",
            "gstreamer1.0-svt-hevc": "SVT-HEVC encoder plugin for GStreamer",
            "kvazaar": "Open-source HEVC encoder",
            "lib64de265_0": "H.265/HEVC decoder",
            "lib64dvdcss": "DVD decryption library",
            "x264": "H.264/AVC encoder",
            "lib64xvid4": "MPEG-4 video codec",
            "lib64dca0": "DTS audio decoder",
            "lib64fdk-aac": "AAC audio codec",
            "lib64heif": "HEIF image format support",
            "x265": "H.265/HEVC encoder",
            "vvenc": "Versatile Video Encoder",
            "vvdec": "Versatile Video Decoder",
            "uvg266": "Open-source VVC encoder",
            "svt-hevc": "SVT-HEVC encoder",
            "kf6-kimageformats-heif": "HEIF format plugin for KDE"
        }
        
        # Create checkboxes for each codec
        self.check_buttons = {}
        for codec, description in self.codecs.items():
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            box.set_margin_top(10)
            box.set_margin_bottom(10)
            box.set_margin_start(10)
            box.set_margin_end(10)
            
            check = Gtk.CheckButton()
            self.check_buttons[codec] = check
            box.append(check)
            
            labels_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            
            name_label = Gtk.Label()
            name_label.set_markup(f"<b>{codec}</b>")
            name_label.set_halign(Gtk.Align.START)
            labels_box.append(name_label)
            
            desc_label = Gtk.Label(label=description)
            desc_label.set_halign(Gtk.Align.START)
            desc_label.add_css_class("dim-label")
            labels_box.append(desc_label)
            
            box.append(labels_box)
            row.set_child(box)
            list_box.append(row)
        
        scrolled.set_child(list_box)
        main_box.append(scrolled)
        
        # Add buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_margin_top(20)
        button_box.set_halign(Gtk.Align.END)
        
        select_all_button = Gtk.Button(label="Select All")
        select_all_button.connect("clicked", self._on_select_all_clicked)
        button_box.append(select_all_button)
        
        clear_button = Gtk.Button(label="Clear")
        clear_button.connect("clicked", self._on_clear_clicked)
        button_box.append(clear_button)
        
        install_button = Gtk.Button(label="Install Selected")
        install_button.add_css_class("suggested-action")
        install_button.connect("clicked", self._on_install_clicked)
        button_box.append(install_button)
        
        main_box.append(button_box)
        
        self.append(main_box)

    def _on_select_all_clicked(self, button):
        for check in self.check_buttons.values():
            check.set_active(True)

    def _on_clear_clicked(self, button):
        for check in self.check_buttons.values():
            check.set_active(False)

    def _on_install_clicked(self, button):
        selected_codecs = [codec for codec, check in self.check_buttons.items() if check.get_active()]
        
        if not selected_codecs:
            dialog = Adw.MessageDialog.new(
                self.get_root(),
                "No Codecs Selected",
                "Please select at least one codec to install."
            )
            dialog.add_response("ok", "OK")
            dialog.present()
            return
        
        # Create progress dialog
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Installing Codecs",
            "Please wait while the selected codecs are being installed..."
        )
        dialog.add_response("cancel", "Cancel")
        
        # Create progress box with fixed size
        progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        progress_box.set_margin_top(10)
        progress_box.set_margin_bottom(10)
        progress_box.set_margin_start(10)
        progress_box.set_margin_end(10)
        progress_box.set_size_request(400, 200)
        
        # Add progress bar
        progress_bar = Gtk.ProgressBar()
        progress_bar.set_show_text(True)
        progress_box.append(progress_bar)
        
        # Add scrolled window for status text
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        # Add status label with monospace font
        status_label = Gtk.Label()
        status_label.set_wrap(True)
        status_label.set_halign(Gtk.Align.START)
        status_label.set_markup("<span font_family='monospace' size='small'></span>")
        status_label.set_justify(Gtk.Justification.LEFT)
        scroll.set_child(status_label)
        progress_box.append(scroll)
        
        dialog.set_extra_child(progress_box)
        dialog.present()

        def update_progress(fraction, text):
            progress_bar.set_fraction(fraction)
            status_label.set_markup(f"<span font_family='monospace' size='small'>{text}</span>")
            # Scroll to the bottom
            adj = scroll.get_vadjustment()
            adj.set_value(adj.get_upper() - adj.get_page_size())

        def install_thread():
            try:
                # Get system information
                GLib.idle_add(update_progress, 0.1, "Checking system information...")
                
                # Get OS version
                os_info = subprocess.run(['cat', '/etc/os-release'], 
                                      capture_output=True, text=True, check=True)
                for line in os_info.stdout.split('\n'):
                    if line.startswith('VERSION='):
                        if 'Cooker' in line:
                            os_version = 'cooker'
                        elif 'Rome' in line:
                            os_version = 'rolling'
                        elif 'Rock' in line:
                            os_version = 'rock'
                        break
                
                # Get architecture
                arch_info = subprocess.run(['uname', '-a'], 
                                        capture_output=True, text=True, check=True)
                if 'x86_64' in arch_info.stdout:
                    arch = 'x86_64'
                elif 'znver1' in arch_info.stdout:
                    arch = 'znver1'
                elif 'aarch64' in arch_info.stdout:
                    arch = 'aarch64'
                elif 'riscv64' in arch_info.stdout:
                    arch = 'riscv64'
                else:
                    arch = 'x86_64'  # default to x86_64 if unknown
                
                # Prepare DNF command
                packages = ' '.join(selected_codecs)
                repo_arg = f'--enablerepo={os_version}-{arch}-restricted'
                dnf_cmd = ['pkexec', 'dnf', 'install', '-y'] + packages.split() + [repo_arg]
                
                GLib.idle_add(update_progress, 0.2, f"Installing selected codecs using {os_version}-{arch} repository...\n")
                
                # Run DNF with output capture
                process = subprocess.Popen(
                    dnf_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )

                # Process output in real-time
                output_lines = []
                progress = 0.2
                downloading = False
                installing = False
                
                while True:
                    line = process.stdout.readline()
                    if not line:
                        break
                    
                    line = line.strip()
                    if line:
                        # Keep only the last 8 lines
                        output_lines = (output_lines + [line])[-8:]
                        
                        # Update progress based on operation
                        if "Downloading" in line:
                            if not downloading:
                                downloading = True
                                progress = 0.4
                        elif "Installing" in line or "Upgrading" in line:
                            if not installing:
                                installing = True
                                progress = 0.7
                        elif "Complete!" in line:
                            progress = 0.9
                        
                        GLib.idle_add(update_progress, progress, "\n".join(output_lines))

                # Wait for process to complete
                process.wait()

                if process.returncode == 0:
                    GLib.idle_add(update_progress, 1.0, "Codec installation completed successfully!")
                    GLib.idle_add(dialog.close)
                    
                    success_dialog = Adw.MessageDialog.new(
                        self.get_root(),
                        "Installation Complete",
                        f"Selected codecs have been successfully installed!"
                    )
                    success_dialog.add_response("ok", "OK")
                    GLib.idle_add(success_dialog.present)
                else:
                    raise subprocess.CalledProcessError(process.returncode, dnf_cmd)
                
            except Exception as e:
                GLib.idle_add(dialog.close)
                error_dialog = Adw.MessageDialog.new(
                    self.get_root(),
                    "Installation Error",
                    f"Failed to install codecs: {str(e)}"
                )
                error_dialog.add_response("ok", "OK")
                GLib.idle_add(error_dialog.present)

        thread = threading.Thread(target=install_thread)
        thread.daemon = True
        thread.start()

class DriversPage(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        # Create main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        
        # Add title
        title_label = Gtk.Label()
        title_label.set_markup("<span size='large'>Graphics Drivers</span>")
        title_label.set_halign(Gtk.Align.START)
        main_box.append(title_label)
        
        # Add description
        desc_label = Gtk.Label()
        desc_label.set_markup("Install graphics drivers for your system:")
        desc_label.set_halign(Gtk.Align.START)
        desc_label.set_margin_bottom(10)
        main_box.append(desc_label)
        
        # Add driver options
        nvidia_button = self._create_driver_button(
            "NVIDIA Drivers",
            "Proprietary drivers for NVIDIA graphics cards",
            "Install the NVIDIA proprietary drivers from the system repository."
        )
        main_box.append(nvidia_button)
        
        amd_button = self._create_driver_button(
            "AMD ROCm",
            "Open-source ROCm drivers for AMD graphics cards",
            "Install the ROCm compute stack for AMD graphics cards."
        )
        main_box.append(amd_button)
        
        amdvlk_button = self._create_driver_button(
            "AMDVLK",
            "Open-source Vulkan drivers for AMD graphics cards",
            "Install the AMDVLK Vulkan drivers (for advanced users)."
        )
        main_box.append(amdvlk_button)
        
        self.append(main_box)

    def _create_driver_button(self, name, description, tooltip):
        button = Gtk.Button()
        button.add_css_class("flat")
        button.set_hexpand(True)
        button.set_tooltip_text(tooltip)
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        
        label = Gtk.Label(label=name)
        label.set_markup(f"<b>{name}</b>")
        box.append(label)
        
        desc_label = Gtk.Label(label=description)
        desc_label.set_markup(f"<small>{description}</small>")
        box.append(desc_label)
        
        button.set_child(box)
        button.connect("clicked", self._on_driver_clicked, name)
        
        return button

    def _on_driver_clicked(self, button, name):
        if name == "NVIDIA Drivers":
            self._install_nvidia_drivers()
        elif name == "AMD ROCm":
            self._install_rocm_drivers()
        elif name == "AMDVLK":
            self._install_amdvlk_drivers()

    def _install_nvidia_drivers(self):
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Install NVIDIA Drivers",
            "This will install the NVIDIA proprietary drivers from the system repository. Do you want to continue?"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("install", "Install")
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", self._on_nvidia_response)
        dialog.present()

    def _on_nvidia_response(self, dialog, response):
        if response == "install":
            self._run_installation(
                "NVIDIA drivers",
                ["dnf", "install", "-y", "nvidia", "nvidia-settings"]
            )

    def _install_rocm_drivers(self):
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Install AMD ROCm",
            "This will install the ROCm compute stack. Do you want to continue?"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("install", "Install")
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", self._on_rocm_response)
        dialog.present()

    def _on_rocm_response(self, dialog, response):
        if response == "install":
            self._run_installation(
                "ROCm drivers",
                ["dnf", "install", "-y", "lib64hsakmt1", "rocm-clinfo", "rocm-comgr", 
                 "rocm-device-libs", "rocm-opencl", "rocm-runtime", "rocm-smi", "rocminfo"],
                post_success_message="Installation successful! To use ROCm, you need to:\n\n"
                                   "1. Add your user to the render and video groups\n"
                                   "2. Restart your computer"
            )

    def _install_amdvlk_drivers(self):
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Install AMDVLK",
            "This will install the AMDVLK Vulkan drivers. Do you want to continue?"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("install", "Install")
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", self._on_amdvlk_response)
        dialog.present()

    def _on_amdvlk_response(self, dialog, response):
        if response == "install":
            self._run_installation(
                "AMDVLK drivers",
                ["dnf", "install", "-y", "amdvlk-vulkan-driver", "amdvlk-vulkan-driver-32"]
            )

    def _run_installation(self, driver_name, command, post_success_message=None):
        # Create progress dialog
        progress_dialog = Adw.MessageDialog.new(
            self.get_root(),
            f"Installing {driver_name}",
            "Please wait while the drivers are being installed..."
        )
        progress_dialog.present()
        
        def on_installation_complete(process):
            progress_dialog.close()
            
            if process.returncode == 0:
                message = f"{driver_name} have been installed successfully!"
                if post_success_message:
                    message += "\n\n" + post_success_message
                
                success_dialog = Adw.MessageDialog.new(
                    self.get_root(),
                    "Installation Successful",
                    message
                )
                success_dialog.add_response("ok", "OK")
                success_dialog.present()
            else:
                error_dialog = Adw.MessageDialog.new(
                    self.get_root(),
                    "Installation Failed",
                    f"Failed to install {driver_name}. Please check the system logs for more information."
                )
                error_dialog.add_response("ok", "OK")
                error_dialog.present()
        # Run the installation with pkexec
        try:
            process = subprocess.Popen(
                ["pkexec"] + command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Use GLib.idle_add to check process status
            def check_process():
                if process.poll() is None:
                    return True
                
                on_installation_complete(process)
                return False
            
            GLib.idle_add(check_process)
            
        except Exception as e:
            progress_dialog.close()
            error_dialog = Adw.MessageDialog.new(
                self.get_root(),
                "Installation Failed",
                f"Failed to start installation: {str(e)}"
            )
            error_dialog.add_response("ok", "OK")
            error_dialog.present()
