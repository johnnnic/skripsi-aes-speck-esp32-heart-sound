"""Calculate ciphertext statistics for AES-128 and SPECK over WAV heart sound files.

Place f01.wav ... f15.wav in data/heart_sound_wav/ before running.
Output: results/excel/04_Statistik_Ciphertext.xlsx
"""
from pathlib import Path

import numpy as np
import pandas as pd
from Crypto.Cipher import AES
from scipy.stats import chisquare

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "heart_sound_wav"
OUT_DIR = ROOT / "results" / "excel"
OUT_DIR.mkdir(parents=True, exist_ok=True)

AES_KEY = bytes([
    0x2b, 0x7e, 0x15, 0x16,
    0x28, 0xae, 0xd2, 0xa6,
    0xab, 0xf7, 0x15, 0x88,
    0x09, 0xcf, 0x4f, 0x3c,
])
SPECK_KEY = [0x0f0e0d0c0b0a0908, 0x0706050403020100]
MASK64 = 0xFFFFFFFFFFFFFFFF


def ror64(x: int, r: int) -> int:
    return ((x >> r) | (x << (64 - r))) & MASK64


def rol64(x: int, r: int) -> int:
    return ((x << r) | (x >> (64 - r))) & MASK64


def speck_encrypt_block(block: bytes, key: list[int]) -> bytes:
    x = int.from_bytes(block[0:8], byteorder="little")
    y = int.from_bytes(block[8:16], byteorder="little")
    b = key[0]
    a = key[1]
    for i in range(32):
        x = (ror64(x, 8) + y) & MASK64
        x ^= b
        y = rol64(y, 3) ^ x
        a = (ror64(a, 8) + b) & MASK64
        a ^= i
        b = rol64(b, 3) ^ a
    return x.to_bytes(8, byteorder="little") + y.to_bytes(8, byteorder="little")


def pad_16(data: bytes) -> bytes:
    remainder = len(data) % 16
    return data if remainder == 0 else data + bytes(16 - remainder)


def kategori_file(no: int) -> str:
    if 1 <= no <= 5:
        return "Kecil"
    if 6 <= no <= 10:
        return "Sedang"
    return "Besar"


def load_audio_bytes(path: Path) -> bytes:
    raw = path.read_bytes()
    if len(raw) <= 44:
        raise ValueError(f"File terlalu kecil atau bukan WAV valid: {path}")
    return raw[44:]


def encrypt_aes(data: bytes) -> bytes:
    cipher = AES.new(AES_KEY, AES.MODE_ECB)
    return cipher.encrypt(pad_16(data))[: len(data)]


def encrypt_speck(data: bytes) -> bytes:
    padded = pad_16(data)
    out = []
    for i in range(0, len(padded), 16):
        out.append(speck_encrypt_block(padded[i : i + 16], SPECK_KEY))
    return b"".join(out)[: len(data)]


def entropy(data: bytes) -> float:
    arr = np.frombuffer(data, dtype=np.uint8)
    counts = np.bincount(arr, minlength=256)
    probs = counts[counts > 0] / arr.size
    return float(-(probs * np.log2(probs)).sum())


def correlation(original: bytes, encrypted: bytes) -> float:
    x = np.frombuffer(original, dtype=np.uint8).astype(float)
    y = np.frombuffer(encrypted, dtype=np.uint8).astype(float)
    n = min(len(x), len(y))
    if n < 2:
        return float("nan")
    return float(np.corrcoef(x[:n], y[:n])[0, 1])


def histogram_cv(data: bytes) -> float:
    counts = np.bincount(np.frombuffer(data, dtype=np.uint8), minlength=256).astype(float)
    mean = counts.mean()
    return float(counts.std(ddof=0) / mean) if mean else float("nan")


def chi_square_uniform(data: bytes) -> tuple[float, float]:
    counts = np.bincount(np.frombuffer(data, dtype=np.uint8), minlength=256).astype(float)
    expected = np.full(256, counts.sum() / 256)
    stat, p_value = chisquare(counts, expected)
    return float(stat), float(p_value)


def main() -> None:
    rows = []
    for no in range(1, 16):
        filename = f"f{no:02d}.wav"
        path = DATA_DIR / filename
        if not path.exists():
            print(f"Lewati {filename}: file belum ada di {DATA_DIR}")
            continue
        original = load_audio_bytes(path)
        for algo, encrypted in [
            ("AES-128", encrypt_aes(original)),
            ("SPECK", encrypt_speck(original)),
        ]:
            chi, p_value = chi_square_uniform(encrypted)
            rows.append({
                "No": no,
                "File": filename,
                "Kategori": kategori_file(no),
                "Algoritma": algo,
                "Entropy": entropy(encrypted),
                "Correlation": correlation(original, encrypted),
                "Histogram CV": histogram_cv(encrypted),
                "Chi-square": chi,
                "P-value": p_value,
            })

    if not rows:
        print("Tidak ada file WAV yang diproses.")
        return

    df = pd.DataFrame(rows)
    summary = df.groupby(["Kategori", "Algoritma"], as_index=False)[
        ["Entropy", "Correlation", "Histogram CV", "Chi-square", "P-value"]
    ].mean()
    total = df.groupby(["Algoritma"], as_index=False)[
        ["Entropy", "Correlation", "Histogram CV", "Chi-square", "P-value"]
    ].mean()
    total.insert(0, "Kategori", "Total")
    summary = pd.concat([summary, total], ignore_index=True)

    with pd.ExcelWriter(OUT_DIR / "04_Statistik_Ciphertext.xlsx", engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Per_File", index=False)
        summary.to_excel(writer, sheet_name="Ringkasan", index=False)
    print("Selesai:", OUT_DIR / "04_Statistik_Ciphertext.xlsx")


if __name__ == "__main__":
    main()
