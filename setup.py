#!/usr/bin/env python3

from setuptools import setup, find_packages
import os
import glob

def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()

# Read requirements from requirements.txt
def read_requirements(filename):
    with open(filename) as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Create executable script content
SCRIPT_CONTENT = '''#!/usr/bin/env python3
import sys
import os

# Add the package directory to the Python path
package_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'share', 'tears-of-mandrake'))
if package_dir not in sys.path:
    sys.path.insert(0, package_dir)

from tears_of_mandrake.main import main

if __name__ == '__main__':
    sys.exit(main())
'''

# Create the executable script
os.makedirs('bin', exist_ok=True)
with open('bin/tears-of-mandrake', 'w') as f:
    f.write(SCRIPT_CONTENT)
os.chmod('bin/tears-of-mandrake', 0o755)

# Collect all image files
def collect_images():
    images = []
    for ext in ['*.png', '*.svg']:
        images.extend(glob.glob(os.path.join('images', ext)))
    return images

setup(
    name="tears-of-mandrake",
    version="0.1.0",
    author="OpenMandriva Team",
    author_email="team@openmandriva.org",
    description="Modern system management tool for OpenMandriva",
    long_description=read('README.md'),
    long_description_content_type="text/markdown",
    license="GPLv3",
    keywords="openmandriva system management gtk4 libadwaita",
    url="https://github.com/OpenMandrivaSoftware/tears-of-mandrake",
    packages=find_packages(),
    install_requires=read_requirements('requirements.txt'),
    scripts=['bin/tears-of-mandrake'],
    data_files=[
        ('share/applications', ['tears-of-mandrake.desktop']),
        ('share/icons/hicolor/scalable/apps', ['data/icons/tears-of-mandrake.svg']),
        ('share/tears-of-mandrake/images', collect_images()),
        ('share/tears-of-mandrake', ['main.py']),
    ],
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Topic :: System :: Systems Administration",
    ],
    python_requires='>=3.10',
)
