import gi
import subprocess
import pwd
import grp
from gi.repository import Gtk, Adw, GLib, Gio, Pango

class UserDialog(Adw.Window):
    def __init__(self, parent, user=None):
        super().__init__(transient_for=parent)
        self.parent = parent
        self.user = user
        self.set_modal(True)
        self.set_title("Add User" if user is None else "Edit User")
        self.set_default_size(400, -1)
        
        # Main layout
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Header bar
        header = Adw.HeaderBar()
        self.main_box.append(header)
        
        # Content
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content.set_margin_top(10)
        content.set_margin_bottom(10)
        content.set_margin_start(10)
        content.set_margin_end(10)
        
        # Username
        username_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        username_label = Gtk.Label(label="Username")
        username_label.set_halign(Gtk.Align.START)
        self.username_entry = Gtk.Entry()
        if user:
            self.username_entry.set_text(user.pw_name)
            self.username_entry.set_sensitive(False)
        username_box.append(username_label)
        username_box.append(self.username_entry)
        content.append(username_box)
        
        # Full Name
        fullname_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        fullname_label = Gtk.Label(label="Full Name")
        fullname_label.set_halign(Gtk.Align.START)
        self.fullname_entry = Gtk.Entry()
        if user and user.pw_gecos:
            self.fullname_entry.set_text(user.pw_gecos)
        fullname_box.append(fullname_label)
        fullname_box.append(self.fullname_entry)
        content.append(fullname_box)
        
        # Password
        if not user:  # Only show password fields for new users
            password_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            password_label = Gtk.Label(label="Password")
            password_label.set_halign(Gtk.Align.START)
            self.password_entry = Gtk.PasswordEntry()
            password_box.append(password_label)
            password_box.append(self.password_entry)
            content.append(password_box)
            
            confirm_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            confirm_label = Gtk.Label(label="Confirm Password")
            confirm_label.set_halign(Gtk.Align.START)
            self.confirm_entry = Gtk.PasswordEntry()
            confirm_box.append(confirm_label)
            confirm_box.append(self.confirm_entry)
            content.append(confirm_box)
        
        # Administrator checkbox
        self.admin_check = Gtk.CheckButton(label="Administrator")
        if user:
            # Check if user is in wheel/sudo group
            groups = [g.gr_name for g in grp.getgrall() if user.pw_name in g.gr_mem]
            self.admin_check.set_active("wheel" in groups or "sudo" in groups)
        content.append(self.admin_check)
        
        # Groups
        groups_label = Gtk.Label(label="Additional Groups")
        groups_label.set_halign(Gtk.Align.START)
        content.append(groups_label)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_min_content_height(150)
        scrolled.set_max_content_height(150)
        
        self.groups_list = Gtk.ListBox()
        self.groups_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.groups_list.add_css_class("boxed-list")
        
        # Add common groups with checkboxes
        common_groups = ["audio", "video", "render", "wheel", "network", "storage"]
        user_groups = []
        if user:
            user_groups = [g.gr_name for g in grp.getgrall() if user.pw_name in g.gr_mem]
        
        for group_name in common_groups:
            try:
                group = grp.getgrnam(group_name)
                row = Gtk.ListBoxRow()
                box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                box.set_margin_top(5)
                box.set_margin_bottom(5)
                box.set_margin_start(10)
                box.set_margin_end(10)
                
                check = Gtk.CheckButton(label=group_name)
                check.set_active(group_name in user_groups)
                box.append(check)
                
                row.set_child(box)
                row.check = check  # Store reference to checkbox
                self.groups_list.append(row)
            except KeyError:
                continue
        
        scrolled.set_child(self.groups_list)
        content.append(scrolled)
        
        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.END)
        
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda x: self.close())
        button_box.append(cancel_button)
        
        save_button = Gtk.Button(label="Save")
        save_button.add_css_class("suggested-action")
        save_button.connect("clicked", self.on_save)
        button_box.append(save_button)
        
        content.append(button_box)
        
        self.main_box.append(content)
        self.set_content(self.main_box)
    
    def get_selected_groups(self):
        groups = []
        for row in self.groups_list:
            if row.check.get_active():
                groups.append(row.check.get_label())
        return groups
    
    def on_save(self, button):
        username = self.username_entry.get_text().strip()
        fullname = self.fullname_entry.get_text().strip()
        is_admin = self.admin_check.get_active()
        groups = self.get_selected_groups()
        
        if not username:
            self.show_error("Username is required")
            return
        
        if not self.user:  # Adding new user
            password = self.password_entry.get_text()
            confirm = self.confirm_entry.get_text()
            
            if not password:
                self.show_error("Password is required")
                return
            
            if password != confirm:
                self.show_error("Passwords do not match")
                return
            
            try:
                # Create user
                cmd = ["useradd", "-m", "-c", fullname or username, username]
                if is_admin:
                    cmd.extend(["-G", "wheel"])
                subprocess.run(["pkexec"] + cmd, check=True)
                
                # Set password
                p = subprocess.Popen(["pkexec", "passwd", username],
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
                p.communicate(input=f"{password}\n{password}\n".encode())
            except subprocess.CalledProcessError as e:
                self.show_error(f"Failed to create user: {e}")
                return
        else:  # Editing existing user
            try:
                # Update full name
                if fullname != self.user.pw_gecos:
                    subprocess.run(["pkexec", "usermod", "-c", fullname, username], check=True)
                
                # Update groups
                current_groups = [g.gr_name for g in grp.getgrall() if username in g.gr_mem]
                groups_to_add = [g for g in groups if g not in current_groups]
                groups_to_remove = [g for g in current_groups if g not in groups and g != username]
                
                if groups_to_add:
                    subprocess.run(["pkexec", "usermod", "-a", "-G", ",".join(groups_to_add), username], check=True)
                
                if groups_to_remove:
                    for group in groups_to_remove:
                        subprocess.run(["pkexec", "gpasswd", "-d", username, group], check=True)
            except subprocess.CalledProcessError as e:
                self.show_error(f"Failed to update user: {e}")
                return
        
        self.parent.refresh_users()
        self.close()
    
    def show_error(self, message):
        dialog = Adw.MessageDialog.new(
            self,
            "Error",
            message
        )
        dialog.add_response("ok", "OK")
        dialog.present()

class GroupDialog(Adw.Window):
    def __init__(self, parent, group=None):
        super().__init__(transient_for=parent)
        self.parent = parent
        self.group = group
        self.set_modal(True)
        self.set_title("Add Group" if group is None else "Edit Group")
        self.set_default_size(400, -1)
        
        # Main layout
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Header bar
        header = Adw.HeaderBar()
        self.main_box.append(header)
        
        # Content
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content.set_margin_top(10)
        content.set_margin_bottom(10)
        content.set_margin_start(10)
        content.set_margin_end(10)
        
        # Group name
        groupname_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        groupname_label = Gtk.Label(label="Group Name")
        groupname_label.set_halign(Gtk.Align.START)
        self.groupname_entry = Gtk.Entry()
        if group:
            self.groupname_entry.set_text(group.gr_name)
            self.groupname_entry.set_sensitive(False)
        groupname_box.append(groupname_label)
        groupname_box.append(self.groupname_entry)
        content.append(groupname_box)
        
        # Members
        members_label = Gtk.Label(label="Members")
        members_label.set_halign(Gtk.Align.START)
        content.append(members_label)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_min_content_height(200)
        scrolled.set_max_content_height(200)
        
        self.members_list = Gtk.ListBox()
        self.members_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.members_list.add_css_class("boxed-list")
        
        # Add users with checkboxes
        group_members = []
        if group:
            group_members = group.gr_mem
        
        for user in pwd.getpwall():
            # Skip system users
            if user.pw_uid < 1000 and user.pw_uid != 0:
                continue
            
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            box.set_margin_top(5)
            box.set_margin_bottom(5)
            box.set_margin_start(10)
            box.set_margin_end(10)
            
            check = Gtk.CheckButton(label=user.pw_name)
            check.set_active(user.pw_name in group_members)
            box.append(check)
            
            if user.pw_gecos:
                desc = Gtk.Label()
                desc.set_markup(f"<small>{user.pw_gecos}</small>")
                desc.set_halign(Gtk.Align.START)
                box.append(desc)
            
            row.set_child(box)
            row.check = check  # Store reference to checkbox
            self.members_list.append(row)
        
        scrolled.set_child(self.members_list)
        content.append(scrolled)
        
        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.END)
        
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda x: self.close())
        button_box.append(cancel_button)
        
        save_button = Gtk.Button(label="Save")
        save_button.add_css_class("suggested-action")
        save_button.connect("clicked", self.on_save)
        button_box.append(save_button)
        
        content.append(button_box)
        
        self.main_box.append(content)
        self.set_content(self.main_box)
    
    def get_selected_members(self):
        members = []
        for row in self.members_list:
            if row.check.get_active():
                members.append(row.check.get_label())
        return members
    
    def on_save(self, button):
        groupname = self.groupname_entry.get_text().strip()
        members = self.get_selected_members()
        
        if not groupname:
            self.show_error("Group name is required")
            return
        
        try:
            if not self.group:  # Adding new group
                subprocess.run(["pkexec", "groupadd", groupname], check=True)
            
            # Update members
            if self.group:
                current_members = self.group.gr_mem
            else:
                current_members = []
            
            members_to_add = [m for m in members if m not in current_members]
            members_to_remove = [m for m in current_members if m not in members]
            
            for member in members_to_add:
                subprocess.run(["pkexec", "gpasswd", "-a", member, groupname], check=True)
            
            for member in members_to_remove:
                subprocess.run(["pkexec", "gpasswd", "-d", member, groupname], check=True)
            
        except subprocess.CalledProcessError as e:
            self.show_error(f"Failed to {'create' if not self.group else 'update'} group: {e}")
            return
        
        self.parent.refresh_groups()
        self.close()
    
    def show_error(self, message):
        dialog = Adw.MessageDialog.new(
            self,
            "Error",
            message
        )
        dialog.add_response("ok", "OK")
        dialog.present()

class UsersPage(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        
        # Create stack for different pages
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        
        # Create and add main users page
        self.main_users_page = self.create_main_users_page()
        self.stack.add_named(self.main_users_page, "main")
        
        # Create and add user management page
        self.user_management = self.create_user_management_page()
        self.stack.add_named(self.user_management, "user_management")
        
        self.append(self.stack)

        # Connect to the stack's notify::visible-child signal
        self.connect("map", self.on_page_mapped)

    def on_page_mapped(self, widget):
        # When the page becomes visible, always show the main view
        self.stack.set_visible_child_name("main")

    def create_user_management_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Header with title
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header.add_css_class("toolbar")
        header.set_margin_top(10)
        header.set_margin_bottom(10)
        header.set_margin_start(10)
        header.set_margin_end(10)
        
        title = Gtk.Label()
        title.set_markup("<span size='large'>User Management</span>")
        title.set_halign(Gtk.Align.CENTER)
        header.append(title)
        
        page.append(header)
        
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        page.append(separator)
        
        # Create notebook for Users and Groups tabs
        notebook = self.create_notebook_page()
        notebook.set_vexpand(True)
        
        # Users tab
        users_page = self.create_users_tab()
        notebook.append_page(users_page, Gtk.Label(label="Users"))
        
        # Groups tab
        groups_page = self.create_groups_tab()
        notebook.append_page(groups_page, Gtk.Label(label="Groups"))
        
        page.append(notebook)
        return page

    def create_notebook_page(self):
        notebook = Gtk.Notebook()
        notebook.connect("switch-page", self.on_notebook_switch)
        return notebook

    def create_users_tab(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        page.set_margin_top(10)
        page.set_margin_bottom(10)
        page.set_margin_start(10)
        page.set_margin_end(10)
        
        # Toolbar
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        add_button = Gtk.Button()
        add_button.set_icon_name("list-add-symbolic")
        add_button.add_css_class("suggested-action")
        add_button.connect("clicked", self.on_add_user)
        toolbar.append(add_button)
        
        edit_button = Gtk.Button()
        edit_button.set_icon_name("document-edit-symbolic")
        edit_button.connect("clicked", self.on_edit_user)
        toolbar.append(edit_button)
        
        delete_button = Gtk.Button()
        delete_button.set_icon_name("user-trash-symbolic")
        delete_button.add_css_class("destructive-action")
        delete_button.connect("clicked", self.on_delete_user)
        toolbar.append(delete_button)
        
        page.append(toolbar)
        
        # Users list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        
        self.users_list = Gtk.ListBox()
        self.users_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.users_list.add_css_class("boxed-list")
        
        scrolled.set_child(self.users_list)
        page.append(scrolled)
        
        return page

    def create_groups_tab(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        page.set_margin_top(10)
        page.set_margin_bottom(10)
        page.set_margin_start(10)
        page.set_margin_end(10)
        
        # Toolbar
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        add_button = Gtk.Button()
        add_button.set_icon_name("list-add-symbolic")
        add_button.add_css_class("suggested-action")
        add_button.connect("clicked", self.on_add_group)
        toolbar.append(add_button)
        
        edit_button = Gtk.Button()
        edit_button.set_icon_name("document-edit-symbolic")
        edit_button.connect("clicked", self.on_edit_group)
        toolbar.append(edit_button)
        
        delete_button = Gtk.Button()
        delete_button.set_icon_name("user-trash-symbolic")
        delete_button.add_css_class("destructive-action")
        delete_button.connect("clicked", self.on_delete_group)
        toolbar.append(delete_button)
        
        page.append(toolbar)
        
        # Groups list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        
        self.groups_list = Gtk.ListBox()
        self.groups_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.groups_list.add_css_class("boxed-list")
        
        scrolled.set_child(self.groups_list)
        page.append(scrolled)
        
        return page

    def on_back_clicked(self, button):
        self.stack.set_visible_child_name("main")

    def on_option_clicked(self, button, title):
        if title == "Users management":
            self.refresh_users()
            self.refresh_groups()
            self.stack.set_visible_child_name("user_management")
        elif title == "Install guest account":
            self._install_guest_account()

    def on_notebook_switch(self, notebook, page, page_num):
        # When switching away from the user management page (page 1),
        # reset to the main view
        if page_num == 0 and self.stack.get_visible_child_name() == "user_management":
            self.stack.set_visible_child_name("main")

    def refresh_users(self):
        # Clear existing items
        while True:
            row = self.users_list.get_first_child()
            if row is None:
                break
            self.users_list.remove(row)
        
        # Add users
        for user in pwd.getpwall():
            # Skip system users
            if user.pw_uid < 1000 and user.pw_uid != 0:
                continue
            
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            box.set_margin_top(10)
            box.set_margin_bottom(10)
            box.set_margin_start(10)
            box.set_margin_end(10)
            
            # User icon
            icon = Gtk.Image.new_from_icon_name("system-users-symbolic")
            box.append(icon)
            
            # User info
            info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            
            username = Gtk.Label(label=user.pw_name)
            username.set_halign(Gtk.Align.START)
            username.add_css_class("heading")
            info_box.append(username)
            
            details = []
            if user.pw_gecos:
                details.append(user.pw_gecos)
            
            # Get user groups
            groups = [g.gr_name for g in grp.getgrall() if user.pw_name in g.gr_mem]
            if groups:
                details.append(f"Groups: {', '.join(groups)}")
            
            if details:
                details_label = Gtk.Label()
                details_label.set_markup(f"<small>{', '.join(details)}</small>")
                details_label.set_halign(Gtk.Align.START)
                details_label.set_ellipsize(Pango.EllipsizeMode.END)
                info_box.append(details_label)
            
            box.append(info_box)
            
            row.set_child(box)
            self.users_list.append(row)

    def refresh_groups(self):
        # Clear existing items
        while True:
            row = self.groups_list.get_first_child()
            if row is None:
                break
            self.groups_list.remove(row)
        
        # Add groups
        for group in grp.getgrall():
            # Skip system groups
            if group.gr_gid < 1000 and group.gr_gid not in [0, 10, 20, 27, 33]:  # Include some important system groups
                continue
            
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            box.set_margin_top(10)
            box.set_margin_bottom(10)
            box.set_margin_start(10)
            box.set_margin_end(10)
            
            # Group icon
            icon = Gtk.Image.new_from_icon_name("system-users-symbolic")
            box.append(icon)
            
            # Group info
            info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            
            groupname = Gtk.Label(label=group.gr_name)
            groupname.set_halign(Gtk.Align.START)
            groupname.add_css_class("heading")
            info_box.append(groupname)
            
            if group.gr_mem:
                members_label = Gtk.Label()
                members_label.set_markup(f"<small>Members: {', '.join(group.gr_mem)}</small>")
                members_label.set_halign(Gtk.Align.START)
                members_label.set_ellipsize(Pango.EllipsizeMode.END)
                info_box.append(members_label)
            
            box.append(info_box)
            
            row.set_child(box)
            self.groups_list.append(row)

    def on_add_user(self, button):
        dialog = UserDialog(self.get_root())
        dialog.present()

    def on_edit_user(self, button):
        row = self.users_list.get_selected_row()
        if row is None:
            return
        
        username = row.get_child().get_first_child().get_next_sibling().get_first_child().get_label()
        try:
            user = pwd.getpwnam(username)
            dialog = UserDialog(self.get_root(), user)
            dialog.present()
        except KeyError:
            pass

    def on_delete_user(self, button):
        row = self.users_list.get_selected_row()
        if row is None:
            return
        
        username = row.get_child().get_first_child().get_next_sibling().get_first_child().get_label()
        
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Delete User",
            f"Are you sure you want to delete user '{username}'?\nThis action cannot be undone."
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("delete", "Delete")
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self.on_delete_user_response, username)
        dialog.present()

    def on_delete_user_response(self, dialog, response, username):
        if response == "delete":
            try:
                subprocess.run(["pkexec", "userdel", "-r", username], check=True)
                self.refresh_users()
            except subprocess.CalledProcessError as e:
                error_dialog = Adw.MessageDialog.new(
                    self.get_root(),
                    "Error",
                    f"Failed to delete user: {e}"
                )
                error_dialog.add_response("ok", "OK")
                error_dialog.present()

    def on_add_group(self, button):
        dialog = GroupDialog(self.get_root())
        dialog.present()

    def on_edit_group(self, button):
        row = self.groups_list.get_selected_row()
        if row is None:
            return
        
        groupname = row.get_child().get_first_child().get_next_sibling().get_first_child().get_label()
        try:
            group = grp.getgrnam(groupname)
            dialog = GroupDialog(self.get_root(), group)
            dialog.present()
        except KeyError:
            pass

    def on_delete_group(self, button):
        row = self.groups_list.get_selected_row()
        if row is None:
            return
        
        groupname = row.get_child().get_first_child().get_next_sibling().get_first_child().get_label()
        
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Delete Group",
            f"Are you sure you want to delete group '{groupname}'?\nThis action cannot be undone."
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("delete", "Delete")
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self.on_delete_group_response, groupname)
        dialog.present()

    def on_delete_group_response(self, dialog, response, groupname):
        if response == "delete":
            try:
                subprocess.run(["pkexec", "groupdel", groupname], check=True)
                self.refresh_groups()
            except subprocess.CalledProcessError as e:
                error_dialog = Adw.MessageDialog.new(
                    self.get_root(),
                    "Error",
                    f"Failed to delete group: {e}"
                )
                error_dialog.add_response("ok", "OK")
                error_dialog.present()

    def create_main_users_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Create title
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        title_box.set_margin_top(20)
        title_box.set_margin_bottom(20)
        title_box.set_margin_start(20)
        title_box.set_margin_end(20)
        
        title_label = Gtk.Label()
        title_label.set_markup("<span size='large'>Users</span>")
        title_label.set_justify(Gtk.Justification.CENTER)
        title_box.append(title_label)
        
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        
        page.append(title_box)
        page.append(separator)
        
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
            ("Users management", "system-users-symbolic", "Manage system users and groups"),
            ("Install guest account", "avatar-default-symbolic", "Install and configure guest account support")
        ]
        
        for i, (title, icon_name, description) in enumerate(options):
            button = self.create_option_button(title, icon_name, description)
            grid.attach(button, i % 2, i // 2, 1, 1)
        
        page.append(grid)
        return page

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

    def _install_guest_account(self):
        dialog = Adw.MessageDialog.new(
            self.get_root(),
            "Install Guest Account",
            "This will install the guest account support. Do you want to continue?"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("install", "Install")
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", self._on_guest_response)
        dialog.present()

    def _on_guest_response(self, dialog, response):
        if response == "install":
            # Create progress dialog
            progress_dialog = Adw.MessageDialog.new(
                self.get_root(),
                "Installing Guest Account",
                "Please wait while guest account support is being installed..."
            )
            progress_dialog.present()
            
            def on_installation_complete(process):
                progress_dialog.close()
                
                if process.returncode == 0:
                    success_dialog = Adw.MessageDialog.new(
                        self.get_root(),
                        "Installation Successful",
                        "Guest account support has been installed successfully!"
                    )
                    success_dialog.add_response("ok", "OK")
                    success_dialog.present()
                else:
                    error_dialog = Adw.MessageDialog.new(
                        self.get_root(),
                        "Installation Failed",
                        "Failed to install guest account support. Please check the system logs for more information."
                    )
                    error_dialog.add_response("ok", "OK")
                    error_dialog.present()
            
            # Run the installation with pkexec
            try:
                process = subprocess.Popen(
                    ["pkexec", "dnf", "install", "-y", "xguest"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Use GLib.idle_add to check process status
                def check_process():
                    if process.poll() is None:
                        return True
                    
                    on_installation_complete(process)
                    return False
                
                GLib.idle_add(check_process)
                
            except Exception as e:
                progress_dialog.close()
                error_dialog = Adw.MessageDialog.new(
                    self.get_root(),
                    "Installation Failed",
                    f"Failed to start installation: {str(e)}"
                )
                error_dialog.add_response("ok", "OK")
                error_dialog.present()

    def show_main(self):
        self.stack.set_visible_child_name("main")
