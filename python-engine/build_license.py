"""Nuitka build script for the license module.

Compiles src/license/ into a native .pyd extension to prevent reverse engineering
of the activation validation logic.

Usage:
    python build_license.py

Output:
    dist/license.pyd (or license.cp311-win_amd64.pyd)
"""

import subprocess
import sys
import os


def build():
    """Compile the license module with Nuitka."""
    src_dir = os.path.join(os.path.dirname(__file__), "src", "license")

    cmd = [
        sys.executable, "-m", "nuitka",
        "--module",
        "--output-dir=dist",
        "--remove-output",
        "--no-pyi-file",
        # Optimization
        "--lto=yes",
        "--follow-imports",
        # Include sub-modules
        "--include-module=src.license.fingerprint",
        "--include-module=src.license.store",
        "--include-module=src.license.validator",
        # Windows specific
        "--windows-disable-console",
        # The package to compile
        src_dir,
    ]

    print(f"[nuitka] Building license module...")
    print(f"[nuitka] Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, cwd=os.path.dirname(__file__))

    if result.returncode == 0:
        print("[nuitka] License module compiled successfully")
    else:
        print(f"[nuitka] Build failed with code {result.returncode}")
        sys.exit(1)


if __name__ == "__main__":
    build()
