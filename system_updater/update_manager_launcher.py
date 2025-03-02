#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from system_updater.update_manager import main

if __name__ == "__main__":
    # Initialize Adwaita
    Adw.init()
    # Run the application
    sys.exit(main())
