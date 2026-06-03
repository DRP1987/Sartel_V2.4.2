"""Auto-update manager for SarTel application.

The build uses --onedir (COLLECT in spec), so the entire
dist/CANBusMonitor/ folder must be replaced, not just the .exe.

ZIP structure expected (no wrapper folder):
    update.zip
    ├── CANBusMonitor.exe
    └── _internal/
            └── ...

The updater:
  1. Checks version.json on GitHub for a newer version
  2. Downloads the ZIP (CANBusMonitor.exe + _internal/ at the root of the ZIP)
  3. Extracts the ZIP contents directly into a sibling staging folder
  4. Writes a .bat that (after the app exits) clears the old install folder,
     copies the staged files in, and relaunches the exe
  5. Calls sys.exit(0) to hand control to the .bat
"""

import os
import sys
import hashlib
import tempfile
import subprocess
import zipfile
import shutil
import requests
from packaging import version as pkg_version
from config.app_config import APP_VERSION, VERSION_MANIFEST_URL

CHECK_TIMEOUT = 5  # seconds for version check request

def get_install_dir():
    """
    Return the directory that contains CANBusMonitor.exe.
    Works both when running frozen (PyInstaller --onedir) and in plain Python dev mode.
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        # In dev mode, updater.py lives in utils/, so go up one level to project root
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def check_for_update():
    """
    Fetch version.json from GitHub and return update info if a newer version exists.

    Returns:
        dict with keys: latest_version, release_date, download_url, (optional) checksum_sha256
        or None if no update available or network error.
    """
    try:
        resp = requests.get(VERSION_MANIFEST_URL, timeout=CHECK_TIMEOUT)
        resp.raise_for_status()
        manifest = resp.json()
        latest = manifest.get("latest_version", "0.0.0")
        if pkg_version.parse(latest) > pkg_version.parse(APP_VERSION):
            return manifest
        return None
    except Exception as e:
        print(f"[Updater] Update check skipped: {e}")
        return None

def download_update(download_url, checksum_sha256=None, progress_callback=None):
    """
    Download the update ZIP to a temporary file.

    Args:
        download_url:      Direct URL to the .zip file.
        checksum_sha256:   Optional expected SHA-256 hex string for integrity verification.
        progress_callback: Optional callable(bytes_downloaded: int, total_bytes: int).

    Returns:
        Local filesystem path to the downloaded .zip, or None on failure.
    """
    try:
        resp = requests.get(download_url, stream=True, timeout=120)
        resp.raise_for_status()

        total = int(resp.headers.get("content-length", 0))
        downloaded = 0

        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".zip", prefix="SarTel_update_")
        sha = hashlib.sha256()

        with os.fdopen(tmp_fd, "wb") as f:
            for chunk in resp.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
                    sha.update(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded, total)

        if checksum_sha256:
            actual = sha.hexdigest()
            if actual.lower() != checksum_sha256.lower():
                os.remove(tmp_path)
                print(f"[Updater] Checksum mismatch! Expected {checksum_sha256}, got {actual}")
                return None

        print(f"[Updater] Downloaded update to: {tmp_path}")
        return tmp_path

    except Exception as e:
        print(f"[Updater] Download error: {e}")
        return None

def apply_update(zip_path):
    """
    Prepare the update and schedule an in-place file replacement via a .bat launcher.

    The ZIP is expected to contain CANBusMonitor.exe and _internal/ at its root
    (no wrapper folder).  The updater extracts those files into a sibling staging
    folder, then the .bat:
      - Waits for this process to exit
      - Deletes the contents of the current install folder (preserving the folder
        itself so the path stays valid)
      - Copies the staged files into the install folder
      - Relaunches CANBusMonitor.exe
      - Cleans up staging folder, downloaded zip, and itself

    The user's license file (~/.canbus_license.key) is in the home directory and
    is NEVER touched.

    Args:
        zip_path: Local path to the downloaded update .zip file.
    """
    install_dir = get_install_dir()
    parent_dir  = os.path.dirname(install_dir)
    exe_name    = os.path.basename(sys.executable) if getattr(sys, 'frozen', False) else "CANBusMonitor.exe"

    # ── 1. Extract ZIP into a staging folder next to the install dir ────────
    staging_dir = os.path.join(parent_dir, "_sartel_update_staging")
    if os.path.exists(staging_dir):
        shutil.rmtree(staging_dir, ignore_errors=True)
    os.makedirs(staging_dir, exist_ok=True)

    print(f"[Updater] Extracting {zip_path} to staging: {staging_dir}")
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(staging_dir)

    # ── 2. Verify exe is present at the root of the staging folder ──────────
    expected_exe = os.path.join(staging_dir, exe_name)
    if not os.path.exists(expected_exe):
        contents = os.listdir(staging_dir)
        print(f"[Updater] ERROR: {exe_name} not found in staging folder.")
        print(f"[Updater] Staging contents: {contents}")
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise FileNotFoundError(
            f"Update ZIP does not contain '{exe_name}' at the root level.\n"
            f"Found instead: {contents}\n"
            f"Please ZIP CANBusMonitor.exe and _internal\\ together WITHOUT any wrapper folder."
        )

    # ── 3. Write the .bat that swaps files after the app exits ──────────────
    current_pid = os.getpid()
    bat_path    = os.path.join(parent_dir, "_sartel_updater.bat")
    exe_path    = os.path.join(install_dir, exe_name)

    bat_content = (
        "@echo off\n"
        "setlocal\n"
        ":: SarTel auto-updater — waits for old process then replaces files in-place\n"
        "\n"
        ":wait_loop\n"
        "tasklist /FI \"PID eq {pid}\" 2>NUL | find /I \"{pid}\" >NUL\n"
        "if not errorlevel 1 (\n"
        "    timeout /t 1 /nobreak >NUL\n"
        "    goto wait_loop\n"
        ")\n"
        "\n"
        ":: Small extra pause to ensure file handles are released\n"
        "timeout /t 2 /nobreak >NUL\n"
        "\n"
        ":: Delete all files/subfolders inside the install folder (keep the folder itself)\n"
        "for /d %%D in (\"{install_dir}\*\") do rd /s /q \"%%D\"\n"
        "del /f /q \"{install_dir}\*\"\n"
        "\n"
        ":: Copy staged files into the install folder\n"
        "xcopy /e /i /y /q \"{staging_dir}\*\" \"{install_dir}\"\n"
        "\n"
        ":: Remove staging folder\n"
        "rd /s /q \"{staging_dir}\"\n"
        "\n"
        ":: Clean up downloaded zip\n"
        "if exist \"{zip_path}\" del /f /q \"{zip_path}\"\n"
        "\n"
        ":: Relaunch the updated application\n"
        "start \"\" \"{exe_path}\"\n"
        "\n"
        "endlocal\n"
        ":: Self-delete this batch file\n"
        "(goto) 2>nul & del \"%~f0\"\n"
    ).format(
        pid=current_pid,
        install_dir=install_dir,
        staging_dir=staging_dir,
        zip_path=zip_path,
        exe_path=exe_path,
    )

    with open(bat_path, "w") as f:
        f.write(bat_content)

    # ── 4. Launch the bat and exit ───────────────────────────────────────────
    print(f"[Updater] Launching updater bat: {bat_path}")
    subprocess.Popen(
        ["cmd.exe", "/c", bat_path],
        creationflags=subprocess.CREATE_NO_WINDOW,
        close_fds=True,
    )

    sys.exit(0)