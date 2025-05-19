#!/usr/bin/env python
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
REGIONS = {
    "REGIÓN DE AYSÉN DEL GENERAL CARLOS IBÁÑEZ DEL CAMPO": "AI",  # none
    "REGIÓN DE ANTOFAGASTA": "AN",
    "REGIÓN DE ARICA Y PARINACOTA": "AP",  # none?
    "REGIÓN DE LA ARAUCANÍA": "AR",
    "REGIÓN DE ATACAMA": "AT",
    "REGIÓN DEL BIOBÍO": "BI",
    "REGIÓN DE COQUIMBO": "CO",
    "REGIÓN DEL LIBERTADOR GENERAL BERNARDO O'HIGGINS": "OH",
    "REGIÓN DE LOS LAGOS": "LL",
    "REGIÓN DE LOS RÍOS": "LR",
    "REGIÓN DE MAGALLANES Y DE LA ANTÁRTICA CHILENA": "MG",  # none
    "REGIÓN DEL MAULE": "MA",
    "REGIÓN DE NUBLE": "NB",
    "REGIÓN METROPOLITANA DE SANTIAGO": "RM",
    "REGIÓN DE TARAPACÁ": "TA",
    "REGIÓN DE VALPARAÍSO": "VA",
}
BANDS = {
    "2m": [144, 148],
    "1.25m": [220, 225],
    "70cm": [420, 450]
}
NARROW = [
    "CE3PA-A",
    "CE3PA-B",
    "CE3PA-D"
]


def check_regions(l: list[str]):
    for region in l:
        if region not in REGIONS.values():
            raise typer.BadParameter("Expected any of " + ", ".join(REGIONS.values()))
    return l


def check_bands(b: list[str]):
    for band in b:
        if band not in BANDS.keys():
            raise typer.BadParameter("Expected any of " + ", ".join(BANDS.keys()))
    return b


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


def get_band_for_frequency(freq: float):
    for band_name, band_range in BANDS.items():
        if band_range[0] <= freq <= band_range[1]:
            return band_name

    return None


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
        args[9] = REGIONS[args[9]] if args[9] is not None else "AA"
        args[13] = parse_coords(args[13])
        args[14] = parse_coords(args[14])

        repeater = Repeater(*args)

        if repeater.region == "AA":
            print(f"{Fore.RED}Warning! {Fore.CYAN}Repeater {repeater.identifier} does not has a valid region!{Style.RESET_ALL} ")

        entries.append(repeater)

    print(f"{Fore.CYAN}Found {Fore.WHITE}{len(entries)} {Fore.CYAN}repeaters!{Style.RESET_ALL}")

    return entries


def write_csv_from_repeaters(repeaters: list[Repeater], regions: list[str] | None, bands: list[str] | None):
    print(f"{Fore.RED}Writing {Fore.WHITE}{len(repeaters)} {Fore.RED}repeaters to {Fore.WHITE}cl_repeaters.csv{Style.RESET_ALL}")

    with open("cl_repeaters.csv", "w", newline="\n", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_NONE)
        writer.writerow(HEADER)

        last_index = 0

        for r in repeaters:
            if regions is not None and r.region not in regions:
                print(f"{Fore.RED}Skipping {Fore.WHITE}{r.identifier}{Fore.RED} because its not in the specified regions {Style.RESET_ALL}")
                continue

            band = get_band_for_frequency(r.rx)

            if bands is not None and band not in bands:
                print(f"{Fore.RED}Skipping {Fore.WHITE}{r.identifier}{Fore.RED} because its outside of our specified bands {Style.RESET_ALL}")
                continue

            offset = round(r.rx - r.tx, 1)
            mode = "NFM" if r.identifier in NARROW else "FM"

            print(f"{Fore.RED}Writing {Fore.WHITE}{r.identifier} ({mode}) {Fore.RED}...{Style.RESET_ALL}")

            writer.writerow([
                last_index,  # Location
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
                mode,  # Mode
                "1",  # TStep
                "",  # Skip
                "50W",  # Power
                r.operator + " @ " + r.location.replace(",", ""),  # Comment
                "",  # URCALL
                "",  # RPT1CALL
                "",  # RPT2CALL
                ""  # DVCODE
            ])

            last_index += 1


def main(input_file: Annotated[str, typer.Option(help="Local XLSX file to parse.")] = None,
         fetch_url: Annotated[str, typer.Option(help="URL of XLSX to request and parse.")] = None,
         regions: Annotated[list[str], typer.Option(help="The regions to fetch.", callback=check_regions)] = None,
         bands: Annotated[list[str], typer.Option(help="The bands to fetch.", callback=check_bands)] = None):
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
    write_csv_from_repeaters(repeaters, regions, bands)

    print(f"{Fore.MAGENTA}Success!{Style.RESET_ALL}")


if __name__ == "__main__":
    typer.run(main)
