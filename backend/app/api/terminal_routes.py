import uuid
import logging
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, Dict

from app.db.session import get_db
from app.db.models import Employee, AccessLog, AccessLogStatus
from app.services.biometric_service import generate_face_embedding, verify_face

# Setup logging for better traceability
logger = logging.getLogger(__name__)

terminalRouter = APIRouter(prefix="/api/terminal", tags=["terminal"])

@terminalRouter.post("/access-verify")
async def verify_access(
    employee_uid: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Terminal Endpoint:
    Verifies an employee based on their QR UUID and a real-time face photo.
    """

    # 1. UUID Validation
    try:
        uid_obj = uuid.UUID(employee_uid)
    except ValueError:
        return {"access": "DENIED", "reason": "INVALID_UUID_FORMAT"}

    # 2. Fetch Employee
    employee = db.query(Employee).filter(Employee.uuid == uid_obj).first()

    # Logic: No employee or inactive -> Deny (QR failure)
    if not employee or not employee.is_active:
        log = AccessLog(
            status=AccessLogStatus.DENIED_QR,
            employee_id=uid_obj if employee else None
        )
        db.add(log)
        db.commit()
        return {"access": "DENIED", "reason": "QR_INVALID_OR_INACTIVE"}

    # 3. Biometric Verification
    try:
        # Read file content safely
        photo_bytes = await file.read()

        # Check if the file is empty
        if not photo_bytes:
            return {"access": "DENIED", "reason": "EMPTY_IMAGE_FILE"}

        # Generate embedding from the uploaded photo
        new_embedding = generate_face_embedding(photo_bytes)

        # Handle cases where no face is detected in the photo
        if new_embedding is None:
            log = AccessLog(
                status=AccessLogStatus.DENIED_FACE,
                employee_id=employee.uuid
            )
            db.add(log)
            db.commit()
            return {"access": "DENIED", "reason": "NO_FACE_DETECTED"}

        # Compare with the stored biometric vector
        is_match = verify_face(employee.embedding, new_embedding)

        if is_match:
            # SUCCESS
            log = AccessLog(
                status=AccessLogStatus.GRANTED,
                employee_id=employee.uuid
            )
            db.add(log)
            db.commit()
            return {
                "access": "GRANTED",
                "name": employee.name,
                "message": f"Welcome, {employee.name}"
            }
        else:
            # FACE DOES NOT MATCH
            log = AccessLog(
                status=AccessLogStatus.DENIED_FACE,
                employee_id=employee.uuid
            )
            db.add(log)
            db.commit()
            return {"access": "DENIED", "reason": "FACE_MISMATCH"}

    except Exception as e:
        # Log the actual error for debugging
        logger.error(f"Biometric processing error: {str(e)}")
        db.rollback()
        return {"access": "DENIED", "reason": "PROCESSING_ERROR"}

    finally:
        # Ensure file is closed after reading
        await file.close()
