# plate_recognition.py

import cv2
import pytesseract
from plates.models import LicensePlate
from django.core.wsgi import get_wsgi_application
import os
import django

# Cấu hình Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LicensePlateRecognition.settings')
django.setup()

def detect_license_plate(image_path):
    # Đọc ảnh từ file
    image = cv2.imread(image_path)
    if image is None:
        print("Không thể đọc ảnh từ đường dẫn:", image_path)
        return

    # Chuyển sang ảnh xám
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Tiền xử lý ảnh (lọc nhiễu, làm mịn, ...)
    gray = cv2.bilateralFilter(gray, 11, 17, 17)

    # Phát hiện các cạnh
    edged = cv2.Canny(gray, 30, 200)

    # Tìm các đường viền
    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

    # Tìm biển số
    license_plate = None
    for contour in contours:
        # Xấp xỉ đa giác
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.018 * peri, True)

        # Biển số thường có 4 đỉnh
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(contour)
            license_plate = gray[y:y + h, x:x + w]
            break

    if license_plate is None:
        print("Không tìm thấy biển số trong ảnh.")
        return

    # Nhận diện ký tự trên biển số
    text = pytesseract.image_to_string(license_plate, config='--psm 8')
    plate_number = text.strip()

    if plate_number:
        print("Biển số nhận diện:", plate_number)
        # Lưu vào cơ sở dữ liệu
        plate, created = LicensePlate.objects.get_or_create(plate_number=plate_number)
        if created:
            # Tự động ghi vào Google Sheets và gửi Discord
            from google_sheets import save_to_google_sheets
            #from discord_notification import send_to_discord
            save_to_google_sheets(plate_number)
           # send_to_discord(plate_number)
    else:
        print("Không nhận diện được biển số.")
