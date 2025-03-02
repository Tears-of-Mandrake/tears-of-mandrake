import gi
import subprocess
import socket
import threading
import urllib.request
from urllib.parse import urlparse
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

class NetworkPage(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        # Create stack for different pages
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        
        # Create and add main network page
        self.main_network_page = self.create_main_network_page()
        self.stack.add_named(self.main_network_page, "main")
        
        self.append(self.stack)

    def create_main_network_page(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Create title
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        title_box.set_margin_top(20)
        title_box.set_margin_bottom(20)
        title_box.set_margin_start(20)
        title_box.set_margin_end(20)
        
        title_label = Gtk.Label()
        title_label.set_markup("<span size='large'>Network</span>")
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
            ("Manage Internet connection", "network-wireless-symbolic", "Configure network connections"),
            ("Check connection", "network-transmit-receive-symbolic", "Test internet connectivity"),
            ("OpenMandriva Services Uptime", "network-server-symbolic", "Check OpenMandriva services status")
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
        if title == "Manage Internet connection":
            dialog = Adw.MessageDialog.new(
                self.get_root(),
                "Network Management",
                "Choose the type of connection you want to configure:"
            )
            dialog.add_response("wired", "Wired")
            dialog.add_response("wireless", "Wireless")
            dialog.add_response("cancel", "Cancel")
            dialog.set_default_response("cancel")
            dialog.set_close_response("cancel")
            dialog.connect("response", self._on_network_management_response)
            dialog.present()
        elif title == "Check connection":
            self._check_connection()
        elif title == "OpenMandriva Services Uptime":
            self._check_openmandriva_services()

    def _on_network_management_response(self, dialog, response):
        if response == "wired":
            subprocess.Popen(["gnome-control-center", "network"])
        elif response == "wireless":
            subprocess.Popen(["gnome-control-center", "wifi"])

    def _check_connection(self):
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Check Connection",
            "Do you want to start checking the internet connection?"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("check", "Check")
        dialog.set_default_response("check")
        dialog.set_close_response("cancel")
        dialog.connect("response", self._on_check_connection_response)
        dialog.present()

    def _on_check_connection_response(self, dialog, response):
        if response == "check":
            progress_dialog = Adw.MessageDialog.new(
                self.get_root(),
                "Checking Connection",
                "Please wait while checking connection status..."
            )
            progress_dialog.present()

            def check_connection():
                services = [
                    "www.google.com",
                    "www.wikipedia.com",
                    "www.internet.gov.pl"
                ]
                
                results = []
                working_services = 0
                
                # Get IP address
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    ip_address = s.getsockname()[0]
                    s.close()
                except:
                    ip_address = "Unable to determine IP address"

                for service in services:
                    try:
                        output = subprocess.check_output(
                            ["ping", "-c", "1", "-W", "2", service],
                            stderr=subprocess.STDOUT,
                            universal_newlines=True
                        )
                        if "time=" in output:
                            time_ms = float(output.split("time=")[1].split()[0])
                            results.append((service, True, time_ms))
                            working_services += 1
                        else:
                            results.append((service, False, None))
                    except:
                        results.append((service, False, None))

                GLib.idle_add(self._show_connection_results, results, working_services > 0, ip_address)
                GLib.idle_add(progress_dialog.close)

            thread = threading.Thread(target=check_connection)
            thread.daemon = True
            thread.start()

    def _show_connection_results(self, results, network_working, ip_address):
        result_text = f"Current IP Address: {ip_address}\n\nPing Results:\n\n"
        
        for service, working, time_ms in results:
            status = "✓ Working" if working else "✗ Not responding"
            time_info = f" (ping: {time_ms:.1f}ms)" if working else ""
            result_text += f"{service}: {status}{time_info}\n"
        
        result_text += f"\nOverall Network Status: {'✓ Working' if network_working else '✗ Not working'}"

        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Connection Test Results",
            result_text
        )
        dialog.add_response("ok", "OK")
        dialog.present()

    def _check_openmandriva_services(self):
        progress_dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Checking OpenMandriva Services",
            "Please wait while checking services status..."
        )
        progress_dialog.present()

        def check_services():
            services = [
                "https://abf.openmandriva.org/",
                "https://openmandriva.org/",
                "https://forum.openmandriva.org/",
                "https://abf-downloads.openmandriva.org/",
                "https://github.com/OpenMandrivaAssociation"
            ]
            
            results = []
            
            for service in services:
                try:
                    urllib.request.urlopen(service, timeout=5)
                    results.append((service, True))
                except:
                    results.append((service, False))

            GLib.idle_add(self._show_services_results, results)
            GLib.idle_add(progress_dialog.close)

        thread = threading.Thread(target=check_services)
        thread.daemon = True
        thread.start()

    def _show_services_results(self, results):
        result_text = "OpenMandriva Services Status:\n\n"
        
        for service, working in results:
            status = "✓ Working" if working else "✗ Not responding"
            # Get domain name from URL for cleaner display
            domain = urlparse(service).netloc
            if not domain:
                domain = service
            result_text += f"{domain}: {status}\n"

        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "OpenMandriva Services Status",
            result_text
        )
        dialog.add_response("ok", "OK")
        dialog.present()

    def show_main(self):
        self.stack.set_visible_child_name("main")
