import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from system_info import get_system_info
from hardware_info import HardwareInfoPage
from datetime_settings import DateTimeSettingsPage
from system_logs import SystemLogsPage
from kernel_manager import KernelManagerPage
from tweaks import TweaksPage
from news import NewsPage

class SystemInfoPage(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        # Get system information
        info = get_system_info()
        
        # Create title
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        title_box.set_margin_top(20)
        title_box.set_margin_bottom(20)
        title_box.set_margin_start(20)
        title_box.set_margin_end(20)
        
        title_label = Gtk.Label()
        title_label.set_markup("<span size='large'>System Information</span>")
        title_label.set_justify(Gtk.Justification.CENTER)
        title_box.append(title_label)
        
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        
        self.append(title_box)
        self.append(separator)
        
        # Create info grid
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        info_box.set_margin_top(20)
        info_box.set_margin_bottom(20)
        info_box.set_margin_start(20)
        info_box.set_margin_end(20)
        
        # Add system information
        info_items = [
            ("System Name", info['system_name']),
            ("Distribution", info['distribution']),
            ("Architecture", info['architecture']),
            ("Kernel Version", info['kernel']),
            ("Desktop Environment", info['desktop_environment']),
            ("Graphics Driver", info['graphics_driver']),
            ("Hostname", info['hostname'])
        ]
        
        for label, value in info_items:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            row.set_margin_bottom(10)
            
            label_widget = Gtk.Label()
            label_widget.set_markup(f"<b>{label}:</b>")
            label_widget.set_halign(Gtk.Align.START)
            label_widget.set_width_chars(20)
            
            value_widget = Gtk.Label(label=value)
            value_widget.set_halign(Gtk.Align.START)
            value_widget.set_selectable(True)
            
            row.append(label_widget)
            row.append(value_widget)
            
            info_box.append(row)
        
        self.append(info_box)

class SystemPage(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        # Create stack for different pages
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        
        # Create and add main system page
        self.main_system_page = self.create_main_system_page()
        self.stack.add_named(self.main_system_page, "main")
        
        # Create and add system info page
        self.system_info_page = SystemInfoPage()
        self.stack.add_named(self.system_info_page, "system_info")
        
        self.append(self.stack)
    
    def create_main_system_page(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Create title
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        title_box.set_margin_top(20)
        title_box.set_margin_bottom(20)
        title_box.set_margin_start(20)
        title_box.set_margin_end(20)
        
        title_label = Gtk.Label()
        title_label.set_markup("<span size='large'>System</span>")
        title_label.set_justify(Gtk.Justification.CENTER)
        title_box.append(title_label)
        
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        
        main_box.append(title_box)
        main_box.append(separator)
        
        # Create grid for options
        grid = Gtk.Grid()
        grid.set_row_spacing(5)
        grid.set_column_spacing(10)
        grid.set_margin_top(10)
        grid.set_margin_bottom(10)
        grid.set_margin_start(20)
        grid.set_margin_end(20)
        
        # Add options
        row = 0
        col = 0
        
        # System Info option
        system_info_button = self.create_option_button(
            "System Info",
            "computer-symbolic",
            "View system information"
        )
        grid.attach(system_info_button, col, row, 1, 1)
        
        # Hardware Info option
        col = (col + 1) % 2
        hardware_info_button = self.create_option_button(
            "Hardware Info",
            "applications-engineering-symbolic",
            "View hardware information"
        )
        grid.attach(hardware_info_button, col, row, 1, 1)
        
        # System Resources option
        row += 1
        col = 0
        resources_button = self.create_option_button(
            "System Resources",
            "system-run-symbolic",
            "Monitor system resources"
        )
        grid.attach(resources_button, col, row, 1, 1)
        
        # News option
        col = (col + 1) % 2
        news_button = self.create_option_button(
            "News",
            "printer-symbolic",
            "Latest news and updates"
        )
        grid.attach(news_button, col, row, 1, 1)
        
        # Date & Time option
        row += 1
        col = 0
        datetime_button = self.create_option_button(
            "Date & Time",
            "preferences-system-time-symbolic",
            "Configure date and time settings"
        )
        grid.attach(datetime_button, col, row, 1, 1)
        
        # System Logs option
        col = (col + 1) % 2
        logs_button = self.create_option_button(
            "System Logs",
            "text-x-generic-symbolic",
            "View system logs"
        )
        grid.attach(logs_button, col, row, 1, 1)
        
        # Tweaks option
        row += 1
        col = 0
        tweaks_button = self.create_option_button(
            "Tweaks",
            "system-run-symbolic",
            "Advanced system settings"
        )
        grid.attach(tweaks_button, col, row, 1, 1)
        
        # Kernels option
        col = (col + 1) % 2
        kernels_button = self.create_option_button(
            "Kernels",
            "system-software-install-symbolic",
            "Manage system kernels"
        )
        grid.attach(kernels_button, col, row, 1, 1)
        
        main_box.append(grid)
        return main_box
    
    def create_option_button(self, title, icon_name, description):
        button = Gtk.Button()
        button.add_css_class("flat")
        button.set_hexpand(True)
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        box.set_margin_top(5)
        box.set_margin_bottom(5)
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
        button.connect("clicked", self.on_option_clicked, title)
        
        return button
    
    def on_option_clicked(self, button, title):
        if title == "System Info":
            self.stack.set_visible_child_name("system_info")
        elif title == "Hardware Info":
            if not hasattr(self, 'hardware_info_page'):
                self.hardware_info_page = HardwareInfoPage()
                self.stack.add_named(self.hardware_info_page, "hardware_info")
            self.stack.set_visible_child_name("hardware_info")
        elif title == "Date & Time":
            if not hasattr(self, 'datetime_page'):
                self.datetime_page = DateTimeSettingsPage()
                self.stack.add_named(self.datetime_page, "datetime")
            self.stack.set_visible_child_name("datetime")
        elif title == "System Logs":
            if not hasattr(self, 'logs_page'):
                self.logs_page = SystemLogsPage()
                self.stack.add_named(self.logs_page, "logs")
            self.stack.set_visible_child_name("logs")
        elif title == "Kernels":
            if not hasattr(self, 'kernel_page'):
                self.kernel_page = KernelManagerPage(self)
                self.stack.add_named(self.kernel_page, "kernels")
            self.stack.set_visible_child_name("kernels")
        elif title == "News":
            if not hasattr(self, 'news_page'):
                self.news_page = NewsPage(self)
                self.stack.add_named(self.news_page, "news")
            self.stack.set_visible_child_name("news")
        elif title == "Tweaks":
            if not hasattr(self, 'tweaks_page'):
                self.tweaks_page = TweaksPage(self)
            if not hasattr(self, 'tweaks'):
                self.stack.add_named(self.tweaks_page, "tweaks")
            self.stack.set_visible_child_name("tweaks")
        else:
            # Show dialog for unimplemented features
            dialog = Adw.MessageDialog.new(
                button.get_root(),
                f"{title}",
                "This feature is not implemented yet."
            )
            dialog.add_response("ok", "OK")
            dialog.present()
    
    def show_main(self):
        self.stack.set_visible_child_name("main")
