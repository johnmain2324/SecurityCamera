#include <SPI.h>
#include <MFRC522.h>

const int SS_PIN = 10;
const int RST_PIN = 0;
const int SCK_PIN = 6;
const int MISO_PIN = 5;
const int MOSI_PIN = 7;

MFRC522 rfid(SS_PIN, RST_PIN);

void setup() {
  Serial.begin(115200);
  delay(1500);
  SPI.begin(SCK_PIN, MISO_PIN, MOSI_PIN, SS_PIN);
  rfid.PCD_Init();
  byte phienBan = rfid.PCD_ReadRegister(rfid.VersionReg);
  Serial.print("Phien ban RC522: 0x");
  Serial.println(phienBan, HEX);
  if (phienBan == 0x00 || phienBan == 0xFF) {
    Serial.println("Khong thay RC522 - kiem tra lai day");
  } else {
    Serial.println("RC522 OK - dua the lai gan");
  }
}

void loop() {
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) return;
  Serial.print("UID:");
  for (byte i = 0; i < rfid.uid.size; i++) {
    Serial.print(rfid.uid.uidByte[i] < 0x10 ? " 0" : " ");
    Serial.print(rfid.uid.uidByte[i], HEX);
  }
  Serial.println();
  rfid.PICC_HaltA();
  delay(500);
}