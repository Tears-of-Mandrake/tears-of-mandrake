#!/usr/bin/env python3
import gi
import subprocess
import threading
import sys
import os
from typing import List, Optional, Tuple

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, GObject

class UpdateManagerApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id='org.tearsofmandrake.updater',
                        flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect('activate', self.on_activate)
        
    def on_activate(self, app):
        self.win = UpdateManager(application=app)
        self.win.present()

class UpdateManager(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.set_default_size(800, 600)
        self.set_title("System Update Manager")
        
        # Main layout
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_content(self.main_box)
        
        # Header bar
        header = Adw.HeaderBar()
        self.main_box.append(header)
        
        # Package list
        self.package_list = Gtk.ListBox()
        self.package_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.package_list.add_css_class("boxed-list")
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(300)
        scrolled.set_child(self.package_list)
        self.main_box.append(scrolled)
        
        # Progress area
        self.progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.progress_box.set_margin_top(10)
        self.progress_box.set_margin_bottom(10)
        self.progress_box.set_margin_start(10)
        self.progress_box.set_margin_end(10)
        self.main_box.append(self.progress_box)
        
        self.status_label = Gtk.Label()
        self.status_label.set_wrap(True)
        self.status_label.set_xalign(0)
        self.progress_box.append(self.status_label)
        
        self.progress_bar = Gtk.ProgressBar()
        self.progress_box.append(self.progress_bar)
        
        # Action buttons
        self.action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.action_box.set_halign(Gtk.Align.END)
        self.action_box.set_margin_top(10)
        self.action_box.set_margin_bottom(10)
        self.action_box.set_margin_start(10)
        self.action_box.set_margin_end(10)
        self.main_box.append(self.action_box)
        
        self.refresh_button = Gtk.Button(label="Check for Updates")
        self.refresh_button.connect("clicked", self.check_updates)
        self.action_box.append(self.refresh_button)
        
        self.update_button = Gtk.Button(label="Update System")
        self.update_button.add_css_class("suggested-action")
        self.update_button.connect("clicked", self.on_update_clicked)
        self.action_box.append(self.update_button)
        
        # Initial state
        self.progress_box.set_visible(False)
        self.update_button.set_sensitive(False)
        self.check_updates()

    def add_package_row(self, package_info):
        """Add a package row to the list with action type and details"""
        row = Gtk.ListBoxRow()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_margin_top(5)
        box.set_margin_bottom(5)
        box.set_margin_start(10)
        box.set_margin_end(10)
        
        # Package info box (left side)
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Package name with arch
        name_label = Gtk.Label(label=f"{package_info['name']} ({package_info['arch']})")
        name_label.set_xalign(0)
        name_label.add_css_class("heading")
        info_box.append(name_label)
        
        # Version and size
        details = []
        if "version" in package_info:
            details.append(package_info["version"])
        if "size" in package_info:
            details.append(package_info["size"])
        
        if details:
            version_label = Gtk.Label()
            version_label.set_markup(f'<span size="small">{" - ".join(details)}</span>')
            version_label.set_xalign(0)
            info_box.append(version_label)
        
        box.append(info_box)
        
        # Action type (right side)
        action_label = Gtk.Label()
        action_label.add_css_class("caption")
        
        action_colors = {
            "upgrade": "#2ec27e",    # Green
            "reinstall": "#1c71d8",  # Blue
            "downgrade": "#e66100",  # Orange
            "install": "#3584e4",    # Light Blue
            "remove": "#c01c28"      # Red
        }
        
        action_text = package_info["action"].capitalize()
        color = action_colors.get(package_info["action"], "#888888")
        action_label.set_markup(f'<span color="{color}">{action_text}</span>')
        
        box.append(action_label)
        
        row.set_child(box)
        self.package_list.append(row)

    def clear_package_list(self):
        while True:
            row = self.package_list.get_first_child()
            if row is None:
                break
            self.package_list.remove(row)

    def check_updates(self, button=None):
        self.clear_package_list()
        self.status_label.set_markup("<i>Checking for updates...</i>")
        self.progress_box.set_visible(True)
        self.progress_bar.set_fraction(0.0)
        self.update_button.set_sensitive(False)
        
        def check_thread():
            try:
                # Use pkexec with sh -c to run both commands with a single root prompt
                process = subprocess.Popen(
                    ["pkexec", "sh", "-c", "dnf5 clean all && dnf5 distro-sync --assumeno"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                output, error = process.communicate()
                updates = []
                current_section = None
                
                for line in output.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Track sections
                    if line.startswith("Reinstalling:"):
                        current_section = "reinstall"
                        continue
                    elif line.startswith("Upgrading:"):
                        current_section = "upgrade"
                        continue
                    elif line.startswith("Downgrading:"):
                        current_section = "downgrade"
                        continue
                    elif line.startswith("Installing:"):
                        current_section = "install"
                        continue
                    elif line.startswith("Removing:"):
                        current_section = "remove"
                        continue
                    elif line.startswith("Transaction Summary:"):
                        break
                    
                    # Parse package lines
                    if current_section and not line.startswith(" ") and not line.startswith("replacing"):
                        try:
                            parts = line.split()
                            if len(parts) >= 3:  # name arch version repo size
                                package_info = {
                                    "name": parts[0],
                                    "arch": parts[1],
                                    "version": parts[2],
                                    "action": current_section
                                }
                                
                                # Try to get size if available
                                if len(parts) >= 5:
                                    package_info["size"] = f"{parts[-2]} {parts[-1]}"
                                
                                updates.append(package_info)
                        except Exception as e:
                            print(f"Error parsing package line: {str(e)}")
                            continue
                
                GLib.idle_add(self.update_package_list, updates)
                
            except Exception as e:
                GLib.idle_add(
                    self.status_label.set_markup,
                    f"<span color='red'>Error checking updates: {str(e)}</span>"
                )
        
        thread = threading.Thread(target=check_thread)
        thread.daemon = True
        thread.start()

    def update_package_list(self, updates):
        self.clear_package_list()
        if updates:
            for package in updates:
                self.add_package_row(package)
            self.status_label.set_markup(
                f"<i>{len(updates)} package{'s' if len(updates) != 1 else ''} to update</i>"
            )
            self.update_button.set_sensitive(True)
        else:
            self.status_label.set_markup("<i>System is up to date</i>")
            self.update_button.set_sensitive(False)
        self.progress_bar.set_fraction(1.0)

    def on_update_clicked(self, button):
        self.start_update()

    def start_update(self):
        self.progress_box.set_visible(True)
        self.progress_bar.set_visible(True)
        self.progress_bar.set_fraction(0.0)
        self.package_list.set_visible(False)
        self.action_box.set_visible(True)
        self.status_label.set_visible(True)
        self.refresh_button.set_sensitive(False)
        self.update_button.set_sensitive(False)
        
        def update_thread():
            try:
                self.status_label.set_markup("<i>Starting system update...</i>")
                self.update_process = subprocess.Popen(
                    ["pkexec", "dnf5", "distro-sync", "-y"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    bufsize=1
                )
                
                updated_packages = []
                total_size = None
                current_phase = None
                current_item = 0
                total_items = 0
                
                while True:
                    output = self.update_process.stdout.readline()
                    if output == '' and self.update_process.poll() is not None:
                        break
                    if output:
                        output = output.strip()
                        print(f"DNF5 Output: {output}")
                        
                        # Parse total size
                        if "Total size of inbound packages is" in output:
                            try:
                                total_size = output.split("is")[1].split(".")[0].strip()
                                GLib.idle_add(
                                    self.status_label.set_markup,
                                    f"<i>Total download size: {total_size}</i>"
                                )
                            except Exception as e:
                                print(f"Error parsing total size: {str(e)}")
                        
                        # Parse progress lines [X/Y]
                        elif "[" in output and "]" in output:
                            try:
                                progress_part = output[output.find("[")+1:output.find("]")]
                                current_item, total_items = map(int, progress_part.split("/"))
                                
                                # Extract package name and progress
                                rest = output[output.find("]")+1:].strip()
                                
                                if "%" in output:  # Download/Install progress
                                    parts = rest.split("%", 1)
                                    package_name = parts[0].strip()
                                    progress = float(package_name.split()[-1])
                                    package_name = " ".join(package_name.split()[:-1])
                                    
                                    # Extract speed and size if available
                                    extra_info = ""
                                    if "|" in parts[1]:
                                        details = parts[1].split("|")
                                        if len(details) >= 3:
                                            speed = details[1].strip()
                                            size = details[2].strip()
                                            extra_info = f"\nSpeed: {speed}\nSize: {size}"
                                    
                                    status = f"<i>Processing [{current_item}/{total_items}]:\n{package_name}\n{progress}%{extra_info}</i>"
                                    GLib.idle_add(
                                        self.status_label.set_markup,
                                        status
                                    )
                                    GLib.idle_add(
                                        self.progress_bar.set_fraction,
                                        progress / 100.0
                                    )
                                
                                # Update overall progress
                                overall_progress = current_item / total_items
                                GLib.idle_add(
                                    self.progress_bar.set_fraction,
                                    overall_progress
                                )
                            
                            except Exception as e:
                                print(f"Error parsing progress: {str(e)}")
                        
                        # Track transaction phases
                        elif "Running transaction" in output:
                            current_phase = "install"
                            GLib.idle_add(
                                self.status_label.set_markup,
                                "<i>Running transaction...</i>"
                            )
                        elif "Verify package files" in output:
                            current_phase = "verify"
                            GLib.idle_add(
                                self.status_label.set_markup,
                                "<i>Verifying package files...</i>"
                            )
                        elif "Prepare transaction" in output:
                            current_phase = "prepare"
                            GLib.idle_add(
                                self.status_label.set_markup,
                                "<i>Preparing transaction...</i>"
                            )
                
                return_code = self.update_process.poll()
                if return_code == 0:
                    GLib.idle_add(
                        self.show_success_dialog,
                        "Update Complete",
                        "System has been successfully updated.",
                        updated_packages
                    )
                else:
                    error = self.update_process.stderr.read()
                    GLib.idle_add(
                        self.show_error_dialog,
                        "Update Failed",
                        f"Error updating system: {error}"
                    )
            
            except Exception as e:
                GLib.idle_add(
                    self.show_error_dialog,
                    "Update Error",
                    f"Error during update: {str(e)}"
                )
            finally:
                GLib.idle_add(self.on_update_complete)
        
        thread = threading.Thread(target=update_thread)
        thread.daemon = True
        thread.start()

    def on_update_complete(self):
        self.progress_box.set_visible(True)
        self.package_list.set_visible(True)
        self.action_box.set_visible(True)
        self.refresh_button.set_sensitive(True)
        self.update_button.set_sensitive(False)

    def show_success_dialog(self, title, message, updated_packages):
        # Update the status label with success message and package list
        success_msg = (
            '<span color="#2ec27e">'
            '<b>✓ System Update Completed Successfully</b>\n'
            'The following packages have been updated:\n'
            '</span>'
        )
        
        # Create a list of updated packages with their actions
        package_list = []
        for pkg in updated_packages:
            action_colors = {
                "upgrade": "#2ec27e",    # Green
                "reinstall": "#1c71d8",  # Blue
                "downgrade": "#e66100",  # Orange
                "install": "#3584e4",    # Light Blue
                "remove": "#c01c28"      # Red
            }
            color = action_colors.get(pkg["action"], "#888888")
            action = pkg["action"].capitalize()
            package_list.append(
                f'<span color="{color}">{action}</span>: '
                f'{pkg["name"]} ({pkg["arch"]}) - {pkg.get("version", "")}'
            )
        
        # Add the package list to the message
        if package_list:
            package_text = "\n".join([f"• {pkg}" for pkg in package_list])
            success_msg += "\n" + package_text + "\n"
        
        # Add restart notice
        success_msg += (
            '\n<span color="#2ec27e">'
            'You may need to restart some applications or your system '
            'for all changes to take effect.'
            '</span>'
        )
        
        self.status_label.set_markup(success_msg)
        self.progress_bar.set_fraction(1.0)
        
        # Show a non-blocking success toast
        toast = Adw.Toast.new(message)
        toast.set_timeout(3)
        self.add_toast(toast)

    def show_error_dialog(self, title, message):
        # Update the status label with error message
        self.status_label.set_markup(
            f'<span color="#c01c28">'
            f'<b>⚠ Update Error</b>\n\n'
            f'{message}\n\n'
            f'Please try again later or check the system logs for more information.'
            f'</span>'
        )
        self.progress_bar.set_fraction(0.0)
        
        # Show a non-blocking error toast
        toast = Adw.Toast.new("Update failed. Check the error message for details.")
        toast.set_timeout(5)
        self.add_toast(toast)

def main():
    app = UpdateManagerApp()
    return app.run(sys.argv)

if __name__ == "__main__":
    main()
