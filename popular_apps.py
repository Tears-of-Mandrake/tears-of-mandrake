import gi
import subprocess
import os
import threading
from pathlib import Path
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
import tempfile

ICONS_DIR = "/usr/share/tears-of-mandrake/images"

class Application:
    def __init__(self, name, package, binary_path, description, icon_name=None):
        self.name = name
        self.package = package
        self.binary_path = binary_path
        self.description = description
        # If no icon_name provided, use package name as icon name
        self.icon_name = icon_name if icon_name else package

class Category:
    def __init__(self, name, icon_name, applications):
        self.name = name
        self.icon_name = icon_name
        self.applications = applications

class PopularAppsPage(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        # Add page title and description
        title_group = Adw.PreferencesGroup()
        title_label = Gtk.Label()
        title_label.set_markup("<span size='x-large' weight='bold'>Popular Applications</span>")
        title_label.set_margin_bottom(10)
        title_group.add(title_label)
        
        description_label = Gtk.Label(
            label="Install and manage popular Linux applications. Applications are grouped by category "
                  "for easy navigation. Click Install to add new applications or Launch for installed ones."
        )
        description_label.set_wrap(True)
        description_label.set_margin_bottom(10)
        title_group.add(description_label)
        self.append(title_group)

        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        
        # Main box for categories
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        main_box.set_margin_start(10)
        main_box.set_margin_end(10)
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        
        # Define categories and applications
        self._add_category(main_box, "Web Browsers", [
            Application("Mozilla Firefox", "firefox", "/usr/bin/firefox", 
                      "Popular open-source web browser from Mozilla", "firefox"),
            Application("Chromium", "chromium-browser", "/usr/bin/chromium", 
                      "Open-source browser that powers Chrome", "chromium"),
            Application("Falkon", "plasma6-falkon", "/usr/bin/falkon", 
                      "Web browser based on QtWebEngine", "falkon"),
            Application("GNOME Web (Epiphany)", "epiphany", "/usr/bin/epiphany", 
                      "Simple and clean web browser for GNOME", "epiphany"),
            Application("Konqueror", "plasma6-konqueror", "/usr/bin/konqueror", 
                      "KDE's powerful web browser and file manager", "konqueror"),
            Application("SeaMonkey", "seamonkey", "/usr/bin/seamonkey", 
                      "All-in-one internet application suite", "seamonkey"),
            Application("Dooble", "dooble", "/usr/bin/Dooble", 
                      "Secure and private web browser", "dooble")
        ])

        self._add_category(main_box, "Email Clients", [
            Application("Mozilla Thunderbird", "thunderbird", "/usr/bin/thunderbird", 
                      "Full-featured email, RSS and newsgroup client", "thunderbird"),
            Application("Evolution", "evolution", "/usr/bin/evolution", 
                      "Integrated mail, calendar and address book", "evolution"),
            Application("KMail", "plasma6-kmail", "/usr/bin/kmail", 
                      "KDE's powerful email client", "kmail"),
            Application("Geary", "geary", "/usr/bin/geary", 
                      "Lightweight email client for GNOME", "geary"),
            Application("Claws Mail", "claws-mail", "/usr/bin/claws-mail", 
                      "Lightweight and fast email client", "claws-mail")
        ])

        self._add_category(main_box, "Office Suites", [
            Application("LibreOffice", "libreoffice", "/usr/bin/soffice", 
                      "Full-featured office suite compatible with Microsoft Office", "libreoffice"),
            Application("AbiWord", "abiword", "/usr/bin/abiword", 
                      "Lightweight word processor", "abiword"),
            Application("Calligra", "calligra", "/usr/bin/calligra", 
                      "Integrated office suite for KDE", "calligra")
        ])

        self._add_category(main_box, "Launchers", [
            Application("Steam", "steam", "/usr/bin/steam", "Popular gaming platform", "steam"),
            Application("WINE", "wine", None, "Windows compatibility layer"),
            Application("Proton", "wine", None, "Steam Play compatibility tool"),
            Application("Proton Experimental", "wine", None, "Experimental version of Proton"),
            Application("Proton Bleeding Edge", "wine", None, "Latest development version of Proton"),
            Application("DXVK", "dxvk", None, "Vulkan-based implementation of DirectX"),
            Application("Lutris", "lutris", "/usr/bin/lutris", "Game manager for Linux"),
            Application("Rare", "rare", "/usr/bin/rare", "Epic Games Launcher for Linux"),
            Application("Faugus Launcher", "faugus-launcher", "/usr/bin/faugus-launcher", "Game launcher")
        ])

        self._add_category(main_box, "Audio Players", [
            Application("G4Music", "g4music", "/usr/bin/g4music", "Modern GTK4 music player"),
            Application("LxMusic", "lxmusic", "/usr/bin/lxmusic", "Lightweight music player"),
            Application("Amarok", "amarok", "/usr/bin/amarok", "Feature-rich music player"),
            Application("Qmmp", "qmmp", "/usr/bin/qmmp", "Qt-based multimedia player"),
            Application("Audacious", "audacious", "/usr/bin/audacious", "Advanced audio player"),
            Application("Rhythmbox", "rhythmbox", "/usr/bin/rhythmbox", "Music management application"),
            Application("Amberol", "amberol", "/usr/bin/amberol", "Elegant music player"),
            Application("Nulloy", "nulloy", "/usr/bin/nulloy", "Music player with clean interface"),
            Application("Clementine", "clementine", "/usr/bin/clementine", "Modern music player and library organizer"),
            Application("Strawberry", "strawberry", "/usr/bin/strawberry", "Music player and collection organizer")
        ])

        self._add_category(main_box, "Video Players", [
            Application("Clapper", "clapper", "/usr/bin/clapper", "GNOME media player"),
            Application("MPV", "mpv", "/usr/bin/mpv", "Minimalist video player"),
            Application("VLC", "vlc", "/usr/bin/vlc", "Versatile media player"),
            Application("QMPlay2", "qmplay2", "/usr/bin/QMPlay2", "Video and audio player"),
            Application("Celluloid", "celluloid", "/usr/bin/celluloid", "GTK frontend for mpv"),
            Application("SMPlayer", "smplayer", "/usr/bin/smplayer", "Complete front-end for MPlayer")
        ])

        self._add_category(main_box, "Graphics", [
            Application("GIMP 3", "gimp", "/usr/bin/gimp", "Image manipulation program"),
            Application("Inkscape", "inkscape", "/usr/bin/inkscape", "Vector graphics editor"),
            Application("Darktable", "darktable", "/usr/bin/darktable", "Photography workflow application"),
            Application("RawTherapee", "rawtherapee", "/usr/bin/rawtherapee", "Raw image processing program"),
            Application("Krita", "krita", "/usr/bin/krita", "Digital painting program")
        ])

        self._add_category(main_box, "Video Editors", [
            Application("Kdenlive", "kdenlive", "/usr/bin/kdenlive", "Non-linear video editor"),
            Application("Shotcut", "shotcut", "/usr/bin/shotcut", "Cross-platform video editor"),
            Application("OpenShot", "openshot", "/usr/bin/openshot-qt", "Simple video editor"),
            Application("Pitivi", "pitivi", "/usr/bin/pitivi", "Free video editor")
        ])

        self._add_category(main_box, "Screen Recording / Stream", [
            Application("OBS Studio", "obs-studio", "/usr/bin/obs", "Streaming and recording program", "obs-studio"),
            Application("GPU Screen Recorder", "gpu-screen-recorder-gtk", "/usr/bin/gpu-screen-recorder-gtk", "Hardware-accelerated screen recorder"),
            Application("Vokoscreen NG", "vokoscreenng", "/usr/bin/vokoscreenNG", "Screen recorder")
        ])

        self._add_category(main_box, "Games", [
            Application("0 A.D.", "0ad", "/usr/games/0ad", "Ancient warfare game"),
            Application("SuperTux2", "supertux", "/usr/games/supertux2", "Jump'n'run game"),
            Application("Battle for Wesnoth", "wesnoth", "/usr/bin/wesnoth", "Turn-based strategy game"),
            Application("Widelands", "widelands", "/usr/bin/widelands", "Real-time strategy game"),
            Application("SuperTuxKart", "supertuxkart", "/usr/bin/supertuxkart", "3D racing game"),
            Application("ET Legacy", "etlegacy", "/usr/games/etl", "Wolfenstein: Enemy Territory game"),
            Application("Warzone 2100", "warzone2100", "/usr/bin/warzone2100", "Real-time strategy game"),
            Application("Endless Sky", "endless-sky", "/usr/games/endless-sky", "Space trading and combat game"),
            Application("ExtremeTuxRacer", "extremetuxracer", "/usr/bin/etr", "High-speed arctic racing game"),
            Application("TuxPusher", "tuxpusher", "/usr/bin/tuxpusher", "Coin pusher game"),
            Application("Veloren", "airshipper", "/usr/bin/airshipper", "Multiplayer voxel RPG"),
            Application("OpenTTD", "openttd", "/usr/games/openttd", "Transport simulation game"),
            Application("FreeCIV", "freeciv-client-gtk4", "/usr/bin/freeciv-gtk4", "Civilization-like game"),
            Application("Xonotic", "xonotic", "/usr/games/xonotic-glx", "Fast-paced arena shooter", None),
            Application("RedEclipse", "redeclipse", "/usr/bin/redeclipse", "Fast-paced arena shooter", None),
            Application("Tales of Maj'Eyal", "tome4", "/usr/bin/tome4", "Roguelike RPG"),
            Application("OpenArena", "openarena", "/usr/games/openarena", "Arena shooter game", None),
            Application("Sauerbraten", "sauerbraten", "/usr/bin/sauerbraten.sh", "FPS game engine", None),
            Application("Alien Arena", "alienarena", "/usr/bin/alienarena", "Sci-fi arena shooter", None),
            Application("7kaa", "7kaa", "/usr/bin/7kaa", "Strategy game"),
            Application("Hedgewars", "hedgewars", "/usr/bin/hedgewars", "Turn-based strategy game")
        ])

        self._add_category(main_box, "Games That Need Assets", [
            Application("VCMI", "vcmi", "/usr/bin/vcmilauncher", "Heroes III engine", None),
            Application("FHeroes2", "fheroes2", "/usr/bin/fheroes2", "Heroes II engine"),
            Application("DevilutionX", "devilutionx", "/usr/bin/devilutionx", "Diablo engine"),
            Application("OpenMW", "openmw", "/usr/bin/openmw-launcher", "Morrowind engine", None),
            Application("GZDoom", "gzdoom", "/usr/bin/gzdoom", "Advanced Doom engine", None),
            Application("VKQuake", "vkquake", "/usr/games/vkquake", "Vulkan Quake port")
        ])

        self._add_category(main_box, "Messengers", [
            Application("Fractal", "fractal", "/usr/bin/fractal", "Matrix client"),
            Application("Nheko", "nheko", "/usr/bin/nheko", "Matrix client"),
            Application("Quaternion", "quaternion", "/usr/bin/quaternion", "Matrix client"),
            Application("Pidgin", "pidgin", "/usr/bin/pidgin", "Multi-protocol messenger"),
            Application("Telegram", "telegram-desktop", "/usr/bin/telegram-desktop", "Telegram messenger")
        ])

        self._add_category(main_box, "Utility", [
            Application("Audacity", "audacity", "/usr/bin/audacity", "Audio editor"),
            Application("Blender", "blender", "/usr/bin/blender", "3D creation suite"),
            Application("Dropbox", "dropbox", "/usr/bin/dropbox", "Cloud storage service", None),
            Application("HandBrake", "handbrake", "/usr/bin/handbrake", "Video transcoder", None),
            Application("Mixxx", "mixxx", "/usr/bin/mixxx", "DJ software", None),
            Application("Zrythm", "zrythm", "/usr/bin/zrythm", "Digital audio workstation"),
            Application("VirtualBox", "virtualbox", "/usr/bin/VirtualBox", "Virtualization software")
        ])

        scrolled.set_child(main_box)
        self.append(scrolled)

    def _add_category(self, main_box, category_name, applications):
        category_group = Adw.PreferencesGroup()
        
        # Category header
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        category_icon = Gtk.Image.new_from_icon_name("applications-symbolic")
        header_box.append(category_icon)
        
        category_label = Gtk.Label()
        category_label.set_markup(f"<span size='large' weight='bold'>{category_name}</span>")
        header_box.append(category_label)
        
        category_group.set_header_suffix(header_box)
        
        # Add applications
        for app in applications:
            self.create_app_row(app, category_group)
        
        main_box.append(category_group)

    def create_app_row(self, app, category_group):
        row = Adw.ActionRow()
        row.set_title(app.name)
        row.set_subtitle(app.description)
        
        # Add app icon
        icon_path = os.path.join(ICONS_DIR, app.icon_name)
        if os.path.exists(f"{icon_path}.png"):
            app_icon = Gtk.Image.new_from_file(f"{icon_path}.png")
        elif os.path.exists(f"{icon_path}.svg"):
            app_icon = Gtk.Image.new_from_file(f"{icon_path}.svg")
        else:
            app_icon = Gtk.Image.new_from_icon_name("application-x-executable")
        app_icon.set_pixel_size(32)
        row.add_prefix(app_icon)
        
        # Check if app is installed
        is_installed = os.path.exists(app.binary_path) if app.binary_path else False
        
        # Add button
        if is_installed:
            if app.binary_path:  # Only add Launch button if there's a binary path
                button = Gtk.Button(label="Launch")
                button.add_css_class('success')
                button.connect('clicked', self.launch_application, app.binary_path)
            else:
                button = Gtk.Button(label="Installed")
                button.set_sensitive(False)
        else:
            button = Gtk.Button(label="Install")
            button.add_css_class('suggested-action')
            button.connect('clicked', self.install_package, app.package, app.name, app.binary_path)
        
        row.add_suffix(button)
        category_group.add(row)

    def launch_application(self, button, binary_path):
        try:
            subprocess.Popen([binary_path])
        except Exception as e:
            self.show_error_dialog("Launch Error", f"Failed to launch application.\nError: {str(e)}")

    def install_package(self, button, package_name, app_name, binary_path=None):
        button.set_sensitive(False)
        button.set_label("Installing...")

        # Create progress dialog
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            f"Installing {app_name}",
            "Please wait while the application is being installed..."
        )
        dialog.add_response("cancel", "Cancel")
        
        # Create progress box with fixed size
        progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        progress_box.set_margin_top(10)
        progress_box.set_margin_bottom(10)
        progress_box.set_margin_start(10)
        progress_box.set_margin_end(10)
        
        # Set fixed size for the box
        progress_box.set_size_request(600, 300)  # Increased size
        
        # Add progress bar
        progress_bar = Gtk.ProgressBar()
        progress_bar.set_show_text(True)
        progress_box.append(progress_bar)
        
        # Add scrolled window for status text
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)  # Allow horizontal scroll
        scroll.set_min_content_height(200)  # Set minimum height
        
        # Add status label with monospace font for DNF output
        status_label = Gtk.Label()
        status_label.set_wrap(False)  # Disable wrapping
        status_label.set_halign(Gtk.Align.START)
        status_label.set_margin_start(5)
        status_label.set_margin_end(5)
        status_label.set_markup("<span font_family='monospace' size='small'></span>")
        status_label.set_xalign(0)  # Left align text
        status_label.set_selectable(True)
        scroll.set_child(status_label)
        progress_box.append(scroll)
        
        # Set the extra child
        dialog.set_extra_child(progress_box)
        dialog.present()

        def update_progress(fraction, text):
            progress_bar.set_fraction(fraction)
            # Format text as a single line with newlines
            formatted_text = text.replace('\n', '\n')
            status_label.set_markup(f"<span font_family='monospace' size='small'>{formatted_text}</span>")
            # Scroll to the bottom to show latest output
            adj = scroll.get_vadjustment()
            adj.set_value(adj.get_upper() - adj.get_page_size())

        def show_success_dialog():
            success_dialog = Adw.MessageDialog.new(
                self.get_root(),
                "Installation Complete",
                f"{app_name} has been successfully installed!"
            )
            success_dialog.add_response("ok", "OK")
            success_dialog.present()



        def install_thread():
            try:

                # Start DNF installation with real-time output capture
                GLib.idle_add(update_progress, 0.2, "Starting installation...\n")
                
                # Prepare the DNF command
                dnf_cmd = ["pkexec", "dnf", "install", "-y", package_name]
                
                # Run DNF with output capture
                process = subprocess.Popen(
                    dnf_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )

                # Process output in real-time
                output_lines = []
                error_lines = []
                progress = 0.2
                downloading = False
                installing = False
                
                # Read both stdout and stderr
                def read_output(pipe, is_error=False):
                    while True:
                        line = pipe.readline()
                        if not line:
                            break
                        line = line.strip()
                        if line:
                            if is_error:
                                error_lines.append(line)
                                GLib.idle_add(update_progress, progress, f"Status: {line}")
                            else:
                                output_lines.append(line)
                                current_text = "\n".join(output_lines[-10:])  # Keep last 10 lines
                                if "Downloading Packages:" in line:
                                    GLib.idle_add(update_progress, 0.3, f"Downloading packages...\n{current_text}")
                                elif "Dependencies resolved." in line:
                                    GLib.idle_add(update_progress, 0.4, f"Dependencies resolved, preparing installation...\n{current_text}")
                                elif "Installing:" in line:
                                    pkg_info = line.split("Installing:")[-1].strip()
                                    GLib.idle_add(update_progress, 0.6, f"Installing: {pkg_info}\n{current_text}")
                                elif "Installed:" in line:
                                    pkg_info = line.split("Installed:")[-1].strip()
                                    GLib.idle_add(update_progress, 0.8, f"Installed: {pkg_info}\n{current_text}")
                                elif "Complete!" in line:
                                    GLib.idle_add(update_progress, 0.9, f"Installation complete!\n{current_text}")
                                else:
                                    GLib.idle_add(update_progress, progress, current_text)

                # Start reading in separate threads to avoid blocking
                import threading
                stdout_thread = threading.Thread(target=lambda: read_output(process.stdout))
                stderr_thread = threading.Thread(target=lambda: read_output(process.stderr, True))
                
                stdout_thread.start()
                stderr_thread.start()
                
                stdout_thread.join()
                stderr_thread.join()

                # Get any remaining stderr
                stderr_output = process.stderr.read()
                if stderr_output:
                    error_lines.append(stderr_output.strip())
                
                # Wait for the process to complete
                process.wait()
                
                # Combine all output
                error_output = "\n".join(output_lines)
                if error_lines:
                    error_output += "\n\nErrors:\n" + "\n".join(error_lines)
                
                if process.returncode == 0:
                    GLib.idle_add(update_progress, 1.0, "Installation completed successfully!")
                    GLib.idle_add(dialog.close)
                    GLib.idle_add(show_success_dialog)
                    
                    # Update button state
                    def update_button():
                        if binary_path and os.path.exists(binary_path):
                            button.set_label("Launch")
                            button.set_sensitive(True)
                            button.disconnect_by_func(self.install_package)
                            button.connect("clicked", self.launch_application, binary_path)
                        else:
                            button.set_label("Installed")
                            button.set_sensitive(False)
                    
                    GLib.idle_add(update_button)
                else:
                    # Show error dialog with the captured output
                    GLib.idle_add(dialog.close)
                    GLib.idle_add(lambda: self.show_repo_error_dialog(error_output, button))
                    GLib.idle_add(lambda: button.set_label("Install"))
                    GLib.idle_add(lambda: button.set_sensitive(True))
                    return
                
            except Exception as e:
                GLib.idle_add(dialog.close)
                GLib.idle_add(lambda: self.show_error_dialog(f"Error installing {app_name}", str(e)))
                GLib.idle_add(lambda: button.set_label("Install"))
                GLib.idle_add(lambda: button.set_sensitive(True))

        thread = threading.Thread(target=install_thread)
        thread.daemon = True
        thread.start()

    def show_error_dialog(self, title, message):
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            title,
            message
        )
        dialog.add_response("ok", "OK")
        dialog.present()

    def show_repo_error_dialog(self, error_msg, button=None):
        repo_dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Installation Error",
            f"Error installing package:\n{error_msg}\n\n" +
            "The package might be in a repository that is not enabled.\n" +
            "Would you like to run the repository configuration tool?"
        )
        repo_dialog.add_response("cancel", "Cancel")
        repo_dialog.add_response("configure", "Configure Repositories")
        repo_dialog.set_default_response("configure")
        repo_dialog.set_close_response("cancel")
        
        def on_repo_response(dialog, response):
            if response == "configure":
                # Launch the repository configuration tool
                try:
                    subprocess.Popen(
                        ["python3", "repo-test.py"],
                        cwd=os.path.dirname(os.path.abspath(__file__))
                    )
                except Exception as e:
                    self.show_error_dialog(
                        "Launch Error",
                        f"Failed to launch repository configuration tool: {str(e)}"
                    )
            # Reset button state
            if button:
                button.set_sensitive(True)
                button.set_label("Install")
        
        repo_dialog.connect("response", on_repo_response)
        repo_dialog.present()
