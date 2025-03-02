import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
import subprocess
import threading
import os

class InstallProgressDialog(Adw.Window):
    def __init__(self, parent, kernel_name):
        super().__init__(
            transient_for=parent,
            modal=True,
            title=f"Installing {kernel_name}",
            default_width=600,
            default_height=400
        )
        
        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        
        # Progress label
        self.status_label = Gtk.Label(label="Preparing installation...")
        self.status_label.set_halign(Gtk.Align.START)
        main_box.append(self.status_label)
        
        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_text("0%")
        main_box.append(self.progress_bar)
        
        # Scrolled window for output
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_margin_top(10)
        
        # Output text view with monospace font
        self.output_view = Gtk.TextView()
        self.output_view.set_editable(False)
        self.output_view.set_cursor_visible(False)
        self.output_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.output_view.get_style_context().add_class('monospace')
        self.output_buffer = self.output_view.get_buffer()
        
        scrolled.set_child(self.output_view)
        main_box.append(scrolled)
        
        self.set_content(main_box)
    
    def update_progress(self, fraction, status=None):
        self.progress_bar.set_fraction(fraction)
        self.progress_bar.set_text(f"{int(fraction * 100)}%")
        if status:
            self.status_label.set_text(status)
    
    def append_output(self, text):
        end_iter = self.output_buffer.get_end_iter()
        self.output_buffer.insert(end_iter, text + "\n")
        # Scroll to bottom
        mark = self.output_buffer.create_mark(None, end_iter, False)
        self.output_view.scroll_mark_onscreen(mark)
        self.output_buffer.delete_mark(mark)

class KernelManagerPage(Gtk.Box):
    def __init__(self, parent):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.parent = parent
        self.installed_kernels = self.get_installed_kernels()
        self.default_kernel = self.get_default_kernel()

        # Add page title and description
        title_group = Adw.PreferencesGroup()
        title_label = Gtk.Label()
        title_label.set_markup("<span size='x-large' weight='bold'>Kernel Manager</span>")
        title_label.set_margin_bottom(10)
        title_group.add(title_label)
        
        description_label = Gtk.Label(
            label="Manage your system kernels. You can install additional kernels or remove unused ones. "
                  "The default system kernel cannot be removed for system stability."
        )
        description_label.set_wrap(True)
        description_label.set_margin_bottom(10)
        title_group.add(description_label)
        
        self.append(title_group)

        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        
        # Main content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_margin_top(20)
        content_box.set_margin_bottom(20)
        content_box.set_margin_start(20)
        content_box.set_margin_end(20)
        content_box.set_spacing(20)

        # Desktop Kernels Section
        desktop_label = Gtk.Label()
        desktop_label.set_markup("<span weight='bold' size='large'>Desktop Kernels</span>")
        desktop_label.set_halign(Gtk.Align.START)
        content_box.append(desktop_label)

        # Desktop kernels grid
        desktop_grid = self.create_kernel_grid([
            {
                'name': 'kernel-desktop',
                'description': 'Desktop kernel compiled with Clang',
                'compiler': 'Clang'
            },
            {
                'name': 'kernel-desktop-gcc',
                'description': 'Desktop kernel compiled with GCC',
                'compiler': 'GCC'
            },
            {
                'name': 'kernel-rc-desktop',
                'description': 'Release Candidate desktop kernel compiled with Clang',
                'compiler': 'Clang',
                'is_testing': True
            },
            {
                'name': 'kernel-rc-desktop-gcc',
                'description': 'Release Candidate desktop kernel compiled with GCC',
                'compiler': 'GCC',
                'is_testing': True
            }
        ])
        content_box.append(desktop_grid)

        # Server Kernels Section
        server_label = Gtk.Label()
        server_label.set_markup("<span weight='bold' size='large'>Server Kernels</span>")
        server_label.set_halign(Gtk.Align.START)
        server_label.set_margin_top(20)
        content_box.append(server_label)

        # Server kernels grid
        server_grid = self.create_kernel_grid([
            {
                'name': 'kernel-server',
                'description': 'Server kernel compiled with Clang',
                'compiler': 'Clang'
            },
            {
                'name': 'kernel-server-gcc',
                'description': 'Server kernel compiled with GCC',
                'compiler': 'GCC'
            },
            {
                'name': 'kernel-rc-server',
                'description': 'Release Candidate server kernel compiled with Clang',
                'compiler': 'Clang',
                'is_testing': True
            },
            {
                'name': 'kernel-rc-server-gcc',
                'description': 'Release Candidate server kernel compiled with GCC',
                'compiler': 'GCC',
                'is_testing': True
            }
        ])
        content_box.append(server_grid)

        scrolled.set_child(content_box)
        self.append(scrolled)

    def get_installed_kernels(self):
        try:
            result = subprocess.run(
                ["rpm", "-qa", "kernel*"],
                capture_output=True,
                text=True
            )
            return result.stdout.splitlines()
        except:
            return []

    def get_default_kernel(self):
        try:
            result = subprocess.run(
                ["grubby", "--default-kernel"],
                capture_output=True,
                text=True
            )
            # Extract just the kernel name from the full path
            kernel_path = result.stdout.strip()
            if kernel_path:
                # Convert path like /boot/vmlinuz-6.1.0-1-amd64 to kernel-6.1.0-1-amd64
                return "kernel-" + kernel_path.split('vmlinuz-')[1]
            return ""
        except:
            return ""

    def create_kernel_grid(self, kernels):
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(10)
        grid.set_margin_start(10)
        
        for i, kernel in enumerate(kernels):
            # Kernel name and description
            info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            info_box.set_spacing(5)
            
            name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            name_label = Gtk.Label(label=kernel['name'])
            name_label.set_halign(Gtk.Align.START)
            name_box.append(name_label)
            
            # Add compiler badge
            compiler_label = Gtk.Label()
            compiler_label.add_css_class('caption')
            compiler_label.add_css_class('heading')
            compiler_label.set_markup(f"<span size='small'>{kernel['compiler']}</span>")
            name_box.append(compiler_label)
            
            # Add badges box
            badges_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            badges_box.set_margin_start(5)
            
            # Add RC badge if it's a testing kernel
            if kernel.get('is_testing', False):
                rc_label = Gtk.Label()
                rc_label.add_css_class('caption')
                rc_label.add_css_class('heading')
                rc_label.set_markup("<span size='small' foreground='orange'>RC</span>")
                badges_box.append(rc_label)
            
            # Add default badge if this is the current running kernel
            if self.default_kernel and kernel['name'] in self.default_kernel:
                default_label = Gtk.Label()
                default_label.add_css_class('caption')
                default_label.add_css_class('heading')
                default_label.set_markup("<span size='small' foreground='green'>DEFAULT</span>")
                badges_box.append(default_label)
            
            name_box.append(badges_box)
            info_box.append(name_box)
            
            desc_label = Gtk.Label(label=kernel['description'])
            desc_label.set_halign(Gtk.Align.START)
            desc_label.add_css_class('caption')
            info_box.append(desc_label)
            
            grid.attach(info_box, 0, i, 1, 1)
            
            # Button box
            button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            button_box.set_halign(Gtk.Align.END)
            button_box.set_hexpand(True)
            
            is_installed = any(kernel['name'] in k for k in self.installed_kernels)
            is_default = self.default_kernel and kernel['name'] in self.default_kernel
            is_protected = kernel['name'] == 'kernel-desktop'  # Protect kernel-desktop
            
            if is_installed:
                if not is_default and not is_protected:
                    # Show remove button only for non-default and non-protected kernels
                    remove_button = Gtk.Button(label="Remove")
                    remove_button.add_css_class('destructive-action')
                    remove_button.connect('clicked', self.on_remove_clicked, kernel['name'])
                    button_box.append(remove_button)
                
                # Status label with green background for installed kernels
                status_box = Gtk.Box()
                status_box.add_css_class('success')
                status_box.add_css_class('pill')
                status_box.set_margin_start(5)
                status_label = Gtk.Label(label="Installed")
                status_label.add_css_class('caption')
                status_label.set_margin_start(5)
                status_label.set_margin_end(5)
                status_box.append(status_label)
                button_box.append(status_box)
            else:
                # Install button
                install_button = Gtk.Button(label="Install")
                install_button.add_css_class('suggested-action')
                install_button.connect('clicked', self.on_install_clicked, kernel['name'])
                button_box.append(install_button)
            
            grid.attach(button_box, 1, i, 1, 1)
        
        return grid

    def on_install_clicked(self, button, kernel_name):
        # Create installation dialog
        confirm_dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Install Kernel",
            f"Do you want to install {kernel_name}?\n\nThis will install an additional kernel to your system."
        )
        confirm_dialog.add_response("cancel", "Cancel")
        confirm_dialog.add_response("install", "Install")
        confirm_dialog.set_response_appearance("install", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(dialog, response):
            if response == "install":
                # Create and show progress dialog
                progress_dialog = InstallProgressDialog(self.get_root(), kernel_name)
                progress_dialog.present()
                
                # Start installation in a separate thread
                thread = threading.Thread(
                    target=self.install_kernel,
                    args=(button, kernel_name, progress_dialog)
                )
                thread.daemon = True
                thread.start()
        
        confirm_dialog.connect("response", on_response)
        confirm_dialog.present()

    def on_remove_clicked(self, button, kernel_name):
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Remove Kernel",
            f"Do you want to remove {kernel_name}?\n\nThis will remove the kernel from your system."
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("remove", "Remove")
        dialog.set_response_appearance("remove", Adw.ResponseAppearance.DESTRUCTIVE)
        
        def on_response(dialog, response):
            if response == "remove":
                # Create and show progress dialog
                progress_dialog = InstallProgressDialog(self.get_root(), kernel_name)
                progress_dialog.present()
                
                # Start removal in a separate thread
                thread = threading.Thread(
                    target=self.remove_kernel,
                    args=(button, kernel_name, progress_dialog)
                )
                thread.daemon = True
                thread.start()
        
        dialog.connect("response", on_response)
        dialog.present()

    def remove_kernel(self, button, kernel_name, progress_dialog):
        try:
            cmd = ["pkexec", "dnf", "remove", "-y", kernel_name]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Track removal progress
            current_step = 0
            total_steps = 4  # Dependencies, Remove, Cleanup, Done
            
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                
                # Update progress based on key phrases
                if "Resolving Dependencies" in line:
                    current_step = 1
                    GLib.idle_add(progress_dialog.update_progress, 0.25, "Resolving dependencies...")
                elif "Removing" in line:
                    current_step = 2
                    GLib.idle_add(progress_dialog.update_progress, 0.50, "Removing kernel...")
                elif "Cleanup" in line:
                    current_step = 3
                    GLib.idle_add(progress_dialog.update_progress, 0.75, "Cleaning up...")
                
                # Update output text
                GLib.idle_add(progress_dialog.append_output, line.strip())

            stdout, stderr = process.communicate()

            def update_ui(success):
                # Close the progress dialog first
                progress_dialog.destroy()
                
                if success:
                    # Update installed kernels list and refresh the page
                    self.installed_kernels = self.get_installed_kernels()
                    
                    # Remove all children from the parent box
                    while child := self.get_first_child():
                        self.remove(child)
                    
                    # Recreate the kernel grids
                    desktop_grid = self.create_kernel_grid([
                        {
                            'name': 'kernel-desktop',
                            'description': 'Desktop kernel compiled with Clang',
                            'compiler': 'Clang'
                        },
                        {
                            'name': 'kernel-desktop-gcc',
                            'description': 'Desktop kernel compiled with GCC',
                            'compiler': 'GCC'
                        },
                        {
                            'name': 'kernel-rc-desktop',
                            'description': 'Release Candidate desktop kernel compiled with Clang',
                            'compiler': 'Clang',
                            'is_testing': True
                        },
                        {
                            'name': 'kernel-rc-desktop-gcc',
                            'description': 'Release Candidate desktop kernel compiled with GCC',
                            'compiler': 'GCC',
                            'is_testing': True
                        }
                    ])
                    
                    server_grid = self.create_kernel_grid([
                        {
                            'name': 'kernel-server',
                            'description': 'Server kernel compiled with Clang',
                            'compiler': 'Clang'
                        },
                        {
                            'name': 'kernel-server-gcc',
                            'description': 'Server kernel compiled with GCC',
                            'compiler': 'GCC'
                        },
                        {
                            'name': 'kernel-rc-server',
                            'description': 'Release Candidate server kernel compiled with Clang',
                            'compiler': 'Clang',
                            'is_testing': True
                        },
                        {
                            'name': 'kernel-rc-server-gcc',
                            'description': 'Release Candidate server kernel compiled with GCC',
                            'compiler': 'GCC',
                            'is_testing': True
                        }
                    ])
                    
                    # Add page title and description
                    title_group = Adw.PreferencesGroup()
                    title_label = Gtk.Label()
                    title_label.set_markup("<span size='x-large' weight='bold'>Kernel Manager</span>")
                    title_label.set_margin_bottom(10)
                    title_group.add(title_label)
                    
                    description_label = Gtk.Label(
                        label="Manage your system kernels. You can install additional kernels or remove unused ones. "
                              "The default system kernel cannot be removed for system stability."
                    )
                    description_label.set_wrap(True)
                    description_label.set_margin_bottom(10)
                    title_group.add(description_label)
                    
                    self.append(title_group)
                    
                    # Add desktop kernels section
                    desktop_section = Adw.PreferencesGroup()
                    desktop_section.set_title("Desktop Kernels")
                    desktop_section.set_description("Kernels optimized for desktop use")
                    desktop_section.add(desktop_grid)
                    self.append(desktop_section)
                    
                    # Add server kernels section
                    server_section = Adw.PreferencesGroup()
                    server_section.set_title("Server Kernels")
                    server_section.set_description("Kernels optimized for server use")
                    server_section.add(server_grid)
                    self.append(server_section)
                    
                    dialog = Adw.MessageDialog.new(
                        self.get_root(),
                        "Operation Complete",
                        f"Successfully completed operation on {kernel_name}."
                    )
                else:
                    button.set_label("Remove")
                    button.set_sensitive(True)
                    dialog = Adw.MessageDialog.new(
                        self.get_root(),
                        "Operation Failed",
                        f"Failed to complete operation on {kernel_name}.\nError: {stderr}"
                    )
                dialog.add_response("ok", "OK")
                dialog.present()

            GLib.idle_add(update_ui, process.returncode == 0)

        except Exception as e:
            def show_error():
                # Close the progress dialog first
                progress_dialog.destroy()
                
                button.set_label("Remove")
                button.set_sensitive(True)
                dialog = Adw.MessageDialog.new(
                    self.get_root(),
                    "Removal Error",
                    f"An error occurred while removing {kernel_name}:\n{str(e)}"
                )
                dialog.add_response("ok", "OK")
                dialog.present()

            GLib.idle_add(show_error)

    def install_kernel(self, button, kernel_name, progress_dialog):
        try:
            cmd = ["pkexec", "dnf", "install", "-y", kernel_name]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                
                # Update progress based on key phrases
                if "Downloading" in line:
                    GLib.idle_add(progress_dialog.update_progress, 0.25, "Downloading packages...")
                elif "Dependencies resolved" in line:
                    GLib.idle_add(progress_dialog.update_progress, 0.50, "Dependencies resolved...")
                elif "Installing" in line:
                    GLib.idle_add(progress_dialog.update_progress, 0.75, "Installing kernel...")
                elif "Complete!" in line:
                    GLib.idle_add(progress_dialog.update_progress, 1.0, "Installation complete!")
                
                # Update output text
                GLib.idle_add(progress_dialog.append_output, line.strip())

            stdout, stderr = process.communicate()

            def update_ui(success):
                # Close the progress dialog first
                progress_dialog.destroy()
                
                if success:
                    # Update installed kernels list and refresh the page
                    self.installed_kernels = self.get_installed_kernels()
                    
                    # Remove all children from the parent box
                    while child := self.get_first_child():
                        self.remove(child)
                    
                    # Recreate the kernel grids
                    desktop_grid = self.create_kernel_grid([
                        {
                            'name': 'kernel-desktop',
                            'description': 'Desktop kernel compiled with Clang',
                            'compiler': 'Clang'
                        },
                        {
                            'name': 'kernel-desktop-gcc',
                            'description': 'Desktop kernel compiled with GCC',
                            'compiler': 'GCC'
                        },
                        {
                            'name': 'kernel-rc-desktop',
                            'description': 'Release Candidate desktop kernel compiled with Clang',
                            'compiler': 'Clang',
                            'is_testing': True
                        },
                        {
                            'name': 'kernel-rc-desktop-gcc',
                            'description': 'Release Candidate desktop kernel compiled with GCC',
                            'compiler': 'GCC',
                            'is_testing': True
                        }
                    ])
                    
                    server_grid = self.create_kernel_grid([
                        {
                            'name': 'kernel-server',
                            'description': 'Server kernel compiled with Clang',
                            'compiler': 'Clang'
                        },
                        {
                            'name': 'kernel-server-gcc',
                            'description': 'Server kernel compiled with GCC',
                            'compiler': 'GCC'
                        },
                        {
                            'name': 'kernel-rc-server',
                            'description': 'Release Candidate server kernel compiled with Clang',
                            'compiler': 'Clang',
                            'is_testing': True
                        },
                        {
                            'name': 'kernel-rc-server-gcc',
                            'description': 'Release Candidate server kernel compiled with GCC',
                            'compiler': 'GCC',
                            'is_testing': True
                        }
                    ])
                    
                    # Add page title and description
                    title_group = Adw.PreferencesGroup()
                    title_label = Gtk.Label()
                    title_label.set_markup("<span size='x-large' weight='bold'>Kernel Manager</span>")
                    title_label.set_margin_bottom(10)
                    title_group.add(title_label)
                    
                    description_label = Gtk.Label(
                        label="Manage your system kernels. You can install additional kernels or remove unused ones. "
                              "The default system kernel cannot be removed for system stability."
                    )
                    description_label.set_wrap(True)
                    description_label.set_margin_bottom(10)
                    title_group.add(description_label)
                    
                    self.append(title_group)
                    
                    # Add desktop kernels section
                    desktop_section = Adw.PreferencesGroup()
                    desktop_section.set_title("Desktop Kernels")
                    desktop_section.set_description("Kernels optimized for desktop use")
                    desktop_section.add(desktop_grid)
                    self.append(desktop_section)
                    
                    # Add server kernels section
                    server_section = Adw.PreferencesGroup()
                    server_section.set_title("Server Kernels")
                    server_section.set_description("Kernels optimized for server use")
                    server_section.add(server_grid)
                    self.append(server_section)
                    
                    dialog = Adw.MessageDialog.new(
                        self.get_root(),
                        "Operation Complete",
                        f"Successfully completed operation on {kernel_name}."
                    )
                else:
                    button.set_label("Install")
                    button.set_sensitive(True)
                    dialog = Adw.MessageDialog.new(
                        self.get_root(),
                        "Operation Failed",
                        f"Failed to complete operation on {kernel_name}.\nError: {stderr}"
                    )
                dialog.add_response("ok", "OK")
                dialog.present()

            GLib.idle_add(update_ui, process.returncode == 0)

        except Exception as e:
            def show_error():
                # Close the progress dialog first
                progress_dialog.destroy()
                
                button.set_label("Install")
                button.set_sensitive(True)
                dialog = Adw.MessageDialog.new(
                    self.get_root(),
                    "Installation Error",
                    f"An error occurred while installing {kernel_name}:\n{str(e)}"
                )
                dialog.add_response("ok", "OK")
                dialog.present()

            GLib.idle_add(show_error)
