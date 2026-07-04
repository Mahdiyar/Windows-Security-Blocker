import subprocess
import ctypes
import sys
import winreg
import os
import logging

# Setup logging
logging.basicConfig(filename='defender_disable.log', level=logging.INFO,
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

def set_registry_key(path, name, value, value_type=winreg.REG_DWORD):
    try:
        key = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY)
        winreg.SetValueEx(key, name, 0, value_type, value)
        winreg.CloseKey(key)
        logging.info(f"Set {name} = {value} at {path}")
        print(f"✓ Set {name} = {value}")
        return True
    except Exception as e:
        logging.error(f"Registry error {path}\\{name}: {e}")
        print(f"✗ Registry error: {e}")
        return False

def run_powershell_command(cmd):
    try:
        result = subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-Command', cmd],
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✓ {cmd}")
            logging.info(f"PS Success: {cmd}")
        else:
            print(f"⚠ {cmd} -> {result.stderr.strip()}")
        return result.returncode == 0
    except Exception as e:
        print(f"✗ PowerShell error: {e}")
        logging.error(f"PS Error: {cmd} -> {e}")
        return False

def main():
    run_as_admin()
    
    print("=== Windows Defender Aggressive Disable Tool ===\n")
    print("⚠️  IMPORTANT: Make sure Tamper Protection is turned OFF first!\n")
    
    # Wait a bit instead of input() to avoid stdin error
    print("Starting in 5 seconds...")
    import time
    time.sleep(5)

    # Registry settings (same as before)
    print("\nApplying registry settings...")
    paths = [
        r"SOFTWARE\Policies\Microsoft\Windows Defender",
        r"SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection",
        r"SOFTWARE\Policies\Microsoft\Windows Defender\SpyNet",
    ]
    
    for base_path in paths:
        set_registry_key(base_path, "DisableAntiSpyware", 1)
        set_registry_key(base_path, "DisableRealtimeMonitoring", 1)
        set_registry_key(base_path, "DisableOnAccessProtection", 1)
        set_registry_key(base_path, "DisableBehaviorMonitoring", 1)
        set_registry_key(base_path, "DisableIOAVProtection", 1)
        set_registry_key(base_path, "DisableScriptScanning", 1)
    
    set_registry_key(r"SOFTWARE\Policies\Microsoft\Windows Advanced Threat Protection", 
                    "ForceDefenderPassiveMode", 1)

    # Services
    print("\nStopping services...")
    services = ["WinDefend", "WdNisSvc", "SecurityHealthService", "wscsvc"]
    for svc in services:
        subprocess.run(['sc', 'stop', svc], capture_output=True, check=False)
        subprocess.run(['sc', 'config', svc, 'start=', 'disabled'], capture_output=True, check=False)
        print(f"✓ Processed service: {svc}")

    # PowerShell
    print("\nApplying PowerShell settings...")
    ps_cmds = [
        "Set-MpPreference -DisableRealtimeMonitoring $true",
        "Set-MpPreference -DisableBehaviorMonitoring $true",
        "Set-MpPreference -DisableIOAVProtection $true",
        "Set-MpPreference -DisableScriptScanning $true",
        "Set-MpPreference -DisableArchiveScanning $true",
        "Set-MpPreference -DisableIntrusionPreventionSystem $true",
        "Set-MpPreference -DisableBlockAtFirstSeen $true",
        "Set-MpPreference -MAPSReporting 0",
        "Set-MpPreference -SubmitSamplesConsent 0"
    ]
    
    for cmd in ps_cmds:
        run_powershell_command(cmd)

    os.system('cls')
    print("Closing window in 1 second...")
    time.sleep(1)
    
    os.system('exit')
    
    try:
        ctypes.windll.user32.PostMessageW(
            ctypes.windll.kernel32.GetConsoleWindow(), 
            0x0010, 0, 0
        )
    except:
        pass

    sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Critical error: {e}")
        print(f"Error: {e}")
        import time
        time.sleep(10)