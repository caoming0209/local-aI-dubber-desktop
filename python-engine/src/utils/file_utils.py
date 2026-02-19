"""File utility functions: path normalization, thumbnail extraction, file size formatting."""

import os
import subprocess
from pathlib import Path
from typing import Optional


def normalize_path(p: str) -> str:
    """Normalize a file path to use forward slashes and resolve."""
    return str(Path(p).resolve())


def ensure_dir(p: str) -> str:
    """Ensure directory exists, create if not."""
    Path(p).mkdir(parents=True, exist_ok=True)
    return str(Path(p).resolve())


def extract_thumbnail(video_path: str, output_path: str) -> Optional[str]:
    """Extract first frame from video as JPEG thumbnail using FFmpeg."""
    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            output_path,
        ]
        subprocess.run(cmd, capture_output=True, check=True, timeout=10)
        if os.path.exists(output_path):
            return output_path
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable form."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def get_file_size(path: str) -> Optional[int]:
    """Get file size in bytes, or None if file doesn't exist."""
    try:
        return os.path.getsize(path)
    except OSError:
        return None


def get_video_duration(video_path: str) -> Optional[float]:
    """Get video duration in seconds using FFprobe."""
    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            video_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=10)
        import json
        info = json.loads(result.stdout)
        return float(info["format"]["duration"])
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, KeyError, FileNotFoundError):
        return None
