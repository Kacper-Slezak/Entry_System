from deepface import DeepFace
from scipy.spatial.distance import cosine
import numpy as np
import cv2

def generate_face_embedding(file_bytes: bytes) -> list:
    """
    Generates a facial embedding for the given image using DeepFace.
    """
    np_array = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
    embedding = DeepFace.represent(img_path=img)[0]["embedding"]
    return embedding


def verify_face(embedding_db: list, embedding_new: list, threshold: float = 0.4) -> bool:
    """
    Compares two face embedding vectors.
    Returns True if they are similar enough (distance < threshold).
    For DeepFace (VGG-Face) a threshold of 0.4 is typically suitable for cosine distance.
    """
    if embedding_db is None or embedding_new is None:
        return False

    distance = cosine(embedding_db, embedding_new)
    return distance < threshold
