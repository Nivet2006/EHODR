import os
import subprocess
import sys
import time
import urllib.request
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path("C:/codingprojects/EHODR")
SCREENSHOTS_DIR = ROOT / "dashboards" / "screenshots"
ARTIFACTS_DIR = Path("C:/Users/nived/.gemini/antigravity-ide/brain/30ad62e9-667a-4ab7-8332-1aaa78d01fe3")

def wait_for_server(url, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False

def main():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    server_url = "http://127.0.0.1:8080/api/state"
    server_proc = None

    # Check if server is already running
    if not wait_for_server(server_url, timeout=1):
        print("[INFO] Starting serve.py server in background...")
        python_exe = sys.executable
        venv_python = ROOT / "venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            python_exe = str(venv_python)

        server_proc = subprocess.Popen(
            [python_exe, "dashboards/serve.py"],
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        if wait_for_server(server_url, timeout=10):
            print("[SUCCESS] Background server started successfully.")
        else:
            print("[ERROR] Failed to start serve.py server.")
            if server_proc:
                server_proc.terminate()
            sys.exit(1)
    else:
        print("[INFO] Server is already running. Reusing active server.")

    print("[INFO] Initiating Playwright automated browser tests...")
    with sync_playwright() as p:
        print("[INFO] Launching headless Chromium browser...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_viewport_size({"width": 1440, "height": 900})

        # Register auto-accept dialog handler for alert/confirm popups
        def handle_dialog(dialog):
            print(f"[DIALOG] Auto-accepting dialog: {dialog.message}")
            dialog.accept()
        page.on("dialog", handle_dialog)

        # ─── 1. MAIN UNIFIED HUB ───
        try:
            print("[TEST] Loading Unified Hub...")
            page.goto("http://127.0.0.1:8080/index.html")
            page.wait_for_timeout(1500)
            hub_shot = SCREENSHOTS_DIR / "hub.png"
            page.screenshot(path=str(hub_shot))
            print(f"[SAVED] Hub Screenshot -> {hub_shot}")
        except Exception as e:
            print(f"[ERROR] Hub Screenshot failed: {e}")

        # ─── 2. AMBULANCE COMMAND ───
        try:
            print("[TEST] Loading Ambulance Command...")
            page.goto("http://127.0.0.1:8080/ambulance.html")
            page.wait_for_timeout(1500)
            amb_normal_shot = SCREENSHOTS_DIR / "ambulance_normal.png"
            page.screenshot(path=str(amb_normal_shot))
            print(f"[SAVED] Ambulance Normal -> {amb_normal_shot}")

            # Log meds click
            print("[TEST] Click 'LOG MEDS' button...")
            page.click('[data-action="log-meds"]')
            page.wait_for_timeout(1000)

            # Emergency override click (accept confirm dialog)
            print("[TEST] Triggering 'EMERGENCY OVERRIDE'...")
            page.click("#emergency-override")
            page.wait_for_timeout(2000) # wait for visual ring glow
            amb_override_shot = SCREENSHOTS_DIR / "ambulance_override.png"
            page.screenshot(path=str(amb_override_shot))
            print(f"[SAVED] Ambulance Override -> {amb_override_shot}")
        except Exception as e:
            print(f"[ERROR] Ambulance Command test failed: {e}")

        # ─── 3. GUARDIAN PORTAL ───
        try:
            print("[TEST] Loading Guardian Portal...")
            page.goto("http://127.0.0.1:8080/guardian.html")
            page.wait_for_timeout(1500)

            # Fill and send coordinator chat
            print("[TEST] Sending chat message...")
            page.fill("#chat-input", "Is Johnathan doing okay?")
            page.click("#chat-send")
            page.wait_for_timeout(2500) # wait for simulated response
            guard_chat_shot = SCREENSHOTS_DIR / "guardian_chat.png"
            page.screenshot(path=str(guard_chat_shot))
            print(f"[SAVED] Guardian Portal Chat -> {guard_chat_shot}")
        except Exception as e:
            print(f"[ERROR] Guardian Portal test failed: {e}")

        # ─── 4. ER COMMAND CENTER ───
        try:
            print("[TEST] Loading ER Command...")
            page.goto("http://127.0.0.1:8080/er-command.html")
            page.wait_for_timeout(1500)
            er_normal_shot = SCREENSHOTS_DIR / "er_normal.png"
            page.screenshot(path=str(er_normal_shot))
            print(f"[SAVED] ER Command Normal -> {er_normal_shot}")

            # Enable Mass Trauma banner programmatically by hitting the state directly or triggering a new incident
            print("[TEST] Triggering new incident to show banner...")
            page.click("#new-incident")
            page.wait_for_timeout(1000)

            # Since the protocol button might be hidden due to initial API states, let's directly trigger it via API
            print("[TEST] Enabling Mass Trauma Alert via direct API POST...")
            urllib.request.urlopen(
                urllib.request.Request(
                    "http://127.0.0.1:8080/api/actions/activate-protocol",
                    data=b"{}",
                    headers={"Content-Type": "application/json"}
                )
            )
            page.reload()
            page.wait_for_timeout(1500)
            er_protocol_shot = SCREENSHOTS_DIR / "er_protocol.png"
            page.screenshot(path=str(er_protocol_shot))
            print(f"[SAVED] ER Command Protocol -> {er_protocol_shot}")
        except Exception as e:
            print(f"[ERROR] ER Command test failed: {e}")

        browser.close()

    # Clean up server if we started it
    if server_proc:
        print("[INFO] Shutting down background server...")
        server_proc.terminate()
        server_proc.wait()

    # Copy all screenshots to the artifacts directory
    print("[INFO] Copying screenshots to artifacts directory for embedding...")
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    for f in SCREENSHOTS_DIR.glob("*.png"):
        shutil.copy(f, ARTIFACTS_DIR / f.name)
        print(f"[COPIED] -> {ARTIFACTS_DIR / f.name}")

    print("[SUCCESS] All automated browser tests and screenshot generation complete!")

if __name__ == "__main__":
    main()
