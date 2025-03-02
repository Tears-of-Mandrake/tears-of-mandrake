import gi
import os
import subprocess
from datetime import datetime

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

class SystemLogsPage(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        # Create main box with padding
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        
        # Add title
        title = Gtk.Label()
        title.set_markup("<big><b>System Logs</b></big>")
        main_box.append(title)
        
        # Add description
        description = Gtk.Label()
        description.set_markup("Click the button below to collect system logs.\nLogs will be saved in your Documents folder.")
        description.set_margin_top(10)
        main_box.append(description)
        
        # Add collect logs button
        collect_button = Gtk.Button(label="Collect System Logs")
        collect_button.set_margin_top(20)
        collect_button.connect("clicked", self._on_collect_clicked)
        main_box.append(collect_button)
        
        # Add status label
        self.status_label = Gtk.Label()
        self.status_label.set_margin_top(10)
        main_box.append(self.status_label)
        
        self.append(main_box)

    def _on_collect_clicked(self, button):
        try:
            # Create logs directory in Documents if it doesn't exist
            home_dir = os.path.expanduser("~")
            docs_dir = os.path.join(home_dir, "Documents")
            logs_dir = os.path.join(docs_dir, "system_logs")
            os.makedirs(logs_dir, exist_ok=True)
            
            # Generate timestamp for log files
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Collect journal logs
            journal_file = os.path.join(logs_dir, f"journal_{timestamp}.log")
            subprocess.run(['journalctl', '-b'], stdout=open(journal_file, 'w'))
            
            # Collect dmesg logs
            dmesg_file = os.path.join(logs_dir, f"dmesg_{timestamp}.log")
            subprocess.run(['dmesg'], stdout=open(dmesg_file, 'w'))
            
            self.status_label.set_markup(
                f'<span foreground="green">Logs collected successfully!\n'
                f'Location: {logs_dir}</span>'
            )
            
            # Show success dialog
            dialog = Adw.MessageDialog.new(
                self.get_root(),
                "Success",
                f"Logs have been saved to:\n{logs_dir}"
            )
            dialog.add_response("ok", "OK")
            dialog.present()
            
        except Exception as e:
            self.status_label.set_markup(
                f'<span foreground="red">Error collecting logs: {str(e)}</span>'
            )
            
            # Show error dialog
            dialog = Adw.MessageDialog.new(
                self.get_root(),
                "Error",
                f"Failed to collect logs: {str(e)}"
            )
            dialog.add_response("ok", "OK")
            dialog.present()
