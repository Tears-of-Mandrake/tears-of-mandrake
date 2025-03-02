import gi
import subprocess
import threading
import requests
from datetime import datetime
from urllib.parse import urljoin
import re
import base64

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Pango, Gdk

class NewsPage(Gtk.Box):
    def __init__(self, parent):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.parent = parent
        
        # Add page title and description
        title_group = Adw.PreferencesGroup()
        title_label = Gtk.Label()
        title_label.set_markup("<span size='x-large' weight='bold'>Tears of Mandrake News</span>")
        title_label.set_margin_bottom(10)
        title_group.add(title_label)
        
        description_label = Gtk.Label(
            label="Stay up to date with the latest news from OpenMandriva and the Tears of Mandrake project. "
                  "Get information about new features, updates, and community announcements."
        )
        description_label.set_wrap(True)
        description_label.set_margin_bottom(10)
        title_group.add(description_label)
        self.append(title_group)

        # Create scrolled window for news entries
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        
        # Main box for news entries
        self.news_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.news_box.set_margin_start(10)
        self.news_box.set_margin_end(10)
        self.news_box.set_margin_top(10)
        self.news_box.set_margin_bottom(10)
        
        scrolled.set_child(self.news_box)
        self.append(scrolled)
        
        # Loading indicator
        self.loading_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.loading_box.set_valign(Gtk.Align.CENTER)
        self.loading_box.set_halign(Gtk.Align.CENTER)
        
        spinner = Gtk.Spinner()
        spinner.set_size_request(32, 32)
        spinner.start()
        self.loading_box.append(spinner)
        
        loading_label = Gtk.Label(label="Loading news...")
        self.loading_box.append(loading_label)
        
        self.news_box.append(self.loading_box)
        
        # Start loading news
        self.load_news()

    def load_news(self):
        def fetch_news():
            try:
                # Try to fetch README.md directly from raw GitHub content
                url = 'https://raw.githubusercontent.com/Tears-of-Mandrake/web/main/README.md'
                headers = {
                    'User-Agent': 'Mozilla/5.0',
                    'Accept': 'text/plain',
                    'Cache-Control': 'no-cache'
                }
                print(f"Attempting to fetch from: {url}")
                response = requests.get(url, headers=headers, timeout=10)
                print(f"Response status: {response.status_code}")
                print(f"Response headers: {response.headers}")
                
                response.raise_for_status()
                content = response.text
                print(f"Content received: {content[:200]}...")  # Print first 200 chars for debugging
                
                if not content.strip():
                    raise ValueError("Empty content received")

                # Parse news entries
                entries = []
                current_entry = None
                
                # First, split content into sections by date headers
                sections = re.split(r'(?m)^###\s+\d{4}\.\d{2}\.\d{2}\s*$', content)
                headers = re.findall(r'(?m)^###\s+(\d{4}\.\d{2}\.\d{2})\s*$', content)
                
                # Process each section with its header
                for i, (header, section) in enumerate(zip(headers, sections[1:])):
                    try:
                        date = datetime.strptime(header, '%Y.%m.%d')
                        content_lines = [line.strip() for line in section.split('\n') if line.strip()]
                        
                        if content_lines:  # Only add if there's actual content
                            entries.append({
                                'date': date,
                                'content': content_lines
                            })
                    except ValueError as e:
                        print(f"Error parsing date {header}: {e}")
                        continue
                
                # Sort entries by date (newest first)
                entries.sort(key=lambda x: x['date'], reverse=True)
                
                # If no entries were found, use sample content
                if not entries:
                    raise ValueError("No news entries found in the GitHub repository")

            except Exception as e:
                print(f"Failed to fetch news from GitHub: {str(e)}")
                # Fall back to sample content
                entries = [
                    {
                        'date': datetime.strptime('2025.01.05', '%Y.%m.%d'),
                        'content': [
                            '### Welcome to Tears of Mandrake!',
                            'We are excited to announce the first release of Tears of Mandrake, a powerful system management tool for OpenMandriva.',
                            '',
                            '### Key Features:',
                            '• Advanced Kernel Management with support for multiple kernels',
                            '• Easy shell switching and configuration',
                            '• GNOME Tweaks integration',
                            '• Modern, user-friendly interface built with GTK4 and libadwaita',
                            '',
                            '### Coming Soon:',
                            '• System backup and restore',
                            '• Advanced hardware monitoring',
                            '• Performance optimization tools'
                        ]
                    },
                    {
                        'date': datetime.strptime('2025.01.04', '%Y.%m.%d'),
                        'content': [
                            '### Development Update',
                            'The development team has been working hard on improving the kernel management features:',
                            '',
                            '• Added support for Clang and GCC compiled kernels',
                            '• Implemented kernel installation progress tracking',
                            '• Added safety features to prevent removal of the running kernel',
                            '',
                            '### Community',
                            'Join our growing community! We welcome contributors of all skill levels.',
                            'Visit our GitHub repository to get involved.'
                        ]
                    },
                    {
                        'date': datetime.strptime('2025.01.03', '%Y.%m.%d'),
                        'content': [
                            '### Project Announcement',
                            'Today marks the beginning of the Tears of Mandrake project, a new initiative to create a comprehensive system management tool for OpenMandriva.',
                            '',
                            '### Goals:',
                            '• Simplify system administration tasks',
                            '• Provide a modern, user-friendly interface',
                            '• Integrate deeply with OpenMandriva',
                            '• Build a strong community around the project'
                        ]
                    }
                ]

            def update_ui():
                # Remove loading indicator
                if self.loading_box.get_parent():
                    self.loading_box.get_parent().remove(self.loading_box)
                
                # Add news entries
                for entry in entries:
                    # Create entry card
                    card = Adw.PreferencesGroup()
                    
                    # Date header
                    date_label = Gtk.Label()
                    date_str = entry['date'].strftime('%B %d, %Y')
                    date_label.set_markup(f"<span size='large' weight='bold'>{date_str}</span>")
                    date_label.set_halign(Gtk.Align.START)
                    date_label.set_margin_bottom(10)
                    card.add(date_label)
                    
                    # Content
                    content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
                    for line in entry['content']:
                        if line.startswith('###'):
                            # Subheader
                            subtitle = line.replace('###', '').strip()
                            subtitle_label = Gtk.Label()
                            subtitle_label.set_markup(f"<span weight='bold'>{subtitle}</span>")
                            subtitle_label.set_halign(Gtk.Align.START)
                            subtitle_label.set_margin_top(5)
                            content_box.append(subtitle_label)
                        elif line.startswith('•'):
                            # Bullet point
                            bullet_label = Gtk.Label()
                            bullet_label.set_markup(f"<span font_family='monospace'>  •</span> {line[1:].strip()}")
                            bullet_label.set_halign(Gtk.Align.START)
                            bullet_label.set_wrap(True)
                            bullet_label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
                            content_box.append(bullet_label)
                        elif line.strip():
                            # Regular content
                            content_label = Gtk.Label(label=line)
                            content_label.set_wrap(True)
                            content_label.set_halign(Gtk.Align.START)
                            content_label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
                            content_box.append(content_label)
                    
                    card.add(content_box)
                    self.news_box.append(card)
            
            GLib.idle_add(update_ui)
        
        # Start loading in a thread
        thread = threading.Thread(target=fetch_news)
        thread.daemon = True
        thread.start()
