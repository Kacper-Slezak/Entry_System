# Entry System - Biometric 2FA Access Control

## Project Overview

This system provides a high-security access control solution using Two-Factor Authentication (2FA). It is designed to verify identities by combining dynamic QR code scanning with facial recognition technology. The project was developed as part of the Software Engineering (IO) course to demonstrate integration between backend APIs, biometric services, and real-time terminal processing.

## Key Functionalities

* **Identity Verification (2FA):** The system first validates a unique UUID from a scanned QR code and then performs a biometric comparison using a live camera feed.
* **Biometric Analysis:** Facial verification is powered by the Facenet512 model, utilizing a 512-dimensional embedding vector with a distance threshold set to 0.3 for precision.
* **Admin Management:** A dedicated dashboard allows administrators to create employee profiles, update biometric data, and manage account expiration.
* **Automated Delivery:** Upon employee creation, the system automatically generates a QR code and sends it to the user via an asynchronous email task.
* **Access Logging:** Every entry attempt (granted or denied) is logged in the database with specific error reasons like `FACE_MISMATCH` or `QR_INVALID`.

## Technical Stack

* **Backend:** FastAPI (Python 3.11/3.13).
* **Database:** PostgreSQL managed via SQLAlchemy ORM.
* **Biometrics:** DeepFace and OpenCV.
* **DevOps:** Docker and Docker Compose for containerized deployment.
* **CI/CD:** GitHub Actions for automated testing on every pull request.

## Installation and Startup

### Backend & Database

1. Configure your environment variables in a `.env` file (Database credentials, Mail server settings).
2. Build and run the containers:

```bash
docker compose up --build -d

```

1. Access the API documentation at `http://localhost:8000/docs`.

### Terminal

1. Ensure you have a working camera and the required libraries installed locally (OpenCV, Requests).
2. Run the terminal application:

```bash
python terminal/main.py

```

## Testing Suite

The project includes a robust testing framework using `pytest`. The suite covers:

* **Admin Routes:** Creation, deletion, and profile update logic (including email conflict checks).
* **Terminal Routes:** Access verification for active, inactive, and expired accounts.
* **Biometric Mocks:** Tests use mocked embeddings to ensure consistent results during CI/CD without requiring local AI model weights.

To run tests manually:

```bash
PYTHONPATH=./backend pytest backend/tests

```

## Security Implementation

* **JWT Authentication:** Admin endpoints are protected by JSON Web Tokens.
* **Dependency Overrides:** The testing environment uses security overrides to simulate an active admin session.
* **Data Integrity:** The system performs UUID format validation and checks for unique email constraints before committing changes.
