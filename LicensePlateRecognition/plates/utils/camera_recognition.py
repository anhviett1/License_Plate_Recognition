# camera_recognition.py

import cv2
import pytesseract
from plates.models import LicensePlate
from django.core.wsgi import get_wsgi_application
import os
import django
from ..utils.google_sheets import save_to_google_sheets
from ..utils.discord_notification import send_to_discord 

# Cấu hình Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LicensePlateRecognition.settings')
django.setup()

def detect_license_plate(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    edged = cv2.Canny(gray, 30, 200)

    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

    license_plate = None
    for contour in contours:
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.018 * peri, True)

        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(contour)
            license_plate = gray[y:y + h, x:x + w]
            break

    if license_plate is None:
        return None

    text = pytesseract.image_to_string(license_plate, config='--psm 8')
    plate_number = text.strip()

    if plate_number:
        print("Biển số nhận diện:", plate_number)
        plate, created = LicensePlate.objects.get_or_create(plate_number=plate_number)
        if created:
            save_to_google_sheets(plate_number)
            send_to_discord(plate_number)
    return plate_number

def main():
    cap = cv2.VideoCapture(0)  # 0 là camera mặc định

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        plate_number = detect_license_plate(frame)
        if plate_number:
            cv2.putText(frame, plate_number, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("Camera Feed", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
