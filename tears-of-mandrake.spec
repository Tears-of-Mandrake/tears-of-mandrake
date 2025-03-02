Name:           tears-of-mandrake
Version:        0.1.1
Release:        1
Summary:        Modern system management tool for OpenMandriva
Group:          System/Configuration/
License:        GPLv3
URL:            https://github.com/Tears-of-Mandrake/tears-of-mandrake
Source0:        https://github.com/Tears-of-Mandrake/tears-of-mandrake/archive/%{version}/%{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  pkgconfig(python)
BuildRequires:  pkgconfig(gtk4)
BuildRequires:  pkgconfig(libadwaita-1)
BuildRequires:  imagemagick

Requires:       python3 >= 3.10
Requires:       python-gobject3
Requires:       python-gi
Requires:       python-psutil
Requires:       gtk4
Requires:       libadwaita-common
Requires:       %{_lib}adwaita1_0
Requires:       %{_lib}adwaita-gir1
Requires:       python-pip
Requires:       polkit
Requires:       dnf
Requires:       yumex
# To do
Suggests:       system-updater

%description
Tears of Mandrake is a modern GTK4/Libadwaita application for OpenMandriva system
management and software installation. It provides an easy-to-use interface for
installing software, managing updates, configuring repositories, and more.

%prep
%autosetup

%build
# Nothing to build - pure Python

%install
# Create directories
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_datadir}/%{name}
mkdir -p %{buildroot}%{_datadir}/applications
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/scalable/apps
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/256x256/apps
mkdir -p %{buildroot}%{python3_sitelib}/%{name}

# Install Python modules
cp -a *.py %{buildroot}%{_datadir}/%{name}/
cp -a images %{buildroot}%{_datadir}/%{name}/

# Create the main executable
cat > %{buildroot}%{_bindir}/%{name} << 'EOF'
#!/usr/bin/env python3
import sys
import os

# Add the package directory to the Python path
package_dir = '%{_datadir}/%{name}'
if package_dir not in sys.path:
    sys.path.insert(0, package_dir)

from main import main

if __name__ == '__main__':
    sys.exit(main())
EOF

chmod 755 %{buildroot}%{_bindir}/%{name}

# Install desktop file
cat > %{buildroot}%{_datadir}/applications/%{name}.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Tears of Mandrake
GenericName=System Management Tool
Comment=Manage software, updates, and system settings
Keywords=system;software;update;install;package;repository;codec;driver;
Exec=%{name}
Icon=%{name}
Terminal=false
Categories=Settings;System;
StartupNotify=true
StartupWMClass=%{name}
EOF

# Install icons
install -p -m 644 %{name}.png %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/%{name}.png
for size in 16 22 24 32 48 64 128 256; do
    mkdir -p %{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps
    convert %{name}.png -resize ${size}x${size} \
        %{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps/%{name}.png
done

%files
%license license
%doc README.md
%{_bindir}/%{name}
%{_datadir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/*/apps/%{name}.png

%post
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
/usr/bin/update-desktop-database &>/dev/null || :

%postun
if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :
fi
/usr/bin/update-desktop-database &>/dev/null || :

%posttrans
/usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :
