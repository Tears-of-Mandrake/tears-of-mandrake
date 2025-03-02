import gi
import subprocess
import threading
import os
import tempfile
from pathlib import Path
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio

ICONS_DIR = "/usr/share/tears-of-mandrake/images"

class ExternalApplication:
    def __init__(self, name, package, binary_path, description, icon_name, repo_content, repo_path, key_url=None):
        self.name = name
        self.package = package
        self.binary_path = binary_path
        self.description = description
        self.icon_name = icon_name
        self.repo_content = repo_content
        self.repo_path = repo_path
        self.key_url = key_url

class DownloadManagerPage(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        self.append(scrolled)
        
        # Create main content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content_box.set_margin_top(10)
        content_box.set_margin_bottom(10)
        content_box.set_margin_start(10)
        content_box.set_margin_end(10)
        scrolled.set_child(content_box)
        
        # Define applications
        self.applications = [
            ExternalApplication(
                "Opera Browser",
                "opera-stable",
                "/usr/bin/opera",
                "Fast and secure web browser",
                "opera",
                """[opera]
name=Opera Browser
type=rpm-md
baseurl=https://rpm.opera.com/rpm
gpgcheck=1
gpgkey=https://rpm.opera.com/rpmrepo.key
enabled=1""",
                "/etc/yum.repos.d/opera.repo",
                "https://rpm.opera.com/rpmrepo.key"
            ),
            ExternalApplication(
                "Brave Browser",
                "brave-browser",
                "/usr/bin/brave-browser",
                "Privacy-focused web browser",
                "brave",
                """[brave-browser]
name=Brave Browser
baseurl=https://brave-browser-rpm-release.s3.brave.com/x86_64/
enabled=1
gpgcheck=1
gpgkey=https://brave-browser-rpm-release.s3.brave.com/brave-core.asc""",
                "/etc/yum.repos.d/brave-browser.repo"
            ),
            ExternalApplication(
                "Google Chrome",
                "google-chrome-stable",
                "/usr/bin/google-chrome",
                "Popular web browser from Google",
                "google-chrome",
                """[google-chrome]
name=Google Chrome
baseurl=https://dl.google.com/linux/chrome/rpm/stable/$basearch
enabled=1
gpgcheck=0""",
                "/etc/yum.repos.d/google-chrome.repo"
            ),
            ExternalApplication(
                "Vivaldi Browser",
                "vivaldi-stable",
                "/usr/bin/vivaldi",
                "Feature-rich web browser",
                "vivaldi",
                """[vivaldi]
name=Vivaldi browser
baseurl=https://repo.vivaldi.com/archive/rpm/x86_64
enabled=1
gpgcheck=0""",
                "/etc/yum.repos.d/vivaldi.repo"
            ),
            ExternalApplication(
                "Microsoft Edge",
                "microsoft-edge-stable",
                "/usr/bin/microsoft-edge",
                "Chromium-based browser from Microsoft",
                "microsoft-edge",
                """[microsoft-edge]
name=Microsoft Edge
baseurl=https://packages.microsoft.com/yumrepos/edge
enabled=1
gpgcheck=1
gpgkey=https://packages.microsoft.com/keys/microsoft.asc""",
                "/etc/yum.repos.d/microsoft-edge.repo"
            ),
            ExternalApplication(
                "Visual Studio Code",
                "code",
                "/usr/bin/code",
                "Popular code editor from Microsoft",
                "vscode",
                """[code]
name=Visual Studio Code
baseurl=https://packages.microsoft.com/yumrepos/vscode
enabled=1
gpgcheck=1
gpgkey=https://packages.microsoft.com/keys/microsoft.asc""",
                "/etc/yum.repos.d/vscode.repo",
                "https://packages.microsoft.com/keys/microsoft.asc"
            )
        ]
        
        # Add applications to the window
        self.add_applications(content_box)
    
    def add_applications(self, content_box):
        # Add description label
        desc_label = Gtk.Label()
        desc_label.set_markup("<span size='small'>This is a list of external applications (independent of OpenMandriva) whose repositories can be added to the system.</span>")
        desc_label.set_wrap(True)
        desc_label.set_margin_bottom(10)
        desc_label.set_halign(Gtk.Align.START)
        content_box.append(desc_label)

        group = Adw.PreferencesGroup()
        
        # Add header
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header_icon = Gtk.Image.new_from_icon_name("folder-download-symbolic")
        header_box.append(header_icon)
        
        header_label = Gtk.Label()
        header_label.set_markup("<span size='large' weight='bold'>External Applications</span>")
        header_box.append(header_label)
        
        group.set_header_suffix(header_box)
        
        # Add applications
        for app in self.applications:
            row = Adw.ActionRow()
            row.set_title(app.name)
            row.set_subtitle(app.description)
            
            # Application icon
            icon_path = os.path.join(ICONS_DIR, app.icon_name)
            if os.path.exists(f"{icon_path}.png"):
                app_icon = Gtk.Image.new_from_file(f"{icon_path}.png")
            elif os.path.exists(f"{icon_path}.svg"):
                app_icon = Gtk.Image.new_from_file(f"{icon_path}.svg")
            else:
                app_icon = Gtk.Image.new_from_icon_name("application-x-executable")
            app_icon.set_pixel_size(32)
            row.add_prefix(app_icon)
            
            # Create button box for progress label and button
            button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            
            # Add progress label (hidden by default)
            progress_label = Gtk.Label()
            progress_label.set_visible(False)
            button_box.append(progress_label)
            
            # Check if app is installed
            is_installed = os.path.exists(app.binary_path) if app.binary_path else False
            
            # Add action button
            if is_installed:
                button = Gtk.Button(label="Launch")
                button.add_css_class("success")
                button.connect("clicked", self.on_launch_clicked, app)
            else:
                button = Gtk.Button(label="Install")
                button.add_css_class("suggested-action")
                button.connect("clicked", self.on_install_clicked, app, progress_label)
            
            button_box.append(button)
            row.add_suffix(button_box)
            group.add(row)
        
        content_box.append(group)
    
    def on_launch_clicked(self, button, app):
        try:
            subprocess.Popen([app.binary_path])
        except Exception as e:
            self.show_error_dialog(f"Error launching {app.name}", str(e))
    
    def on_install_clicked(self, button, app, progress_label):
        button.set_sensitive(False)
        button.set_label("Installing...")
        
        # Create progress dialog
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            f"Installing {app.name}",
            "Please wait while the application is being installed..."
        )
        dialog.add_response("cancel", "Cancel")
        
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
        dialog.set_extra_child(progress_box)
        dialog.present()
        
        def update_progress(fraction, text):
            progress_bar.set_fraction(fraction)
            status_label.set_markup(f"<span size='small'>{text}</span>")
        
        def install_thread():
            try:
                steps = []
                if app.key_url:
                    steps.append(("Importing signing key...", 0.2))
                steps.extend([
                    ("Adding repository...", 0.4),
                    ("Refreshing package cache...", 0.6),
                    ("Installing package...", 0.8),
                    ("Finalizing installation...", 1.0)
                ])
                
                current_step = 0
                
                # Create a temporary script with all commands
                script_content = "#!/bin/bash\n\n"
                
                # Add key import if needed
                if app.key_url:
                    GLib.idle_add(update_progress, steps[current_step][1], steps[current_step][0])
                    script_content += f"rpm --import {app.key_url}\n"
                    current_step += 1
                
                # Add repo file creation
                GLib.idle_add(update_progress, steps[current_step][1], steps[current_step][0])
                script_content += f"cat > {app.repo_path} << 'EOF'\n{app.repo_content}\nEOF\n"
                current_step += 1
                
                # Add dnf cache refresh
                GLib.idle_add(update_progress, steps[current_step][1], steps[current_step][0])
                script_content += "dnf makecache\n"
                current_step += 1
                
                # Add package installation
                GLib.idle_add(update_progress, steps[current_step][1], steps[current_step][0])
                script_content += f"dnf install -y {app.package}\n"
                current_step += 1
                
                # Create temporary script file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as script_file:
                    script_file.write(script_content)
                    script_path = script_file.name
                
                # Make script executable
                os.chmod(script_path, 0o755)
                
                # Execute script with pkexec
                subprocess.run(["pkexec", script_path], check=True)
                
                # Remove temporary script
                os.unlink(script_path)
                
                # Final step
                GLib.idle_add(update_progress, steps[current_step][1], steps[current_step][0])
                
                GLib.idle_add(dialog.close)
                GLib.idle_add(self.on_install_complete, button, app, True, progress_label)
            except Exception as e:
                GLib.idle_add(dialog.close)
                GLib.idle_add(self.on_install_complete, button, app, False, progress_label, str(e))
        
        thread = threading.Thread(target=install_thread)
        thread.daemon = True
        thread.start()
    
    def on_install_complete(self, button, app, success, progress_label, error_message=None):
        if success:
            progress_label.set_visible(False)
            button.set_label("Launch")
            button.set_sensitive(True)
            button.remove_css_class("suggested-action")
            button.add_css_class("success")
            button.disconnect_by_func(self.on_install_clicked)
            button.connect("clicked", self.on_launch_clicked, app)
        else:
            progress_label.set_visible(False)
            button.set_label("Install")
            button.set_sensitive(True)
            self.show_error_dialog(f"Error installing {app.name}", error_message)
    
    def show_error_dialog(self, title, message):
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            title,
            message
        )
        dialog.add_response("ok", "OK")
        dialog.present()
