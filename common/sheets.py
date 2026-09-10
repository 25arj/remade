import gspread
from google.oauth2.service_account import Credentials

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_sheet(service_account_file: str, sheet_id: str, tab_name: str):
    creds = Credentials.from_service_account_file(service_account_file, scopes=_SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(sheet_id)
    try:
        return spreadsheet.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=10)


def ensure_header(worksheet, header: list) -> None:
    if not worksheet.get_all_values():
        append_row(worksheet, header)


def append_row(worksheet, row: list) -> None:
    worksheet.append_row(row, value_input_option="USER_ENTERED")
