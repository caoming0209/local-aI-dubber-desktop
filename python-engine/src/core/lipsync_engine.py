"""Wav2Lip lipsync engine wrapper.

Stub implementation. Actual Wav2Lip inference will be integrated
when the model weights are available.
"""

import os
import uuid
import shutil
from typing import Optional

from src.core.gpu_detector import gpu_detector


class LipsyncEngine:
    def __init__(self):
        self._model = None
        self._device: str = "cpu"

    def load_model(self, model_path: str, device: Optional[str] = None) -> None:
        """Load Wav2Lip model."""
        self._device = device or gpu_detector.get_inference_device()
        print(f"[lipsync] Loading Wav2Lip model on {self._device}")

    def process(
        self,
        video_path: str,
        audio_path: str,
        output_dir: str = "",
    ) -> str:
        """Run lipsync: combine video with audio to produce lip-synced video.

        Args:
            video_path: Path to the digital human video (H.264, 25fps)
            audio_path: Path to the TTS audio (WAV 16kHz)
            output_dir: Directory for output video

        Returns:
            Path to the lip-synced video (MP4, no audio track yet)
        """
        if not output_dir:
            output_dir = os.path.join(os.environ.get("TEMP", "/tmp"), "zhiying_lipsync")
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, f"lipsync_{uuid.uuid4().hex[:8]}.mp4")

        # Stub: copy input video as placeholder
        # Real implementation will run Wav2Lip inference
        if os.path.exists(video_path):
            shutil.copy2(video_path, output_path)
        else:
            # Create empty placeholder
            with open(output_path, "wb") as f:
                f.write(b"")

        print(f"[lipsync] Processed: {output_path}")
        return output_path


lipsync_engine = LipsyncEngine()
