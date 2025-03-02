#!/usr/bin/env python3
import gi
import subprocess
import threading
import tempfile
import os
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
from pathlib import Path
from typing import Optional
import re

class HardwarePage(Gtk.Box):
    def __init__(self, parent):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.parent = parent
        
        # Create stack for different pages
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        
        # Create and add main hardware page
        self.main_hardware_page = self.create_main_hardware_page()
        self.stack.add_named(self.main_hardware_page, "main")
        
        self.append(self.stack)

    def create_main_hardware_page(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Create title
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        title_box.set_margin_top(20)
        title_box.set_margin_bottom(20)
        title_box.set_margin_start(20)
        title_box.set_margin_end(20)
        
        title_label = Gtk.Label()
        title_label.set_markup("<span size='large'>Hardware</span>")
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
        options = [
            ("Sound", "audio-speakers-symbolic", "Configure audio devices and settings"),
            ("Display", "video-display-symbolic", "Configure displays and graphics settings"),
            ("Disks", "drive-harddisk-symbolic", "Manage disks and storage devices"),
            ("Printers", "printer-symbolic", "Configure printers and printing options")
        ]
        
        for i, (title, icon_name, description) in enumerate(options):
            button = self.create_option_button(title, icon_name, description)
            grid.attach(button, i % 2, i // 2, 1, 1)
        
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
        if title == "Printers":
            if not hasattr(self, 'printer_page'):
                self.printer_page = PrintersPage(self)
                self.stack.add_named(self.printer_page, "printer")
            self.stack.set_visible_child_name("printer")
        elif title == "Sound":
            if not hasattr(self, 'sound_page'):
                self.sound_page = SoundPage(self)
                self.stack.add_named(self.sound_page, "sound")
            self.sound_page.stack.set_visible_child_name("main")
            self.stack.set_visible_child_name("sound")
        elif title == "Disks":
            if not hasattr(self, 'disks_page'):
                self.disks_page = DiskPage(self)
                self.stack.add_named(self.disks_page, "disks")
            self.stack.set_visible_child_name("disks")
        else:
            dialog = Adw.MessageDialog.new(
                self.get_root(),
                f"{title} Configuration",
                "This feature is not yet implemented."
            )
            dialog.add_response("ok", "OK")
            dialog.present()

    def handle_printer_config(self):
        printer_config = Path("/usr/bin/system-config-printer")
        if printer_config.exists():
            try:
                subprocess.Popen([str(printer_config)])
            except Exception as e:
                dialog = Adw.MessageDialog.new(
                    self.get_root(),
                    "Error",
                    f"Failed to launch printer configuration: {str(e)}"
                )
                dialog.add_response("ok", "OK")
                dialog.present()
        else:
            self.prompt_printer_config_install()

    def prompt_printer_config_install(self):
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Printer Configuration Not Found",
            "The printer configuration tool is not installed. Would you like to install it?"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("install", "Install")
        dialog.set_response_appearance("install", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", self._on_install_confirmation_response)
        dialog.present()

    def _on_install_confirmation_response(self, dialog, response):
        if response == "install":
            self.prompt_for_password()

    def prompt_for_password(self):
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Authentication Required",
            "Enter your root password to continue with the installation:"
        )
        
        # Create password entry
        password_entry = Gtk.PasswordEntry()
        password_entry.set_show_peek_icon(True)
        dialog.set_extra_child(password_entry)
        
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("authenticate", "Authenticate")
        dialog.set_response_appearance("authenticate", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", self._on_password_entered, password_entry)
        dialog.present()

    def _on_password_entered(self, dialog, response, password_entry):
        if response == "authenticate":
            password = password_entry.get_text()
            if password:
                self.install_printer_config(password)

    def install_printer_config(self, password):
        progress_dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Installing Printer Configuration",
            "Please wait while the printer configuration tool is being installed..."
        )
        progress_dialog.present()

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
dnf install -y system-config-printer-gui 2>&1 | handle_output
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
                        GLib.idle_add(progress_dialog.set_body, message)
                        GLib.idle_add(progress_dialog.set_subtitle, f"{percent}%")
                    elif line.startswith("INFO:"):
                        _, message = line.strip().split(":", 1)
                        GLib.idle_add(progress_dialog.set_body, message)
                
                # Check if process was successful
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, "pkexec")
                
                # Remove temporary script
                os.unlink(script_path)
                
                # Launch printer configuration tool
                GLib.idle_add(lambda: subprocess.Popen(['system-config-printer']))
                GLib.idle_add(progress_dialog.close)
                
            except Exception as e:
                GLib.idle_add(progress_dialog.close)
                GLib.idle_add(lambda: self.show_result_dialog(
                    False,
                    f"Failed to install printer configuration tool: {str(e)}"
                ))
        
        thread = threading.Thread(target=install_thread)
        thread.daemon = True
        thread.start()

    def update_progress_dialog(self, dialog, message):
        dialog.set_body(message)
        return False

    def show_result_dialog(self, success: bool, message: str):
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Installation " + ("Successful" if success else "Failed"),
            message
        )
        dialog.add_response("ok", "OK")
        dialog.present()
        return False

    def launch_printer_config(self):
        try:
            subprocess.Popen(["/usr/bin/system-config-printer"])
        except Exception as e:
            self.show_result_dialog(False, f"Failed to launch printer configuration: {str(e)}")
        return False

    def show_main(self):
        # Reset all sub-pages to their main views
        if hasattr(self, 'sound_page'):
            self.sound_page.stack.set_visible_child_name("main")
        if hasattr(self, 'disks_page'):
            self.disks_page.stack.set_visible_child_name("main")
        
        # Show the main hardware page
        self.stack.set_visible_child_name("main")

    def on_back_clicked(self, button):
        self.stack.set_visible_child_name("main")
        self.parent.stack.set_visible_child_name("main")


class PrintersPage(Gtk.Box):
    def __init__(self, parent):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.parent = parent
        
        # Create title box
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        title_box.set_margin_top(20)
        title_box.set_margin_bottom(20)
        title_box.set_margin_start(20)
        title_box.set_margin_end(20)
        
        # Add title
        title_label = Gtk.Label()
        title_label.set_markup("<span size='large'>Printer Settings</span>")
        title_label.set_margin_start(10)
        title_box.append(title_label)
        
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        
        self.append(title_box)
        self.append(separator)
        
        # Create grid for options
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(10)
        grid.set_margin_top(20)
        grid.set_margin_bottom(20)
        grid.set_margin_start(20)
        grid.set_margin_end(20)
        
        # Add options
        options = [
            ("Configure Printers", "printer-symbolic", "Configure and manage printers"),
            ("Install/Run HPLIP", "printer-network-symbolic", "HP Linux Imaging and Printing system"),
            ("Install Epson Drivers", "printer-symbolic", "Install Epson printer drivers"),
            ("Install Canon Drivers", "printer-symbolic", "Install Canon printer drivers"),
            ("Install All Drivers", "printer-symbolic", "Install all printer drivers")
        ]
        
        for i, (title, icon_name, description) in enumerate(options):
            button = self.create_option_button(title, icon_name, description)
            grid.attach(button, i % 2, i // 2, 1, 1)
        
        self.append(grid)

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
        if title == "Configure Printers":
            self.run_printer_config()
        elif title == "Install/Run HPLIP":
            self.handle_hplip()
        elif title == "Install Epson Drivers":
            self.check_and_install_package("task-printing-epson", "Epson")
        elif title == "Install Canon Drivers":
            self.check_and_install_package("task-printing-canon", "Canon")
        elif title == "Install All Drivers":
            self.check_and_install_package("task-printing", "printer")

    def run_printer_config(self):
        try:
            subprocess.run(['which', 'system-config-printer'], check=True)
            subprocess.Popen(['system-config-printer'])
        except subprocess.CalledProcessError:
            dialog = Adw.MessageDialog.new(
                self.get_root(),
                "Install Printer Configuration Tool",
                "The printer configuration tool is not installed. Would you like to install it now?"
            )
            dialog.add_response("cancel", "Cancel")
            dialog.add_response("install", "Install")
            dialog.set_default_response("install")
            dialog.connect("response", self.on_printer_install_response)
            dialog.present()

    def on_printer_install_response(self, dialog, response):
        if response == "install":
            # Create progress dialog
            progress_dialog = Adw.MessageDialog.new(
                self.get_root(),
                "Installing Printer Configuration Tool",
                "Please wait while the application is being installed..."
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
dnf install -y system-config-printer-gui 2>&1 | handle_output
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
                    
                    # Launch printer configuration tool
                    GLib.idle_add(lambda: subprocess.Popen(['system-config-printer']))
                    GLib.idle_add(progress_dialog.close)
                    
                except Exception as e:
                    GLib.idle_add(progress_dialog.close)
                    GLib.idle_add(lambda: self.show_error_dialog(
                        "Installation Error",
                        f"Failed to install printer configuration tool.\nError: {str(e)}"
                    ))
            
            thread = threading.Thread(target=install_thread)
            thread.daemon = True
            thread.start()

    def handle_hplip(self):
        hplip_path = Path("/usr/bin/hp-toolbox")
        if hplip_path.exists():
            try:
                subprocess.Popen([str(hplip_path)])
            except Exception as e:
                self.show_error_dialog("Launch Error", f"Failed to launch HPLIP: {str(e)}")
        else:
            self.check_and_install_package("hplip-gui", "HPLIP")

    def check_and_install_package(self, package_name: str, display_name: str):
        try:
            subprocess.run(["rpm", "-q", package_name], check=True)
            if package_name == "hplip-gui":
                subprocess.Popen(["/usr/bin/hp-toolbox"])
            else:
                dialog = Adw.MessageDialog.new(
                    self.get_root(),
                    f"{display_name} Drivers",
                    f"{display_name} printer drivers are already installed."
                )
                dialog.add_response("ok", "OK")
                dialog.present()
        except subprocess.CalledProcessError:
            dialog = Adw.MessageDialog.new(
                self.get_root(),
                f"Install {display_name}",
                f"Would you like to install {display_name}?"
            )
            dialog.add_response("cancel", "Cancel")
            dialog.add_response("install", "Install")
            dialog.set_default_response("install")
            dialog.connect("response", lambda d, r: self.on_package_install_response(d, r, package_name, display_name))
            dialog.present()

    def on_package_install_response(self, dialog, response, package_name, display_name):
        if response == "install":
            # Create progress dialog
            progress_dialog = Adw.MessageDialog.new(
                self.get_root(),
                f"Installing {display_name}",
                "Please wait while the package is being installed..."
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
                    script_content = f"""#!/bin/bash
set -e

# Function to handle dnf output
handle_output() {{
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
}}

# Update package cache
echo "PROGRESS:10:Refreshing package cache..."
dnf makecache 2>&1 | handle_output

# Install package
echo "PROGRESS:20:Starting installation..."
dnf install -y {package_name} 2>&1 | handle_output
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
                    
                    # Launch HPLIP if it was installed
                    if package_name == "hplip-gui":
                        GLib.idle_add(lambda: subprocess.Popen(["/usr/bin/hp-toolbox"]))
                    else:
                        GLib.idle_add(lambda: self.show_success_dialog(f"{display_name} drivers have been successfully installed!"))
                    GLib.idle_add(progress_dialog.close)
                    
                except Exception as e:
                    GLib.idle_add(progress_dialog.close)
                    GLib.idle_add(lambda: self.show_error_dialog(
                        "Installation Error",
                        f"Failed to install {display_name}.\nError: {str(e)}"
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

    def show_success_dialog(self, message):
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Installation Successful",
            message
        )
        dialog.add_response("ok", "OK")
        dialog.present()

    def on_back_clicked(self, button):
        self.parent.stack.set_visible_child_name("main")


class VolumeControlPage(Gtk.Box):
    def __init__(self, parent):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.parent = parent
        self._updating_controls = False  # Flag to prevent feedback loops
        self._sink_name_map = {}  # Map friendly names to sink names
        
        # Create title
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        title_box.set_margin_top(20)
        title_box.set_margin_bottom(20)
        title_box.set_margin_start(20)
        title_box.set_margin_end(20)
        
        # Add title
        title_label = Gtk.Label()
        title_label.set_markup("<span size='large'>Volume Control</span>")
        title_label.set_margin_start(10)
        title_box.append(title_label)
        
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        
        self.append(title_box)
        self.append(separator)
        
        # Main content
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)

        # Output Device Selection
        device_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        device_label = Gtk.Label()
        device_label.set_markup("<b>Output Device</b>")
        device_label.set_halign(Gtk.Align.START)
        device_box.append(device_label)
        
        self.device_dropdown = Gtk.DropDown()
        self.device_dropdown.set_hexpand(True)
        self.device_dropdown.connect("notify::selected", self.on_device_changed)
        device_box.append(self.device_dropdown)
        main_box.append(device_box)

        # Master Volume Control
        master_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        master_label = Gtk.Label()
        master_label.set_markup("<b>Master Volume</b>")
        master_label.set_halign(Gtk.Align.START)
        master_box.append(master_label)

        master_control = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        self.master_mute = Gtk.ToggleButton()
        self.master_mute.add_css_class("flat")
        self.master_icon = Gtk.Image.new_from_icon_name("audio-volume-high-symbolic")
        self.master_mute.set_child(self.master_icon)
        self.master_mute.connect("toggled", self.on_master_mute_toggled)
        master_control.append(self.master_mute)

        self.master_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.master_scale.set_hexpand(True)
        self.master_scale.connect("value-changed", self.on_master_volume_changed)
        self.master_scale.set_draw_value(True)
        self.master_scale.set_value_pos(Gtk.PositionType.RIGHT)
        master_control.append(self.master_scale)
        master_box.append(master_control)
        main_box.append(master_box)

        # Microphone Control
        mic_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        mic_label = Gtk.Label()
        mic_label.set_markup("<b>Microphone</b>")
        mic_label.set_halign(Gtk.Align.START)
        mic_box.append(mic_label)

        mic_control = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        self.mic_mute = Gtk.ToggleButton()
        self.mic_mute.set_icon_name("microphone-sensitivity-muted-symbolic")
        self.mic_mute.add_css_class("flat")
        self.mic_mute.connect("toggled", self.on_mic_mute_toggled)
        mic_control.append(self.mic_mute)

        self.mic_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.mic_scale.set_hexpand(True)
        self.mic_scale.connect("value-changed", self.on_mic_volume_changed)
        self.mic_scale.set_draw_value(True)
        self.mic_scale.set_value_pos(Gtk.PositionType.RIGHT)
        mic_control.append(self.mic_scale)
        mic_box.append(mic_control)
        main_box.append(mic_box)

        # Applications
        apps_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        apps_label = Gtk.Label()
        apps_label.set_markup("<b>Applications</b>")
        apps_label.set_halign(Gtk.Align.START)
        apps_box.append(apps_label)

        self.apps_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        apps_box.append(self.apps_container)
        main_box.append(apps_box)

        self.append(main_box)
        
        # Start volume update timer
        GLib.timeout_add(1000, self.update_volumes)
        # Initial update
        self.update_volumes()

    def update_volumes(self):
        if self._updating_controls:
            return True
        
        try:
            self._updating_controls = True
            
            # Update output devices list
            result = subprocess.run(
                ["pactl", "list", "sinks"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                current_model = self.device_dropdown.get_model()
                if current_model is None:
                    string_list = Gtk.StringList()
                    self.device_dropdown.set_model(string_list)
                else:
                    string_list = current_model
                    string_list.splice(0, string_list.get_n_items())

                # Get default sink
                current_sink = subprocess.run(
                    ["pactl", "get-default-sink"],
                    capture_output=True,
                    text=True
                ).stdout.strip()

                # Parse full format output to get better descriptions
                sinks = result.stdout.split("\n\n")
                selected_idx = 0
                self._sink_name_map.clear()  # Clear the old mapping

                for i, sink in enumerate(sinks):
                    if not sink.strip():
                        continue
                    
                    name_match = re.search(r"Nazwa: (.+)", sink)
                    desc_match = re.search(r"Opis: (.+)", sink)
                    port_match = re.search(r"Aktywny port: (.+)", sink)
                    if name_match and desc_match:
                        name = name_match.group(1).strip()
                        desc = desc_match.group(1).strip()
                        
                        # If there's an active port, add its name to the description
                        if port_match:
                            port = port_match.group(1).strip()
                            port_desc_match = re.search(fr"{port}: ([^(]+)", sink)
                            if port_desc_match:
                                desc = f"{desc} - {port_desc_match.group(1).strip()}"
                        
                        self._sink_name_map[desc] = name  # Store mapping
                        string_list.append(desc)  # Only show the friendly name
                        if name == current_sink:
                            selected_idx = i

                if string_list.get_n_items() > 0:
                    self.device_dropdown.set_selected(selected_idx)

            # Update master volume and mute state
            result = subprocess.run(
                ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                volume_match = re.search(r"(\d+)%", result.stdout)
                if volume_match:
                    volume = int(volume_match.group(1))
                    if abs(self.master_scale.get_value() - volume) > 1:  # Prevent feedback loops
                        self.master_scale.set_value(volume)
                    
                    # Update icon based on volume level and mute state
                    if self.master_mute.get_active():
                        self.master_icon.set_from_icon_name("audio-volume-muted-symbolic")
                    else:
                        icon_name = "audio-volume-low-symbolic" if volume < 33 else \
                                  "audio-volume-medium-symbolic" if volume < 66 else \
                                  "audio-volume-high-symbolic"
                        self.master_icon.set_from_icon_name(icon_name)

            result = subprocess.run(
                ["pactl", "get-sink-mute", "@DEFAULT_SINK@"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                is_muted = "tak" in result.stdout
                if self.master_mute.get_active() != is_muted:
                    self._updating_controls = False  # Temporarily allow the mute toggle
                    self.master_mute.set_active(is_muted)
                    self._updating_controls = True
                if is_muted:
                    self.master_icon.set_from_icon_name("audio-volume-muted-symbolic")

            # Update microphone volume and mute state
            result = subprocess.run(
                ["pactl", "get-source-volume", "@DEFAULT_SOURCE@"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                volume_match = re.search(r"(\d+)%", result.stdout)
                if volume_match:
                    volume = int(volume_match.group(1))
                    if abs(self.mic_scale.get_value() - volume) > 1:  # Prevent feedback loops
                        self.mic_scale.set_value(volume)

            result = subprocess.run(
                ["pactl", "get-source-mute", "@DEFAULT_SOURCE@"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                is_muted = "tak" in result.stdout
                if self.mic_mute.get_active() != is_muted:
                    self._updating_controls = False  # Temporarily allow the mute toggle
                    self.mic_mute.set_active(is_muted)
                    self._updating_controls = True

            # Update application volumes
            # First, remove all existing app controls
            while True:
                child = self.apps_container.get_first_child()
                if child is None:
                    break
                self.apps_container.remove(child)

            # Get list of applications
            result = subprocess.run(
                ["pactl", "list", "sink-inputs"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                has_apps = False
                current_app = {}
                app_text = ""
                sink_inputs = result.stdout.split("\n\n")

                for sink_input in sink_inputs:
                    if not sink_input.strip():
                        continue

                    index_match = re.search(r"^(\d+)\.", sink_input)
                    if not index_match:
                        continue

                    current_app = {'index': index_match.group(1)}
                    
                    # Try to find the best name for the application
                    media_name_match = re.search(r'media\.name = "([^"]+)"', sink_input)
                    app_name_match = re.search(r'application\.name = "([^"]+)"', sink_input)
                    
                    if media_name_match:
                        current_app['name'] = media_name_match.group(1)
                    elif app_name_match:
                        current_app['name'] = app_name_match.group(1)
                    else:
                        current_app['name'] = "Unknown"

                    # Get volume
                    volume_match = re.search(r'Poziom głośności:.*?(\d+)%', sink_input, re.DOTALL)
                    if volume_match:
                        current_app['volume'] = int(volume_match.group(1))
                    else:
                        current_app['volume'] = 100

                    # Get mute state
                    current_app['muted'] = 'Wyciszenie: tak' in sink_input

                    if current_app.get('index'):
                        has_apps = True
                        self.add_app_control(
                            current_app['index'],
                            current_app.get('name', 'Unknown'),
                            current_app.get('volume', 100),
                            current_app.get('muted', False)
                        )

                if not has_apps:
                    no_apps_label = Gtk.Label(label="No applications currently using audio")
                    no_apps_label.set_sensitive(False)
                    self.apps_container.append(no_apps_label)

        except Exception as e:
            print(f"Error updating volumes: {e}")
        finally:
            self._updating_controls = False

        return True  # Keep the timer running

    def on_device_changed(self, dropdown, *args):
        try:
            selected_idx = dropdown.get_selected()
            if selected_idx >= 0:
                model = dropdown.get_model()
                selected_desc = model.get_string(selected_idx)
                if selected_desc in self._sink_name_map:
                    sink_name = self._sink_name_map[selected_desc]
                    subprocess.run(
                        ["pactl", "set-default-sink", sink_name],
                        check=True
                    )
                    # Move all inputs to the new sink
                    result = subprocess.run(
                        ["pactl", "list", "short", "sink-inputs"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        for line in result.stdout.splitlines():
                            if line.strip():
                                input_id = line.split()[0]
                                subprocess.run(
                                    ["pactl", "move-sink-input", input_id, sink_name],
                                    check=True
                                )
        except subprocess.CalledProcessError as e:
            print(f"Error changing output device: {e}")

    def on_master_volume_changed(self, scale):
        if self._updating_controls:
            return
        volume = int(scale.get_value())
        try:
            subprocess.run(
                ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{volume}%"],
                check=True
            )
            # Update icon based on volume level
            if not self.master_mute.get_active():
                icon_name = "audio-volume-low-symbolic" if volume < 33 else \
                          "audio-volume-medium-symbolic" if volume < 66 else \
                          "audio-volume-high-symbolic"
                self.master_icon.set_from_icon_name(icon_name)
        except subprocess.CalledProcessError as e:
            print(f"Error setting master volume: {e}")

    def on_master_mute_toggled(self, button):
        if self._updating_controls:
            return
        try:
            is_muted = button.get_active()
            subprocess.run(
                ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1" if is_muted else "0"],
                check=True
            )
            # Update icon immediately
            if is_muted:
                self.master_icon.set_from_icon_name("audio-volume-muted-symbolic")
            else:
                volume = self.master_scale.get_value()
                icon_name = "audio-volume-low-symbolic" if volume < 33 else \
                          "audio-volume-medium-symbolic" if volume < 66 else \
                          "audio-volume-high-symbolic"
                self.master_icon.set_from_icon_name(icon_name)
        except subprocess.CalledProcessError as e:
            print(f"Error toggling master mute: {e}")
            # Revert the button state on error
            button.set_active(not is_muted)

    def on_mic_volume_changed(self, scale):
        if self._updating_controls:
            return
        volume = int(scale.get_value())
        try:
            subprocess.run(
                ["pactl", "set-source-volume", "@DEFAULT_SOURCE@", f"{volume}%"],
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Error setting microphone volume: {e}")

    def on_mic_mute_toggled(self, button):
        if self._updating_controls:
            return
        try:
            is_muted = button.get_active()
            subprocess.run(
                ["pactl", "set-source-mute", "@DEFAULT_SOURCE@", "1" if is_muted else "0"],
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Error toggling mic mute: {e}")
            # Revert the button state on error
            button.set_active(not is_muted)

    def add_app_control(self, index, app_name, volume, is_muted):
        app_control = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        # Mute button
        mute_button = Gtk.ToggleButton()
        mute_button.set_icon_name("audio-volume-muted-symbolic")
        mute_button.add_css_class("flat")
        mute_button.set_active(is_muted)
        mute_button.connect("toggled", self.on_app_mute_toggled, index)
        app_control.append(mute_button)

        app_icon = Gtk.Image.new_from_icon_name("application-x-executable-symbolic")
        app_icon.set_pixel_size(24)
        
        app_name_label = Gtk.Label(label=app_name)
        app_name_label.set_size_request(100, -1)
        app_name_label.set_halign(Gtk.Align.START)
        
        app_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        app_scale.set_draw_value(True)
        app_scale.set_value_pos(Gtk.PositionType.RIGHT)
        app_scale.set_hexpand(True)
        app_scale.set_value(volume)
        app_scale.connect("value-changed", self.on_app_volume_changed, index)
        
        app_control.append(app_icon)
        app_control.append(app_name_label)
        app_control.append(app_scale)
        
        self.apps_container.append(app_control)

    def on_app_volume_changed(self, scale, index):
        if self._updating_controls:
            return
        volume = int(scale.get_value())
        try:
            subprocess.run(
                ["pactl", "set-sink-input-volume", str(index), f"{volume}%"],
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Error setting application volume: {e}")

    def on_app_mute_toggled(self, button, index):
        if self._updating_controls:
            return
        try:
            is_muted = button.get_active()
            subprocess.run(
                ["pactl", "set-sink-input-mute", str(index), "1" if is_muted else "0"],
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Error toggling app mute: {e}")
            # Revert the button state on error
            button.set_active(not is_muted)

    def on_back_clicked(self, button):
        self.parent.show_main()


class DiskPage(Gtk.Box):
    def __init__(self, parent):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.parent = parent

        # Create title box
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        title_box.set_margin_top(20)
        title_box.set_margin_bottom(20)
        title_box.set_margin_start(20)
        title_box.set_margin_end(20)
        
        # Add title
        title_label = Gtk.Label()
        title_label.set_markup("<span size='large'>Disk Management</span>")
        title_label.set_margin_start(10)
        title_box.append(title_label)
        
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        
        self.append(title_box)
        self.append(separator)

        # Create main content
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)

        # Add disk utility options
        options = [
            ("GNOME Disks", "drive-harddisk-symbolic", "Manage and configure disk drives"),
            ("GParted", "drive-harddisk-system-symbolic", "Advanced partition editor")
        ]

        for title, icon_name, description in options:
            button = self.create_option_button(title, icon_name, description)
            main_box.append(button)

        self.append(main_box)

    def create_option_button(self, title, icon_name, description):
        button = Gtk.Button()
        button.add_css_class("flat")
        button.set_hexpand(True)
        
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        
        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.set_pixel_size(48)
        box.append(icon)
        
        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        text_box.set_hexpand(True)
        text_box.set_halign(Gtk.Align.START)
        
        label = Gtk.Label(label=title)
        label.set_markup(f"<b>{title}</b>")
        label.set_halign(Gtk.Align.START)
        text_box.append(label)
        
        desc_label = Gtk.Label(label=description)
        desc_label.set_markup(f"<small>{description}</small>")
        desc_label.set_halign(Gtk.Align.START)
        text_box.append(desc_label)
        
        box.append(text_box)
        button.set_child(box)
        button.connect("clicked", self.on_option_clicked, title)
        
        return button

    def on_option_clicked(self, button, title):
        if title == "GNOME Disks":
            self.launch_gnome_disks()
        elif title == "GParted":
            self.launch_gparted()

    def launch_gnome_disks(self):
        disks_path = Path("/usr/bin/gnome-disks")
        if disks_path.exists():
            try:
                subprocess.Popen([str(disks_path)])
            except Exception as e:
                self.show_error_dialog(f"Failed to launch GNOME Disks: {str(e)}")
        else:
            self.install_gnome_disks()

    def launch_gparted(self):
        gparted_path = Path("/usr/bin/gparted")
        if gparted_path.exists():
            try:
                subprocess.Popen(["pkexec", str(gparted_path)])
            except Exception as e:
                self.show_error_dialog(f"Failed to launch GParted: {str(e)}")
        else:
            self.install_gparted()

    def install_gnome_disks(self):
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Install GNOME Disks",
            "GNOME Disks is required for disk management. Would you like to install it?"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("install", "Install")
        dialog.set_response_appearance("install", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", self._on_gnome_disks_install_response)
        dialog.present()

    def install_gparted(self):
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Install GParted",
            "GParted is required for partition management. Would you like to install it?"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("install", "Install")
        dialog.set_response_appearance("install", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", self._on_gparted_install_response)
        dialog.present()

    def _on_gnome_disks_install_response(self, dialog, response):
        if response == "install":
            self.prompt_for_password("gnome-disk-utility")

    def _on_gparted_install_response(self, dialog, response):
        if response == "install":
            self.prompt_for_password("gparted")

    def prompt_for_password(self, package_name):
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Authentication Required",
            f"Enter your root password to install {package_name}:"
        )
        
        password_entry = Gtk.PasswordEntry()
        password_entry.set_show_peek_icon(True)
        dialog.set_extra_child(password_entry)
        
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("authenticate", "Authenticate")
        dialog.set_response_appearance("authenticate", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", self._on_password_entered, password_entry, package_name)
        dialog.present()

    def _on_password_entered(self, dialog, response, password_entry, package_name):
        if response == "authenticate":
            password = password_entry.get_text()
            if password:
                self.install_package(password, package_name)

    def install_package(self, password, package_name):
        progress_dialog = Adw.MessageDialog.new(
            self.get_root(),
            f"Installing {package_name}",
            f"Please wait while {package_name} is being installed..."
        )
        progress_dialog.present()

        def install_thread():
            try:
                # Create temporary script file
                script_content = f"""#!/bin/bash
set -e

# Function to handle dnf output
handle_output() {{
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
}}

# Update package cache
echo "PROGRESS:10:Refreshing package cache..."
dnf makecache 2>&1 | handle_output

# Install package
echo "PROGRESS:20:Starting installation..."
dnf install -y {package_name} 2>&1 | handle_output
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
                        GLib.idle_add(progress_dialog.set_body, message)
                        GLib.idle_add(progress_dialog.set_subtitle, f"{percent}%")
                    elif line.startswith("INFO:"):
                        _, message = line.strip().split(":", 1)
                        GLib.idle_add(progress_dialog.set_body, message)
                
                # Check if process was successful
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, "pkexec")
                
                # Remove temporary script
                os.unlink(script_path)
                
                # Launch GNOME Disks after successful installation
                if package_name == "gnome-disk-utility":
                    GLib.idle_add(lambda: subprocess.Popen(['gnome-disks']))
                else:
                    GLib.idle_add(lambda: self.show_success_dialog(f"{package_name} has been successfully installed!"))
                GLib.idle_add(progress_dialog.close)
                
            except Exception as e:
                GLib.idle_add(progress_dialog.close)
                GLib.idle_add(lambda: self.show_error_dialog(
                    f"Failed to install {package_name}: {str(e)}"
                ))
        
        thread = threading.Thread(target=install_thread)
        thread.daemon = True
        thread.start()

    def show_success_and_launch(self, package_name):
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Installation Successful",
            f"{package_name} has been installed successfully."
        )
        dialog.add_response("ok", "OK")
        dialog.connect("response", lambda d, r: self.launch_after_install(package_name))
        dialog.present()

    def launch_after_install(self, package_name):
        if package_name == "gnome-disk-utility":
            self.launch_gnome_disks()
        elif package_name == "gparted":
            self.launch_gparted()

    def update_progress_dialog(self, dialog, message):
        dialog.set_body(message)
        return False

    def show_error_dialog(self, message: str):
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Error",
            message
        )
        dialog.add_response("ok", "OK")
        dialog.present()

    def on_back_clicked(self, button):
        self.parent.show_main()


class SoundPage(Gtk.Box):
    def __init__(self, parent):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.parent = parent
        
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        
        # Create main page
        self.main_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Create title box
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        title_box.set_margin_top(20)
        title_box.set_margin_bottom(20)
        title_box.set_margin_start(20)
        title_box.set_margin_end(20)
        
        # Add title
        title_label = Gtk.Label()
        title_label.set_markup("<span size='large'>Sound Settings</span>")
        title_label.set_margin_start(10)
        title_box.append(title_label)
        
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        
        self.main_page.append(title_box)
        self.main_page.append(separator)
        
        # Create grid for options
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(10)
        grid.set_margin_top(20)
        grid.set_margin_bottom(20)
        grid.set_margin_start(20)
        grid.set_margin_end(20)
        
        # Add options
        options = [
            ("Configure Sound", "preferences-system-symbolic", "Configure sound devices and settings"),
            ("Sound Volume", "audio-volume-high-symbolic", "Adjust system volume levels"),
            ("Sound Backend", "audio-card-symbolic", "Choose between PipeWire and PulseAudio"),
            ("Manage ALSA", "audio-speakers-symbolic", "Configure ALSA backend settings"),
            ("Manage JACK", "audio-input-microphone-symbolic", "Configure JACK audio settings")
        ]
        
        for i, (title, icon_name, description) in enumerate(options):
            button = self.create_option_button(title, icon_name, description)
            grid.attach(button, i % 2, i // 2, 1, 1)
        
        self.main_page.append(grid)
        
        # Add pages to stack
        self.stack.add_named(self.main_page, "main")
        self.append(self.stack)

    def on_option_clicked(self, button, title):
        if title == "Configure Sound":
            self.launch_pavucontrol()
        elif title == "Sound Volume":
            if not hasattr(self, 'volume_page'):
                self.volume_page = VolumeControlPage(self)
                self.stack.add_named(self.volume_page, "volume")
            self.stack.set_visible_child_name("volume")
        elif title == "Sound Backend":
            self.show_backend_selection()
        elif title == "Manage ALSA":
            self.show_alsa_selection()
        elif title == "Manage JACK":
            self.show_jack_selection()

    def show_main(self):
        self.stack.set_visible_child_name("main")

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

    def show_backend_selection(self):
        # First check which backend is currently installed
        def check_package_installed(package_name):
            try:
                result = subprocess.run(
                    ["rpm", "-q", package_name],
                    capture_output=True,
                    text=True
                )
                return result.returncode == 0
            except Exception:
                return False

        is_pipewire = check_package_installed("pipewire-pulse")
        is_pulseaudio = check_package_installed("pulseaudio-server")

        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Select Sound Backend",
            "Choose your preferred sound backend:"
        )
        
        # Create radio buttons for backend selection
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        
        pipewire_btn = Gtk.CheckButton()
        pipewire_btn.set_label("PipeWire (Modern audio server)")
        box.append(pipewire_btn)
        
        pulseaudio_btn = Gtk.CheckButton()
        pulseaudio_btn.set_label("PulseAudio (Traditional audio server)")
        pulseaudio_btn.set_group(pipewire_btn)
        box.append(pulseaudio_btn)

        # Set the active backend based on what's installed
        if is_pipewire:
            pipewire_btn.set_active(True)
        elif is_pulseaudio:
            pulseaudio_btn.set_active(True)
        else:
            # Default to PipeWire if neither is installed
            pipewire_btn.set_active(True)
        
        dialog.set_extra_child(box)
        
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("ok", "Apply")
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
        
        dialog.connect("response", self._on_backend_selected, pipewire_btn)
        dialog.present()

    def _on_backend_selected(self, dialog, response, pipewire_btn):
        if response == "ok":
            if pipewire_btn.get_active():
                self.switch_to_pipewire()
            else:
                self.switch_to_pulseaudio()

    def switch_to_pipewire(self):
        self.prompt_for_password("PipeWire", [
            "dnf remove -y pulseaudio-server",
            "dnf install -y pipewire-pulse"
        ])

    def switch_to_pulseaudio(self):
        self.prompt_for_password("PulseAudio", [
            "dnf remove -y pipewire-pulse",
            "dnf install -y pulseaudio-server"
        ])

    def prompt_for_password(self, backend_name, commands):
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Authentication Required",
            f"Enter your root password to switch to {backend_name}:"
        )
        
        # Create password entry
        password_entry = Gtk.PasswordEntry()
        password_entry.set_show_peek_icon(True)
        dialog.set_extra_child(password_entry)
        
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("authenticate", "Authenticate")
        dialog.set_response_appearance("authenticate", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", self._on_password_entered, password_entry, backend_name, commands)
        dialog.present()

    def _on_password_entered(self, dialog, response, password_entry, backend_name, commands):
        if response == "authenticate":
            password = password_entry.get_text()
            if password:
                self.switch_backend(password, backend_name, commands)

    def switch_backend(self, password, backend_name, commands):
        progress_dialog = Adw.MessageDialog.new(
            self.get_root(),
            f"Switching to {backend_name}",
            f"Please wait while switching to {backend_name}..."
        )
        progress_dialog.present()

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

"""
                for cmd in commands:
                    script_content += f"echo \"{password}\" | sudo -S {cmd} 2>&1 | handle_output\n"
                
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
                        GLib.idle_add(progress_dialog.set_body, message)
                        GLib.idle_add(progress_dialog.set_subtitle, f"{percent}%")
                    elif line.startswith("INFO:"):
                        _, message = line.strip().split(":", 1)
                        GLib.idle_add(progress_dialog.set_body, message)
                
                # Check if process was successful
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, "pkexec")
                
                # Remove temporary script
                os.unlink(script_path)
                
                GLib.idle_add(self.show_result_dialog, True, 
                    f"Successfully switched to {backend_name}! Please restart your system for changes to take effect.")
                GLib.idle_add(progress_dialog.close)
                
            except Exception as e:
                GLib.idle_add(self.show_result_dialog, False, f"Error during backend switch: {str(e)}")
                GLib.idle_add(progress_dialog.close)

        thread = threading.Thread(target=install_thread)
        thread.daemon = True
        thread.start()

    def update_progress_dialog(self, dialog, message):
        dialog.set_body(message)
        return False

    def show_result_dialog(self, success: bool, message: str):
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Backend Switch " + ("Successful" if success else "Failed"),
            message
        )
        dialog.add_response("ok", "OK")
        dialog.present()
        return False

    def launch_pavucontrol(self):
        pavucontrol_path = Path("/usr/bin/pavucontrol-gtk")
        if pavucontrol_path.exists():
            try:
                subprocess.Popen([str(pavucontrol_path)])
            except Exception as e:
                self.show_error_dialog(f"Failed to launch pavucontrol: {str(e)}")
        else:
            self.install_pavucontrol()

    def install_pavucontrol(self):
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Install PulseAudio Volume Control",
            "The pavucontrol application is required for advanced sound settings. Would you like to install it?"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("install", "Install")
        dialog.set_response_appearance("install", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", self._on_pavucontrol_install_response)
        dialog.present()

    def _on_pavucontrol_install_response(self, dialog, response):
        if response == "install":
            self.prompt_for_pavucontrol_password()

    def prompt_for_pavucontrol_password(self):
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Authentication Required",
            "Enter your root password to install pavucontrol:"
        )
        
        password_entry = Gtk.PasswordEntry()
        password_entry.set_show_peek_icon(True)
        dialog.set_extra_child(password_entry)
        
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("authenticate", "Authenticate")
        dialog.set_response_appearance("authenticate", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", self._on_pavucontrol_password_entered, password_entry)
        dialog.present()

    def _on_pavucontrol_password_entered(self, dialog, response, password_entry):
        if response == "authenticate":
            password = password_entry.get_text()
            if password:
                self.install_pavucontrol_package(password)

    def install_pavucontrol_package(self, password):
        progress_dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Installing PulseAudio Volume Control",
            "Please wait while pavucontrol is being installed..."
        )
        progress_dialog.present()

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
dnf install -y pavucontrol 2>&1 | handle_output
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
                        GLib.idle_add(progress_dialog.set_body, message)
                        GLib.idle_add(progress_dialog.set_subtitle, f"{percent}%")
                    elif line.startswith("INFO:"):
                        _, message = line.strip().split(":", 1)
                        GLib.idle_add(progress_dialog.set_body, message)
                
                # Check if process was successful
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, "pkexec")
                
                # Remove temporary script
                os.unlink(script_path)
                
                GLib.idle_add(self.show_success_and_launch_pavucontrol)
                GLib.idle_add(progress_dialog.close)
                
            except Exception as e:
                GLib.idle_add(progress_dialog.close)
                GLib.idle_add(lambda: self.show_error_dialog(
                    f"Failed to install pavucontrol: {str(e)}"
                ))
        
        thread = threading.Thread(target=install_thread)
        thread.daemon = True
        thread.start()

    def show_success_and_launch_pavucontrol(self):
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Installation Successful",
            "PulseAudio Volume Control has been installed successfully."
        )
        dialog.add_response("ok", "OK")
        dialog.connect("response", lambda d, r: self.launch_pavucontrol())
        dialog.present()

    def show_error_dialog(self, message: str):
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Error",
            message
        )
        dialog.add_response("ok", "OK")
        dialog.present()

    def show_alsa_selection(self):
        def check_package_installed(package_name):
            try:
                result = subprocess.run(
                    ["rpm", "-q", package_name],
                    capture_output=True,
                    text=True
                )
                return result.returncode == 0
            except Exception:
                return False

        is_pipewire_alsa = check_package_installed("pipewire-alsa")
        is_pulseaudio_alsa = check_package_installed("lib64alsa-plugins-pulseaudio")

        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Configure ALSA Backend",
            "Choose your preferred ALSA configuration:"
        )
        
        # Create radio buttons for ALSA selection
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        
        basic_alsa_btn = Gtk.CheckButton()
        basic_alsa_btn.set_label("Basic ALSA (Hardware direct)")
        box.append(basic_alsa_btn)
        
        pipewire_alsa_btn = Gtk.CheckButton()
        pipewire_alsa_btn.set_label("PipeWire ALSA (Modern audio)")
        pipewire_alsa_btn.set_group(basic_alsa_btn)
        box.append(pipewire_alsa_btn)
        
        pulseaudio_alsa_btn = Gtk.CheckButton()
        pulseaudio_alsa_btn.set_label("PulseAudio ALSA (Traditional audio)")
        pulseaudio_alsa_btn.set_group(basic_alsa_btn)
        box.append(pulseaudio_alsa_btn)

        # Set active based on what's installed
        if is_pipewire_alsa:
            pipewire_alsa_btn.set_active(True)
        elif is_pulseaudio_alsa:
            pulseaudio_alsa_btn.set_active(True)
        else:
            basic_alsa_btn.set_active(True)
        
        dialog.set_extra_child(box)
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("ok", "Apply")
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
        
        dialog.connect("response", self._on_alsa_selected, basic_alsa_btn, pipewire_alsa_btn)
        dialog.present()

    def _on_alsa_selected(self, dialog, response, basic_btn, pipewire_btn):
        if response == "ok":
            if basic_btn.get_active():
                self.switch_to_basic_alsa()
            elif pipewire_btn.get_active():
                self.switch_to_pipewire_alsa()
            else:
                self.switch_to_pulseaudio_alsa()

    def show_jack_selection(self):
        def check_package_installed(package_name):
            try:
                result = subprocess.run(
                    ["rpm", "-q", package_name],
                    capture_output=True,
                    text=True
                )
                return result.returncode == 0
            except Exception:
                return False

        is_jack = check_package_installed("jackit")
        is_pipewire_jack = check_package_installed("pipewire-libjack")
        is_pulseaudio_jack = check_package_installed("pulseaudio-module-jack")

        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Configure JACK Backend",
            "Choose your preferred JACK configuration:"
        )
        
        # Create radio buttons for JACK selection
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        
        jack_btn = Gtk.CheckButton()
        jack_btn.set_label("JACK (Professional audio server)")
        box.append(jack_btn)
        
        pipewire_jack_btn = Gtk.CheckButton()
        pipewire_jack_btn.set_label("PipeWire JACK (Modern audio)")
        pipewire_jack_btn.set_group(jack_btn)
        box.append(pipewire_jack_btn)
        
        pulseaudio_jack_btn = Gtk.CheckButton()
        pulseaudio_jack_btn.set_label("PulseAudio JACK (Traditional audio)")
        pulseaudio_jack_btn.set_group(jack_btn)
        box.append(pulseaudio_jack_btn)

        # Set active based on what's installed
        if is_pipewire_jack:
            pipewire_jack_btn.set_active(True)
        elif is_pulseaudio_jack:
            pulseaudio_jack_btn.set_active(True)
        elif is_jack:
            jack_btn.set_active(True)
        else:
            pipewire_jack_btn.set_active(True)  # Default to PipeWire JACK
        
        dialog.set_extra_child(box)
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("ok", "Apply")
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
        
        dialog.connect("response", self._on_jack_selected, jack_btn, pipewire_jack_btn)
        dialog.present()

    def _on_jack_selected(self, dialog, response, jack_btn, pipewire_btn):
        if response == "ok":
            if jack_btn.get_active():
                self.switch_to_jack()
            elif pipewire_btn.get_active():
                self.switch_to_pipewire_jack()
            else:
                self.switch_to_pulseaudio_jack()

    def switch_to_basic_alsa(self):
        # Remove other ALSA implementations
        self.prompt_for_password("Basic ALSA", [
            "dnf remove -y pipewire-alsa lib64alsa-plugins-pulseaudio"
        ])

    def switch_to_pipewire_alsa(self):
        self.prompt_for_password("PipeWire ALSA", [
            "dnf remove -y lib64alsa-plugins-pulseaudio",
            "dnf install -y pipewire-alsa"
        ])

    def switch_to_pulseaudio_alsa(self):
        self.prompt_for_password("PulseAudio ALSA", [
            "dnf remove -y pipewire-alsa",
            "dnf install -y lib64alsa-plugins-pulseaudio"
        ])

    def switch_to_jack(self):
        self.prompt_for_password("JACK", [
            "dnf remove -y pipewire-libjack pulseaudio-module-jack",
            "dnf install -y jackit"
        ])

    def switch_to_pipewire_jack(self):
        self.prompt_for_password("PipeWire JACK", [
            "dnf remove -y jackit pulseaudio-module-jack",
            "dnf install -y pipewire-libjack"
        ])

    def switch_to_pulseaudio_jack(self):
        self.prompt_for_password("PulseAudio JACK", [
            "dnf remove -y jackit pipewire-libjack",
            "dnf install -y pulseaudio-module-jack"
        ])

    def on_back_clicked(self, button):
        self.stack.set_visible_child_name("main")
        self.parent.stack.set_visible_child_name("main")


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def on_option_clicked(self, button, title):
        if title == "Hardware":
            if not hasattr(self, 'hardware_page'):
                self.hardware_page = HardwarePage(self)
                self.stack.add_named(self.hardware_page, "hardware")
            self.hardware_page.stack.set_visible_child_name("main")  # Always show hardware main menu
            self.stack.set_visible_child_name("hardware")
        elif title == "Sound":
            if not hasattr(self, 'sound_page'):
                self.sound_page = SoundPage(self)
                self.stack.add_named(self.sound_page, "sound")
            self.stack.set_visible_child_name("sound")

    def on_printer_clicked(self, button):
        try:
            subprocess.run(['which', 'system-config-printer'], check=True)
            subprocess.Popen(['system-config-printer'])
        except subprocess.CalledProcessError:
            dialog = Adw.MessageDialog.new(
                self.get_root(),
                "Install Printer Configuration Tool",
                "The printer configuration tool is not installed. Would you like to install it now?"
            )
            dialog.add_response("cancel", "Cancel")
            dialog.add_response("install", "Install")
            dialog.set_default_response("install")
            dialog.connect("response", self.on_printer_install_response)
            dialog.present()

    def on_printer_install_response(self, dialog, response):
        if response == "install":
            # Create progress dialog
            progress_dialog = Adw.MessageDialog.new(
                self.get_root(),
                "Installing Printer Configuration Tool",
                "Please wait while the application is being installed..."
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
dnf install -y system-config-printer-gui 2>&1 | handle_output
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
                    
                    # Launch printer configuration tool
                    GLib.idle_add(lambda: subprocess.Popen(['system-config-printer']))
                    GLib.idle_add(progress_dialog.close)
                    
                except Exception as e:
                    GLib.idle_add(progress_dialog.close)
                    GLib.idle_add(lambda: self.show_error_dialog(
                        "Installation Error",
                        f"Failed to install printer configuration tool.\nError: {str(e)}"
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
