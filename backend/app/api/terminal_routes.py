import uuid
import logging
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Any, Dict

from app.db.session import get_db
from app.db.models import Employee, AccessLog, AccessLogStatus
from app.services.biometric_service import generate_face_embedding, verify_face

# Setup logging
logger = logging.getLogger("uvicorn")

terminalRouter = APIRouter(prefix="/api/terminal", tags=["terminal"])

@terminalRouter.post("/access-verify")
async def verify_access(
    employee_uid: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Terminal Endpoint:
    Verifies an employee's identity based on their QR UUID and a real-time face photo.

    Args:
        employee_uid (str): The UUID string scanned from the QR code (via Form data).
        file (UploadFile): The image file captured by the terminal camera.
        db (Session): Database session dependency.

    Returns:
        Dict[str, Any]: A JSON response containing:
            - "access": "GRANTED" or "DENIED"
            - "reason": Error code if denied (e.g., "FACE_MISMATCH")
            - "name": Employee name (if granted)
            - "debug_distance": The calculated cosine distance (for debugging purposes)
    """

    logger.info(f"Processing verification request for UUID: {employee_uid}")

    # 1. UUID Validation
    try:
        uid_obj = uuid.UUID(employee_uid)
    except ValueError:
        logger.warning(f"Invalid UUID format received: {employee_uid}")
        return {"access": "DENIED", "reason": "INVALID_UUID_FORMAT"}

    # 2. Fetch Employee
    employee = db.query(Employee).filter(Employee.uuid == uid_obj).first()

    # Logic: If employee does not exist or is inactive -> Deny
    if not employee or not employee.is_active:
        logger.info(f"Access denied (QR): Unknown or inactive employee {employee_uid}")
        reason_msg = "QR_INVALID_OR_INACTIVE"
        log = AccessLog(
            status=AccessLogStatus.DENIED_QR,
            reason=reason_msg,
            employee_id=uid_obj if employee else None
        )
        db.add(log)
        db.commit()
        return {"access": "DENIED", "reason": reason_msg}

    logger.info(f"QR Validated for employee: {employee.name}. Starting biometric check.")

    # 3. Biometric Verification
    try:
        # Read file content safely
        photo_bytes = await file.read()

        if not photo_bytes:
            return {"access": "DENIED", "reason": "EMPTY_IMAGE_FILE"}

        # Generate embedding from the uploaded photo
        new_embedding = generate_face_embedding(photo_bytes)

        # Handle cases where no face is detected
        if new_embedding is None:
            reason_msg = "NO_FACE_DETECTED"
            logger.warning(f"Biometrics failed: {reason_msg} for {employee.name}")
            log = AccessLog(
                status=AccessLogStatus.DENIED_FACE,
                reason=reason_msg,
                employee_id=employee.uuid
            )
            db.add(log)
            db.commit()
            return {"access": "DENIED", "reason": reason_msg}

        # Compare with the stored biometric vector
        # Returns (is_match, distance)
        is_match, distance = verify_face(employee.embedding, new_embedding)

        # --- LOGGING THE DISTANCE FOR DEBUGGING ---
        logger.info(f"DEBUG: Comparison for {employee.name} | Distance: {distance:.4f} | Threshold: 0.3")

        if is_match:
            log = AccessLog(
                status=AccessLogStatus.GRANTED,
                reason="Verification successful",
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
            reason_msg = f"FACE_MISMATCH"
            logger.info(f"Access denied (Face): Distance {distance:.4f} too high for {employee.name}")
            log = AccessLog(
                status=AccessLogStatus.DENIED_FACE,
                reason=reason_msg,
                employee_id=employee.uuid
            )
            db.add(log)
            db.commit()
            return {
                "access": "DENIED",
                "reason": reason_msg,
                "debug_distance": distance
            }

    except Exception as e:
        logger.error(f"Biometric processing critical error: {str(e)}")
        db.rollback()
        return {"access": "DENIED", "reason": "PROCESSING_ERROR"}

    finally:

        await file.close()
