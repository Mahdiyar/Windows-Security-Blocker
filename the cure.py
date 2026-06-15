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
        print("Requesting administrator privileges...")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)

def delete_registry_key(path, name):
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY)
        winreg.DeleteValue(key, name)
        winreg.CloseKey(key)
        print(f"✓ Deleted {name} from {path}")
        logging.info(f"Deleted {name} from {path}")
        return True
    except FileNotFoundError:
        print(f"✓ Key already removed: {name}")
        return True
    except Exception as e:
        print(f"✗ Could not delete {name}: {e}")
        logging.error(f"Delete error {path}\\{name}: {e}")
        return False

def set_registry_key(path, name, value, value_type=winreg.REG_DWORD):
    try:
        key = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY)
        winreg.SetValueEx(key, name, 0, value_type, value)
        winreg.CloseKey(key)
        print(f"✓ Restored {name} = {value}")
        return True
    except Exception as e:
        print(f"✗ Registry error: {e}")
        return False

def run_powershell_command(cmd):
    try:
        result = subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-Command', cmd],
                              capture_output=True, text=True, timeout=30)
        print(f"✓ {cmd}")
        return True
    except Exception as e:
        print(f"✗ PowerShell error: {e}")
        return False

def main():
    run_as_admin()
    
    print("=== Windows Defender Restore Tool ===\n")

    # Remove disable policies
    print("Restoring registry settings...")
    paths = [
        r"SOFTWARE\Policies\Microsoft\Windows Defender",
        r"SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection",
        r"SOFTWARE\Policies\Microsoft\Windows Defender\SpyNet",
    ]
    
    for base_path in paths:
        delete_registry_key(base_path, "DisableAntiSpyware")
        delete_registry_key(base_path, "DisableRealtimeMonitoring")
        delete_registry_key(base_path, "DisableOnAccessProtection")
        delete_registry_key(base_path, "DisableBehaviorMonitoring")
        delete_registry_key(base_path, "DisableIOAVProtection")
        delete_registry_key(base_path, "DisableScriptScanning")
        delete_registry_key(base_path, "DisableIntrusionPreventionSystem")

    # Remove Passive Mode force
    delete_registry_key(r"SOFTWARE\Policies\Microsoft\Windows Advanced Threat Protection", "ForceDefenderPassiveMode")

    # Restore services
    print("\nRestoring services...")
    services = ["WinDefend", "WdNisSvc", "SecurityHealthService", "wscsvc"]
    for svc in services:
        subprocess.run(['sc', 'config', svc, 'start=', 'auto'], capture_output=True, check=False)
        subprocess.run(['sc', 'start', svc], capture_output=True, check=False)
        print(f"✓ Restored service: {svc}")

    # Reset PowerShell preferences
    print("\nResetting Defender preferences...")
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
    
    for cmd in ps_cmds:
        run_powershell_command(cmd)

    # Remove persistence task
    print("\nRemoving scheduled task...")
    try:
        subprocess.run(['schtasks', '/Delete', '/TN', 'DefenderDisablePersistence', '/F'], 
                      capture_output=True, check=False)
        print("✓ Removed persistence task")
    except:
        pass

    print("\n=== Restore Completed ===")
    print("Restart your computer to fully restore Windows Defender.")
    print("After restart, open Windows Security and check the status.")

    time.sleep(8)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Critical error: {e}")
        time.sleep(10)