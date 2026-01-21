from deepface import DeepFace
from scipy.spatial.distance import cosine
import numpy as np
import cv2
import logging

# Configuration for DeepFace
# RetinaFace is slower but much more accurate for detection.
# Facenet512 provides 512-dimensional embeddings
DETECTOR_BACKEND = 'retinaface'
MODEL_NAME = 'Facenet512'

def generate_face_embedding(file_bytes: bytes) -> list:
    """
    Generates a facial embedding vector for the given image bytes using DeepFace.

    Args:
        file_bytes (bytes): The raw bytes of the image file (e.g., from an upload).

    Returns:
        list: A list of floats representing the facial embedding if a face is detected.
        None: If no face is detected or an error occurs.
    """
    try:
        # Convert bytes to numpy array
        np_array = np.frombuffer(file_bytes, np.uint8)
        img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        # Generate embedding
        # enforce_detection=True raises ValueError if no face is found
        embedding_obj = DeepFace.represent(
            img_path=img,
            model_name=MODEL_NAME,
            detector_backend=DETECTOR_BACKEND,
            enforce_detection=True
        )
        if len(embedding_obj) > 1:
            raise ValueError("MULTIPLE_FACES_DETECTED")
        return embedding_obj[0]["embedding"]

    except ValueError as e:
        if str(e) == "MULTIPLE_FACES_DETECTED":
            raise e
        return None
    except Exception as e:
        logging.error(f"DeepFace processing error: {e}")
        return None


def verify_face(embedding_db: list, embedding_new: list, threshold: float = 0.3) -> tuple[bool, float]:
    """
    Compares two facial embedding vectors using Cosine Similarity.

    Args:
        embedding_db (list): The reference embedding stored in the PostgreSQL database.
        embedding_new (list): The new embedding generated from the terminal's camera.
        threshold (float): Similarity limit. Lower values increase security but may
                           increase False Rejection Rate. Defaults to 0.3.

    Returns:
        tuple[bool, float]:
            - bool: True if the calculated distance is below the threshold.
            - float: The raw cosine distance between the two vectors.
    """
    if embedding_db is None or embedding_new is None:
        return False, 1.0

    # Calculate cosine distance (lower means more similar)
    distance = cosine(embedding_db, embedding_new)

    is_match = distance < threshold
    return is_match, distance
