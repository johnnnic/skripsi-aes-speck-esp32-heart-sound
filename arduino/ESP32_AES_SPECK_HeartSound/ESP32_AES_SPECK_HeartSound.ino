#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <SPI.h>
#include <SD.h>
#include <Crypto.h>
#include <AES.h>

#define LED_MERAH 26
#define LED_HIJAU 27
#define TOMBOL 4

#define SD_CS   5
#define SD_MOSI 23
#define SD_MISO 19
#define SD_SCK  18

LiquidCrystal_I2C lcd(0x27, 16, 2);

byte aesKey[16] = {
  0x2b, 0x7e, 0x15, 0x16,
  0x28, 0xae, 0xd2, 0xa6,
  0xab, 0xf7, 0x15, 0x88,
  0x09, 0xcf, 0x4f, 0x3c
};

AES128 aes;

uint64_t speckKey[2] = {
  0x0f0e0d0c0b0a0908ULL,
  0x0706050403020100ULL
};

const char* daftarFile[15] = {
  "/f01.wav", "/f02.wav", "/f03.wav", "/f04.wav", "/f05.wav",
  "/f06.wav", "/f07.wav", "/f08.wav", "/f09.wav", "/f10.wav",
  "/f11.wav", "/f12.wav", "/f13.wav", "/f14.wav", "/f15.wav"
};

uint64_t ROR64(uint64_t x, uint8_t r) {
  return (x >> r) | (x << (64 - r));
}

uint64_t ROL64(uint64_t x, uint8_t r) {
  return (x << r) | (x >> (64 - r));
}

void speckEncrypt128(const uint64_t pt[2], uint64_t ct[2], const uint64_t key[2]) {
  uint64_t x = pt[0];
  uint64_t y = pt[1];
  uint64_t b = key[0];
  uint64_t a = key[1];

  for (uint8_t i = 0; i < 32; i++) {
    x = (ROR64(x, 8) + y) ^ b;
    y = ROL64(y, 3) ^ x;
    a = (ROR64(a, 8) + b) ^ i;
    b = ROL64(b, 3) ^ a;
  }

  ct[0] = x;
  ct[1] = y;
}

void speckDecrypt128(const uint64_t ct[2], uint64_t pt[2], const uint64_t key[2]) {
  uint64_t roundKeys[32];
  uint64_t b = key[0];
  uint64_t a = key[1];

  for (uint8_t i = 0; i < 32; i++) {
    roundKeys[i] = b;
    a = (ROR64(a, 8) + b) ^ i;
    b = ROL64(b, 3) ^ a;
  }

  uint64_t x = ct[0];
  uint64_t y = ct[1];

  for (int8_t i = 31; i >= 0; i--) {
    y = ROR64(y ^ x, 3);
    x = ROL64((x ^ roundKeys[i]) - y, 8);
  }

  pt[0] = x;
  pt[1] = y;
}

bool prosesAESFile(const char *filename, unsigned long &encTime, unsigned long &decTime,
                   size_t &totalBytes, bool &verifyOK) {
  File file = SD.open(filename);
  if (!file) return false;

  encTime = 0;
  decTime = 0;
  totalBytes = 0;
  verifyOK = true;

  if (file.size() <= 44) {
    file.close();
    return false;
  }

  file.seek(44);  // Lewati header WAV.

  uint8_t plain[16];
  uint8_t cipher[16];
  uint8_t decrypted[16];

  while (file.available()) {
    int n = file.read(plain, 16);
    if (n <= 0) break;

    if (n < 16) {
      for (int i = n; i < 16; i++) plain[i] = 0x00;
    }

    unsigned long t1 = micros();
    aes.encryptBlock(cipher, plain);
    encTime += micros() - t1;

    unsigned long t2 = micros();
    aes.decryptBlock(decrypted, cipher);
    decTime += micros() - t2;

    for (int i = 0; i < n; i++) {
      if (plain[i] != decrypted[i]) {
        verifyOK = false;
        break;
      }
    }

    totalBytes += n;
    if (!verifyOK) break;
  }

  file.close();
  return true;
}

bool prosesSPECKFile(const char *filename, unsigned long &encTime, unsigned long &decTime,
                     size_t &totalBytes, bool &verifyOK) {
  File file = SD.open(filename);
  if (!file) return false;

  encTime = 0;
  decTime = 0;
  totalBytes = 0;
  verifyOK = true;

  if (file.size() <= 44) {
    file.close();
    return false;
  }

  file.seek(44);  // Lewati header WAV.

  uint8_t plain[16];
  uint8_t decryptedBytes[16];
  uint64_t pt[2];
  uint64_t ct[2];
  uint64_t dt[2];

  while (file.available()) {
    int n = file.read(plain, 16);
    if (n <= 0) break;

    if (n < 16) {
      for (int i = n; i < 16; i++) plain[i] = 0x00;
    }

    memcpy(pt, plain, 16);

    unsigned long t1 = micros();
    speckEncrypt128(pt, ct, speckKey);
    encTime += micros() - t1;

    unsigned long t2 = micros();
    speckDecrypt128(ct, dt, speckKey);
    decTime += micros() - t2;

    memcpy(decryptedBytes, dt, 16);

    for (int i = 0; i < n; i++) {
      if (plain[i] != decryptedBytes[i]) {
        verifyOK = false;
        break;
      }
    }

    totalBytes += n;
    if (!verifyOK) break;
  }

  file.close();
  return true;
}

void tampilSiap() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Sistem Siap");
  lcd.setCursor(0, 1);
  lcd.print("Tekan Tombol");
}

void jalankanPengujian15File() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Cek SD Card...");

  if (!SD.begin(SD_CS)) {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("SD Error");
    Serial.println("SD_ERROR");
    delay(3000);
    tampilSiap();
    return;
  }

  Serial.println("Run,No,File,AES Bytes,AES Encrypt us,AES Decrypt us,AES Verify,SPECK Bytes,SPECK Encrypt us,SPECK Decrypt us,SPECK Verify");

  for (int run = 1; run <= 5; run++) {
    for (int i = 0; i < 15; i++) {
      const char* filename = daftarFile[i];

      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Run ");
      lcd.print(run);
      lcd.print(" File ");
      lcd.print(i + 1);
      lcd.setCursor(0, 1);
      lcd.print(filename);

      unsigned long aesEnc = 0, aesDec = 0;
      unsigned long speckEnc = 0, speckDec = 0;
      size_t aesBytes = 0, speckBytes = 0;
      bool aesOK = false, speckOK = false;
      bool aesFileOK, speckFileOK;

      digitalWrite(LED_MERAH, HIGH);
      aesFileOK = prosesAESFile(filename, aesEnc, aesDec, aesBytes, aesOK);
      digitalWrite(LED_MERAH, LOW);
      delay(200);

      digitalWrite(LED_HIJAU, HIGH);
      speckFileOK = prosesSPECKFile(filename, speckEnc, speckDec, speckBytes, speckOK);
      digitalWrite(LED_HIJAU, LOW);
      delay(200);

      if (!aesFileOK || !speckFileOK) {
        Serial.print(run);
        Serial.print(",");
        Serial.print(i + 1);
        Serial.print(",");
        Serial.print(filename);
        Serial.println(",FILE_ERROR,FILE_ERROR,FILE_ERROR,FILE_ERROR,FILE_ERROR,FILE_ERROR,FILE_ERROR,FILE_ERROR");
      } else {
        Serial.print(run);
        Serial.print(",");
        Serial.print(i + 1);
        Serial.print(",");
        Serial.print(filename);
        Serial.print(",");
        Serial.print(aesBytes);
        Serial.print(",");
        Serial.print(aesEnc);
        Serial.print(",");
        Serial.print(aesDec);
        Serial.print(",");
        Serial.print(aesOK ? "BERHASIL" : "GAGAL");
        Serial.print(",");
        Serial.print(speckBytes);
        Serial.print(",");
        Serial.print(speckEnc);
        Serial.print(",");
        Serial.print(speckDec);
        Serial.print(",");
        Serial.println(speckOK ? "BERHASIL" : "GAGAL");
      }
    }
  }

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Pengujian");
  lcd.setCursor(0, 1);
  lcd.print("Selesai");
  Serial.println("SELESAI");
  delay(5000);
  tampilSiap();
}

void setup() {
  Serial.begin(115200);

  pinMode(LED_MERAH, OUTPUT);
  pinMode(LED_HIJAU, OUTPUT);
  pinMode(TOMBOL, INPUT_PULLUP);
  digitalWrite(LED_MERAH, LOW);
  digitalWrite(LED_HIJAU, LOW);

  Wire.begin(21, 22);
  lcd.init();
  lcd.backlight();

  SPI.begin(SD_SCK, SD_MISO, SD_MOSI, SD_CS);

  aes.setKey(aesKey, 16);
  tampilSiap();
}

void loop() {
  if (digitalRead(TOMBOL) == LOW) {
    delay(50);
    if (digitalRead(TOMBOL) == LOW) {
      jalankanPengujian15File();
      while (digitalRead(TOMBOL) == LOW) {
        delay(10);
      }
    }
  }
}
