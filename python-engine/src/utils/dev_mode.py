"""Dev mode detection utility.

When DEV_MODE=1 or NODE_ENV=development:
- License checks are skipped (unlimited generation)
- No watermark is added to generated videos
- Trial count is not consumed
"""

import os


def is_dev_mode() -> bool:
    """Check if the application is running in development mode."""
    if os.environ.get("DEV_MODE", "").strip() == "1":
        return True
    if os.environ.get("NODE_ENV", "").strip().lower() == "development":
        return True
    return False
