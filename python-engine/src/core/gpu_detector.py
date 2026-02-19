"""GPU detection: NVIDIA CUDA, AMD ROCm, and CPU fallback."""

import subprocess
from typing import Optional


class GpuDetector:
    def __init__(self):
        self._cached_info: Optional[dict] = None

    def detect(self) -> dict:
        """Detect GPU availability (NVIDIA CUDA or AMD ROCm)."""
        if self._cached_info:
            return self._cached_info

        info = {
            "gpu_available": False,
            "gpu_name": "Unknown",
            "gpu_vendor": "none",       # nvidia / amd / none
            "gpu_vram_gb": 0,
            "backend": "cpu",           # cuda / rocm / cpu
            "cuda_version": None,
            "rocm_version": None,
            "recommendation": "not_detected",
        }

        # Try PyTorch detection (covers both CUDA and ROCm)
        try:
            import torch

            # ROCm exposes itself through torch.cuda API (HIP compatibility layer)
            hip_version = getattr(torch.version, "hip", None)

            if torch.cuda.is_available():
                info["gpu_available"] = True
                info["gpu_name"] = torch.cuda.get_device_name(0)
                info["gpu_vram_gb"] = round(
                    torch.cuda.get_device_properties(0).total_mem / (1024**3), 1
                )

                if hip_version:
                    # AMD ROCm (HIP maps to cuda API)
                    info["gpu_vendor"] = "amd"
                    info["backend"] = "rocm"
                    info["rocm_version"] = hip_version
                else:
                    # NVIDIA CUDA
                    info["gpu_vendor"] = "nvidia"
                    info["backend"] = "cuda"
                    info["cuda_version"] = torch.version.cuda

                info["recommendation"] = (
                    "compatible" if info["gpu_vram_gb"] >= 4 else "incompatible"
                )

            elif hip_version:
                # ROCm installed but no GPU detected
                info["rocm_version"] = hip_version

        except ImportError:
            # PyTorch not installed, try system-level detection
            self._detect_nvidia_smi(info)
            if not info["gpu_available"]:
                self._detect_amd_wmi(info)

        self._cached_info = info
        return info

    def _detect_nvidia_smi(self, info: dict) -> None:
        """Fallback: detect NVIDIA GPU via nvidia-smi."""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split(",")
                info["gpu_available"] = True
                info["gpu_vendor"] = "nvidia"
                info["backend"] = "cuda"
                info["gpu_name"] = parts[0].strip()
                info["gpu_vram_gb"] = round(float(parts[1].strip()) / 1024, 1)
                info["recommendation"] = (
                    "compatible" if info["gpu_vram_gb"] >= 4 else "incompatible"
                )
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            pass

    def _detect_amd_wmi(self, info: dict) -> None:
        """Fallback: detect AMD GPU via Windows WMI."""
        try:
            import wmi
            w = wmi.WMI()
            for gpu in w.Win32_VideoController():
                name = gpu.Name or ""
                if "AMD" in name.upper() or "RADEON" in name.upper():
                    vram_bytes = gpu.AdapterRAM or 0
                    vram_gb = round(vram_bytes / (1024**3), 1) if vram_bytes > 0 else 0
                    info["gpu_available"] = True
                    info["gpu_vendor"] = "amd"
                    info["backend"] = "rocm"
                    info["gpu_name"] = name
                    info["gpu_vram_gb"] = vram_gb
                    info["recommendation"] = (
                        "compatible" if vram_gb >= 4 else "incompatible"
                    )
                    break
        except Exception:
            pass

    def get_inference_device(self, mode: str = "auto") -> str:
        """Return 'cuda' or 'cpu' based on mode and availability.

        Note: ROCm also returns 'cuda' because PyTorch HIP maps to the cuda API.
        """
        if mode == "cpu":
            return "cpu"
        if mode == "gpu":
            info = self.detect()
            return "cuda" if info["gpu_available"] else "cpu"
        # auto mode
        info = self.detect()
        return "cuda" if info["gpu_available"] and info["recommendation"] == "compatible" else "cpu"

    def clear_cache(self) -> None:
        """Clear cached detection results (useful after driver install)."""
        self._cached_info = None


gpu_detector = GpuDetector()
