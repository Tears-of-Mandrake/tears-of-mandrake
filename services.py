#!/usr/bin/env python3
import gi
import subprocess
from typing import List, Tuple, Optional

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, Gdk, GObject

class ServiceInfo:
    def __init__(self, name: str, description: str, status: str, active: bool):
        self.name = name
        self.description = description
        self.status = status
        self.active = active

class ServicesPage(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        # Initialize filter state
        self.current_filter = "all"
        self.current_search = ""
        
        # Create stack for different pages
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        
        # Create and add main services page
        self.main_services_page = self.create_main_services_page()
        self.stack.add_named(self.main_services_page, "main")
        
        self.append(self.stack)

    def create_main_services_page(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Create title
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        title_box.set_margin_top(20)
        title_box.set_margin_bottom(20)
        title_box.set_margin_start(20)
        title_box.set_margin_end(20)
        
        title_label = Gtk.Label()
        title_label.set_markup("<span size='large'>System Services</span>")
        title_label.set_justify(Gtk.Justification.CENTER)
        title_box.append(title_label)
        
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        
        main_box.append(title_box)
        main_box.append(separator)

        # Create search entry
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        search_box.set_margin_top(10)
        search_box.set_margin_bottom(10)
        search_box.set_margin_start(20)
        search_box.set_margin_end(20)
        
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_hexpand(True)
        self.search_entry.connect('search-changed', self.on_search_changed)
        search_box.append(self.search_entry)
        
        main_box.append(search_box)

        # Create filter buttons
        filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        filter_box.set_margin_bottom(10)
        filter_box.set_margin_start(20)
        filter_box.set_margin_end(20)
        filter_box.set_spacing(10)

        self.all_button = Gtk.ToggleButton(label="All Services")
        self.all_button.connect("toggled", self.on_filter_toggled, "all")
        self.all_button.set_active(True)
        
        self.active_button = Gtk.ToggleButton(label="Active")
        self.active_button.connect("toggled", self.on_filter_toggled, "active")
        
        self.inactive_button = Gtk.ToggleButton(label="Inactive")
        self.inactive_button.connect("toggled", self.on_filter_toggled, "inactive")

        filter_box.append(self.all_button)
        filter_box.append(self.active_button)
        filter_box.append(self.inactive_button)

        main_box.append(filter_box)

        # Create scrolled window for services list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_margin_start(20)
        scrolled.set_margin_end(20)
        scrolled.set_margin_bottom(20)

        # Create list box for services
        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.list_box.set_show_separators(True)
        
        scrolled.set_child(self.list_box)
        main_box.append(scrolled)

        # Load services
        self.load_services()
        
        return main_box

    def get_services(self) -> List[ServiceInfo]:
        services = []
        try:
            # Get list of all services
            output = subprocess.check_output(
                ["systemctl", "list-units", "--type=service", "--all", "--no-pager", "--no-legend"],
                universal_newlines=True
            )
            
            for line in output.splitlines():
                parts = line.split()
                if len(parts) >= 4 and parts[0].endswith('.service'):
                    name = parts[0].replace('.service', '')
                    active = parts[2] == "active"
                    status = parts[2]
                    
                    # Get service description
                    try:
                        desc_output = subprocess.check_output(
                            ["systemctl", "show", "-p", "Description", name],
                            universal_newlines=True
                        )
                        description = desc_output.strip().split("=")[1]
                    except:
                        description = "No description available"
                    
                    services.append(ServiceInfo(name, description, status, active))
            
        except subprocess.CalledProcessError:
            dialog = Adw.MessageDialog.new(
                self.get_root(),
                "Error",
                "Failed to get services list. Make sure you have the necessary permissions."
            )
            dialog.add_response("ok", "OK")
            dialog.present()
        
        return services

    def load_services(self):
        # Clear existing list
        while True:
            row = self.list_box.get_first_child()
            if row is None:
                break
            self.list_box.remove(row)

        # Get services and add them to the list
        services = self.get_services()
        
        for service in services:
            if self.should_show_service(service):
                self.list_box.append(self.create_service_row(service))

    def create_service_row(self, service: ServiceInfo) -> Gtk.ListBoxRow:
        row = Gtk.ListBoxRow()
        
        # Main box for the row
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        
        # Service info box (name and description)
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        info_box.set_hexpand(True)
        
        name_label = Gtk.Label(label=service.name)
        name_label.set_halign(Gtk.Align.START)
        name_label.add_css_class("heading")
        
        desc_label = Gtk.Label(label=service.description)
        desc_label.set_halign(Gtk.Align.START)
        desc_label.set_wrap(True)
        desc_label.add_css_class("caption")
        
        info_box.append(name_label)
        info_box.append(desc_label)
        
        # Status label
        status_label = Gtk.Label()
        status_label.set_markup(
            f"<span foreground='{'green' if service.active else 'red'}'>{service.status}</span>"
        )
        status_label.set_margin_end(10)
        
        # Action buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        if service.active:
            stop_button = Gtk.Button(label="Stop")
            stop_button.add_css_class("destructive-action")
            stop_button.connect("clicked", self.on_service_action, service.name, "stop")
            button_box.append(stop_button)
            
            restart_button = Gtk.Button(label="Restart")
            restart_button.connect("clicked", self.on_service_action, service.name, "restart")
            button_box.append(restart_button)
        else:
            start_button = Gtk.Button(label="Start")
            start_button.add_css_class("suggested-action")
            start_button.connect("clicked", self.on_service_action, service.name, "start")
            button_box.append(start_button)
        
        box.append(info_box)
        box.append(status_label)
        box.append(button_box)
        
        row.set_child(box)
        return row

    def should_show_service(self, service: ServiceInfo) -> bool:
        # Apply search filter
        if self.current_search and self.current_search.lower() not in service.name.lower():
            return False
            
        # Apply status filter
        if self.current_filter == "active" and not service.active:
            return False
        elif self.current_filter == "inactive" and service.active:
            return False
            
        return True

    def on_search_changed(self, entry):
        self.current_search = entry.get_text()
        self.load_services()

    def on_filter_toggled(self, button, filter_type):
        if button.get_active():
            # Deactivate other buttons
            if filter_type != "all":
                self.all_button.set_active(False)
            if filter_type != "active":
                self.active_button.set_active(False)
            if filter_type != "inactive":
                self.inactive_button.set_active(False)
                
            self.current_filter = filter_type
            self.load_services()
        elif not self.all_button.get_active() and not self.active_button.get_active() and not self.inactive_button.get_active():
            # If no button is active, activate "All" button
            self.all_button.set_active(True)

    def on_service_action(self, button, service_name: str, action: str):
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            f"Confirm {action.title()}",
            f"Are you sure you want to {action} the service '{service_name}'?"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("confirm", action.title())
        dialog.set_response_appearance("confirm", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self._on_service_action_response, service_name, action)
        dialog.present()

    def _on_service_action_response(self, dialog, response, service_name: str, action: str):
        if response == "confirm":
            try:
                subprocess.check_call(["systemctl", action, f"{service_name}.service"])
                self.load_services()  # Refresh the list
            except subprocess.CalledProcessError:
                error_dialog = Adw.MessageDialog.new(
                    self.get_root(),
                    "Error",
                    f"Failed to {action} service '{service_name}'. Make sure you have the necessary permissions."
                )
                error_dialog.add_response("ok", "OK")
                error_dialog.present()

    def show_main(self):
        self.stack.set_visible_child_name("main")
