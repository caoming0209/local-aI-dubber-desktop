"""TTS engine wrapper for CosyVoice 2 (primary) and VITS (fallback).

This is a stub implementation. The actual model loading and inference
will be integrated when CosyVoice 2 / VITS models are available.
"""

import os
import uuid
from pathlib import Path
from typing import Optional

from src.core.gpu_detector import gpu_detector


class TTSEngine:
    def __init__(self):
        self._model = None
        self._model_type: Optional[str] = None
        self._device: str = "cpu"

    def load_model(self, voice_id: str, model_path: str, device: Optional[str] = None) -> None:
        """Load TTS model for the given voice."""
        self._device = device or gpu_detector.get_inference_device()
        self._model_type = "cosyvoice2"
        # Actual model loading will be implemented with CosyVoice 2 integration
        print(f"[tts] Loading model for voice {voice_id} on {self._device}")

    def synthesize(
        self,
        text: str,
        voice_id: str,
        speed: float = 1.0,
        volume: float = 1.0,
        emotion: float = 0.5,
        output_dir: str = "",
    ) -> str:
        """Synthesize speech from text, return path to WAV file.

        Output: WAV 24kHz mono, to be resampled to 16kHz for Wav2Lip.
        """
        if not output_dir:
            output_dir = os.path.join(os.environ.get("TEMP", "/tmp"), "zhiying_tts")
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, f"tts_{uuid.uuid4().hex[:8]}.wav")

        # Stub: create a placeholder WAV file
        # Real implementation will call CosyVoice 2 model
        self._create_placeholder_wav(output_path, duration=3.0)

        print(f"[tts] Synthesized: {output_path} (voice={voice_id}, speed={speed})")
        return output_path

    def preview(
        self,
        text: str,
        voice_id: str,
        speed: float = 1.0,
        volume: float = 1.0,
        emotion: float = 0.5,
    ) -> bytes:
        """Synthesize preview audio, return WAV bytes."""
        path = self.synthesize(text, voice_id, speed, volume, emotion)
        with open(path, "rb") as f:
            data = f.read()
        os.remove(path)
        return data

    def _create_placeholder_wav(self, path: str, duration: float = 3.0) -> None:
        """Create a silent WAV file as placeholder."""
        import struct
        sample_rate = 24000
        num_samples = int(sample_rate * duration)
        # WAV header + silent PCM data
        data_size = num_samples * 2  # 16-bit mono
        with open(path, "wb") as f:
            # RIFF header
            f.write(b"RIFF")
            f.write(struct.pack("<I", 36 + data_size))
            f.write(b"WAVE")
            # fmt chunk
            f.write(b"fmt ")
            f.write(struct.pack("<I", 16))  # chunk size
            f.write(struct.pack("<H", 1))   # PCM
            f.write(struct.pack("<H", 1))   # mono
            f.write(struct.pack("<I", sample_rate))
            f.write(struct.pack("<I", sample_rate * 2))  # byte rate
            f.write(struct.pack("<H", 2))   # block align
            f.write(struct.pack("<H", 16))  # bits per sample
            # data chunk
            f.write(b"data")
            f.write(struct.pack("<I", data_size))
            f.write(b"\x00" * data_size)


tts_engine = TTSEngine()
