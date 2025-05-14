import io
from collections import namedtuple
from pathlib import Path

import requests
import typer
from openpyxl.reader.excel import load_workbook


Repeater = namedtuple("Repeater", [
    "operator",
    "rut",
    "band",
    "identifier",
    "tx",
    "rx",
    "tone",
    "power",
    "gain",
    "region",
    "comuna",
    "awarded",
    "expires",
    "latitude",
    "longitude",
    "location"
])


def fix_float(num: str):
    # second one is unicode 8217, not the regular ', aka unicode 39
    num = num.rstrip("°").rstrip("’").rstrip("\"").replace(",", ".")
    return float(num)


def clean_identifier(identifier: str):
    return identifier.replace(" RPR-", "-").replace("/RPT-", "-").replace(" RPT-", "-").replace(" ", "")


def parse_coords(coords: str):
    split = coords.split(" ")
    degrees = fix_float(split[0])
    minutes = fix_float(split[1])
    seconds = fix_float(split[2])

    dd = degrees + (minutes / 60.0) + (seconds / 3600.0)
    return -dd


def process_excel(contents: bytes):
    bytes_io = io.BytesIO(contents)
    wb = load_workbook(bytes_io, read_only=True)
    ws = wb.active

    entries = []

    for i, row in enumerate(ws.rows):
        if i == 0:
            continue

        args = [x.value for x in row]
        args[3] = clean_identifier(args[3])
        args[13] = parse_coords(args[13])
        args[14] = parse_coords(args[14])

        repeater = Repeater(*args)
        entries.append(repeater)

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
