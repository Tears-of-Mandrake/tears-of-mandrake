# Tears of Mandrake

A modern GTK4/Libadwaita application for OpenMandriva system management and software installation.

## Features

- Software Management
  - Install and remove applications using Yumex
  - Install popular applications from curated categories
  - Install external applications
  - Configure media sources (repositories)
  - Install multimedia codecs
  - Install system drivers

- System Updates
  - Update system packages
  - Configure update frequency
  - Optional integration with System Updater

## Requirements

- Python 3.10 or higher
- GTK 4.0
- Libadwaita 1.0
- DNF package manager
- PolicyKit for system operations

### Optional Dependencies

- yumex-dnf: For package management
- system-updater: For enhanced update management

## Installation

### From Source

1. Install required dependencies:
```bash
dnf install python3-gobject gtk4 libadwaita python3-pip polkit
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python3 main.py
```

### From RPM Package

```bash
dnf install tears-of-mandrake
```

## Development

### Building from Source

1. Clone the repository:
```bash
git clone https://github.com/OpenMandrivaSoftware/tears-of-mandrake.git
cd tears-of-mandrake
```

2. Install build dependencies:
```bash
dnf install python3-devel gtk4-devel libadwaita-devel
```

3. Build RPM package:
```bash
rpmbuild -ba tears-of-mandrake.spec
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the GPLv3 License - see the LICENSE file for details.

## Acknowledgments

- Tears of Mandrake team for support and guidance
- GTK and Libadwaita developers for the excellent toolkit
- All contributors and testers
