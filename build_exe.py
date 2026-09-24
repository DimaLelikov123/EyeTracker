import os
import sys
import shutil
import zipfile
import hashlib
import subprocess

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def compute_sha256(filepath):
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()

def main():
    print("=" * 60)
    print("=== EyeTracker: Automated Standalone Windows Build ===")
    print("=" * 60)

    project_dir = os.path.abspath(os.path.dirname(__file__))
    os.chdir(project_dir)

    # 1. Clean previous build artifacts
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            print(f"Cleaning existing {folder}/ directory...")
            shutil.rmtree(folder, ignore_errors=True)

    icon_path = os.path.join("assets", "icon.ico")
    if not os.path.exists(icon_path):
        print(f"Error: Icon not found at {icon_path}!")
        sys.exit(1)

    print(f"Using application icon: {icon_path}")

    # 2. Construct PyInstaller command
    pyinstaller_cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name", "EyeTracker",
        "--windowed",                 # No console window
        f"--icon={icon_path}",
        "--add-data", f"assets{os.pathsep}assets",
        "--collect-all", "customtkinter",
        "--collect-all", "mediapipe",
        "--collect-all", "win11toast",
        "--collect-all", "pygrabber",
        "--hidden-import", "PIL._tkinter_finder",
        "--hidden-import", "sqlite3",
        "run.py"
    ]

    print("\nStarting PyInstaller compilation (this takes ~1-2 minutes)...")
    print("Command:", " ".join(pyinstaller_cmd[:8]) + " ...")
    
    result = subprocess.run(pyinstaller_cmd)
    if result.returncode != 0:
        print(f"\n❌ Build failed with return code {result.returncode}")
        sys.exit(result.returncode)

    exe_path = os.path.join("dist", "EyeTracker", "EyeTracker.exe")
    if not os.path.exists(exe_path):
        print(f"\n[ERROR] Build succeeded but {exe_path} was not found!")
        sys.exit(1)

    print(f"\n[OK] Standalone executable built successfully: {exe_path}")

    # Copy assets directly to dist/EyeTracker/assets
    dest_assets = os.path.join("dist", "EyeTracker", "assets")
    if os.path.exists(dest_assets):
        shutil.rmtree(dest_assets)
    shutil.copytree("assets", dest_assets)
    print(f"[OK] Assets copied to: {dest_assets}")

    # 3. Create Release ZIP archive
    zip_name = "EyeTracker-v1.0-Windows.zip"
    zip_path = os.path.join("dist", zip_name)
    dist_eyetracker_dir = os.path.join("dist", "EyeTracker")

    print(f"\nPackaging portable release archive: {zip_path}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(dist_eyetracker_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, "dist")
                zf.write(full_path, rel_path)

    zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    sha256 = compute_sha256(zip_path)

    print("\n" + "=" * 60)
    print("=== BUILD & PACKAGING COMPLETE ===")
    print("=" * 60)
    print(f"Executable : {exe_path}")
    print(f"Release ZIP: {zip_path} ({zip_size_mb:.1f} MB)")
    print(f"SHA-256    : {sha256}")
    print("=" * 60)
    print("\nReady to upload to GitHub Releases!")

if __name__ == "__main__":
    main()
