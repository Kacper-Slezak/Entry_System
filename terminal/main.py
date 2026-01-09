import cv2
import numpy as np
import time
import requests

# API Configuration
API_URL = "http://localhost:8000/api/v1/access-verify"

def capture_image():
    # Initialize camera and QR detector
    cap = cv2.VideoCapture(0)
    detector = cv2.QRCodeDetector()

    if not cap.isOpened():
        print("Error: Could not open video stream.")
        return

    last_scan_time = 0
    scan_interval = 5  # Seconds to wait between successful scans
    message = "Scan QR code to gain access"
    display_color = (255, 255, 255)

    print("Camera started. Press 'q' to exit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame from camera.")
            break

        current_time = time.time()

        if current_time - last_scan_time >= scan_interval:
            message = "Scan QR code"
            display_color = (255, 255, 255)

            data, bbox, _ = detector.detectAndDecode(frame)

            if data:
                print(f"QR Detected: {data}")
                last_scan_time = current_time
                message = "Processing..."

                _, img_encoded = cv2.imencode('.jpg', frame)

                try:
                    files = {
                        'file': ('capture.jpg', img_encoded.tobytes(), 'image/jpeg')
                    }
                    payload = {
                        'employee_uid': data
                    }

                    response = requests.post(API_URL, data=payload, files=files, timeout=10)

                    if response.status_code == 200:
                        result = response.json()
                        if result.get("access") == "GRANTED":
                            message = "ACCESS GRANTED"
                            display_color = (0, 255, 0) # Green
                        else:
                            message = "ACCESS DENIED"
                            display_color = (0, 0, 255) # Red
                    else:
                        message = f"Server Error: {response.status_code}"
                        display_color = (0, 165, 255) # Orange

                except Exception as e:
                    print(f"Connection Error: {e}")
                    message = "API Connection Error"
                    display_color = (0, 0, 255)

        cv2.rectangle(frame, (0, 0), (640, 50), display_color, -1)
        cv2.putText(frame, message, (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

        cv2.imshow('FaceOn Terminal', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Resource cleanup
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    capture_image()
