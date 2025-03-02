#!/usr/bin/env python3
import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk, GLib, Gio, GObject
from system import SystemPage
from software import SoftwarePage
from users import UsersPage
from network import NetworkPage
from services import ServicesPage
from security import SecurityPage
from hardware import HardwarePage

class ControlCenterWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.set_title("Tears of Mandrake")
        self.set_default_size(800, 600)
        
        # Create main box
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Create header with back button
        self.header = Adw.HeaderBar()
        self.back_button = Gtk.Button(icon_name="go-previous-symbolic")
        self.back_button.connect("clicked", self.on_back_clicked)
        self.back_button.set_visible(False)
        self.header.pack_start(self.back_button)
        self.main_box.append(self.header)
        
        # Create stack for pages
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        
        # Create and add main page
        self.main_page = self.create_main_page()
        self.stack.add_named(self.main_page, "main")
        
        # Create and add system page
        self.system_page = SystemPage()
        self.stack.add_named(self.system_page, "system")
        
        # Create and add software page
        self.software_page = SoftwarePage()
        self.stack.add_named(self.software_page, "software")
        
        # Create and add users page
        self.users_page = UsersPage()
        self.stack.add_named(self.users_page, "users")
        
        # Create and add network page
        self.network_page = NetworkPage()
        self.stack.add_named(self.network_page, "network")
        
        self.main_box.append(self.stack)
        self.set_content(self.main_box)
    
    def create_main_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Welcome message
        welcome_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        welcome_box.set_margin_top(20)
        welcome_box.set_margin_bottom(20)
        welcome_box.set_margin_start(20)
        welcome_box.set_margin_end(20)
        
        welcome_label = Gtk.Label()
        welcome_label.set_markup("<span size='large'>Welcome to the Tears of Mandrake application,\nwhich is the control center of your Linux distribution</span>")
        welcome_label.set_justify(Gtk.Justification.CENTER)
        welcome_label.set_wrap(True)
        
        welcome_box.append(welcome_label)
        page.append(welcome_box)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        page.append(separator)
        
        # Scrolled window for buttons
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        
        # FlowBox for category buttons
        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_valign(Gtk.Align.START)
        self.flowbox.set_max_children_per_line(3)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flowbox.set_margin_start(20)
        self.flowbox.set_margin_end(20)
        self.flowbox.set_margin_top(20)
        self.flowbox.set_margin_bottom(20)
        
        # Categories
        categories = [
            ("System", "computer-symbolic", "Configure system settings"),
            ("Software", "system-software-install-symbolic", "Install and remove software"),
            ("Network", "network-wireless-symbolic", "Configure network connections"),
            ("Hardware", "drive-harddisk-symbolic", "Configure hardware devices"),
            ("Security", "security-high-symbolic", "Security and firewall settings"),
            ("Boot", "system-run-symbolic", "Boot and startup configuration"),
            ("Users", "system-users-symbolic", "User account management"),
            ("Services", "system-run-symbolic", "System services configuration"),
            ("Backup", "system-run-symbolic", "System backup and restore")
        ]
        
        for title, icon_name, description in categories:
            self.flowbox.append(self.create_category_button(title, icon_name, description))
        
        scrolled.set_child(self.flowbox)
        page.append(scrolled)
        
        return page

    def create_category_button(self, title, icon_name, description):
        button = Gtk.Button()
        button.add_css_class("flat")
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        
        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.set_pixel_size(48)
        box.append(icon)
        
        label = Gtk.Label(label=title)
        label.add_css_class("heading")
        box.append(label)
        
        desc_label = Gtk.Label(label=description)
        desc_label.add_css_class("caption")
        desc_label.set_wrap(True)
        desc_label.set_max_width_chars(25)
        box.append(desc_label)
        
        button.set_child(box)
        button.connect("clicked", self.on_category_clicked, title)
        
        return button

    def on_category_clicked(self, button, category):
        if category == "System":
            self.stack.set_visible_child_name("system")
            system_page = self.stack.get_visible_child()
            system_page.show_main()  # Always show main system page when entering System category
            self.back_button.set_visible(True)
        elif category == "Software":
            self.software_page.show_main()
            self.stack.set_visible_child_name("software")
            self.back_button.set_visible(True)
        elif category == "Network":
            self.stack.set_visible_child_name("network")
            self.back_button.set_visible(True)
        elif category == "Users":
            self.stack.set_visible_child_name("users")
            self.back_button.set_visible(True)
        elif category == "Services":
            if not hasattr(self, 'services_page'):
                self.services_page = ServicesPage()
                self.stack.add_named(self.services_page, "services")
            self.stack.set_visible_child_name("services")
            self.back_button.set_visible(True)
        elif category == "Security":
            if not hasattr(self, 'security_page'):
                self.security_page = SecurityPage()
                self.stack.add_named(self.security_page, "security")
            self.stack.set_visible_child_name("security")
            self.back_button.set_visible(True)
        elif category == "Hardware":
            if not hasattr(self, 'hardware_page'):
                self.hardware_page = HardwarePage(self)
                self.stack.add_named(self.hardware_page, "hardware")
            self.hardware_page.stack.set_visible_child_name("main")  # Always show hardware main page
            self.stack.set_visible_child_name("hardware")
            self.back_button.set_visible(True)
        else:
            dialog = Adw.MessageDialog.new(
                self,
                f"{category} Settings",
                "This feature is not implemented yet."
            )
            dialog.add_response("ok", "OK")
            dialog.present()
    
    def on_back_clicked(self, button):
        if isinstance(self.stack.get_visible_child(), SystemPage):
            system_page = self.stack.get_visible_child()
            if system_page.stack.get_visible_child_name() == "system_info":
                system_page.show_main()  # Go back to system main page
            else:
                self.stack.set_visible_child_name("main")  # Go back to main menu
                self.back_button.set_visible(False)
        elif isinstance(self.stack.get_visible_child(), SoftwarePage):
            self.stack.set_visible_child_name("main")  # Go back to main menu
            self.back_button.set_visible(False)
        elif isinstance(self.stack.get_visible_child(), HardwarePage):
            hardware_page = self.stack.get_visible_child()
            if hardware_page.stack.get_visible_child_name() != "main":
                hardware_page.stack.set_visible_child_name("main")  # Go back to hardware main page
            else:
                self.stack.set_visible_child_name("main")  # Go back to main menu
                self.back_button.set_visible(False)
        else:
            self.stack.set_visible_child_name("main")  # Go back to main menu
            self.back_button.set_visible(False)


class ControlCenterApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.win = ControlCenterWindow(application=app)
        self.win.present()

def main():
    app = ControlCenterApp(application_id="org.tearsofmandrake.controlcenter")
    return app.run(sys.argv)

if __name__ == "__main__":
    main()
