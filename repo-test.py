import gi
import subprocess
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, Gdk

class MyApp(Adw.Application):

    def __init__(self):
        super().__init__(application_id='com.example.MyApp',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        win = MyAppWindow(application=app)
        win.present()

class MyAppWindow(Adw.ApplicationWindow):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("OpenMandriva Repository Manager")
        self.set_default_size(800, 500)
        
        # Track repository states
        self.repo_states = {
            "extra": False,
            "restricted": False,
            "non-free": False
        }

        # Tworzenie kontenera głównego
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.set_content(main_box)

        # Create header
        header_bar = Adw.HeaderBar()
        header_bar.set_title_widget(Gtk.Label(label="OpenMandriva Repository Manager"))

        # Dodanie nagłówka do głównego kontenera
        main_box.append(header_bar)

        # Tworzenie stylizacji CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            label.title {
                font-weight: bold;
                font-size: 20px;
            }
        """)

        # Dodanie stylizacji do kontekstu
        display = Gdk.Display.get_default()
        Gtk.StyleContext.add_provider_for_display(
            display,
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Add welcome title
        title_label = Gtk.Label(label="OpenMandriva Repository Manager")
        title_label.get_style_context().add_class("title")
        title_label.set_margin_top(20)
        title_label.set_margin_bottom(10)
        title_label.set_halign(Gtk.Align.CENTER)
        title_label.set_valign(Gtk.Align.CENTER)
        title_label.set_wrap(True)
        title_label.set_max_width_chars(60)
        main_box.append(title_label)

        # Add description
        description_label = Gtk.Label(
            label="Manage OpenMandriva repositories with ease. You can enable or disable additional repositories "
                  "such as Extra (unsupported/contrib), Restricted, and Non-Free. Click a button to toggle "
                  "the repository state on/off."
        )
        description_label.set_margin_top(10)
        description_label.set_margin_bottom(20)
        description_label.set_halign(Gtk.Align.CENTER)
        description_label.set_valign(Gtk.Align.CENTER)
        description_label.set_wrap(True)
        description_label.set_max_width_chars(60)
        main_box.append(description_label)

        # Create a box for buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        button_box.set_margin_top(10)
        button_box.set_margin_bottom(10)
        button_box.set_halign(Gtk.Align.CENTER)

        # Main button to enable all repositories
        self.all_button = Gtk.Button(label="Enable All Repositories")
        self.all_button.connect("clicked", self.on_button_clicked, "all")
        self.all_button.set_margin_bottom(20)  # Add some space before specific buttons
        button_box.append(self.all_button)

        # Button for extra repository
        self.extra_button = Gtk.Button()
        self.extra_button.connect("clicked", self.on_button_clicked, "extra")
        button_box.append(self.extra_button)

        # Button for restricted repository
        self.restricted_button = Gtk.Button()
        self.restricted_button.connect("clicked", self.on_button_clicked, "restricted")
        button_box.append(self.restricted_button)

        # Button for non-free repository
        self.nonfree_button = Gtk.Button()
        self.nonfree_button.connect("clicked", self.on_button_clicked, "non-free")
        button_box.append(self.nonfree_button)
        
        main_box.append(button_box)
        
        # Now that buttons are created, update repository states
        self.update_repo_states()

    def get_base_type(self):
        try:
            result = subprocess.run(["cat", "/etc/openmandriva-release"], capture_output=True, text=True, check=True)
            release_info = result.stdout.strip()
            if "ROME" in release_info or "Rolling" in release_info:
                return "rolling"
            elif "ROCK" in release_info:
                return "rock"
            else:
                return "cooker"
        except:
            return "cooker"  # Default to cooker if can't determine

    def check_repo_enabled(self, repo_name):
        try:
            # Use dnf repolist to check if repository is enabled
            result = subprocess.run(
                ["dnf", "repolist", "--enabled"], 
                capture_output=True, 
                text=True
            )
            return repo_name in result.stdout
        except Exception as e:
            print(f"Error checking repository {repo_name}: {e}")
            return False

    def update_repo_states(self):
        base_type = self.get_base_type()
        try:
            # Check each repository's actual state using dnf repolist
            self.repo_states["extra"] = self.check_repo_enabled(f"{base_type}-x86_64-extra")
            self.repo_states["restricted"] = self.check_repo_enabled(f"{base_type}-x86_64-restricted")
            self.repo_states["non-free"] = self.check_repo_enabled(f"{base_type}-x86_64-non-free")
            
            print("Current repository states:")
            for repo, state in self.repo_states.items():
                print(f"{repo}: {'enabled' if state else 'disabled'}")
            
            self.update_button_labels()
        except Exception as e:
            print(f"Error checking repository states: {e}")
            dialog = Adw.MessageDialog(
                transient_for=self,
                heading="Warning",
                body="Could not determine repository states. Please check your system configuration."
            )
            dialog.add_response("ok", "OK")
            dialog.present()

    def update_button_labels(self):
        # Update individual repo buttons
        self.extra_button.set_label("Disable Extra" if self.repo_states["extra"] else "Enable Extra")
        self.restricted_button.set_label("Disable Restricted" if self.repo_states["restricted"] else "Enable Restricted")
        self.nonfree_button.set_label("Disable Non-Free" if self.repo_states["non-free"] else "Enable Non-Free")
        
        # Update all repositories button
        all_enabled = all(self.repo_states.values())
        self.all_button.set_label("Disable All Repositories" if all_enabled else "Enable All Repositories")

    def on_button_clicked(self, button, repo_type_arg):
        try:
            base_type = self.get_base_type()
            enable = True  # Default to enable

            if repo_type_arg != "all":
                # Toggle individual repository
                enable = not self.repo_states[repo_type_arg]

            # Prepare command
            command = ["pkexec", "dnf", "config-manager", "--enable" if enable else "--disable"]
            
            if repo_type_arg == "all":
                # If any repo is disabled, enable all. Otherwise, disable all.
                enable = not all(self.repo_states.values())
                command.extend([
                    f"{base_type}-x86_64-extra",
                    f"{base_type}-x86_64-restricted",
                    f"{base_type}-x86_64-non-free"
                ])
            else:
                command.append(f"{base_type}-x86_64-{repo_type_arg}")

            # Execute the command
            subprocess.run(command, check=True)
            
            # Wait a moment for DNF to update its cache
            subprocess.run(["dnf", "clean", "expire-cache"], check=True)
            
            # Verify the new states
            self.update_repo_states()

            # Show success dialog
            action = "enabled" if enable else "disabled"
            dialog = Adw.MessageDialog(
                transient_for=self,
                heading="Success",
                body=f"Repository {repo_type_arg} has been {action} successfully."
            )
            dialog.add_response("ok", "OK")
            dialog.present()

        except subprocess.CalledProcessError as e:
            print(f"Error occurred: {e}")
            # Show error dialog
            dialog = Adw.MessageDialog(
                transient_for=self,
                heading="Error",
                body=f"Failed to modify repository: {str(e)}"
            )
            dialog.add_response("ok", "OK")
            dialog.present()
            # Refresh states in case of error
            self.update_repo_states()

if __name__ == '__main__':
    app = MyApp()
    app.run(None)
