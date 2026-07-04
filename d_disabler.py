import subprocess
import ctypes
import sys
import winreg
import os
import logging
import time

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
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)

def clear():
    os.system('cls')

def print_progress(percent, message):
    bar_length = 30
    filled = int(bar_length * percent // 100)
    bar = '█' * filled + '-' * (bar_length - filled)
    print(f"\r{message:40} [{bar}] {percent}%", end='', flush=True)

def set_registry_key(path, name, value, value_type=winreg.REG_DWORD):
    try:
        key = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY)
        winreg.SetValueEx(key, name, 0, value_type, value)
        winreg.CloseKey(key)
        logging.info(f"Set {name} = {value} at {path}")
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

    print("=== Windows Defender Aggressive Disable Tool ===\n")
    print("⚠️  Make sure Tamper Protection is OFF!\n")
    time.sleep(2)
    clear()

    total_steps = 100
    current = 0

    # Stage 1: Registry
    print_progress(current, "Applying registry settings...")
    paths = [
        r"SOFTWARE\Policies\Microsoft\Windows Defender",
        r"SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection",
        r"SOFTWARE\Policies\Microsoft\Windows Defender\SpyNet",
    ]
    
    settings = ["DisableAntiSpyware", "DisableRealtimeMonitoring", "DisableOnAccessProtection",
                "DisableBehaviorMonitoring", "DisableIOAVProtection", "DisableScriptScanning"]

    for base_path in paths:
        for setting in settings:
            set_registry_key(base_path, setting, 1)
            current += 2
            print_progress(current, "Applying registry settings...")
    
    set_registry_key(r"SOFTWARE\Policies\Microsoft\Windows Advanced Threat Protection", 
                    "ForceDefenderPassiveMode", 1)
    current = 35
    print_progress(current, "Applying registry settings...")

    # Stage 2: Services
    time.sleep(0.5)
    print_progress(40, "Stopping and disabling services...")
    services = ["WinDefend", "WdNisSvc", "SecurityHealthService", "wscsvc"]
    for i, svc in enumerate(services):
        subprocess.run(['sc', 'stop', svc], capture_output=True, check=False)
        subprocess.run(['sc', 'config', svc, 'start=', 'disabled'], capture_output=True, check=False)
        current = 40 + (i+1)*8
        print_progress(current, "Stopping and disabling services...")

    # Stage 3: PowerShell
    time.sleep(0.5)
    print_progress(75, "Applying PowerShell preferences...")
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
    
    for i, cmd in enumerate(ps_cmds):
        run_powershell_command(cmd)
        current = 75 + (i+1)*2
        print_progress(current, "Applying PowerShell preferences...")

    # Finish
    print_progress(100, "Disabling Windows Defender...")
    time.sleep(1.5)
    clear()

    print("=== Finished Successfully ===\n")
    print("✅ Windows Defender has been aggressively disabled.")
    print("Restart your VM for best results.\n")
    time.sleep(3)

    # Final clear and close
    clear()
    print("Closing window...")
    time.sleep(1)

    # Close CMD
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
        sys.exit(1)