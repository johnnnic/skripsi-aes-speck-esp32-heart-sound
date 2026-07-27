"""Generate original/encrypted/decrypted byte visualizations for AES-128 and SPECK.

Place f01.wav ... f15.wav in data/heart_sound_wav/ before running.
This script skips the 44-byte WAV header and processes audio bytes per 16-byte block.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from Crypto.Cipher import AES

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "heart_sound_wav"
FIG_DIR = ROOT / "results" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

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


def speck_decrypt_block(block: bytes, key: list[int]) -> bytes:
    b = key[0]
    a = key[1]
    round_keys = []
    for i in range(32):
        round_keys.append(b)
        a = (ror64(a, 8) + b) & MASK64
        a ^= i
        b = rol64(b, 3) ^ a

    x = int.from_bytes(block[0:8], byteorder="little")
    y = int.from_bytes(block[8:16], byteorder="little")
    for rk in reversed(round_keys):
        y = ror64(y ^ x, 3)
        x = rol64(((x ^ rk) - y) & MASK64, 8)
    return x.to_bytes(8, byteorder="little") + y.to_bytes(8, byteorder="little")


def pad_16(data: bytes) -> bytes:
    remainder = len(data) % 16
    if remainder == 0:
        return data
    return data + bytes(16 - remainder)


def process_aes(data: bytes) -> tuple[bytes, bytes]:
    cipher = AES.new(AES_KEY, AES.MODE_ECB)
    padded = pad_16(data)
    encrypted = cipher.encrypt(padded)
    decrypted = cipher.decrypt(encrypted)[: len(data)]
    return encrypted[: len(data)], decrypted


def process_speck(data: bytes) -> tuple[bytes, bytes]:
    padded = pad_16(data)
    encrypted_blocks = []
    decrypted_blocks = []
    for i in range(0, len(padded), 16):
        block = padded[i : i + 16]
        enc = speck_encrypt_block(block, SPECK_KEY)
        dec = speck_decrypt_block(enc, SPECK_KEY)
        encrypted_blocks.append(enc)
        decrypted_blocks.append(dec)
    encrypted = b"".join(encrypted_blocks)[: len(data)]
    decrypted = b"".join(decrypted_blocks)[: len(data)]
    return encrypted, decrypted


def load_audio_bytes(path: Path) -> bytes:
    raw = path.read_bytes()
    if len(raw) <= 44:
        raise ValueError(f"File terlalu kecil atau bukan WAV valid: {path}")
    return raw[44:]


def plot_bytes(original: bytes, encrypted: bytes, decrypted: bytes, title: str, output: Path, limit: int = 1500) -> None:
    original_arr = np.frombuffer(original[:limit], dtype=np.uint8)
    encrypted_arr = np.frombuffer(encrypted[:limit], dtype=np.uint8)
    decrypted_arr = np.frombuffer(decrypted[:limit], dtype=np.uint8)

    plt.figure(figsize=(12, 6))
    plt.plot(original_arr, label="Data asli")
    plt.plot(encrypted_arr, label="Terenkripsi")
    plt.plot(decrypted_arr, label="Terdekripsi")
    plt.title(title)
    plt.xlabel("Index byte")
    plt.ylabel("Nilai byte")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output, dpi=200)
    plt.close()


def main() -> None:
    targets = {
        "kecil": "f01.wav",
        "sedang": "f06.wav",
        "besar": "f15.wav",
    }
    for kategori, filename in targets.items():
        path = DATA_DIR / filename
        if not path.exists():
            print(f"Lewati {filename}: file belum ada di {DATA_DIR}")
            continue
        data = load_audio_bytes(path)
        aes_enc, aes_dec = process_aes(data)
        speck_enc, speck_dec = process_speck(data)
        plot_bytes(data, aes_enc, aes_dec, f"AES-128 - {kategori} ({filename})", FIG_DIR / f"{kategori}_aes_visualisasi.png")
        plot_bytes(data, speck_enc, speck_dec, f"SPECK - {kategori} ({filename})", FIG_DIR / f"{kategori}_speck_visualisasi.png")


if __name__ == "__main__":
    main()
