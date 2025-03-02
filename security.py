#!/usr/bin/env python3
import gi
import subprocess
import threading
from typing import Optional

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

class SecurityPage(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        # Create stack for different pages
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        
        # Create and add main security page
        self.main_security_page = self.create_main_security_page()
        self.stack.add_named(self.main_security_page, "main")
        
        self.append(self.stack)

    def create_main_security_page(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Create title
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        title_box.set_margin_top(20)
        title_box.set_margin_bottom(20)
        title_box.set_margin_start(20)
        title_box.set_margin_end(20)
        
        title_label = Gtk.Label()
        title_label.set_markup("<span size='large'>Security</span>")
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
            ("Install Firewalld", "security-high-symbolic", "Install Firewalld package"),
            ("Manage Firewall", "security-medium-symbolic", "Configure firewall settings")
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
        if title == "Install Firewalld":
            self.confirm_firewalld_installation()
        elif title == "Manage Firewall":
            dialog = Adw.MessageDialog.new(
                self.get_root(),
                "Manage Firewall",
                "This feature is not implemented in the current version of the application."
            )
            dialog.add_response("ok", "OK")
            dialog.present()

    def confirm_firewalld_installation(self):
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Install Firewalld",
            "Do you want to install the Firewalld package?"
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
                self.install_firewalld(password)

    def install_firewalld(self, password):
        progress_dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Installing Firewalld",
            "Please wait while Firewalld is being installed..."
        )
        progress_dialog.present()

        def install_thread():
            try:
                # Create dnf install command
                cmd = f'echo "{password}" | sudo -S dnf install -y firewalld'
                
                # Run the installation
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                # Monitor the output
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        GLib.idle_add(self.update_progress_dialog, progress_dialog, output.strip())

                return_code = process.poll()
                
                # Show final result
                if return_code == 0:
                    GLib.idle_add(self.show_result_dialog, True, "Firewalld has been successfully installed!")
                else:
                    error = process.stderr.read()
                    GLib.idle_add(self.show_result_dialog, False, f"Failed to install Firewalld: {error}")
                
                GLib.idle_add(progress_dialog.close)
                
            except Exception as e:
                GLib.idle_add(self.show_result_dialog, False, f"Error during installation: {str(e)}")
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
            "Installation " + ("Successful" if success else "Failed"),
            message
        )
        dialog.add_response("ok", "OK")
        dialog.present()
        return False

    def show_main(self):
        self.stack.set_visible_child_name("main")
