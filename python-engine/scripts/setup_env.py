"""Environment setup script: detect hardware and install appropriate PyTorch.

Usage:
    python scripts/setup_env.py [--force-cpu] [--force-rocm] [--force-cuda]

IMPORTANT: CosyVoice3 requires Python 3.10-3.12 and PyTorch 2.3.1.
           Python 3.13+ is NOT compatible (no PyTorch 2.3.1 wheels).
"""

import subprocess
import sys
import argparse


# Minimum and maximum supported Python versions for CosyVoice3
PYTHON_MIN = (3, 10)
PYTHON_MAX = (3, 12)


def detect_gpu():
    """Detect GPU vendor and return recommended backend."""
    # Check for NVIDIA GPU
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return "cuda", result.stdout.strip().split("\n")[0]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Check for AMD GPU via Windows WMI
    try:
        import wmi
        w = wmi.WMI()
        for gpu in w.Win32_VideoController():
            name = gpu.Name or ""
            if "AMD" in name.upper() or "RADEON" in name.upper():
                return "rocm", name
    except Exception:
        pass

    # Check via dxdiag-style approach
    try:
        result = subprocess.run(
            ["wmic", "path", "win32_videocontroller", "get", "name"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if "AMD" in line.upper() or "RADEON" in line.upper():
                    return "rocm", line
                if "NVIDIA" in line.upper():
                    return "cuda", line
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return "cpu", "No compatible GPU detected"


# IMPORTANT: PyTorch version MUST match CosyVoice3 requirements (torch==2.3.1).
# Using a newer version (e.g. 2.6.x) causes garbled audio output due to
# autocast behavior changes and internal tensor operation differences.
TORCH_VERSION = "2.3.1"

TORCH_URLS = {
    "rocm": "https://download.pytorch.org/whl/rocm6.0",
    "cuda": "https://download.pytorch.org/whl/cu121",
    "cpu": "https://download.pytorch.org/whl/cpu",
}

# Chinese mirror fallback (used when download.pytorch.org has SSL issues)
TORCH_MIRROR_URLS = {
    "rocm": "https://mirror.sjtu.edu.cn/pytorch-wheels/rocm6.0/",
    "cuda": "https://mirror.sjtu.edu.cn/pytorch-wheels/cu121/",
    "cpu": "https://mirror.sjtu.edu.cn/pytorch-wheels/cpu/",
}


def install_pytorch(backend: str):
    """Install PyTorch with the appropriate backend."""
    index_url = TORCH_URLS[backend]
    mirror_url = TORCH_MIRROR_URLS[backend]
    packages = [f"torch=={TORCH_VERSION}", f"torchaudio=={TORCH_VERSION}"]
    if backend != "cpu":
        packages.append(f"torchvision=={TORCH_VERSION}")

    # Try official index first, fall back to Chinese mirror
    for url in [index_url, mirror_url]:
        cmd = [
            sys.executable, "-m", "pip", "install",
            *packages,
            "--index-url", url,
        ]
        print(f"\n[setup] Installing PyTorch {TORCH_VERSION} ({backend})...")
        print(f"[setup] Command: {' '.join(cmd)}\n")
        try:
            subprocess.check_call(cmd)
            return
        except subprocess.CalledProcessError:
            print(f"[setup] Failed with {url}, trying next mirror...")
    raise RuntimeError("Failed to install PyTorch from all sources")


def install_requirements():
    """Install requirements.txt dependencies."""
    print("\n[setup] Installing requirements.txt...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "-r", "requirements.txt",
    ])


def verify_installation(backend: str):
    """Verify PyTorch installation and GPU detection."""
    print("\n[setup] Verifying installation...")
    try:
        import torch
        print(f"  PyTorch version: {torch.__version__}")

        if backend == "cuda":
            if torch.cuda.is_available():
                print(f"  CUDA available: True")
                print(f"  CUDA version: {torch.version.cuda}")
                print(f"  GPU: {torch.cuda.get_device_name(0)}")
            else:
                print("  WARNING: CUDA not available after installation")

        elif backend == "rocm":
            hip_version = getattr(torch.version, "hip", None)
            if hip_version:
                print(f"  ROCm/HIP version: {hip_version}")
            if torch.cuda.is_available():
                print(f"  GPU (via HIP): {torch.cuda.get_device_name(0)}")
            else:
                print("  WARNING: ROCm GPU not available after installation")

        else:
            print("  CPU-only mode")

        import torchaudio
        print(f"  torchaudio version: {torchaudio.__version__}")
        print("\n[setup] Installation verified successfully!")

    except ImportError as e:
        print(f"\n[setup] ERROR: Verification failed - {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Setup AI inference environment")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--force-cpu", action="store_true", help="Force CPU-only PyTorch")
    group.add_argument("--force-rocm", action="store_true", help="Force ROCm (AMD GPU) PyTorch")
    group.add_argument("--force-cuda", action="store_true", help="Force CUDA (NVIDIA GPU) PyTorch")
    parser.add_argument("--skip-requirements", action="store_true", help="Skip requirements.txt install")
    args = parser.parse_args()

    print("=" * 60)
    print("  AI Dubber - Environment Setup")
    print("=" * 60)

    # Check Python version compatibility
    py_ver = sys.version_info[:2]
    if py_ver > PYTHON_MAX or py_ver < PYTHON_MIN:
        print(f"\n[setup] ERROR: Python {py_ver[0]}.{py_ver[1]} is not compatible!")
        print(f"[setup] CosyVoice3 requires Python {PYTHON_MIN[0]}.{PYTHON_MIN[1]}-{PYTHON_MAX[0]}.{PYTHON_MAX[1]}")
        print(f"[setup] PyTorch {TORCH_VERSION} does not have wheels for Python {py_ver[0]}.{py_ver[1]}")
        print(f"\n[setup] Please install Python 3.11 from https://www.python.org/downloads/")
        print(f"[setup] Then recreate the venv:")
        print(f"        py -3.11 -m venv .venv")
        print(f"        .venv\\Scripts\\activate")
        print(f"        python scripts/setup_env.py")
        sys.exit(1)

    print(f"\n[setup] Python version: {py_ver[0]}.{py_ver[1]} (OK)")

    # Determine backend
    if args.force_cpu:
        backend, gpu_name = "cpu", "Forced CPU mode"
    elif args.force_rocm:
        backend, gpu_name = "rocm", "Forced ROCm mode"
    elif args.force_cuda:
        backend, gpu_name = "cuda", "Forced CUDA mode"
    else:
        backend, gpu_name = detect_gpu()

    print(f"\n[setup] Detected GPU: {gpu_name}")
    print(f"[setup] Selected backend: {backend}")

    # Install — PyTorch first (to avoid dependency resolver pulling wrong versions)
    install_pytorch(backend)
    if not args.skip_requirements:
        install_requirements()
    verify_installation(backend)

    print(f"\n{'=' * 60}")
    print(f"  Setup complete! Backend: {backend}")
    print(f"{'=' * 60}")
    print("\nNext steps:")
    print("1. Download CosyVoice3 model: python download_cosyvoice3.py")
    print("2. Download Wav2Lip model (optional): python download_wav2lip.py")
    print("3. Start the server: python src/api/server.py")


if __name__ == "__main__":
    main()
