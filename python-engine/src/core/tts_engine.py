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
        self._backend: str = "cpu"
        self._lock = threading.Lock()

    def _get_model_dir(self) -> str:
        """Resolve CosyVoice2 model directory from settings."""
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
        return os.path.join(base, "cosyvoice2", "CosyVoice2-0.5B")

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

            from cosyvoice.cli.cosyvoice import CosyVoice2

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

            print(f"[tts] Loading CosyVoice2 model from {model_dir} on {self._device} (backend: {self._backend})")

            fp16 = self._backend in ("cuda", "rocm")
            self._model = CosyVoice2(model_dir, fp16=fp16)
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

    def _prepare_tts_text(self, text: str, min_token_len: int = 60) -> str:
        """Prepare TTS text so CosyVoice2 can handle very short scripts.

        CosyVoice2's frontend has `token_min_n=60` in paragraph splitting.
        Extremely short token sequences can trigger Conv1d kernel-size errors.

        Strategy:
        - Normalize with `split=False` to get a single string.
        - If token length is too short, repeat the normalized text with Chinese comma.
          Remove trailing sentence-ending punctuation before repeating to avoid creating
          many tiny sentences.
        """
        safe_text = (text or "").strip()
        if len(safe_text) < 4:
            raise ValueError("文案太短，至少需要4个字符才能合成语音。")

        # NOTE: Some text frontends (e.g. ttsfrd) may produce mojibake on Windows.
        # Keep frontend normalization off to preserve original Unicode text.
        normalized = self._model.frontend.text_normalize(
            safe_text, split=False, text_frontend=False
        )
        normalized = (normalized or "").strip()
        if not normalized:
            raise ValueError("文案不能为空")

        try:
            _, text_len = self._model.frontend._extract_text_token(normalized)
            token_len = int(text_len.item())
        except Exception:
            return normalized

        if token_len <= 0 or token_len >= min_token_len:
            return normalized

        base = normalized.rstrip("。.!?！？")
        if not base:
            base = normalized

        times = (min_token_len + token_len - 1) // token_len
        expanded = "，".join([base] * times) + "。"
        return expanded

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

        # Collect all speech chunks from the generator
        speech_chunks = []

        prompt_wav_path = None
        prompt_text = None
        instruct_text = None

        if mode in {"zero_shot", "instruct2"}:
            prompt_wav_path = self._resolve_prompt_path(config["prompt_wav"])

        if mode == "zero_shot":
            prompt_text = config["prompt_text"] or ""
            prompt_text = self._model.frontend.text_normalize(
                prompt_text, split=False, text_frontend=False
            )

        if mode == "instruct2":
            instruct_text = config["instruct_text"] or ""
            instruct_text = self._model.frontend.text_normalize(
                instruct_text, split=False, text_frontend=False
            )
            print(
                f"[tts] Using prompt: {prompt_wav_path}, instruct: {instruct_text[:30]}..."
            )

        def _run_inference(tts_text: str) -> None:
            # Pass text_frontend=False to avoid CosyVoice doing its own split/segmenting.
            # We already normalized + expanded short scripts in _prepare_tts_text().
            if mode == "sft":
                speaker_id = config["speaker_id"]
                for output in self._model.inference_sft(
                    tts_text,
                    speaker_id,
                    stream=False,
                    speed=speed,
                    text_frontend=False,
                ):
                    speech_chunks.append(output["tts_speech"])

            elif mode == "zero_shot":
                for output in self._model.inference_zero_shot(
                    tts_text,
                    prompt_text,
                    prompt_wav_path,
                    stream=False,
                    speed=speed,
                    text_frontend=False,
                ):
                    speech_chunks.append(output["tts_speech"])

            elif mode == "instruct2":
                for output in self._model.inference_instruct2(
                    tts_text,
                    instruct_text,
                    prompt_wav_path,
                    stream=False,
                    speed=speed,
                    text_frontend=False,
                ):
                    speech_chunks.append(output["tts_speech"])

            else:
                raise ValueError(f"Unknown TTS mode: {mode}")

        try:
            tts_text = self._prepare_tts_text(text, min_token_len=60)

            # Print as unicode_escape so logs are stable even if the console ends up
            # using a non-UTF8 codepage.
            _head = tts_text[:100]
            _head_escape = _head.encode("unicode_escape", errors="backslashreplace").decode("ascii")
            print(
                f"[tts] Text to synthesize (unicode_escape): {_head_escape}",
                file=sys.stderr,
                flush=True,
            )

            _run_inference(tts_text)

        except RuntimeError as e:
            if "Kernel size can't be greater than actual input size" not in str(e):
                raise

            # Retry once by expanding more, keeping original content.
            speech_chunks = []
            tts_text = self._prepare_tts_text(text, min_token_len=120)
            _run_inference(tts_text)

        except ValueError as e:
            if "prompt wav is too short" in str(e).lower():
                raise ValueError(
                    f"提示音频太短，无法生成语音。请使用至少 1 秒的音频文件。原始错误: {e}"
                ) from e
            raise

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
        # Many Windows players / browser audio decoders behave poorly with
        # 32-bit float WAV (pcm_f32le). Convert to signed 16-bit PCM.
        speech_i16 = (speech * 32767.0).to(torch.int16)
        torchaudio.save(output_path, speech_i16, self._model.sample_rate, encoding="PCM_S", bits_per_sample=16)

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

        full_path = os.path.join(base, "cosyvoice2", relative_path)
        if not os.path.exists(full_path):
            print(f"[tts] WARNING: Prompt WAV not found: {full_path}, using default prompt")
            return default_prompt

        try:
            import torchaudio

            waveform, sr = torchaudio.load(full_path)
            duration = waveform.shape[1] / sr
            if duration < 0.5:
                print(
                    f"[tts] WARNING: Prompt WAV too short ({duration:.2f}s), using default prompt"
                )
                return default_prompt
        except Exception as e:
            print(
                f"[tts] WARNING: Failed to check prompt WAV duration: {e}, using default prompt"
            )
            return default_prompt

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
            f.write(struct.pack("<H", 1))  # PCM
            f.write(struct.pack("<H", 1))  # mono
            f.write(struct.pack("<I", sample_rate))
            f.write(struct.pack("<I", sample_rate * 2))
            f.write(struct.pack("<H", 2))
            f.write(struct.pack("<H", 16))
            f.write(b"data")
            f.write(struct.pack("<I", data_size))
            f.write(b"\x00" * data_size)


tts_engine = TTSEngine()
