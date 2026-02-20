"""FFmpeg video synthesizer: compose final video with background, subtitles, BGM."""

import os
import uuid
import json
from typing import Optional

from src.utils.dev_mode import is_dev_mode


class VideoSynthesizer:
    def __init__(self):
        self._ffmpeg_path = "ffmpeg"

    def synthesize(
        self,
        lipsync_video_path: str,
        audio_path: str,
        output_path: str,
        background: Optional[dict] = None,
        subtitle: Optional[dict] = None,
        bgm: Optional[dict] = None,
        aspect_ratio: str = "9:16",
    ) -> str:
        """Compose final video with all elements.

        Pipeline:
        1. Overlay lip-synced video on background
        2. Add audio track
        3. Burn subtitles (if enabled)
        4. Mix BGM (if enabled)
        5. Output H.264 MP4

        Returns path to final MP4.
        """
        import subprocess

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        if is_dev_mode():
            if lipsync_video_path and os.path.exists(lipsync_video_path):
                import shutil
                shutil.copy2(lipsync_video_path, output_path)
            elif audio_path and os.path.exists(audio_path):
                print(f"[synthesizer] DEV mode: creating placeholder video from audio")
                self._create_placeholder_from_audio(output_path, audio_path)
            else:
                print(f"[synthesizer] DEV mode: creating minimal placeholder video")
                self._create_minimal_placeholder(output_path)
            print(f"[synthesizer] DEV stub output: {output_path}")
            return output_path

        if not lipsync_video_path or not os.path.exists(lipsync_video_path):
            raise RuntimeError(f"口型同步视频文件不存在: {lipsync_video_path or '(空路径)'}")

        # Build FFmpeg command
        cmd = [self._ffmpeg_path, "-y"]

        # Input: lip-synced video
        cmd.extend(["-i", lipsync_video_path])

        # Input: audio
        cmd.extend(["-i", audio_path])

        # BGM input if enabled
        bgm_input_index = None
        if bgm and bgm.get("enabled") and bgm.get("file_path"):
            cmd.extend(["-i", bgm["file_path"]])
            bgm_input_index = 2

        # Video filter chain
        vfilters = []

        # Subtitle filter
        if subtitle and subtitle.get("enabled") and subtitle.get("text"):
            font_size = subtitle.get("font_size", 30)
            color = subtitle.get("color", "white")
            position = subtitle.get("position", "bottom_center")
            y_pos = "h-th-40" if "bottom" in position else "40"
            vfilters.append(
                f"drawtext=text='{subtitle['text']}':fontsize={font_size}"
                f":fontcolor={color}:x=(w-tw)/2:y={y_pos}"
            )

        # Apply video filters
        if vfilters:
            cmd.extend(["-vf", ",".join(vfilters)])

        # Audio mixing
        if bgm_input_index is not None:
            voice_vol = bgm.get("voice_volume", 1.0)
            bgm_vol = bgm.get("bgm_volume", 0.5)
            cmd.extend([
                "-filter_complex",
                f"[1:a]volume={voice_vol}[voice];[{bgm_input_index}:a]volume={bgm_vol}[bgm];"
                f"[voice][bgm]amix=inputs=2:duration=first[aout]",
                "-map", "0:v",
                "-map", "[aout]",
            ])
        else:
            cmd.extend(["-map", "0:v", "-map", "1:a"])

        # Output settings
        cmd.extend([
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            output_path,
        ])

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=600,
            )
            if result.returncode != 0:
                print(f"[synthesizer] FFmpeg error: {result.stderr}")
                raise RuntimeError(f"FFmpeg failed: {result.stderr[:500]}")
        except FileNotFoundError:
            raise RuntimeError("FFmpeg not found. Please install FFmpeg and add it to PATH.")

        print(f"[synthesizer] Output: {output_path}")
        return output_path

    def resample_audio(self, input_path: str, output_path: str, sample_rate: int = 16000) -> str:
        """Resample audio to target sample rate for Wav2Lip input."""
        if is_dev_mode():
            import shutil
            shutil.copy2(input_path, output_path)
            return output_path

        import subprocess

        cmd = [
            self._ffmpeg_path, "-y",
            "-i", input_path,
            "-ar", str(sample_rate),
            "-ac", "1",
            output_path,
        ]
        subprocess.run(cmd, capture_output=True, check=True, timeout=30)
        return output_path

    def extract_thumbnail(self, video_path: str, output_path: str) -> str:
        """Extract first frame as JPEG thumbnail."""
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        if is_dev_mode():
            if video_path and os.path.exists(video_path):
                import subprocess
                cmd = [
                    self._ffmpeg_path, "-y",
                    "-i", video_path,
                    "-vframes", "1",
                    "-q:v", "2",
                    output_path,
                ]
                subprocess.run(cmd, capture_output=True, timeout=10)
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    return output_path
            self._create_placeholder_thumbnail(output_path)
            return output_path

        import subprocess

        cmd = [
            self._ffmpeg_path, "-y",
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            output_path,
        ]
        subprocess.run(cmd, capture_output=True, check=True, timeout=10)
        return output_path

    def _create_placeholder_thumbnail(self, output_path: str) -> None:
        """Create a minimal placeholder JPEG thumbnail."""
        import subprocess

        cmd = [
            self._ffmpeg_path, "-y",
            "-f", "lavfi", "-i", "color=c=gray:s=320x180:d=0.04:r=25",
            "-vframes", "1",
            "-q:v", "2",
            output_path,
        ]
        try:
            subprocess.run(cmd, capture_output=True, timeout=10)
        except FileNotFoundError:
            pass

    def _create_placeholder_from_audio(self, output_path: str, audio_path: str) -> None:
        """Create a placeholder video with audio for dev mode testing."""
        import subprocess

        cmd = [
            self._ffmpeg_path, "-y",
            "-f", "lavfi", "-i", "color=c=gray:s=1080x1920:d=5:r=25",
            "-i", audio_path,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "28",
            "-c:a", "aac",
            "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            output_path,
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"[synthesizer] FFmpeg placeholder error: {result.stderr[:500]}")
                raise RuntimeError(f"创建占位视频失败: {result.stderr[:200]}")
        except FileNotFoundError:
            raise RuntimeError("FFmpeg 未找到，请安装 FFmpeg 并添加到 PATH。")

    def _create_minimal_placeholder(self, output_path: str) -> None:
        """Create a minimal placeholder video for dev mode testing."""
        import subprocess

        cmd = [
            self._ffmpeg_path, "-y",
            "-f", "lavfi", "-i", "color=c=gray:s=1080x1920:d=1:r=25",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "28",
            "-pix_fmt", "yuv420p",
            output_path,
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                print(f"[synthesizer] FFmpeg minimal placeholder error: {result.stderr[:500]}")
                raise RuntimeError(f"创建最小占位视频失败: {result.stderr[:200]}")
        except FileNotFoundError:
            raise RuntimeError("FFmpeg 未找到，请安装 FFmpeg 并添加到 PATH。")


video_synthesizer = VideoSynthesizer()
