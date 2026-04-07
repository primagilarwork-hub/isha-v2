"""
Jalankan sekali untuk inisialisasi Google Spreadsheet:
  python setup_sheets.py
"""
from dotenv import load_dotenv
load_dotenv()

from lib.sheets_sync import setup_spreadsheet

if __name__ == "__main__":
    result = setup_spreadsheet()
    print("✅ Spreadsheet siap!" if result else "❌ Gagal setup spreadsheet")
