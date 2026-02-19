"""Environment setup script: detect hardware and install appropriate PyTorch.

Usage:
    python scripts/setup_env.py [--force-cpu] [--force-rocm] [--force-cuda]
"""

import subprocess
import sys
import argparse


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


TORCH_URLS = {
    "rocm": "https://download.pytorch.org/whl/rocm6.4",
    "cuda": "https://download.pytorch.org/whl/cu118",
    "cpu": "https://download.pytorch.org/whl/cpu",
}


def install_pytorch(backend: str):
    """Install PyTorch with the appropriate backend."""
    index_url = TORCH_URLS[backend]
    packages = ["torch", "torchaudio"]
    if backend != "cpu":
        packages.append("torchvision")

    cmd = [
        sys.executable, "-m", "pip", "install",
        *packages,
        "--index-url", index_url,
    ]
    print(f"\n[setup] Installing PyTorch ({backend})...")
    print(f"[setup] Command: {' '.join(cmd)}\n")
    subprocess.check_call(cmd)


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

    # Install
    if not args.skip_requirements:
        install_requirements()
    install_pytorch(backend)
    verify_installation(backend)

    print(f"\n{'=' * 60}")
    print(f"  Setup complete! Backend: {backend}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
