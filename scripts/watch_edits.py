# ==============================================================================
# PURPOSE: File Watcher & Specification Conformance Automator.
# SCOPE: Monitors workspace file changes, triggers validate_spec.py, and runs test suite.
# DEPENDENCIES: Standard Python library
# RISKS: Relies on polling; minimal background CPU footprint.
# ==============================================================================

import os
import sys
import time
import subprocess

# Configure monitored file directories
MONITORED_PATHS = [
    "gateway",
    "scripts",
    ".env.example",
    "docker-compose.yml"
]

def run_command(args) -> int:
    """
    Safely executes an external system process and returns exit status.
    """
    try:
        res = subprocess.run(args, capture_output=True, text=True, check=False)
        if res.returncode != 0:
            print(f"\033[31mCommand failed:\033[0m {' '.join(args)}")
            print(res.stderr)
        else:
            print(res.stdout)
        return res.returncode
    except Exception as e:
        print(f"\033[31mExecution failure: {e}\033[0m", file=sys.stderr)
        return 1

def check_for_changes(last_states) -> dict:
    """
    Recursively scans files inside monitored directories and returns their modification times.
    """
    current_states = {}
    for path in MONITORED_PATHS:
        if os.path.isfile(path):
            current_states[path] = os.path.getmtime(path)
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                # Avoid scanning cache folders or virtual environment dependencies
                if "__pycache__" in root or ".pytest_cache" in root or "venv" in root:
                    continue
                for f in files:
                    file_path = os.path.join(root, f)
                    try:
                        current_states[file_path] = os.path.getmtime(file_path)
                    except OSError:
                        pass
    return current_states

def start_watcher():
    print("\033[36m[UAMS Auto-Watcher] Initializing file system watcher...\033[0m")
    print("\033[36m[UAMS Auto-Watcher] Monitoring gateway directories for save actions...\033[0m")

    # Capture baseline modification states
    last_states = check_for_changes({})
    
    # Run initial conformance check on start
    print("\n--- Initial Conformance Run ---")
    run_command([sys.executable, "scripts/validate_spec.py"])
    
    try:
        while True:
            time.sleep(1.5)  # Poll filesystem changes every 1.5 seconds
            current_states = check_for_changes(last_states)
            
            modified_files = []
            for path, mtime in current_states.items():
                if path not in last_states or mtime > last_states[path]:
                    modified_files.append(path)
            
            # Detect deletions
            for path in last_states:
                if path not in current_states:
                    modified_files.append(path)
                    
            if modified_files:
                print(f"\n\033[33m[UAMS Auto-Watcher] Changes detected in: {', '.join(modified_files)}\033[0m")
                print("\033[36m[UAMS Auto-Watcher] Triggering specification validator...\033[0m")
                
                # 1. Validate spec alignment
                spec_status = run_command([sys.executable, "scripts/validate_spec.py"])
                
                if spec_status == 0:
                    print("\033[32m[UAMS Auto-Watcher] Specification alignment validated successfully!\033[0m")
                    print("\033[36m[UAMS Auto-Watcher] Triggering asynchronous unit test suite...\033[0m")
                    
                    # 2. Run automated test suite to verify no functional regression
                    run_command(["venv/Scripts/pytest.exe", "-v"])
                else:
                    print("\033[31m[UAMS Auto-Watcher] Spec validation FAILED! Please align edits with system_architecture.md\033[0m")
                
                # Update modification markers
                last_states = current_states
                
    except KeyboardInterrupt:
        print("\n\033[36m[UAMS Auto-Watcher] Watcher terminated by keyboard request.\033[0m")

if __name__ == "__main__":
    start_watcher()
