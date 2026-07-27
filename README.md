# Repository Skripsi - AES-128 dan SPECK pada File Suara Jantung di ESP32

Repository ini berisi kode program pendukung skripsi:

**Evaluasi Kinerja Algoritma Kriptografi Lightweight pada File Suara Jantung di Perangkat IoT sebagai Simulasi Pengamanan Data Medis Digital**

Penulis: John Nicholas Febrian Lumbanbatu  
NIM: 225150307111054  
Program Studi: Teknik Komputer, Fakultas Ilmu Komputer, Universitas Brawijaya

## Struktur Folder

```text
arduino/ESP32_AES_SPECK_HeartSound/
  ESP32_AES_SPECK_HeartSound.ino

python/
  01_process_serial_results.py
  02_visualize_encrypt_decrypt.py
  03_ciphertext_statistics.py
  requirements.txt

data/sample_serial/
  serial_output_75_rows.csv

data/heart_sound_wav/
  README.md

results/excel/
  output file Excel hasil pengolahan data

results/figures/
  output gambar visualisasi
```

## 1. Kode ESP32

File utama:

```text
arduino/ESP32_AES_SPECK_HeartSound/ESP32_AES_SPECK_HeartSound.ino
```

Fungsi utama program ESP32:

1. Membaca file suara jantung `f01.wav` sampai `f15.wav` dari SD card.
2. Melewati header WAV sebesar 44 byte.
3. Memproses data audio per blok 16 byte.
4. Menjalankan enkripsi dan dekripsi AES-128.
5. Menjalankan enkripsi dan dekripsi SPECK.
6. Mengukur waktu enkripsi dan dekripsi menggunakan `micros()`.
7. Memverifikasi hasil dekripsi dengan data asli.
8. Mencetak hasil pengujian ke Serial Monitor dalam format CSV.

## 2. Kebutuhan Library Arduino

Library yang digunakan:

- `Wire`
- `LiquidCrystal_I2C`
- `SPI`
- `SD`
- `Crypto`
- `AES`

Pastikan library AES/Crypto sudah terpasang di Arduino IDE sebelum upload program ke ESP32.

## 3. Format File SD Card

Simpan file WAV pada root SD card dengan nama:

```text
/f01.wav
/f02.wav
...
/f15.wav
```

File yang digunakan pada penelitian berasal dari PhysioNet/Computing in Cardiology Challenge 2016. Dataset WAV tidak disertakan penuh di repository ini. Letakkan file WAV pada folder `data/heart_sound_wav/` untuk menjalankan script Python visualisasi/statistik.

## 4. Pengolahan Hasil Serial Monitor

Script:

```text
python/01_process_serial_results.py
```

Input:

```text
data/sample_serial/serial_output_75_rows.csv
```

Output:

```text
results/excel/01_Data_Raw_5x.xlsx
results/excel/02_Statistik_Per_File.xlsx
results/excel/03_Ringkasan_Kategori.xlsx
```

Cara menjalankan:

```bash
cd Kode_Repository_John_Nicholas
pip install -r python/requirements.txt
python python/01_process_serial_results.py
```

## 5. Visualisasi Data

Script:

```text
python/02_visualize_encrypt_decrypt.py
```

Script ini membuat visualisasi data asli, data terenkripsi, dan data terdekripsi untuk file perwakilan kategori kecil, sedang, dan besar.

Sebelum menjalankan, letakkan file WAV pada:

```text
data/heart_sound_wav/
```

Cara menjalankan:

```bash
python python/02_visualize_encrypt_decrypt.py
```

## 6. Statistik Ciphertext

Script:

```text
python/03_ciphertext_statistics.py
```

Metrik yang dihitung:

- Entropy
- Correlation coefficient
- Histogram uniformity CV
- Chi-square
- P-value

Cara menjalankan:

```bash
python python/03_ciphertext_statistics.py
```

Output:

```text
results/excel/04_Statistik_Ciphertext.xlsx
```

## 7. Catatan Batasan

Kode ini digunakan untuk kebutuhan penelitian dan evaluasi performa dasar. Implementasi enkripsi/dekripsi pada ESP32 menggunakan pemrosesan blok mandiri yang setara dengan pendekatan ECB. Kode ini belum menggunakan mode CBC, CTR, GCM, IV, nonce, atau manajemen kunci aman, sehingga belum ditujukan sebagai sistem keamanan produksi.
