import os
import uuid
import time
import logging

from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter()
logger = logging.getLogger(__name__)

UPLOAD_DIR = "app/data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Allowed file types (optional but recommended)
ALLOWED_EXTENSIONS = {".txt", ".csv", ".json"}


# -----------------------------
# UPLOAD FILE (PRO LOGGING)
# -----------------------------
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    request_id = str(uuid.uuid4())
    start_time = time.time()

    logger.info(f"[{request_id}] [UPLOAD START]")
    logger.info(f"[{request_id}] Filename: {file.filename}")
    logger.info(f"[{request_id}] Content-Type: {file.content_type}")

    try:
        # -----------------------------
        # Validate filename
        # -----------------------------
        if not file.filename:
            logger.warning(f"[{request_id}] Missing filename")
            raise HTTPException(status_code=400, detail="File must have a name")

        # -----------------------------
        # Validate extension
        # -----------------------------
        _, ext = os.path.splitext(file.filename)

        if ext.lower() not in ALLOWED_EXTENSIONS:
            logger.warning(f"[{request_id}] Invalid file type: {ext}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {ALLOWED_EXTENSIONS}"
            )

        # -----------------------------
        # Unique filename (avoid overwrite)
        # -----------------------------
        unique_name = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, unique_name)

        logger.info(f"[{request_id}] Saving to: {file_path}")

        # -----------------------------
        # Save file
        # -----------------------------
        content = await file.read()

        with open(file_path, "wb") as f:
            f.write(content)

        file_size = len(content)

        duration = round(time.time() - start_time, 3)

        logger.info(f"[{request_id}] Upload successful")
        logger.info(f"[{request_id}] Size: {file_size} bytes")
        logger.info(f"[{request_id}] Time: {duration}s")

        return {
            "request_id": request_id,
            "file_path": file_path,
            "file_size": file_size
        }

    except HTTPException as e:
        logger.warning(f"[{request_id}] Client error: {e.detail}")
        raise e

    except Exception as e:
        duration = round(time.time() - start_time, 3)

        logger.error(
            f"[{request_id}] Upload failed after {duration}s: {str(e)}",
            exc_info=True
        )

        raise HTTPException(status_code=500, detail="File upload failed")