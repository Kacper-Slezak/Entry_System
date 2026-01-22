from datetime import datetime
import uuid
import logging
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Any, Dict
from fastapi.concurrency import run_in_threadpool

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
    Verifies employee identity using a 2FA flow (QR Code + Face Recognition).

    This endpoint validates the scanned QR UUID, checks the employee's status/expiry,
    and performs a biometric comparison between the live photo and the stored template.

    Args:
        employee_uid (str): The unique identifier decoded from the employee's QR code.
        file (UploadFile): Real-time image capture from the terminal camera.
        db (Session): Database session provided by the dependency injection.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - access (str): "GRANTED" if both factors pass, "DENIED" otherwise.
            - reason (str, optional): The cause of denial (e.g., "FACE_MISMATCH").
            - name (str, optional): Employee's full name if access is granted.

    Note:
        The biometric threshold is currently set to 0.3 for the Facenet512 model.
    """

    logger.info(f"Processing verification request for UUID: {employee_uid}")

    # 1. UUID Validation
    try:
        uid_obj = uuid.UUID(employee_uid)
    except ValueError:
        logger.warning(f"Invalid UUID format received: {employee_uid}")

        log = AccessLog(
            status=AccessLogStatus.DENIED_QR,
            employee_id=None,
            reason="QR_INVALID_FORMAT"
        )
        db.add(log)
        db.commit()

        return {"access": "DENIED", "reason": "QR_INVALID_FORMAT"}


    # 2. Fetch Employee from Database
    employee = db.query(Employee).filter(Employee.uuid == uid_obj).first()

    # Logic: If employee does not exist, is inactive, or expired -> Deny access
    if not employee or not employee.is_active or (employee.expires_at and datetime.now() > employee.expires_at):
        logger.info(f"Access denied (QR): Unknown or inactive employee {employee_uid}")
        log = AccessLog(
            status=AccessLogStatus.DENIED_QR,
            employee_id=uid_obj if employee else None,
            reason="QR_INVALID_OR_INACTIVE"
        )
        db.add(log)
        db.commit()
        return {"access": "DENIED", "reason": "QR_INVALID_OR_INACTIVE"}

    logger.info(f"QR Validated for employee: {employee.name}. Starting biometric check.")

    # 3. Biometric Verification
    try:
        # Read file content safely
        photo_bytes = await file.read()

        if not photo_bytes:
            return {"access": "DENIED", "reason": "EMPTY_IMAGE_FILE"}

        # Attempt to generate embedding from the uploaded photo
        try:
            new_embedding = await run_in_threadpool(generate_face_embedding, photo_bytes)

        except ValueError as e:
            # Check for multiple faces exception (Anti-Tailgating)
            if str(e) == "MULTIPLE_FACES_DETECTED":
                logger.warning(f"Access denied: Multiple faces detected for {employee.name}")

                log = AccessLog(
                    status=AccessLogStatus.DENIED_FACE,
                    employee_id=employee.uuid,
                    reason="MULTIPLE_FACES"
                )
                db.add(log)
                db.commit()

                # Return strict denial
                return {"access": "DENIED", "reason": "MULTIPLE_FACES"}
            else:
                # Other ValueErrors (e.g., no face found by DeepFace internally)
                new_embedding = None

        # Handle cases where no face is detected (or other minor errors)
        if new_embedding is None:
            logger.warning(f"Biometrics failed: No face detected for {employee.name}")
            log = AccessLog(
                status=AccessLogStatus.DENIED_FACE,
                employee_id=employee.uuid,
                reason="NO_FACE_DETECTED"
            )
            db.add(log)
            db.commit()
            return {"access": "DENIED", "reason": "NO_FACE_DETECTED"}

        # Compare with the stored biometric vector
        # Returns (is_match, distance)
        is_match, distance = verify_face(employee.embedding, new_embedding)

        # Log distance for debugging purposes
        logger.info(f"DEBUG: Comparison for {employee.name} | Distance: {distance:.4f} | Threshold: 0.3")

        if is_match:
            # SUCCESS: Face matches the QR owner
            log = AccessLog(
                status=AccessLogStatus.GRANTED,
                employee_id=employee.uuid,
                reason="SUCCESS"
            )
            db.add(log)
            db.commit()
            return {
                "access": "GRANTED",
                "name": employee.name,
                "message": f"Welcome, {employee.name}"
            }
        else:
            # FAILURE: Face does not match
            logger.info(f"Access denied (Face): Distance {distance:.4f} too high for {employee.name}")
            log = AccessLog(
                status=AccessLogStatus.DENIED_FACE,
                employee_id=employee.uuid,
                reason="FACE_MISMATCH"
            )
            db.add(log)
            db.commit()
            return {
                "access": "DENIED",
                "reason": "FACE_MISMATCH",
            }

    except Exception as e:
        logger.error(f"Biometric processing critical error: {str(e)}")

        try:
            error_log = AccessLog(
                status=AccessLogStatus.DENIED_FACE,
                employee_id=employee.uuid if employee else None,
                reason=f"SYS_ERR: {str(e)[:50]}"
            )
            db.add(error_log)
            db.commit() # Próbujemy zapisać ten jeden log
        except Exception as db_error:
            logger.error(f"Failed to log error to DB: {db_error}")
            db.rollback()

        return {"access": "DENIED", "reason": "PROCESSING_ERROR"}

    finally:
        # Ensure file is closed after reading to free resources
        await file.close()
