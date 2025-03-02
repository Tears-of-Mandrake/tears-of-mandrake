import gi
import subprocess
import os
from pathlib import Path
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

class TweaksPage(Gtk.Box):
    def __init__(self, parent):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.parent = parent
        
        # Add page title and description
        title_group = Adw.PreferencesGroup()
        title_label = Gtk.Label()
        title_label.set_markup("<span size='x-large' weight='bold'>System Tweaks</span>")
        title_label.set_margin_bottom(10)
        title_group.add(title_label)
        
        description_label = Gtk.Label(
            label="Customize your system settings and preferences. You can launch GNOME Tweaks "
                  "for advanced customization and manage your default shell."
        )
        description_label.set_wrap(True)
        description_label.set_margin_bottom(10)
        title_group.add(description_label)
        self.append(title_group)

        # GNOME Tweaks section
        tweaks_group = Adw.PreferencesGroup()
        tweaks_group.set_title("GNOME Tweaks")
        tweaks_group.set_description("Advanced system customization tool")
        
        tweaks_row = Adw.ActionRow()
        tweaks_row.set_title("GNOME Tweaks")
        tweaks_row.set_subtitle("Launch GNOME Tweaks for advanced system customization")
        
        launch_button = Gtk.Button(label="Launch")
        launch_button.add_css_class('suggested-action')
        launch_button.connect('clicked', self.on_launch_tweaks)
        tweaks_row.add_suffix(launch_button)
        tweaks_group.add(tweaks_row)
        
        self.append(tweaks_group)

        # Shell selection section
        shell_group = Adw.PreferencesGroup()
        shell_group.set_title("Default Shell")
        shell_group.set_description("Choose and manage your default command shell")
        
        # Get current shell
        self.current_shell = os.environ.get('SHELL', '/bin/bash')
        self.current_shell = Path(self.current_shell).name
        
        # Available shells with their package names
        self.available_shells = {
            'bash': {'package': 'bash', 'description': 'Default Linux shell with advanced features'},
            'zsh': {'package': 'zsh', 'description': 'Extended Bourne shell with many improvements'},
            'fish': {'package': 'fish', 'description': 'Friendly interactive shell with modern features'},
            'dash': {'package': 'dash', 'description': 'Lightweight POSIX-compliant shell'},
            'ksh': {'package': 'ksh', 'description': 'KornShell with advanced scripting capabilities'},
            'tcsh': {'package': 'tcsh', 'description': 'Enhanced C shell with programmable completion'}
        }
        
        # Create a row for each shell
        for shell_name, shell_info in self.available_shells.items():
            shell_row = Adw.ActionRow()
            shell_row.set_title(shell_name.upper())
            shell_row.set_subtitle(shell_info['description'])
            
            # Check if shell is installed
            is_installed = os.path.exists(f"/bin/{shell_name}")
            
            if shell_name == self.current_shell:
                # Current shell - show "Default" badge
                status_box = Gtk.Box()
                status_box.add_css_class('success')
                status_box.add_css_class('pill')
                status_box.set_margin_start(5)
                status_label = Gtk.Label(label="Default")
                status_label.add_css_class('caption')
                status_label.set_margin_start(5)
                status_label.set_margin_end(5)
                status_box.append(status_label)
                shell_row.add_suffix(status_box)
            else:
                # Other shells - show Set Default button
                set_default_button = Gtk.Button()
                if is_installed:
                    set_default_button.set_label("Set Default")
                    set_default_button.add_css_class('suggested-action')
                else:
                    set_default_button.set_label("Install")
                    set_default_button.add_css_class('suggested-action')
                
                set_default_button.connect('clicked', self.on_set_default_shell, shell_name, shell_info['package'])
                shell_row.add_suffix(set_default_button)
            
            shell_group.add(shell_row)
        
        self.append(shell_group)

    def on_launch_tweaks(self, button):
        tweaks_path = "/usr/bin/gnome-tweaks"
        
        if not os.path.exists(tweaks_path):
            # Show installing dialog
            dialog = Adw.MessageDialog.new(
                self.get_root(),
                "Install GNOME Tweaks",
                "GNOME Tweaks is not installed. Would you like to install it?"
            )
            dialog.add_response("cancel", "Cancel")
            dialog.add_response("install", "Install")
            dialog.set_response_appearance("install", Adw.ResponseAppearance.SUGGESTED)
            
            def on_response(dialog, response):
                if response == "install":
                    self.install_gnome_tweaks()
            
            dialog.connect("response", on_response)
            dialog.present()
        else:
            # Launch GNOME Tweaks
            subprocess.Popen([tweaks_path])

    def install_gnome_tweaks(self):
        # Create and show progress dialog
        progress_dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Installing GNOME Tweaks",
            "Please wait while GNOME Tweaks is being installed..."
        )
        progress_dialog.present()
        
        def install_thread():
            try:
                # Install gnome-tweaks
                subprocess.run(["pkexec", "dnf", "install", "-y", "gnome-tweaks"], check=True)
                
                def on_complete():
                    progress_dialog.destroy()
                    # Show success dialog
                    success_dialog = Adw.MessageDialog.new(
                        self.get_root(),
                        "Installation Complete",
                        "GNOME Tweaks has been installed successfully."
                    )
                    success_dialog.add_response("ok", "Launch")
                    success_dialog.connect("response", lambda d, r: subprocess.Popen(["/usr/bin/gnome-tweaks"]))
                    success_dialog.present()
                
                GLib.idle_add(on_complete)
            
            except subprocess.CalledProcessError as e:
                def show_error():
                    progress_dialog.destroy()
                    error_dialog = Adw.MessageDialog.new(
                        self.get_root(),
                        "Installation Failed",
                        f"Failed to install GNOME Tweaks.\nError: {str(e)}"
                    )
                    error_dialog.add_response("ok", "OK")
                    error_dialog.present()
                
                GLib.idle_add(show_error)
        
        # Start installation in a thread
        import threading
        thread = threading.Thread(target=install_thread)
        thread.daemon = True
        thread.start()

    def on_set_default_shell(self, button, shell_name, package_name):
        if not os.path.exists(f"/bin/{shell_name}"):
            # Show installing dialog
            dialog = Adw.MessageDialog.new(
                self.get_root(),
                f"Install {shell_name.upper()}",
                f"{shell_name.upper()} is not installed. Would you like to install it?"
            )
            dialog.add_response("cancel", "Cancel")
            dialog.add_response("install", "Install")
            dialog.set_response_appearance("install", Adw.ResponseAppearance.SUGGESTED)
            
            def on_response(dialog, response):
                if response == "install":
                    self.install_shell(shell_name, package_name)
            
            dialog.connect("response", on_response)
            dialog.present()
        else:
            self.set_default_shell(shell_name)

    def install_shell(self, shell_name, package_name):
        # Create and show progress dialog
        progress_dialog = Adw.MessageDialog.new(
            self.get_root(),
            f"Installing {shell_name.upper()}",
            f"Please wait while {shell_name.upper()} is being installed..."
        )
        progress_dialog.present()
        
        def install_thread():
            try:
                # Install shell
                subprocess.run(["pkexec", "dnf", "install", "-y", package_name], check=True)
                
                def on_complete():
                    progress_dialog.destroy()
                    # Set as default after successful installation
                    self.set_default_shell(shell_name)
                
                GLib.idle_add(on_complete)
            
            except subprocess.CalledProcessError as e:
                def show_error():
                    progress_dialog.destroy()
                    error_dialog = Adw.MessageDialog.new(
                        self.get_root(),
                        "Installation Failed",
                        f"Failed to install {shell_name.upper()}.\nError: {str(e)}"
                    )
                    error_dialog.add_response("ok", "OK")
                    error_dialog.present()
                
                GLib.idle_add(show_error)
        
        # Start installation in a thread
        import threading
        thread = threading.Thread(target=install_thread)
        thread.daemon = True
        thread.start()

    def set_default_shell(self, shell_name):
        try:
            # Get user's username
            username = os.getenv('USER')
            if not username:
                raise ValueError("Could not determine current user")
            
            # Change default shell
            subprocess.run(["pkexec", "chsh", "-s", f"/bin/{shell_name}", username], check=True)
            
            # Show success dialog
            dialog = Adw.MessageDialog.new(
                self.get_root(),
                "Default Shell Changed",
                f"Your default shell has been changed to {shell_name.upper()}.\nThe change will take effect after you log out and log back in."
            )
            dialog.add_response("ok", "OK")
            dialog.connect("response", lambda d, r: self.parent.on_option_clicked(None, "Tweaks"))
            dialog.present()
        
        except subprocess.CalledProcessError as e:
            error_dialog = Adw.MessageDialog.new(
                self.get_root(),
                "Error",
                f"Failed to change default shell.\nError: {str(e)}"
            )
            error_dialog.add_response("ok", "OK")
            error_dialog.present()
