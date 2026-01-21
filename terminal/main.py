# Entry_System/terminal/main.py
import cv2
import numpy as np
import time
import requests

# API Configuration
API_URL = "http://localhost:8000/api/terminal/access-verify"

def capture_image():
    cap = cv2.VideoCapture(0)
    detector = cv2.QRCodeDetector()

    if not cap.isOpened():
        print("Error: Could not open video stream.")
        return

    last_scan_time = 0
    scan_interval = 5
    message = "Scan QR code"
    sub_message = ""
    display_color = (255, 255, 255)

    print("Camera started. Press 'q' to exit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        current_time = time.time()

        if current_time - last_scan_time > 3 and message != "Scan QR code":
             message = "Scan QR code"
             sub_message = ""
             display_color = (255, 255, 255)

        if current_time - last_scan_time >= scan_interval:
            data, bbox, _ = detector.detectAndDecode(frame)

            if data:
                print(f"QR Detected: {data}")
                last_scan_time = current_time
                message = "Processing..."
                sub_message = "Wait..."
                display_color = (255, 255, 0) # Yellow


                cv2.putText(frame, message, (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, display_color, 2)
                cv2.imshow('FaceOn Terminal', frame)
                cv2.waitKey(1)

                _, img_encoded = cv2.imencode('.jpg', frame)

                try:
                    files = {'file': ('capture.jpg', img_encoded.tobytes(), 'image/jpeg')}
                    payload = {'employee_uid': data}

                    response = requests.post(API_URL, data=payload, files=files, timeout=10)

                    if response.status_code == 200:
                        result = response.json()
                        access = result.get("access")
                        reason = result.get("reason", "")

                        if access == "GRANTED":
                            message = "ACCESS GRANTED"
                            sub_message = result.get("name", "")
                            display_color = (0, 255, 0)
                        else:
                            message = "ACCESS DENIED"
                            display_color = (0, 0, 255)
                            if reason == "NO_FACE_DETECTED":
                                sub_message = "NO_FACE_DETECTED!"
                            elif reason == "FACE_MISMATCH":
                                sub_message = "FACE_MISMATCH!"
                            elif reason == "MULTIPLE_FACES":
                                sub_message = "ONE PERSON ONLY!"
                            elif reason == "QR_INVALID_OR_INACTIVE":
                                sub_message = "QR_INVALID_OR_INACTIVE!"
                            else:
                                sub_message = reason
                    else:
                        message = "Server Error"
                        sub_message = str(response.status_code)
                        display_color = (0, 165, 255)

                except Exception as e:
                    print(f"Connection Error: {e}")
                    message = "API Error"
                    sub_message = "Check connection"
                    display_color = (0, 0, 255)

        cv2.rectangle(frame, (0, 0), (640, 80), (0,0,0), -1)
        cv2.putText(frame, message, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, display_color, 2)
        cv2.putText(frame, sub_message, (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.6, display_color, 1)

        cv2.imshow('FaceOn Terminal', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    capture_image()
