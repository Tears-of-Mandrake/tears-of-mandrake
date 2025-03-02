import os
import platform
import subprocess
import re

def get_system_info():
    info = {}
    
    # Get OS information
    info['system_name'] = platform.system()
    info['distribution'] = get_distribution_info()
    info['architecture'] = platform.machine()
    info['kernel'] = platform.release()
    
    # Get desktop environment
    info['desktop_environment'] = get_desktop_environment()
    
    # Get hostname
    info['hostname'] = platform.node()
    
    # Get graphics driver information
    info['graphics_driver'] = get_graphics_driver_info()
    
    return info

def get_graphics_driver_info():
    # First try to get Mesa information using glxinfo
    try:
        glxinfo = subprocess.run(['glxinfo'], capture_output=True, text=True)
        if glxinfo.returncode == 0:
            output = glxinfo.stdout
            
            # Look for Mesa version
            mesa_match = re.search(r'OpenGL version string: .*Mesa (\d+\.\d+\.\d+)', output)
            if mesa_match:
                return f"Mesa {mesa_match.group(1)}"
            
            # If no Mesa version found, try to get OpenGL vendor and version
            vendor_match = re.search(r'OpenGL vendor string: (.*)', output)
            version_match = re.search(r'OpenGL version string: (.*)', output)
            
            if vendor_match and version_match:
                vendor = vendor_match.group(1).strip()
                version = version_match.group(1).strip()
                if 'nvidia' in vendor.lower():
                    return f"NVIDIA {version}"
                return f"{vendor} - {version}"
    except FileNotFoundError:
        pass
    
    # If glxinfo fails, try nvidia-smi
    try:
        nvidia_info = subprocess.run(['nvidia-smi', '--query-gpu=driver_version', '--format=csv,noheader'],
                                   capture_output=True, text=True)
        if nvidia_info.returncode == 0:
            return f"NVIDIA {nvidia_info.stdout.strip()}"
    except FileNotFoundError:
        pass
    
    # If both methods fail, try lspci as a last resort
    try:
        lspci = subprocess.run(['lspci', '-k'], capture_output=True, text=True)
        if lspci.returncode == 0:
            output = lspci.stdout
            # Look for graphics related entries
            for line in output.split('\n'):
                if 'VGA' in line or '3D controller' in line:
                    # Get the next few lines to find the kernel module
                    lines = output.split('\n')
                    start_idx = lines.index(line)
                    for i in range(start_idx, min(start_idx + 4, len(lines))):
                        if 'Kernel modules:' in lines[i]:
                            modules = lines[i].split(':')[1].strip()
                            # Prefer nvidia or amdgpu over other modules
                            mods = modules.split()
                            for preferred in ['nvidia', 'amdgpu', 'radeon', 'nouveau']:
                                if preferred in mods:
                                    return f"Driver: {preferred}"
                            return f"Driver: {mods[0]}"
    except:
        pass
    
    return "Unknown"

def get_distribution_info():
    try:
        with open('/etc/os-release', 'r') as f:
            lines = f.readlines()
            info = {}
            for line in lines:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    info[key] = value.strip('"')
            
            if 'PRETTY_NAME' in info:
                return info['PRETTY_NAME']
            elif 'NAME' in info and 'VERSION' in info:
                return f"{info['NAME']} {info['VERSION']}"
            elif 'NAME' in info:
                return info['NAME']
    except:
        pass
    return platform.version()

def get_desktop_environment():
    """Get the current desktop environment."""
    # First check the XDG_CURRENT_DESKTOP environment variable
    current_desktop = os.environ.get('XDG_CURRENT_DESKTOP')
    if current_desktop:
        return current_desktop.upper()
    
    # If XDG_CURRENT_DESKTOP is not set, try to detect running processes
    for de in ['gnome', 'kde', 'xfce', 'mate', 'lxde', 'cinnamon']:
        try:
            output = subprocess.check_output(f'pgrep -l {de}', shell=True)
            if output:
                return de.upper()
        except:
            continue
    
    return "Unknown"
