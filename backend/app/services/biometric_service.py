from deepface import DeepFace
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
