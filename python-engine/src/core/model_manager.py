"""Model manager: download, verify, delete model files."""

import hashlib
import json
import os
from pathlib import Path
from typing import Optional

from src.storage.database import get_connection
from src.storage.settings_store import settings_store


class ModelVerifyResult:
    """Result of model verification."""
    def __init__(self, ok: bool, error_code: str = "", message: str = ""):
        self.ok = ok
        self.error_code = error_code
        self.message = message


class ModelManager:
    def get_models_dir(self) -> str:
        """Get the configured model storage directory."""
        settings = settings_store.read()
        models_dir = settings.get("modelStoragePath", "")
        if not models_dir:
            models_dir = str(Path.home() / "Documents" / "local-aI-dubber-desktop" / "models")
        os.makedirs(models_dir, exist_ok=True)
        return models_dir

    def get_model_path(self, model_name: str) -> str:
        """Get full path for a model directory."""
        return os.path.join(self.get_models_dir(), model_name)

    def verify_checksum(self, file_path: str, expected_hash: str, quick: bool = False) -> bool:
        """Verify file integrity via SHA-256.

        Args:
            file_path: Path to the file
            expected_hash: Expected SHA-256 hash (hex)
            quick: If True, only hash first 4KB (startup fast check, <200ms)
        """
        if not os.path.exists(file_path):
            return False

        h = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                if quick:
                    chunk = f.read(4096)
                    h.update(chunk)
                else:
                    while True:
                        chunk = f.read(8192)
                        if not chunk:
                            break
                        h.update(chunk)
        except OSError:
            return False

        return h.hexdigest() == expected_hash

    def verify_model_dir(self, model_dir: str, quick: bool = False) -> ModelVerifyResult:
        """Verify all files in a model directory against checksums.json.

        Returns ModelVerifyResult with error_code:
        - MODEL_CORRUPTED: checksums don't match
        - MODEL_DOWNLOAD_INCOMPLETE: files missing
        """
        if not os.path.isdir(model_dir):
            return ModelVerifyResult(False, "MODEL_NOT_FOUND", f"模型目录不存在: {model_dir}")

        checksums_path = os.path.join(model_dir, "checksums.json")
        if not os.path.exists(checksums_path):
            return ModelVerifyResult(True)  # No checksums file = skip verification

        try:
            with open(checksums_path, "r") as f:
                checksums = json.load(f)
        except (json.JSONDecodeError, OSError):
            return ModelVerifyResult(False, "MODEL_CORRUPTED", "checksums.json 文件损坏")

        for filename, expected in checksums.items():
            file_path = os.path.join(model_dir, filename)
            if not os.path.exists(file_path):
                return ModelVerifyResult(False, "MODEL_DOWNLOAD_INCOMPLETE", f"模型文件缺失: {filename}")

            hash_value = expected.replace("sha256:", "")
            if not self.verify_checksum(file_path, hash_value, quick=quick):
                if quick:
                    # Quick check failed, might be corrupted
                    return ModelVerifyResult(False, "MODEL_CORRUPTED", f"模型文件校验失败(快速): {filename}")
                return ModelVerifyResult(False, "MODEL_CORRUPTED", f"模型文件校验失败: {filename}")

        return ModelVerifyResult(True)

    def check_model_ready(self, voice_id: str, quick: bool = True) -> ModelVerifyResult:
        """Check if a voice model is downloaded and valid.

        Used before pipeline execution to ensure models are ready.
        Quick mode by default for fast startup checks (<200ms).
        In dev mode, missing models are not blocking (engines have fallbacks).
        """
        from src.utils.dev_mode import is_dev_mode

        # Check CosyVoice3 base model exists
        cosyvoice_dir = os.path.join(self.get_models_dir(), "cosyvoice3", "Fun-CosyVoice3-0.5B-2512")
        if not os.path.isdir(cosyvoice_dir):
            if is_dev_mode():
                print("[model_manager] DEV mode: CosyVoice3 model not found, engines will use fallback")
                return ModelVerifyResult(True)
            return ModelVerifyResult(
                False, "MODEL_NOT_FOUND",
                "CosyVoice3 基础模型未下载，请先下载 Fun-CosyVoice3-0.5B-2512 模型。"
            )

        conn = get_connection()
        row = conn.execute(
            "SELECT model_path, download_status FROM voice_models WHERE id = ?",
            (voice_id,),
        ).fetchone()

        if not row:
            if is_dev_mode():
                print(f"[model_manager] DEV mode: voice {voice_id} not in DB, engine will use fallback")
                return ModelVerifyResult(True)
            return ModelVerifyResult(False, "MODEL_NOT_FOUND", f"音色 {voice_id} 不存在")

        if row["download_status"] != "downloaded":
            if is_dev_mode():
                print(f"[model_manager] DEV mode: voice model not downloaded (status={row['download_status']}), engine will use fallback")
                return ModelVerifyResult(True)
            return ModelVerifyResult(False, "MODEL_NOT_FOUND", f"音色模型未下载，当前状态: {row['download_status']}")

        model_path = row["model_path"]
        if not model_path or not os.path.exists(model_path):
            # Model path missing, update status
            self.update_voice_status(voice_id, "not_downloaded", "", 0)
            return ModelVerifyResult(False, "MODEL_NOT_FOUND", "模型文件不存在，请重新下载")

        if os.path.isdir(model_path):
            return self.verify_model_dir(model_path, quick=quick)

        return ModelVerifyResult(True)

    def check_lipsync_model_ready(self) -> ModelVerifyResult:
        """Check if Wav2Lip model files are present.

        Checks for wav2lip_gan.pth in the wav2lip model directory.
        In dev mode, missing models are not blocking (engines have fallbacks).
        """
        from src.utils.dev_mode import is_dev_mode

        wav2lip_dir = os.path.join(self.get_models_dir(), "wav2lip")
        checkpoint = os.path.join(wav2lip_dir, "wav2lip_gan.pth")

        if not os.path.isfile(checkpoint):
            if is_dev_mode():
                print("[model_manager] DEV mode: Wav2Lip model not found, engine will use fallback")
                return ModelVerifyResult(True)
            return ModelVerifyResult(
                False, "MODEL_NOT_FOUND",
                "Wav2Lip 模型未找到，请下载 wav2lip_gan.pth 到模型目录。"
            )

        return ModelVerifyResult(True)

    def verify_on_download_complete(self, voice_id: str, model_path: str) -> ModelVerifyResult:
        """Full verification after download completes."""
        if os.path.isdir(model_path):
            result = self.verify_model_dir(model_path, quick=False)
        else:
            result = ModelVerifyResult(True)

        if result.ok:
            self.update_voice_status(voice_id, "downloaded", model_path, 1.0)
        else:
            self.update_voice_status(voice_id, "error", model_path, 0)

        return result

    def update_voice_status(self, voice_id: str, status: str, model_path: str = "", progress: float = 0) -> None:
        """Update voice model download status in database."""
        conn = get_connection()
        if model_path:
            conn.execute(
                "UPDATE voice_models SET download_status = ?, model_path = ?, download_progress = ? WHERE id = ?",
                (status, model_path, progress, voice_id),
            )
        else:
            conn.execute(
                "UPDATE voice_models SET download_status = ?, download_progress = ? WHERE id = ?",
                (status, progress, voice_id),
            )
        conn.commit()

    def delete_model_files(self, voice_id: str) -> bool:
        """Delete downloaded model files for a voice, keep DB record."""
        conn = get_connection()
        row = conn.execute("SELECT model_path FROM voice_models WHERE id = ?", (voice_id,)).fetchone()
        if not row or not row["model_path"]:
            return False

        model_path = row["model_path"]
        if os.path.isdir(model_path):
            import shutil
            shutil.rmtree(model_path, ignore_errors=True)
        elif os.path.isfile(model_path):
            os.remove(model_path)

        self.update_voice_status(voice_id, "not_downloaded", "", 0)
        return True


model_manager = ModelManager()
