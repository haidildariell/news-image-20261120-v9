# Entrypoint edisi koran gambar 20 November 2026 (v7).
#
# Tugas file ini cuma satu: mengambil gambar koran yang sudah jadi
# (entry.png, satu folder dengan file ini) lalu meletakkan salinannya
# di folder output yang dipakai penilai. Render gambarnya sendiri
# dilakukan di build_image.py, bukan di sini, jadi file ini tidak
# mengolah piksel apa pun — hanya memindahkan berkas.
# Modul yang dipakai semuanya bawaan Python, supaya file ini jalan di
# image python:3.13-slim tanpa Pillow atau paket tambahan apa pun.

from os import environ
from pathlib import Path
from shutil import copyfile

IMAGE_NAME = "entry.png"
FALLBACK_DIR = "/output"


def find_source_image():
    # Gambar sumber tinggal di direktori yang sama dengan file ini,
    # jadi perintah boleh dijalankan dari folder kerja mana saja
    # tanpa mengubah di mana gambar itu dicari.
    here = Path(__file__).resolve().parent
    return here / IMAGE_NAME


def resolve_output_folder():
    # Folder tujuan dibaca dari variabel lingkungan penilai; bila
    # kosong atau tidak diset, pakai jalur baku /output.
    raw = environ.get("MAKEFUN_OUTPUT_DIR", FALLBACK_DIR)
    cleaned = raw.strip() or FALLBACK_DIR
    return Path(cleaned)


def ship_image():
    source = find_source_image()
    if not source.is_file():
        print(f"missing source image: {source}")
        return 1
    output_folder = resolve_output_folder()
    output_folder.mkdir(parents=True, exist_ok=True)
    destination = output_folder / IMAGE_NAME
    copyfile(source, destination)
    print(f"copied {source.name} -> {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(ship_image())
