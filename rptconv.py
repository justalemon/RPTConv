from pathlib import Path

import requests
import typer



def process_excel(contents: str):
    pass


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
