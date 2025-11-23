import os
import shutil
import time
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger("cleanup_service")

def cleanup_stale_files():
    now = time.time()
    timeout_seconds = settings.SESSION_TIMEOUT_MINUTES * 60
    upload_dir = settings.UPLOAD_DIR

    if not os.path.exists(upload_dir):
        return

    for session_id in os.listdir(upload_dir):
        session_path = os.path.join(upload_dir, session_id)
        
        if not os.path.isdir(session_path):
            continue

        last_modified = os.path.getmtime(session_path)
        if now - last_modified > timeout_seconds:
            try:
                logger.info(f"Cleaning up stale session: {session_id}")
                shutil.rmtree(session_path)
                
            except Exception as e:
                logger.error(f"Error cleaning {session_id}: {e}")