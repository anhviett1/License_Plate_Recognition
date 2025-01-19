import gspread
from google.oauth2.service_account import Credentials

def get_google_sheets_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_file('path/to/credentials.json', scopes=scope)
    client = gspread.authorize(credentials)
    return client

def save_to_google_sheets(plate_number):
    # Lấy client Google Sheets
    client = get_google_sheets_client()
    
    # Mở bảng tính và chọn sheet
    try:
        sheet = client.open('LicensePlates').sheet1
    except Exception as e:
        print("Không thể mở Google Sheets:", e)
        return
    
    # Thêm hàng mới với dữ liệu
    try:
        sheet.append_row([plate_number])
        print("Đã ghi biển số vào Google Sheets.")
    except Exception as e:
        print("Không thể ghi dữ liệu vào Google Sheets:", e)
