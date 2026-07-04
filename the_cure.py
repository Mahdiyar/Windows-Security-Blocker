import subprocess
import ctypes
import sys
import winreg
import os
import logging
import time

# Setup logging
logging.basicConfig(filename='defender_restore.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def run_as_admin():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)

def clear():
    os.system('cls')

def print_progress(percent, message):
    bar_length = 30
    filled = int(bar_length * percent // 100)
    bar = '█' * filled + '-' * (bar_length - filled)
    print(f"\r{message:45} [{bar}] {percent}%", end='', flush=True)

def delete_registry_key(path, name):
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY)
        winreg.DeleteValue(key, name)
        winreg.CloseKey(key)
        logging.info(f"Deleted {name} from {path}")
        return True
    except FileNotFoundError:
        logging.info(f"Key already removed: {name}")
        return True
    except Exception as e:
        logging.error(f"Delete error {path}\\{name}: {e}")
        return False

def set_registry_key(path, name, value, value_type=winreg.REG_DWORD):
    try:
        key = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY)
        winreg.SetValueEx(key, name, 0, value_type, value)
        winreg.CloseKey(key)
        return True
    except:
        return False

def run_powershell_command(cmd):
    try:
        subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-Command', cmd],
                       capture_output=True, text=True, timeout=30)
        return True
    except:
        return False

def main():
    run_as_admin()
    clear()

    print("=== Windows Defender Restore Tool ===\n")
    print("Restoring Windows Defender...\n")
    time.sleep(2)
    clear()

    current = 0

    # Stage 1: Registry Restore
    print_progress(current, "Restoring registry settings...")
    paths = [
        r"SOFTWARE\Policies\Microsoft\Windows Defender",
        r"SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection",
        r"SOFTWARE\Policies\Microsoft\Windows Defender\SpyNet",
    ]
    
    settings = ["DisableAntiSpyware", "DisableRealtimeMonitoring", "DisableOnAccessProtection",
                "DisableBehaviorMonitoring", "DisableIOAVProtection", "DisableScriptScanning",
                "DisableIntrusionPreventionSystem"]

    for base_path in paths:
        for setting in settings:
            delete_registry_key(base_path, setting)
            current += 3
            print_progress(current, "Restoring registry settings...")

    delete_registry_key(r"SOFTWARE\Policies\Microsoft\Windows Advanced Threat Protection", 
                       "ForceDefenderPassiveMode")
    current = 40
    print_progress(current, "Restoring registry settings...")

    # Stage 2: Services
    time.sleep(0.5)
    print_progress(45, "Restoring services...")
    services = ["WinDefend", "WdNisSvc", "SecurityHealthService", "wscsvc"]
    for i, svc in enumerate(services):
        subprocess.run(['sc', 'config', svc, 'start=', 'auto'], capture_output=True, check=False)
        subprocess.run(['sc', 'start', svc], capture_output=True, check=False)
        current = 45 + (i+1)*10
        print_progress(current, "Restoring services...")

    # Stage 3: PowerShell
    time.sleep(0.5)
    print_progress(80, "Resetting Defender preferences...")
    ps_cmds = [
        "Set-MpPreference -DisableRealtimeMonitoring $false",
        "Set-MpPreference -DisableBehaviorMonitoring $false",
        "Set-MpPreference -DisableIOAVProtection $false",
        "Set-MpPreference -DisableScriptScanning $false",
        "Set-MpPreference -DisableArchiveScanning $false",
        "Set-MpPreference -DisableIntrusionPreventionSystem $false",
        "Set-MpPreference -DisableBlockAtFirstSeen $false",
        "Set-MpPreference -MAPSReporting 1",
        "Set-MpPreference -SubmitSamplesConsent 1"
    ]
    
    for i, cmd in enumerate(ps_cmds):
        run_powershell_command(cmd)
        current = 80 + (i+1)*2
        print_progress(current, "Resetting Defender preferences...")

    # Stage 4: Remove scheduled task
    print_progress(98, "Removing persistence task...")
    try:
        subprocess.run(['schtasks', '/Delete', '/TN', 'DefenderDisablePersistence', '/F'], 
                      capture_output=True, check=False)
    except:
        pass
    current = 100
    print_progress(100, "Removing persistence task...")

    # Finish
    time.sleep(1.2)
    clear()

    print("=== Restore Completed Successfully ===\n")
    print("✅ Windows Defender has been restored.")
    print("Please restart your computer to fully apply changes.\n")
    time.sleep(4)

    # Final clear + close window
    clear()
    print("Closing window...")
    time.sleep(1)

    os.system('exit')
    try:
        ctypes.windll.user32.PostMessageW(
            ctypes.windll.kernel32.GetConsoleWindow(), 0x0010, 0, 0)
    except:
        pass
    
    sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Critical error: {e}")
        print(f"Error: {e}")
        time.sleep(5)
        sys.exit(1)