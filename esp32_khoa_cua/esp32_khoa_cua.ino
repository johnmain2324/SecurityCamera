#include <SPI.h>
#include <MFRC522.h>

const int RELAY_PIN = 3;
const int LED_PIN = 4;
const int COI_PIN = 1;

const int SS_PIN = 10;
const int RST_PIN = 0;
const int SCK_PIN = 6;
const int MISO_PIN = 5;
const int MOSI_PIN = 7;

struct TheHopLe {
  byte uid[4];
  const char *ten;
};

TheHopLe danhSachThe[] = {
  {{0x71, 0xDD, 0xC6, 0x18}, "SEP"},
};
const int SO_THE = sizeof(danhSachThe) / sizeof(danhSachThe[0]);

const unsigned long THOI_GIAN_MO_KHOA = 4000;
const unsigned long THOI_GIAN_BAO_DONG = 10000;
const unsigned long THOI_GIAN_CHONG_LAP = 2000;
const unsigned long THOI_GIAN_DEM_SAI = 30000;
const int SO_LAN_SAI_TOI_DA = 3;

MFRC522 rfid(SS_PIN, RST_PIN);

bool khoaDangMo = false;
unsigned long mocMoKhoa = 0;

byte uidTruoc[4];
unsigned long lanQuetTruoc = 0;
int demSai = 0;
unsigned long lanSaiTruoc = 0;
unsigned long lanKiemTra = 0;

bool baoDong = false;
unsigned long mocBaoDong = 0;
unsigned long lanNhay = 0;
bool nhay = false;

void guiTrangThai(const char *noiDung) {
  Serial.println(noiDung);
}

void datLed(bool bat) {
  digitalWrite(LED_PIN, bat ? LOW : HIGH);
}

void bip(int soLan, int thoiGian) {
  for (int i = 0; i < soLan; i++) {
    digitalWrite(COI_PIN, HIGH);
    delay(thoiGian);
    digitalWrite(COI_PIN, LOW);
    delay(thoiGian);
  }
}

void khoiDongRC522() {
  pinMode(RST_PIN, OUTPUT);
  digitalWrite(RST_PIN, LOW);
  delay(20);
  digitalWrite(RST_PIN, HIGH);
  delay(50);
  rfid.PCD_Init();
  rfid.PCD_SetAntennaGain(MFRC522::RxGain_max);
}

void batBaoDong(const char *lyDo) {
  guiTrangThai(lyDo);
  baoDong = true;
  mocBaoDong = millis();
}

void tatBaoDong() {
  baoDong = false;
  nhay = false;
  digitalWrite(COI_PIN, LOW);
  datLed(khoaDangMo);
}

void moKhoa() {
  tatBaoDong();
  digitalWrite(RELAY_PIN, HIGH);
  datLed(true);
  mocMoKhoa = millis();
  if (!khoaDangMo) guiTrangThai("KHOA:MO");
  khoaDangMo = true;
  bip(2, 60);
}

int timThe(byte *uid) {
  for (int i = 0; i < SO_THE; i++) {
    if (memcmp(uid, danhSachThe[i].uid, 4) == 0) return i;
  }
  return -1;
}

void xuLyQuetThe(unsigned long bayGio) {
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) return;

  byte uid[4] = {0, 0, 0, 0};
  for (byte i = 0; i < 4 && i < rfid.uid.size; i++) uid[i] = rfid.uid.uidByte[i];
  rfid.PICC_HaltA();

  if (memcmp(uid, uidTruoc, 4) == 0 && bayGio - lanQuetTruoc < THOI_GIAN_CHONG_LAP) return;
  memcpy(uidTruoc, uid, 4);
  lanQuetTruoc = bayGio;

  char chuoi[32];
  sprintf(chuoi, "UID:%02X %02X %02X %02X", uid[0], uid[1], uid[2], uid[3]);
  guiTrangThai(chuoi);

  int viTri = rfid.uid.size == 4 ? timThe(uid) : -1;
  if (viTri >= 0) {
    demSai = 0;
    sprintf(chuoi, "THE:%s", danhSachThe[viTri].ten);
    guiTrangThai(chuoi);
    moKhoa();
    return;
  }

  guiTrangThai("THE:LA");
  if (bayGio - lanSaiTruoc > THOI_GIAN_DEM_SAI) demSai = 0;
  demSai++;
  lanSaiTruoc = bayGio;
  if (demSai >= SO_LAN_SAI_TOI_DA) {
    demSai = 0;
    batBaoDong("CANH_BAO:THE_LA");
  } else {
    bip(1, 400);
  }
}

void xuLyLenh() {
  while (Serial.available()) {
    char lenh = Serial.read();
    if (lenh == 'O') moKhoa();
    else if (lenh == 'X') batBaoDong("CANH_BAO:NGUOI_LA");
    else if (lenh == 'S') {
      tatBaoDong();
      guiTrangThai("THONG_BAO:DA_TAT_BAO_DONG");
    }
  }
}

void capNhatKhoa(unsigned long bayGio) {
  if (khoaDangMo && bayGio - mocMoKhoa >= THOI_GIAN_MO_KHOA) {
    digitalWrite(RELAY_PIN, LOW);
    khoaDangMo = false;
    if (!baoDong) datLed(false);
    guiTrangThai("KHOA:DA_KHOA");
    delay(300);
    khoiDongRC522();
    guiTrangThai("THONG_BAO:RC522_SAN_SANG");
  }
}

void capNhatDenCoi(unsigned long bayGio) {
  if (!baoDong) return;
  if (bayGio - mocBaoDong >= THOI_GIAN_BAO_DONG) {
    tatBaoDong();
  } else if (bayGio - lanNhay >= 100) {
    lanNhay = bayGio;
    nhay = !nhay;
    datLed(nhay);
    digitalWrite(COI_PIN, nhay ? HIGH : LOW);
  }
}

void kiemTraRC522(unsigned long bayGio) {
  if (bayGio - lanKiemTra < 2000) return;
  lanKiemTra = bayGio;
  if (khoaDangMo) return;
  byte phienBan = rfid.PCD_ReadRegister(MFRC522::VersionReg);
  byte anten = rfid.PCD_ReadRegister(MFRC522::TxControlReg);
  bool loi = phienBan == 0x00 || phienBan == 0xFF;
  bool biReset = (anten & 0x03) != 0x03 || rfid.PCD_GetAntennaGain() != MFRC522::RxGain_max;
  if (loi || biReset) {
    guiTrangThai("LOI:RC522_KHOI_DONG_LAI");
    khoiDongRC522();
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  pinMode(COI_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);
  digitalWrite(COI_PIN, LOW);
  datLed(false);

  SPI.begin(SCK_PIN, MISO_PIN, MOSI_PIN, SS_PIN);
  khoiDongRC522();
  delay(500);

  byte phienBan = rfid.PCD_ReadRegister(MFRC522::VersionReg);
  if (phienBan == 0x00 || phienBan == 0xFF) guiTrangThai("LOI:KHONG_THAY_RC522");

  guiTrangThai("KHOA:DA_KHOA");
  guiTrangThai("ESP32:SAN_SANG");
  bip(1, 100);
}

void loop() {
  xuLyLenh();
  kiemTraRC522(millis());
  xuLyQuetThe(millis());
  capNhatKhoa(millis());
  capNhatDenCoi(millis());
}