import gi
import os
import subprocess
import psutil
import json
from datetime import datetime

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

class HardwareInfoPage(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        
        # Create main box with padding
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        
        # Add hardware information sections
        self._add_cpu_info(main_box)
        self._add_memory_info(main_box)
        self._add_storage_info(main_box)
        self._add_gpu_info(main_box)
        self._add_display_info(main_box)
        
        scrolled.set_child(main_box)
        self.append(scrolled)
        
        # Update info every 5 seconds
        GLib.timeout_add(5000, self._update_info)

    def _create_section(self, title):
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        section.set_margin_bottom(15)
        
        header = Gtk.Label()
        header.set_markup(f"<b>{title}</b>")
        header.set_halign(Gtk.Align.START)
        section.append(header)
        
        return section

    def _add_cpu_info(self, parent_box):
        cpu_section = self._create_section("CPU Information")
        
        # Get CPU info
        with open('/proc/cpuinfo') as f:
            cpu_info = f.readlines()
        
        model_name = "Unknown"
        cores = psutil.cpu_count(logical=False)
        threads = psutil.cpu_count(logical=True)
        
        for line in cpu_info:
            if "model name" in line:
                model_name = line.split(':')[1].strip()
                break
        
        freq = psutil.cpu_freq()
        if freq:
            current_freq = f"{freq.current:.2f} MHz"
            max_freq = f"{freq.max:.2f} MHz"
        else:
            current_freq = "Unknown"
            max_freq = "Unknown"
        
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        info_box.set_margin_start(10)
        
        labels = [
            f"Model: {model_name}",
            f"Physical cores: {cores}",
            f"Logical cores: {threads}",
            f"Current Frequency: {current_freq}",
            f"Maximum Frequency: {max_freq}"
        ]
        
        for text in labels:
            label = Gtk.Label(label=text)
            label.set_halign(Gtk.Align.START)
            info_box.append(label)
        
        cpu_section.append(info_box)
        parent_box.append(cpu_section)

    def _add_memory_info(self, parent_box):
        mem_section = self._create_section("Memory Information")
        
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        info_box.set_margin_start(10)
        
        labels = [
            f"Total Memory: {self._format_bytes(mem.total)}",
            f"Available Memory: {self._format_bytes(mem.available)}",
            f"Used Memory: {self._format_bytes(mem.used)} ({mem.percent}%)",
            f"Total Swap: {self._format_bytes(swap.total)}",
            f"Used Swap: {self._format_bytes(swap.used)} ({swap.percent}%)"
        ]
        
        for text in labels:
            label = Gtk.Label(label=text)
            label.set_halign(Gtk.Align.START)
            info_box.append(label)
        
        mem_section.append(info_box)
        parent_box.append(mem_section)

    def _add_storage_info(self, parent_box):
        storage_section = self._create_section("Storage Information")
        
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        info_box.set_margin_start(10)
        
        partitions = psutil.disk_partitions()
        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                label = Gtk.Label(label=f"Device {partition.device} mounted on {partition.mountpoint}:")
                label.set_halign(Gtk.Align.START)
                info_box.append(label)
                
                details = Gtk.Label(label=f"  Total: {self._format_bytes(usage.total)}, "
                                        f"Used: {self._format_bytes(usage.used)} ({usage.percent}%)")
                details.set_halign(Gtk.Align.START)
                info_box.append(details)
            except:
                continue
        
        storage_section.append(info_box)
        parent_box.append(storage_section)

    def _add_gpu_info(self, parent_box):
        gpu_section = self._create_section("GPU Information")
        
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        info_box.set_margin_start(10)
        
        # Try to get NVIDIA GPU info
        try:
            nvidia_info = subprocess.check_output(['nvidia-smi', '--query-gpu=gpu_name,driver_version,memory.total,memory.used',
                                                 '--format=csv,noheader,nounits'], text=True)
            for line in nvidia_info.strip().split('\n'):
                name, driver, total_mem, used_mem = line.split(', ')
                labels = [
                    f"GPU: {name}",
                    f"Driver Version: {driver}",
                    f"Total Memory: {total_mem} MB",
                    f"Used Memory: {used_mem} MB"
                ]
                for text in labels:
                    label = Gtk.Label(label=text)
                    label.set_halign(Gtk.Align.START)
                    info_box.append(label)
        except:
            # Try to get Mesa/AMD GPU info
            try:
                glxinfo = subprocess.check_output(['glxinfo'], text=True)
                vendor = None
                renderer = None
                version = None
                
                for line in glxinfo.split('\n'):
                    if 'OpenGL vendor string' in line:
                        vendor = line.split(':')[1].strip()
                    elif 'OpenGL renderer string' in line:
                        renderer = line.split(':')[1].strip()
                    elif 'OpenGL version string' in line:
                        version = line.split(':')[1].strip()
                
                if vendor and renderer and version:
                    labels = [
                        f"GPU: {renderer}",
                        f"Vendor: {vendor}",
                        f"OpenGL Version: {version}"
                    ]
                    for text in labels:
                        label = Gtk.Label(label=text)
                        label.set_halign(Gtk.Align.START)
                        info_box.append(label)
            except:
                label = Gtk.Label(label="Could not detect GPU information")
                label.set_halign(Gtk.Align.START)
                info_box.append(label)
        
        gpu_section.append(info_box)
        parent_box.append(gpu_section)

    def _add_display_info(self, parent_box):
        display_section = self._create_section("Display Information")
        
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        info_box.set_margin_start(10)
        
        try:
            xrandr = subprocess.check_output(['xrandr'], text=True)
            for line in xrandr.split('\n'):
                if ' connected ' in line:
                    parts = line.split()
                    output = parts[0]
                    resolution = "unknown"
                    for part in parts:
                        if 'x' in part and '+' in part:
                            resolution = part.split('+')[0]
                            break
                    
                    label = Gtk.Label(label=f"Monitor {output}: {resolution}")
                    label.set_halign(Gtk.Align.START)
                    info_box.append(label)
        except:
            label = Gtk.Label(label="Could not detect display information")
            label.set_halign(Gtk.Align.START)
            info_box.append(label)
        
        display_section.append(info_box)
        parent_box.append(display_section)

    def _format_bytes(self, bytes):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024
        return f"{bytes:.2f} PB"

    def _update_info(self):
        # Refresh the widget
        self.queue_draw()
        return True  # Keep the timeout active

    def _on_back_clicked(self, button):
        parent = self.get_parent()
        if isinstance(parent, Gtk.Stack):
            parent.set_visible_child_name("main")
