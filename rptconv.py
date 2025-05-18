import csv
import io
from collections import namedtuple
from pathlib import Path
from typing import Annotated

import requests
import typer
from colorama import Fore, Style
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
HEADER = [
    "Location",
    "Name",
    "Frequency",
    "Duplex",
    "Offset",
    "Tone",
    "rToneFreq",
    "cToneFreq",
    "DtcsCode",
    "DtcsPolarity",
    "RxDtcsCode",
    "CrossMode",
    "Mode",
    "TStep",
    "Skip",
    "Power",
    "Comment",
    "URCALL",
    "RPT1CALL",
    "RPT2CALL",
    "DVCODE"
]


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


def get_repeaters_from_excel(excel: bytes):
    print(f"{Fore.CYAN}Starting repeater processing{Style.RESET_ALL}")

    bytes_io = io.BytesIO(excel)
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

    print(f"{Fore.CYAN}Found {Fore.WHITE}{len(entries)} {Fore.CYAN}repeaters!{Style.RESET_ALL}")

    return entries


def write_csv_from_repeaters(repeaters: list[Repeater]):
    print(f"{Fore.RED}Writing {Fore.WHITE}{len(repeaters)} {Fore.RED}repeaters to {Fore.WHITE}cl_repeaters.csv{Style.RESET_ALL}")

    with open("cl_repeaters.csv", "w", newline="\n", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_NONE)
        writer.writerow(HEADER)

        for i, r in enumerate(repeaters):
            offset = round(r.rx - r.tx, 1)

            print(f"{Fore.RED}Writing {Fore.WHITE}{r.identifier}{Fore.RED}...{Style.RESET_ALL}")

            writer.writerow([
                i,  # Location
                r.identifier,  # Name
                r.rx,  # Frequency
                "-" if offset < 0 else "+",  # Duplex
                abs(offset),  # Offset
                "Tone" if r.tone else "",  # Tone
                r.tone if r.tone else "88.5",  # rToneFreq
                "88.5",  # cToneFreq
                "023",  # DtcsCode
                "NN",  # DtcsPolarity
                "023",  # RxDtcsCode
                "Tone->Tone",  # CrossMode
                "FM",  # Mode
                "1",  # TStep
                "",  # Skip
                "50W",  # Power
                r.operator + " @ " + r.location.replace(",", ""),  # Comment
                "",  # URCALL
                "",  # RPT1CALL
                "",  # RPT2CALL
                ""  # DVCODE
            ])


def main(input_file: Annotated[str, typer.Option(help="Local XLSX file to parse.")] = None,
         fetch_url: Annotated[str, typer.Option(help="URL of XLSX to request and parse.")] = None):
    if fetch_url is None and input_file is None:
        fetch_url = "https://www.subtel.gob.cl/wp-content/uploads/2025/05/Informes_RA_13_05_2025_repetidoras.xlsx"

    if input_file is None:
        print(f"{Fore.GREEN}Will fetch the XLSX from {Fore.WHITE}{fetch_url}{Style.RESET_ALL}")
        request = requests.get(fetch_url)
        request.raise_for_status()
        print(f"{Fore.GREEN}Successfully fetched XLSX from URL{Style.RESET_ALL}")
        excel = request.content
    else:
        path = Path(input_file)
        print(f"{Fore.GREEN}Will use the following XLSX file{Fore.WHITE}: {path}{Style.RESET_ALL}")
        excel = path.read_bytes()

    repeaters = get_repeaters_from_excel(excel)
    write_csv_from_repeaters(repeaters)

    print(f"{Fore.MAGENTA}Success!{Style.RESET_ALL}")


if __name__ == "__main__":
    typer.run(main)
