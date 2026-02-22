"""TTS engine: CosyVoice 3 integration with dev mode fallback.

Lazy-loads the CosyVoice3 model on first use. Thread-safe via Lock.
Supports zero-shot (voice cloning), cross-lingual, and instruct2
(instruction-guided) inference modes.
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
        self._backend: str = "cpu"
        self._lock = threading.Lock()

    def _get_model_dir(self) -> str:
        """Resolve CosyVoice3 model directory from settings."""
        from src.storage.settings_store import settings_store

        settings = settings_store.read()
        base = settings.get("modelStoragePath", "")
        if not base:
            base = os.path.join(
                os.path.expanduser("~"),
                "Documents",
                "local-aI-dubber-desktop",
                "models",
            )
        return os.path.join(base, "cosyvoice3", "Fun-CosyVoice3-0.5B-2512")

    def _get_torch_device(self):
        """Get PyTorch device object based on backend."""
        if self._backend == "directml":
            try:
                import torch_directml
                return torch_directml.device()
            except ImportError:
                return "cpu"
        return self._device

    def _ensure_model(self) -> None:
        """Lazy-load CosyVoice3 model (thread-safe)."""
        if self._model is not None:
            return

        with self._lock:
            if self._model is not None:
                return

            model_dir = self._get_model_dir()
            if not os.path.isdir(model_dir):
                raise RuntimeError(
                    f"CosyVoice3 模型未找到: {model_dir}\n"
                    "请先下载模型或在设置中配置模型存储路径。"
                )

            gpu_info = gpu_detector.detect()
            self._backend = gpu_info.get("backend", "cpu")
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

            from cosyvoice.cli.cosyvoice import CosyVoice3

            # CosyVoice's file_utils.py calls logging.basicConfig() on import,
            # which may create a StreamHandler with the system code page (GBK).
            # Patch all existing StreamHandlers to force UTF-8.
            try:
                import io
                import logging

                for handler in logging.root.handlers:
                    if isinstance(handler, logging.StreamHandler):
                        stream = handler.stream
                        if hasattr(stream, "reconfigure"):
                            try:
                                stream.reconfigure(encoding="utf-8", errors="replace")
                            except Exception:
                                pass
                        elif hasattr(stream, "buffer"):
                            try:
                                handler.stream = io.TextIOWrapper(
                                    stream.buffer, encoding="utf-8", errors="replace"
                                )
                            except Exception:
                                pass
            except Exception:
                pass

            print(f"[tts] Loading CosyVoice3 model from {model_dir} on {self._device} (backend: {self._backend})")

            fp16 = self._backend in ("cuda", "rocm")
            self._model = CosyVoice3(model_dir, fp16=fp16)
            self._model_dir = model_dir
            
            if self._backend == "directml":
                import torch_directml
                device = torch_directml.device()
                self._model.model.device = device
                self._model.model.llm = self._model.model.llm.to(device)
                self._model.model.flow = self._model.model.flow.to(device)
                self._model.model.hift = self._model.model.hift.to(device)
                print(f"[tts] Model moved to DirectML device")
            
            print(
                f"[tts] Model loaded. Available speakers: {self._model.list_available_spks()}"
            )

    def load_model(self, voice_id: str, model_path: str, device: Optional[str] = None) -> None:
        """Load TTS model for the given voice."""
        self._device = device or gpu_detector.get_inference_device()
        try:
            self._ensure_model()
        except Exception as e:
            if is_dev_mode():
                print(f"[tts] DEV mode: skip model loading ({e})")
                return
            raise

    def _prepare_tts_text(self, text: str) -> str:
        """Validate and clean TTS text.

        Does NOT add <|endofprompt|> markers — that is handled per-mode
        in synthesize() according to CosyVoice3's expected input format.
        """
        safe_text = (text or "").strip()
        if len(safe_text) < 4:
            raise ValueError("文案太短，至少需要4个字符才能合成语音。")

        if isinstance(safe_text, bytes):
            safe_text = safe_text.decode('utf-8')

        return safe_text

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
            # Dev mode: try real synthesis, fallback to placeholder if model unavailable
            try:
                self._ensure_model()
            except Exception as e:
                print(f"[tts] DEV mode: model not available ({e}), using placeholder")
                self._create_placeholder_wav(output_path, duration=3.0)
                print(f"[tts] DEV fallback: {output_path}")
                return output_path

        self._ensure_model()

        import torch
        import torchaudio

        config = get_voice_config(voice_id)
        mode = config["mode"]
        print(f"[tts] voice_id={voice_id}, mode={mode}", file=sys.stderr, flush=True)

        # Validate and clean text
        tts_text = self._prepare_tts_text(text)

        # Collect all speech chunks from the generator
        speech_chunks = []

        # CosyVoice3 <|endofprompt|> marker placement follows official examples:
        #   zero_shot:     prompt_text = "You are a helpful assistant.<|endofprompt|>" + prompt_text
        #                  tts_text    = raw user text (no markers)
        #   cross_lingual: tts_text    = "You are a helpful assistant.<|endofprompt|>" + user text
        #   instruct2:     instruct_text = "You are a helpful assistant. " + instruction + "<|endofprompt|>"
        #                  tts_text    = raw user text (no markers)
        SYSTEM_PREFIX = "You are a helpful assistant."
        EOP = "<|endofprompt|>"

        try:
            if mode == "sft":
                speaker_id = config["speaker_id"]
                for output in self._model.inference_sft(
                    tts_text,
                    speaker_id,
                    stream=False,
                    speed=speed,
                ):
                    speech_chunks.append(output["tts_speech"])

            elif mode == "zero_shot":
                prompt_wav_path = self._resolve_prompt_path(config["prompt_wav"])
                # prompt_text must include system prefix + <|endofprompt|> + actual prompt text
                raw_prompt_text = config.get("prompt_text", "") or ""
                prompt_text = f"{SYSTEM_PREFIX}{EOP}{raw_prompt_text}"
                print(f"[tts] zero_shot: prompt={prompt_wav_path}", file=sys.stderr, flush=True)
                for output in self._model.inference_zero_shot(
                    tts_text,
                    prompt_text,
                    prompt_wav_path,
                    zero_shot_spk_id='',
                    stream=False,
                    speed=speed,
                ):
                    speech_chunks.append(output["tts_speech"])

            elif mode == "instruct2":
                prompt_wav_path = self._resolve_prompt_path(config["prompt_wav"])
                # instruct_text must include system prefix + instruction + <|endofprompt|>
                raw_instruct = config.get("instruct_text", "") or ""
                # If already has the system prefix, use as-is; otherwise prepend it
                if raw_instruct.startswith(SYSTEM_PREFIX):
                    instruct_text = raw_instruct
                else:
                    # Strip trailing <|endofprompt|> to rebuild properly
                    instruction = raw_instruct.replace(EOP, "").strip()
                    instruct_text = f"{SYSTEM_PREFIX} {instruction}{EOP}"
                print(f"[tts] instruct2: instruct={instruct_text[:60]}...", file=sys.stderr, flush=True)
                for output in self._model.inference_instruct2(
                    tts_text,
                    instruct_text,
                    prompt_wav_path,
                    zero_shot_spk_id='',
                    stream=False,
                    speed=speed,
                ):
                    speech_chunks.append(output["tts_speech"])

            elif mode == "cross_lingual":
                prompt_wav_path = self._resolve_prompt_path(config["prompt_wav"])
                # Prepend system prefix + <|endofprompt|> to tts_text
                cross_lingual_text = f"{SYSTEM_PREFIX}{EOP}{tts_text}"
                print(f"[tts] cross_lingual: prompt={prompt_wav_path}", file=sys.stderr, flush=True)
                print(f"[tts] cross_lingual: text={cross_lingual_text[:80]}...", file=sys.stderr, flush=True)
                for output in self._model.inference_cross_lingual(
                    cross_lingual_text,
                    prompt_wav_path,
                    zero_shot_spk_id='',
                    stream=False,
                    speed=speed,
                ):
                    speech_chunks.append(output["tts_speech"])

            else:
                raise ValueError(f"Unknown TTS mode: {mode}")

        except RuntimeError as e:
            if "Kernel size can't be greater than actual input size" in str(e):
                raise RuntimeError(
                    f"TTS 合成失败：文本太短，无法生成语音。请尝试使用更长的文本。原始错误: {e}"
                ) from e
            raise

        except ValueError as e:
            if "prompt wav is too short" in str(e).lower():
                raise ValueError(
                    f"提示音频太短，无法生成语音。请使用至少 1 秒的音频文件。原始错误: {e}"
                ) from e
            raise

        if not speech_chunks:
            raise RuntimeError("TTS 合成失败：未生成任何语音数据")

        # Debug: check speech chunks
        for i, chunk in enumerate(speech_chunks):
            print(f"[tts] Chunk {i}: shape={chunk.shape}, min={chunk.min():.4f}, max={chunk.max():.4f}, mean={chunk.mean():.4f}", file=sys.stderr, flush=True)

        # Concatenate all chunks
        speech = torch.cat(speech_chunks, dim=1)

        # Apply volume adjustment
        if volume != 1.0:
            speech = speech * volume

        # Clamp to prevent clipping
        speech = torch.clamp(speech, -1.0, 1.0)

        # Save WAV
        # Many Windows players / browser audio decoders behave poorly with
        # 32-bit float WAV (pcm_f32le). Convert to signed 16-bit PCM.
        speech_i16 = (speech * 32767.0).to(torch.int16)
        import soundfile as sf
        sf.write(output_path, speech_i16.cpu().numpy().T, self._model.sample_rate, format='WAV', subtype='PCM_16')

        print(
            f"[tts] Synthesized: {output_path} (voice={voice_id}, mode={mode}, "
            f"speed={speed}, duration={speech.shape[1] / self._model.sample_rate:.1f}s)",
            file=sys.stderr,
            flush=True,
        )
        return output_path

    def preview(
        self,
        text: str,
        voice_id: str,
        speed: float = 1.0,
        volume: float = 1.0,
        emotion: float = 0.5,
    ) -> bytes:
        """Synthesize preview audio, return WAV bytes.
        
        In dev mode, also saves a copy to project directory for debugging.
        """
        path = self.synthesize(text, voice_id, speed, volume, emotion)
        with open(path, "rb") as f:
            data = f.read()
        
        # In dev mode, save a copy to project directory
        if is_dev_mode():
            try:
                # Get project root directory (python-engine)
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                dev_preview_dir = os.path.join(project_root, "data", "previews")
                os.makedirs(dev_preview_dir, exist_ok=True)
                
                # Create a meaningful filename
                safe_voice_id = voice_id.replace(" ", "_").replace("/", "_")
                timestamp = str(uuid.uuid4().hex[:8])
                dev_preview_path = os.path.join(dev_preview_dir, f"preview_{safe_voice_id}_{timestamp}.wav")
                
                # Copy the file
                import shutil
                shutil.copy2(path, dev_preview_path)
                print(f"[tts] DEV mode: Saved preview to {dev_preview_path}", file=sys.stderr, flush=True)
            except Exception as e:
                print(f"[tts] DEV mode: Failed to save preview copy: {e}", file=sys.stderr, flush=True)
        
        try:
            os.remove(path)
        except OSError:
            pass
        return data

    def _resolve_prompt_path(self, relative_path: Optional[str]) -> str:
        """Resolve prompt WAV path relative to model storage directory.

        Falls back to CosyVoice's default zero_shot_prompt.wav if custom prompt not found.
        Ensures the prompt file is long enough for CosyVoice2 (at least 0.5 seconds).
        """
        default_prompt = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "third_party",
            "CosyVoice",
            "asset",
            "zero_shot_prompt.wav",
        )
        default_prompt = os.path.normpath(default_prompt)

        if not relative_path:
            return default_prompt

        from src.storage.settings_store import settings_store

        settings = settings_store.read()
        base = settings.get("modelStoragePath", "")
        if not base:
            base = os.path.join(
                os.path.expanduser("~"), "Documents", "local-aI-dubber-desktop", "models"
            )

        # Try multiple locations in order of preference:
        # 1. Project voices directory (for development)
        # 2. cosyvoice3 model directory
        # 3. cosyvoice2 model directory
        
        # 1. Check project voices directory
        # relative_path already starts with "voices/", so we don't need to add it again
        project_voices = os.path.join(
            os.path.dirname(__file__), "..", ".."
        )
        project_voices = os.path.normpath(project_voices)
        
        search_paths = [
            os.path.join(project_voices, relative_path),
            os.path.join(base, "cosyvoice3", relative_path),
            os.path.join(base, "cosyvoice2", relative_path),
        ]

        for full_path in search_paths:
            if os.path.exists(full_path):
                try:
                    import soundfile as sf
                    import numpy as np
                    waveform_np, sr = sf.read(full_path)
                    if len(waveform_np.shape) == 2:
                        duration = waveform_np.shape[0] / sr
                    else:
                        duration = len(waveform_np) / sr
                    if duration >= 0.5:
                        print(f"[tts] Using custom prompt: {full_path}")
                        return full_path
                    else:
                        print(f"[tts] WARNING: Prompt WAV too short ({duration:.2f}s): {full_path}")
                except Exception as e:
                    print(f"[tts] WARNING: Failed to check prompt WAV: {e}")
        
        print(f"[tts] WARNING: Prompt WAV not found: {relative_path}, using default prompt")
        return default_prompt

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
        """Create an audible placeholder WAV (dev mode only).

        Returning a perfectly silent WAV makes preview look "broken". This generates
        a short sine-wave tone so playback is obvious even when the real model is
        unavailable.
        """
        import math
        from array import array

        sample_rate = 24000
        num_samples = int(sample_rate * duration)

        freq_hz = 440.0
        amplitude = 0.2
        fade_samples = int(sample_rate * 0.02)

        pcm = array("h")
        for i in range(num_samples):
            t = i / sample_rate
            v = math.sin(2.0 * math.pi * freq_hz * t) * amplitude

            if fade_samples > 0:
                if i < fade_samples:
                    v *= i / fade_samples
                elif i >= num_samples - fade_samples:
                    v *= max(0.0, (num_samples - 1 - i) / fade_samples)

            pcm.append(int(max(-1.0, min(1.0, v)) * 32767.0))

        data_bytes = pcm.tobytes()
        data_size = len(data_bytes)

        with open(path, "wb") as f:
            f.write(b"RIFF")
            f.write(struct.pack("<I", 36 + data_size))
            f.write(b"WAVE")
            f.write(b"fmt ")
            f.write(struct.pack("<I", 16))
            f.write(struct.pack("<H", 1))  # PCM
            f.write(struct.pack("<H", 1))  # mono
            f.write(struct.pack("<I", sample_rate))
            f.write(struct.pack("<I", sample_rate * 2))
            f.write(struct.pack("<H", 2))
            f.write(struct.pack("<H", 16))
            f.write(b"data")
            f.write(struct.pack("<I", data_size))
            f.write(data_bytes)


tts_engine = TTSEngine()
