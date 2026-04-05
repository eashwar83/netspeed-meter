"""Build script to package NetSpeed Meter as a standalone ARM64 .exe using PyInstaller."""

import platform
import subprocess
import sys


def main():
    machine = platform.machine().lower()
    print(f"Python: {sys.version}")
    print(f"Architecture: {machine}")

    if machine not in ("arm64", "aarch64"):
        print(
            "\nWARNING: You are not running an ARM64 Python interpreter.\n"
            "The resulting .exe will NOT be a native ARM64 binary.\n"
            "Install Python for ARM64 from https://www.python.org/downloads/\n"
            "and re-run this script with that interpreter.\n"
        )
        answer = input("Continue anyway? [y/N] ").strip().lower()
        if answer != "y":
            sys.exit(1)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "NetSpeedMeter",
        "--icon", "NONE",
        "main.py",
    ]
    print(f"\nBuilding NetSpeed Meter...")
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    print(f"\nDone! Executable is in dist/NetSpeedMeter.exe ({machine})")


if __name__ == "__main__":
    main()
