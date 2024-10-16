import platform
import subprocess
import winreg

DARK_MODE = "Dark"
LIGHT_MODE = "Light"

def is_windows_dark_mode():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize') as key:
            value = winreg.QueryValueEx(key, 'AppsUseLightTheme')[0]
            return value == 0  # 0 indicates dark mode
    except FileNotFoundError:
        return False  # Default to light mode if the registry key is not found

def is_macos_dark_mode():
    result = subprocess.run(['osascript', '-e', 'tell application "System Events" to tell appearance preferences to get dark mode'], 
                            capture_output=True, text=True)
    return result.stdout.strip() == 'true'

def is_linux_dark_mode():
    result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'gtk-theme'], 
                            capture_output=True, text=True)
    theme = result.stdout.strip()
    return 'dark' in theme.lower()

def get_system_appearance():
    system = platform.system()
    if system == "Windows":
        return DARK_MODE if is_windows_dark_mode() else LIGHT_MODE
    elif system == "Darwin":  # macOS
        return DARK_MODE if is_macos_dark_mode() else LIGHT_MODE
    elif system == "Linux":
        return DARK_MODE if is_linux_dark_mode() else LIGHT_MODE
    else:
        return DARK_MODE