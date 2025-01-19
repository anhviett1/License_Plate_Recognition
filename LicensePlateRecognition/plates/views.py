import asyncio
from django.shortcuts import render, get_object_or_404
import json, cv2, numpy as np
from django.http import JsonResponse, StreamingHttpResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from .models import LicensePlate
from .utils.plate_recognition import detect_license_plate
from .utils.google_sheets import save_to_google_sheets
from .utils.discord_notification import send_message, send_to_discord


def license_plate_list(request):
    query = request.GET.get('q', '')
    plates = LicensePlate.objects.filter(plate_number__icontains=query) if query else LicensePlate.objects.all().order_by('-detected_at')
    return render(request, 'plates/license_plate_list.html', {'plates': plates, 'query': query})

def license_plate_detail(request, plate_id):
    plate = get_object_or_404(LicensePlate, id=plate_id)
    return render(request, 'plates/license_plate_detail.html', {'plate': plate})

@csrf_exempt
def detect_license_plate(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    plates = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_russian_plate_number.xml')
    detected_plates = plates.detectMultiScale(gray, 1.1, 4)
    return detected_plates


@csrf_exempt
def upload_image(request):
    if request.method == 'POST':
        try:
            image = request.FILES['image']
            if not image.content_type.startswith('image/'):
                return JsonResponse({'error': 'Invalid file type'}, status=400)
            image_path = f'media/{image.name}'
            with open(image_path, 'wb+') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)
            detected_plates = detect_license_plate(image_path)
            data = [str(plate) for plate in detected_plates]
            save_to_google_sheets(data)
            asyncio.run(send_message(1323298372202790944, f'Detected Plates: {data}'))
            return JsonResponse({'plates': data})
        except Exception as e:
            return JsonResponse({'error': f'Error processing image: {str(e)}'}, status=500)
    return JsonResponse({'error': 'Invalid request'}, status=400)



@csrf_exempt
def gen_frames():
    camera = cv2.VideoCapture(0)
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def video_feed(request):
    return StreamingHttpResponse(gen_frames(),
                    content_type='multipart/x-mixed-replace; boundary=frame')


@csrf_exempt
def license_plate_add(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        plate_number = data.get('plate_number')
        if plate_number:
            plate, created = LicensePlate.objects.get_or_create(plate_number=plate_number)
            if created:               
                save_to_google_sheets(plate_number)               
                send_to_discord(plate_number)
                return JsonResponse({'message': 'Thêm thành công!', 'plate': plate_number}, status=201)
            else:
                return JsonResponse({'message': 'Biển số đã tồn tại.'}, status=400)
        else:
            return JsonResponse({'message': 'Biển số không hợp lệ.'}, status=400)
    return JsonResponse({'message': 'Invalid request'}, status=400)

@csrf_exempt
def license_plate_edit(request, id):
    plate = get_object_or_404(LicensePlate, id=id)
    if request.method == 'POST':
        data = json.loads(request.body)
        new_plate_number = data.get('plate_number')
        if new_plate_number:
            plate.plate_number = new_plate_number
            plate.save()
            return JsonResponse({'message': 'Cập nhật thành công!', 'plate': new_plate_number}, status=200)
        else:
            return JsonResponse({'message': 'Biển số không hợp lệ.'}, status=400)
    return JsonResponse({'message': 'Invalid request'}, status=400)

@csrf_exempt
def license_plate_delete(request, id):
    plate = get_object_or_404(LicensePlate, id=id)
    if request.method == 'POST':
        plate.delete()
        return JsonResponse({'message': 'Xóa thành công!'}, status=200)
    return JsonResponse({'message': 'Invalid request'}, status=400)
