"""GPU detection and CUDA compatibility check."""

import subprocess
from typing import Optional


class GpuDetector:
    def __init__(self):
        self._cached_info: Optional[dict] = None

    def detect(self) -> dict:
        """Detect GPU and CUDA availability."""
        if self._cached_info:
            return self._cached_info

        info = {
            "gpu_available": False,
            "gpu_name": "Unknown",
            "gpu_vram_gb": 0,
            "cuda_version": None,
            "recommendation": "not_detected",
        }

        # Try PyTorch CUDA detection
        try:
            import torch
            if torch.cuda.is_available():
                info["gpu_available"] = True
                info["gpu_name"] = torch.cuda.get_device_name(0)
                info["gpu_vram_gb"] = round(
                    torch.cuda.get_device_properties(0).total_mem / (1024**3), 1
                )
                info["cuda_version"] = torch.version.cuda
                info["recommendation"] = (
                    "compatible" if info["gpu_vram_gb"] >= 4 else "incompatible"
                )
        except ImportError:
            # PyTorch not installed, try nvidia-smi
            try:
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode == 0 and result.stdout.strip():
                    parts = result.stdout.strip().split(",")
                    info["gpu_available"] = True
                    info["gpu_name"] = parts[0].strip()
                    info["gpu_vram_gb"] = round(float(parts[1].strip()) / 1024, 1)
                    info["recommendation"] = (
                        "compatible" if info["gpu_vram_gb"] >= 4 else "incompatible"
                    )
            except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                pass

        self._cached_info = info
        return info

    def get_inference_device(self, mode: str = "auto") -> str:
        """Return 'cuda' or 'cpu' based on mode and availability."""
        if mode == "cpu":
            return "cpu"
        if mode == "gpu":
            info = self.detect()
            return "cuda" if info["gpu_available"] else "cpu"
        # auto mode
        info = self.detect()
        return "cuda" if info["gpu_available"] and info["recommendation"] == "compatible" else "cpu"


gpu_detector = GpuDetector()
