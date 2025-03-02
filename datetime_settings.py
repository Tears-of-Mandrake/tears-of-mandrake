import gi
import subprocess
import datetime
from zoneinfo import available_timezones

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

class DateTimeSettingsPage(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        # Create main box with padding
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        
        # Current date and time display
        time_label = Gtk.Label()
        time_label.set_markup("<big><b>Current Time</b></big>")
        main_box.append(time_label)
        
        self.current_time = Gtk.Label()
        self.current_time.set_markup("<big>00:00:00</big>")
        main_box.append(self.current_time)
        
        date_label = Gtk.Label()
        date_label.set_markup("<big><b>Current Date</b></big>")
        main_box.append(date_label)
        
        self.current_date = Gtk.Label()
        self.current_date.set_markup("<big>2023-01-01</big>")
        main_box.append(self.current_date)
        
        # Add separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_margin_top(10)
        separator.set_margin_bottom(10)
        main_box.append(separator)
        
        # Automatic time switch
        auto_time_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        auto_time_box.set_margin_bottom(20)
        
        auto_time_label = Gtk.Label(label="Set time automatically")
        auto_time_label.set_halign(Gtk.Align.START)
        auto_time_label.set_hexpand(True)
        auto_time_box.append(auto_time_label)
        
        self.auto_time_switch = Gtk.Switch()
        self.auto_time_switch.set_active(self._is_ntp_active())
        self.auto_time_switch.connect("notify::active", self._on_auto_time_switched)
        auto_time_box.append(self.auto_time_switch)
        
        main_box.append(auto_time_box)
        
        # Manual time settings container
        self.manual_settings_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        # Manual time setting
        settings_label = Gtk.Label()
        settings_label.set_markup("<big><b>Set Date and Time</b></big>")
        self.manual_settings_box.append(settings_label)
        
        # Time setting
        time_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        time_box.set_margin_top(10)
        
        now = datetime.datetime.now()
        
        self.hour_spin = Gtk.SpinButton.new_with_range(0, 23, 1)
        self.hour_spin.set_value(now.hour)
        self.minute_spin = Gtk.SpinButton.new_with_range(0, 59, 1)
        self.minute_spin.set_value(now.minute)
        self.second_spin = Gtk.SpinButton.new_with_range(0, 59, 1)
        self.second_spin.set_value(now.second)
        
        time_box.append(Gtk.Label(label="Time:"))
        time_box.append(self.hour_spin)
        time_box.append(Gtk.Label(label=":"))
        time_box.append(self.minute_spin)
        time_box.append(Gtk.Label(label=":"))
        time_box.append(self.second_spin)
        
        self.manual_settings_box.append(time_box)
        
        # Date setting
        date_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        date_box.set_margin_top(10)
        
        self.year_spin = Gtk.SpinButton.new_with_range(1970, 2100, 1)
        self.year_spin.set_value(now.year)
        self.month_spin = Gtk.SpinButton.new_with_range(1, 12, 1)
        self.month_spin.set_value(now.month)
        self.day_spin = Gtk.SpinButton.new_with_range(1, 31, 1)
        self.day_spin.set_value(now.day)
        
        date_box.append(Gtk.Label(label="Date:"))
        date_box.append(self.year_spin)
        date_box.append(Gtk.Label(label="-"))
        date_box.append(self.month_spin)
        date_box.append(Gtk.Label(label="-"))
        date_box.append(self.day_spin)
        
        self.manual_settings_box.append(date_box)
        
        # Apply button
        apply_button = Gtk.Button(label="Apply Changes")
        apply_button.set_margin_top(20)
        apply_button.connect("clicked", self._on_apply_clicked)
        self.manual_settings_box.append(apply_button)
        
        main_box.append(self.manual_settings_box)
        
        self.append(main_box)
        
        # Update current time display
        self._update_current_time()
        GLib.timeout_add(1000, self._update_current_time)
        
        # Update manual settings sensitivity based on auto time
        self._update_manual_settings_sensitivity()

    def _is_ntp_active(self):
        try:
            result = subprocess.run(['timedatectl', 'show', '--property=NTP'], 
                                 capture_output=True, text=True, check=True)
            return result.stdout.strip() == "NTP=yes"
        except subprocess.CalledProcessError:
            return False

    def _on_auto_time_switched(self, switch, param):
        is_active = switch.get_active()
        try:
            if is_active:
                # Enable NTP
                subprocess.run(['pkexec', 'timedatectl', 'set-ntp', 'true'], check=True)
                # Force immediate synchronization
                subprocess.run(['pkexec', 'systemctl', 'restart', 'systemd-timesyncd'], check=True)
                
                # Show sync in progress dialog
                sync_dialog = Adw.MessageDialog.new(
                    self.get_root(),
                    "Synchronizing Time",
                    "Please wait while the time is being synchronized with internet servers..."
                )
                sync_dialog.add_response("ok", "OK")
                sync_dialog.present()
                
                # Give some time for sync to complete
                GLib.timeout_add(3000, self._check_sync_status, sync_dialog)
            else:
                # Disable NTP
                subprocess.run(['pkexec', 'timedatectl', 'set-ntp', 'false'], check=True)
                
                dialog = Adw.MessageDialog.new(
                    self.get_root(),
                    "Success",
                    "Automatic time synchronization disabled"
                )
                dialog.add_response("ok", "OK")
                dialog.present()
            
            self._update_manual_settings_sensitivity()
            
        except Exception as e:
            # Show error dialog
            dialog = Adw.MessageDialog.new(
                self.get_root(),
                "Error",
                f"Failed to update time synchronization settings: {str(e)}"
            )
            dialog.add_response("ok", "OK")
            dialog.present()
            
            # Revert switch state
            switch.set_active(not is_active)

    def _check_sync_status(self, sync_dialog):
        try:
            # Check sync status
            result = subprocess.run(['timedatectl', 'show', '--property=NTPSynchronized'],
                                 capture_output=True, text=True, check=True)
            is_synced = result.stdout.strip() == "NTPSynchronized=yes"
            
            if is_synced:
                sync_dialog.set_heading("Success")
                sync_dialog.set_body("Time has been synchronized with internet servers")
                # Update the display immediately
                self._update_current_time()
            else:
                # If not synced yet, check again in 2 seconds
                return GLib.timeout_add(2000, self._check_sync_status, sync_dialog)
                
        except Exception as e:
            sync_dialog.set_heading("Warning")
            sync_dialog.set_body(f"Time synchronization status unknown: {str(e)}")
        
        return False

    def _update_manual_settings_sensitivity(self):
        is_auto = self.auto_time_switch.get_active()
        self.manual_settings_box.set_sensitive(not is_auto)

    def _update_current_time(self):
        now = datetime.datetime.now()
        self.current_time.set_markup(f"<big>{now.strftime('%H:%M:%S')}</big>")
        self.current_date.set_markup(f"<big>{now.strftime('%Y-%m-%d')}</big>")
        return True

    def _on_apply_clicked(self, button):
        if self.auto_time_switch.get_active():
            dialog = Adw.MessageDialog.new(
                self.get_root(),
                "Cannot Set Time",
                "Please disable automatic time synchronization before setting the time manually."
            )
            dialog.add_response("ok", "OK")
            dialog.present()
            return
            
        try:
            # Format the date and time string
            new_time = f"{self.year_spin.get_value_as_int():04d}-{self.month_spin.get_value_as_int():02d}-{self.day_spin.get_value_as_int():02d} "
            new_time += f"{self.hour_spin.get_value_as_int():02d}:{self.minute_spin.get_value_as_int():02d}:{self.second_spin.get_value_as_int():02d}"
            
            # Use date command to set system time (requires sudo)
            subprocess.run(['pkexec', 'date', '-s', new_time], check=True)
            
            # Show success dialog
            dialog = Adw.MessageDialog.new(
                self.get_root(),
                "Success",
                "Date and time updated successfully!"
            )
            dialog.add_response("ok", "OK")
            dialog.present()
            
            # Update the display immediately
            self._update_current_time()
            
        except Exception as e:
            # Show error dialog
            dialog = Adw.MessageDialog.new(
                self.get_root(),
                "Error",
                f"Failed to update date and time: {str(e)}"
            )
            dialog.add_response("ok", "OK")
            dialog.present()
