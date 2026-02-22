"""Wav2Lip lipsync engine: real inference with dev mode fallback.

Lazy-loads the Wav2Lip model on first use. Uses OpenCV for video I/O,
Haar cascade for face detection, and the Wav2Lip fork's audio/mel pipeline.
"""

import os
import sys
import uuid
import shutil
import subprocess
import threading
from typing import Optional

import numpy as np

from src.core.gpu_detector import gpu_detector
from src.core.face_cache import face_cache
from src.utils.dev_mode import is_dev_mode


# Wav2Lip constants
_IMG_SIZE = 96
_MEL_STEP_SIZE = 16
_BATCH_SIZE = 128


class LipsyncEngine:
    def __init__(self):
        self._model = None
        self._device: str = "cpu"
        self._lock = threading.Lock()
        self._face_cascade = None
        self._wav2lip_ready = False

    def _get_model_dir(self) -> str:
        """Resolve Wav2Lip model directory from settings."""
        from src.storage.settings_store import settings_store
        settings = settings_store.read()
        base = settings.get("modelStoragePath", "")
        if not base:
            base = os.path.join(
                os.path.expanduser("~"), "Documents", "local-aI-dubber-desktop", "models"
            )
        return os.path.join(base, "wav2lip")

    def _setup_wav2lip_path(self) -> None:
        """Add Wav2Lip third_party to sys.path."""
        if self._wav2lip_ready:
            return
        wav2lip_root = os.path.join(
            os.path.dirname(__file__), "..", "..", "third_party", "Wav2Lip"
        )
        wav2lip_root = os.path.normpath(wav2lip_root)
        if wav2lip_root not in sys.path:
            sys.path.insert(0, wav2lip_root)
        self._wav2lip_ready = True

    def _ensure_model(self) -> None:
        """Lazy-load Wav2Lip model (thread-safe)."""
        if self._model is not None:
            return

        with self._lock:
            if self._model is not None:
                return

            import torch

            model_dir = self._get_model_dir()
            checkpoint_path = os.path.join(model_dir, "wav2lip_gan.pth")
            if not os.path.isfile(checkpoint_path):
                raise RuntimeError(
                    f"Wav2Lip 模型未找到: {checkpoint_path}\n"
                    "请下载 wav2lip_gan.pth 到模型目录。"
                )

            self._device = gpu_detector.get_inference_device()

            # Setup Wav2Lip imports
            self._setup_wav2lip_path()
            from models import Wav2Lip as Wav2LipModel

            print(f"[lipsync] Loading Wav2Lip model from {checkpoint_path} on {self._device}")

            # Load checkpoint
            if self._device == "cuda":
                checkpoint = torch.load(checkpoint_path, weights_only=False)
            else:
                checkpoint = torch.load(
                    checkpoint_path, map_location="cpu", weights_only=False
                )

            model = Wav2LipModel()
            state = checkpoint["state_dict"]
            # Remove "module." prefix from DataParallel keys
            new_state = {k.replace("module.", ""): v for k, v in state.items()}
            model.load_state_dict(new_state)
            model = model.to(self._device).eval()

            self._model = model

            # Load face cascade for detection
            cascade_path = os.path.join(model_dir, "haarcascade_frontalface_default.xml")
            if not os.path.isfile(cascade_path):
                # Fallback to OpenCV's bundled cascade
                import cv2
                cascade_path = os.path.join(
                    os.path.dirname(cv2.__file__), "data",
                    "haarcascade_frontalface_default.xml"
                )
            if os.path.isfile(cascade_path):
                import cv2
                self._face_cascade = cv2.CascadeClassifier(cascade_path)

            print(f"[lipsync] Model loaded on {self._device}")

    def load_model(self, model_path: str, device: Optional[str] = None) -> None:
        """Load Wav2Lip model."""
        self._device = device or gpu_detector.get_inference_device()
        try:
            self._ensure_model()
        except Exception as e:
            if is_dev_mode():
                print(f"[lipsync] DEV mode: skip model loading ({e})")
                return
            raise

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
            Path to the lip-synced video (MP4 with audio)
        """
        if not output_dir:
            output_dir = os.path.join(os.environ.get("TEMP", "/tmp"), "zhiying_lipsync")
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, f"lipsync_{uuid.uuid4().hex[:8]}.mp4")

        if is_dev_mode():
            # Dev mode: try real lipsync, fallback to copy/placeholder if model unavailable
            try:
                self._ensure_model()
            except Exception as e:
                print(f"[lipsync] DEV mode: model not available ({e}), using fallback")
                if video_path and os.path.exists(video_path):
                    shutil.copy2(video_path, output_path)
                else:
                    print(f"[lipsync] DEV fallback: creating placeholder video (no source video)")
                    self._create_placeholder_video(output_path, audio_path)
                print(f"[lipsync] DEV fallback: {output_path}")
                return output_path

        if not video_path or not os.path.exists(video_path):
            raise RuntimeError(f"数字人视频文件不存在: {video_path or '(空路径)'}")

        self._ensure_model()

        import cv2
        import torch

        # Setup Wav2Lip audio module
        self._setup_wav2lip_path()
        import audio as wav2lip_audio

        # 1. Read video frames
        full_frames, fps = self._read_video_frames(video_path)
        if not full_frames:
            raise RuntimeError(f"无法读取视频帧: {video_path}")

        print(f"[lipsync] Video: {len(full_frames)} frames at {fps} fps")

        # 2. Generate mel spectrogram from audio
        wav = wav2lip_audio.load_wav(audio_path, 16000)
        mel = wav2lip_audio.melspectrogram(wav)

        if np.isnan(mel.reshape(-1)).sum() > 0:
            raise RuntimeError("音频 mel 频谱包含 NaN，请检查音频文件。")

        # Pad mel if shorter than one chunk (avoids Conv kernel size error)
        if mel.shape[1] < _MEL_STEP_SIZE:
            pad_width = _MEL_STEP_SIZE - mel.shape[1]
            mel = np.pad(mel, ((0, 0), (0, pad_width)), mode="constant", constant_values=0)
            print(f"[lipsync] Mel padded from {mel.shape[1] - pad_width} to {mel.shape[1]} frames")

        # Split mel into chunks
        mel_chunks = []
        mel_idx_multiplier = 80.0 / fps
        i = 0
        while True:
            start_idx = int(i * mel_idx_multiplier)
            if start_idx + _MEL_STEP_SIZE > mel.shape[1]:
                mel_chunks.append(mel[:, mel.shape[1] - _MEL_STEP_SIZE:])
                break
            mel_chunks.append(mel[:, start_idx: start_idx + _MEL_STEP_SIZE])
            i += 1

        print(f"[lipsync] Mel chunks: {len(mel_chunks)}")

        # 3. Loop video frames if audio is longer than video
        if len(full_frames) < len(mel_chunks):
            original_len = len(full_frames)
            while len(full_frames) < len(mel_chunks):
                full_frames.extend(full_frames[:original_len])
            full_frames = full_frames[:len(mel_chunks)]
        else:
            full_frames = full_frames[:len(mel_chunks)]

        # 4. Face detection (with caching)
        face_det_results = self._detect_faces(video_path, full_frames)

        # 5. Run Wav2Lip inference in batches
        temp_avi = os.path.join(output_dir, f"temp_{uuid.uuid4().hex[:6]}.avi")
        frame_h, frame_w = full_frames[0].shape[:2]
        out_writer = cv2.VideoWriter(
            temp_avi,
            cv2.VideoWriter_fourcc(*"DIVX"),
            fps,
            (frame_w, frame_h),
        )

        gen = self._datagen(full_frames, mel_chunks, face_det_results)
        for img_batch, mel_batch, frames, coords in gen:
            img_batch = torch.FloatTensor(
                np.transpose(img_batch, (0, 3, 1, 2))
            ).to(self._device)
            mel_batch = torch.FloatTensor(
                np.transpose(mel_batch, (0, 3, 1, 2))
            ).to(self._device)

            with torch.no_grad():
                pred = self._model(mel_batch, img_batch)

            pred = pred.cpu().numpy().transpose(0, 2, 3, 1) * 255.0

            for p, f, c in zip(pred, frames, coords):
                y1, y2, x1, x2 = c
                p = cv2.resize(p.astype(np.uint8), (x2 - x1, y2 - y1))
                f[y1:y2, x1:x2] = p
                out_writer.write(f)

        out_writer.release()

        # 6. Mux video + audio with FFmpeg
        self._mux_audio(temp_avi, audio_path, output_path, fps)

        # Cleanup temp file
        try:
            os.remove(temp_avi)
        except OSError:
            pass

        print(f"[lipsync] Output: {output_path}")
        return output_path

    def _read_video_frames(self, video_path: str) -> tuple:
        """Read all frames from video. Returns (frames_list, fps)."""
        import cv2
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()
        return frames, fps

    def _detect_faces(self, video_path: str, frames: list) -> list:
        """Detect faces in frames, using cache when available."""
        import cv2

        # Try cache first
        cached = face_cache.get(video_path)
        if cached and len(cached) >= len(frames):
            print(f"[lipsync] Using cached face detection ({len(cached)} frames)")
            results = []
            for i, box in enumerate(cached[:len(frames)]):
                y1, y2, x1, x2 = box
                face = frames[i][y1:y2, x1:x2]
                results.append([face, (y1, y2, x1, x2)])
            return results

        print(f"[lipsync] Detecting faces in {len(frames)} frames...")

        if self._face_cascade is None:
            cascade_path = os.path.join(
                os.path.dirname(cv2.__file__), "data",
                "haarcascade_frontalface_default.xml"
            )
            self._face_cascade = cv2.CascadeClassifier(cascade_path)

        pads = [0, 10, 0, 0]
        pady1, pady2, padx1, padx2 = pads
        boxes = []
        results = []

        for frame in frames:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self._face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )

            if len(faces) > 0:
                x, y, w, h = faces[0]
                x1 = max(0, x - padx1)
                x2 = min(frame.shape[1], x + w + padx2)
                y1 = max(0, y - pady1)
                y2 = min(frame.shape[0], y + h + pady2)
                boxes.append([y1, y2, x1, x2])
            else:
                # If no face found, use center crop as fallback
                h, w = frame.shape[:2]
                size = min(h, w) // 2
                cy, cx = h // 2, w // 2
                y1 = max(0, cy - size // 2)
                y2 = min(h, cy + size // 2)
                x1 = max(0, cx - size // 2)
                x2 = min(w, cx + size // 2)
                boxes.append([y1, y2, x1, x2])

        # Smooth bounding boxes
        boxes_arr = np.array(boxes)
        for i in range(len(boxes_arr)):
            window_start = max(0, i - 2)
            window_end = min(len(boxes_arr), i + 3)
            boxes_arr[i] = np.mean(boxes_arr[window_start:window_end], axis=0).astype(int)

        # Build results
        for i, (y1, y2, x1, x2) in enumerate(boxes_arr):
            face = frames[i][y1:y2, x1:x2]
            results.append([face, (int(y1), int(y2), int(x1), int(x2))])

        # Cache the boxes
        face_cache.put(video_path, boxes_arr.tolist())

        return results

    def _datagen(self, frames, mels, face_det_results):
        """Generate batches for Wav2Lip inference."""
        import cv2

        img_batch, mel_batch, frame_batch, coords_batch = [], [], [], []

        for i, m in enumerate(mels):
            idx = i % len(frames)
            frame_to_save = frames[idx].copy()
            face, coords = face_det_results[idx]
            face = face.copy()

            face = cv2.resize(face, (_IMG_SIZE, _IMG_SIZE))
            img_batch.append(face)
            mel_batch.append(m)
            frame_batch.append(frame_to_save)
            coords_batch.append(coords)

            if len(img_batch) >= _BATCH_SIZE:
                img_batch = np.asarray(img_batch)
                mel_batch = np.asarray(mel_batch)

                img_masked = img_batch.copy()
                img_masked[:, _IMG_SIZE // 2:] = 0

                img_batch = np.concatenate((img_masked, img_batch), axis=3) / 255.0
                mel_batch = np.reshape(
                    mel_batch,
                    [len(mel_batch), mel_batch.shape[1], mel_batch.shape[2], 1],
                )

                yield img_batch, mel_batch, frame_batch, coords_batch
                img_batch, mel_batch, frame_batch, coords_batch = [], [], [], []

        if len(img_batch) > 0:
            img_batch = np.asarray(img_batch)
            mel_batch = np.asarray(mel_batch)

            img_masked = img_batch.copy()
            img_masked[:, _IMG_SIZE // 2:] = 0

            img_batch = np.concatenate((img_masked, img_batch), axis=3) / 255.0
            mel_batch = np.reshape(
                mel_batch,
                [len(mel_batch), mel_batch.shape[1], mel_batch.shape[2], 1],
            )

            yield img_batch, mel_batch, frame_batch, coords_batch

    def _mux_audio(self, video_path: str, audio_path: str, output_path: str, fps: float) -> None:
        """Combine video and audio using FFmpeg."""
        from src.storage.settings_store import settings_store

        settings = settings_store.read()
        ffmpeg_path = settings.get("ffmpeg_path") or "ffmpeg"

        cmd = [
            ffmpeg_path, "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-r", str(fps),
            "-movflags", "+faststart",
            "-shortest",
            output_path,
        ]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300,
            )
            if result.returncode != 0:
                print(f"[lipsync] FFmpeg mux error: {result.stderr[:500]}")
                raise RuntimeError(f"FFmpeg 合成失败: {result.stderr[:200]}")
        except FileNotFoundError:
            raise RuntimeError("FFmpeg 未找到，请安装 FFmpeg 并添加到 PATH。")

    def _create_placeholder_video(self, output_path: str, audio_path: str) -> None:
        """Create a placeholder video with audio for dev mode testing."""
        import subprocess

        from src.storage.settings_store import settings_store

        settings = settings_store.read()
        ffmpeg_path = settings.get("ffmpeg_path") or "ffmpeg"

        cmd = [
            ffmpeg_path, "-y",
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
                print(f"[lipsync] FFmpeg placeholder error: {result.stderr[:500]}")
                raise RuntimeError(f"创建占位视频失败: {result.stderr[:200]}")
        except FileNotFoundError:
            raise RuntimeError("FFmpeg 未找到，请安装 FFmpeg 并添加到 PATH。")

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
                print("[lipsync] Model unloaded")


lipsync_engine = LipsyncEngine()
