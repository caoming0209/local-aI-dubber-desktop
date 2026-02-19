"""TTS engine: CosyVoice 2 integration with dev mode fallback.

Lazy-loads the CosyVoice2 model on first use. Thread-safe via Lock.
Supports SFT (built-in speakers), zero-shot (voice cloning), and
instruct2 (instruction-guided) inference modes.
"""

import os
import sys
import uuid
import struct
import threading
from typing import Optional

from src.core.gpu_detector import gpu_detector
from src.core.voice_config import get_voice_config
from src.utils.dev_mode import is_dev_mode


class TTSEngine:
    def __init__(self):
        self._model = None
        self._model_dir: str = ""
        self._device: str = "cpu"
        self._lock = threading.Lock()

    def _get_model_dir(self) -> str:
        """Resolve CosyVoice2 model directory from settings."""
        from src.storage.settings_store import settings_store
        settings = settings_store.read()
        base = settings.get("modelStoragePath", "")
        if not base:
            base = os.path.join(
                os.path.expanduser("~"), "Documents", "智影口播", "models"
            )
        return os.path.join(base, "cosyvoice2", "CosyVoice2-0.5B")

    def _ensure_model(self) -> None:
        """Lazy-load CosyVoice2 model (thread-safe)."""
        if self._model is not None:
            return

        with self._lock:
            if self._model is not None:
                return

            model_dir = self._get_model_dir()
            if not os.path.isdir(model_dir):
                raise RuntimeError(
                    f"CosyVoice2 模型未找到: {model_dir}\n"
                    "请先下载模型或在设置中配置模型存储路径。"
                )

            self._device = gpu_detector.get_inference_device()

            # Add CosyVoice to sys.path
            cosyvoice_root = os.path.join(
                os.path.dirname(__file__), "..", "..", "third_party", "CosyVoice"
            )
            cosyvoice_root = os.path.normpath(cosyvoice_root)
            matcha_path = os.path.join(cosyvoice_root, "third_party", "Matcha-TTS")
            for p in [cosyvoice_root, matcha_path]:
                if p not in sys.path:
                    sys.path.insert(0, p)

            from cosyvoice.cli.cosyvoice import CosyVoice2

            print(f"[tts] Loading CosyVoice2 model from {model_dir} on {self._device}")
            self._model = CosyVoice2(model_dir)
            self._model_dir = model_dir
            print(f"[tts] Model loaded. Available speakers: {self._model.list_available_spks()}")

    def load_model(self, voice_id: str, model_path: str, device: Optional[str] = None) -> None:
        """Load TTS model for the given voice."""
        if is_dev_mode():
            self._device = device or "cpu"
            print(f"[tts] DEV mode: skip model loading for voice {voice_id}")
            return
        self._device = device or gpu_detector.get_inference_device()
        self._ensure_model()

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

        Output: WAV (sample rate from model, typically 24kHz), mono.
        """
        if not output_dir:
            output_dir = os.path.join(os.environ.get("TEMP", "/tmp"), "zhiying_tts")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"tts_{uuid.uuid4().hex[:8]}.wav")

        if is_dev_mode():
            self._create_placeholder_wav(output_path, duration=3.0)
            print(f"[tts] DEV stub: {output_path}")
            return output_path

        self._ensure_model()

        import torch
        import torchaudio

        config = get_voice_config(voice_id)
        mode = config["mode"]

        # Collect all speech chunks from the generator
        speech_chunks = []

        if mode == "sft":
            speaker_id = config["speaker_id"]
            for output in self._model.inference_sft(
                text, speaker_id, stream=False, speed=speed
            ):
                speech_chunks.append(output["tts_speech"])

        elif mode == "zero_shot":
            prompt_wav_path = self._resolve_prompt_path(config["prompt_wav"])
            prompt_text = config["prompt_text"] or ""
            for output in self._model.inference_zero_shot(
                text, prompt_text, prompt_wav_path, stream=False, speed=speed
            ):
                speech_chunks.append(output["tts_speech"])

        elif mode == "instruct2":
            prompt_wav_path = self._resolve_prompt_path(config["prompt_wav"])
            instruct_text = config["instruct_text"] or ""
            for output in self._model.inference_instruct2(
                text, instruct_text, prompt_wav_path, stream=False, speed=speed
            ):
                speech_chunks.append(output["tts_speech"])

        else:
            raise ValueError(f"Unknown TTS mode: {mode}")

        if not speech_chunks:
            raise RuntimeError("TTS 合成失败：未生成任何语音数据")

        # Concatenate all chunks
        speech = torch.cat(speech_chunks, dim=1)

        # Apply volume adjustment
        if volume != 1.0:
            speech = speech * volume

        # Clamp to prevent clipping
        speech = torch.clamp(speech, -1.0, 1.0)

        # Save WAV
        torchaudio.save(output_path, speech, self._model.sample_rate)

        print(f"[tts] Synthesized: {output_path} (voice={voice_id}, mode={mode}, "
              f"speed={speed}, duration={speech.shape[1] / self._model.sample_rate:.1f}s)")
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
        try:
            os.remove(path)
        except OSError:
            pass
        return data

    def _resolve_prompt_path(self, relative_path: Optional[str]) -> str:
        """Resolve prompt WAV path relative to model storage directory."""
        if not relative_path:
            return ""
        from src.storage.settings_store import settings_store
        settings = settings_store.read()
        base = settings.get("modelStoragePath", "")
        if not base:
            base = os.path.join(
                os.path.expanduser("~"), "Documents", "智影口播", "models"
            )
        full_path = os.path.join(base, "cosyvoice2", relative_path)
        if not os.path.exists(full_path):
            print(f"[tts] WARNING: Prompt WAV not found: {full_path}")
        return full_path

    def unload_model(self) -> None:
        """Unload model to free memory."""
        with self._lock:
            if self._model is not None:
                del self._model
                self._model = None
                try:
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except ImportError:
                    pass
                print("[tts] Model unloaded")

    def _create_placeholder_wav(self, path: str, duration: float = 3.0) -> None:
        """Create a silent WAV file as placeholder (dev mode only)."""
        sample_rate = 24000
        num_samples = int(sample_rate * duration)
        data_size = num_samples * 2  # 16-bit mono
        with open(path, "wb") as f:
            f.write(b"RIFF")
            f.write(struct.pack("<I", 36 + data_size))
            f.write(b"WAVE")
            f.write(b"fmt ")
            f.write(struct.pack("<I", 16))
            f.write(struct.pack("<H", 1))   # PCM
            f.write(struct.pack("<H", 1))   # mono
            f.write(struct.pack("<I", sample_rate))
            f.write(struct.pack("<I", sample_rate * 2))
            f.write(struct.pack("<H", 2))
            f.write(struct.pack("<H", 16))
            f.write(b"data")
            f.write(struct.pack("<I", data_size))
            f.write(b"\x00" * data_size)


tts_engine = TTSEngine()
