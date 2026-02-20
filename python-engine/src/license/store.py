"""AES-256-GCM encrypted license state storage.

License file: {APPDATA}/local-aI-dubber-desktop/license.dat
Key derived from device fingerprint via PBKDF2.
"""

import base64
import hashlib
import json
import os
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from src.license.fingerprint import get_fingerprint

SALT = b"zhiying_koubo_v1_salt_2024"
PBKDF2_ITERATIONS = 100_000


def _derive_key(fingerprint: str) -> bytes:
    """Derive AES-256 key from device fingerprint."""
    return hashlib.pbkdf2_hmac(
        "sha256", fingerprint.encode(), SALT, PBKDF2_ITERATIONS, dklen=32
    )


def _get_license_path() -> str:
    user_data = os.environ.get("APPDATA", os.path.expanduser("~"))
    license_dir = os.path.join(user_data, "local-aI-dubber-desktop")
    os.makedirs(license_dir, exist_ok=True)
    return os.path.join(license_dir, "license.dat")


class LicenseStore:
    def __init__(self):
        self._path = _get_license_path()
        self._fingerprint = get_fingerprint()
        self._key = _derive_key(self._fingerprint)

    def _encrypt(self, data: dict) -> str:
        """Encrypt dict to base64 string: nonce(12) + ciphertext + tag(16)."""
        plaintext = json.dumps(data, ensure_ascii=False).encode("utf-8")
        aesgcm = AESGCM(self._key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        return base64.b64encode(nonce + ciphertext).decode("ascii")

    def _decrypt(self, encoded: str) -> Optional[dict]:
        """Decrypt base64 string back to dict."""
        try:
            raw = base64.b64decode(encoded)
            nonce = raw[:12]
            ciphertext = raw[12:]
            aesgcm = AESGCM(self._key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return json.loads(plaintext.decode("utf-8"))
        except Exception:
            return None

    def read(self) -> dict:
        """Read and decrypt license state. Returns default trial state if missing/corrupt."""
        if not os.path.exists(self._path):
            return self._default_state()

        try:
            with open(self._path, "r", encoding="utf-8") as f:
                encoded = f.read().strip()
            data = self._decrypt(encoded)
            if data is None:
                # Decryption failed (different device or corrupted)
                return self._default_state()
            return data
        except Exception:
            return self._default_state()

    def write(self, state: dict) -> None:
        """Encrypt and write license state."""
        encoded = self._encrypt(state)
        with open(self._path, "w", encoding="utf-8") as f:
            f.write(encoded)

    def _default_state(self) -> dict:
        """Create and persist default trial state."""
        state = {
            "type": "trial",
            "usedTrialCount": 0,
            "activationCode": None,
            "activatedAt": None,
            "deviceFingerprint": self._fingerprint,
        }
        self.write(state)
        return state

    def get_status(self) -> dict:
        """Get license status in API response format."""
        state = self.read()
        used = state.get("usedTrialCount", 0)
        max_trial = 5
        is_activated = state.get("type") == "activated"

        code = state.get("activationCode")
        masked = None
        if code and len(code) >= 9:
            masked = code[:9] + "****-****"

        return {
            "type": state.get("type", "trial"),
            "used_trial_count": used,
            "max_trial_count": max_trial,
            "remaining_trial_count": max(0, max_trial - used) if not is_activated else 0,
            "activated_at": state.get("activatedAt"),
            "activation_code_masked": masked,
            "device_count": 1,
            "max_device_count": 2,
        }

    def consume_trial(self) -> dict:
        """Increment trial usage count."""
        state = self.read()
        if state.get("type") == "activated":
            return {"remaining_trial_count": 0, "trial_exhausted": False}

        state["usedTrialCount"] = state.get("usedTrialCount", 0) + 1
        self.write(state)

        remaining = max(0, 5 - state["usedTrialCount"])
        return {
            "remaining_trial_count": remaining,
            "trial_exhausted": remaining <= 0,
        }

    def activate(self, activation_code: str, server_response: dict) -> dict:
        """Store activation state after successful server verification."""
        state = self.read()
        state["type"] = "activated"
        state["activationCode"] = activation_code
        state["activatedAt"] = server_response.get("activated_at")
        state["deviceFingerprint"] = self._fingerprint
        self.write(state)
        return state

    def unbind(self) -> dict:
        """Reset to trial state after successful server unbind."""
        state = self._default_state()
        state["usedTrialCount"] = 5  # Keep trial exhausted
        self.write(state)
        return state


license_store = LicenseStore()
