import io
from pathlib import Path

import requests
import typer
from openpyxl.reader.excel import load_workbook


def process_excel(contents: bytes):
    bytes_io = io.BytesIO(contents)
    wb = load_workbook(bytes_io, read_only=True)
    ws = wb.active

    entries = []

    for i, row in enumerate(ws.rows):
        if i == 0:
            continue

        operator = row[0].value
        rut = row[1].value
        band = row[2].value
        identifier = row[3].value
        tx = row[4].value
        rx = row[5].value
        tone = row[6].value
        power = row[7].value
        gain = row[8].value
        region = row[9].value
        comuna = row[10].value
        awarded = row[11].value
        expired = row[12].value
        latitude = row[13].value
        longitude = row[14].value
        location = row[15].value
        entries.append((operator, rut, band, identifier, tx, rx, tone, power, gain, region, comuna, awarded, expired, latitude, longitude, location))

    return entries


def main(file: str = None):
    if file is None:
        request = requests.get("https://www.subtel.gob.cl/wp-content/uploads/2025/03/Informes_RA_26_03_2025_Repetidoras.xlsx")
        request.raise_for_status()
        content = request.content
    else:
        content = Path(file).read_bytes()

    process_excel(content)


if __name__ == "__main__":
    typer.run(main)
