import logging
import pickle
import random
import socket
import threading
import time
import warnings
from collections import deque
import cv2
import paho.mqtt.client as mqtt
import mediapipe as mp
from flask import Flask, jsonify
from cau_hinh import (LuongCamera, NGUON_CAMERA, kiem_tra_camera, THOI_GIAN_CHO_BAO_DONG, PHAT_AM_LAPTOP, TI_LE_MAT_GAN,
                      THOI_GIAN_LA_KHACH, THOI_GIAN_BAO_DONG, SO_LAN_SAI_TOI_DA, THOI_GIAN_MAT_DAU,
                      MQTT_MAY_CHU, MQTT_CONG, CHU_DE_LENH, CHU_DE_SU_KIEN, CHU_DE_TRANG_THAI,
                      CAC_CU_CHI_THU_THACH, DO_DAI_THU_THACH, THOI_GIAN_MOI_BUOC, NGUONG_TIN_CAY_CU_CHI, MAT_KHAU_CU_CHI, CHE_DO_CU_CHI)
from am_thanh import phat_am, dung_am
from telegram_bao import gui_bao_dong, gui_co_khach, gui_mo_cua, kiem_tra_token, gui_the_la

warnings.filterwarnings("ignore", message=".*GetPrototype.*")

CONG_WEB = 5000
CU_CHI_MO_KHOA = "so_2"
NGUONG_COSINE = 0.363
SO_KHUNG_XAC_NHAN = 10
SO_KHUNG_NGUOI_LA = 5
SO_KHUNG_CU_CHI = 15
THOI_GIAN_MO_CUA = 7
THOI_GIAN_TAY_BAO_DONG = 1
THOI_GIAN_MAT_TAY = 0.5
THOI_GIAN_HIEN_SAI = 3

detector = cv2.FaceDetectorYN.create("models/face_detection_yunet_2023mar.onnx", "", (320, 320), 0.8)
recognizer = cv2.FaceRecognizerSF.create("models/face_recognition_sface_2021dec.onnx", "")


lan_gui_telegram = 0
lan_bao_dong = 0
su_kien = {"id": 0, "loai": "", "noi_dung": "", "yeu_cau": ""}
app = Flask(__name__)

THOI_GIAN_HIEN_BAO_DONG_ESP = 10
THOI_GIAN_CHO_KHOA_MO = 2
THOI_GIAN_CHONG_SPAM = 10
THOI_GIAN_HIEN_THE = 5
THOI_GIAN_HIEN_THE_LA = 3
khoa_tt = threading.Lock()
trang_thai_khoa = "?"
thong_bao_the = ("", (0, 255, 0), 0)
lich_su = deque(maxlen=5)
thong_bao_cuoi = ""
thong_bao_la_loi = False
thoi_nhan_khoa_mo = 0
thoi_gui_mo = 0
het_bao_dong = 0
frame_hien_tai = None
lan_gui_canh_bao = {}
trang_thai_esp = "?"
client_mqtt = None

TRANG_WEB = """<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Loa khoa cua</title>
<style>
  body { margin: 0; height: 100vh; display: flex; flex-direction: column; align-items: center;
         justify-content: center; font-family: sans-serif; background: #555; color: #fff;
         transition: background 0.2s; text-align: center; }
  body.mo { background: #1b8f3a; }
  body.bao { animation: nhay 0.4s infinite; }
  @keyframes nhay { 0% { background: #c00; } 50% { background: #500; } 100% { background: #c00; } }
  button { font-size: 8vw; padding: 5vw 8vw; border: 0; border-radius: 4vw; background: #fff; color: #000; }
  #trang_thai { font-size: 9vw; margin: 6vw; padding: 0 4vw; }
  #yeu_cau { font-size: 11vw; font-weight: bold; padding: 0 4vw; color: #ff0; }
  #cua_khoa { font-size: 5vw; margin: 3vw; padding: 1vw 3vw; border-radius: 2vw; background: #fff; color: #000; }
  #thong_bao_esp { font-size: 4vw; padding: 0 4vw; }
  #lich_su { font-size: 3.5vw; margin-top: 3vw; padding: 0 4vw; white-space: pre-line; }
  #thong_bao_esp.loi { color: #f66; font-weight: bold; }
  #cua_khoa.xanh { background: #2e7d32; color: #fff; }
  #cua_khoa.vang { background: #fbc02d; color: #000; }
  #cua_khoa.do { background: #c00; color: #fff; }
</style>
</head>
<body>
<button id="nut">BAT AM THANH</button>
<div id="yeu_cau"></div>
<div id="trang_thai">DANG CHO</div>
<div id="cua_khoa">Khoa: ?</div>
<div id="thong_bao_esp"></div>
<div id="lich_su"></div>
<script>
let ctx = null, idCu = null, hen = null;
const nut = document.getElementById("nut");
const tt = document.getElementById("trang_thai");

nut.onclick = () => {
  ctx = new (window.AudioContext || window.webkitAudioContext)();
  ctx.resume();
  nut.style.display = "none";
};

function nhac(tanSo, batDau, doDai, amLuong) {
  const o = ctx.createOscillator(), g = ctx.createGain();
  o.type = "sine";
  o.frequency.setValueAtTime(tanSo, ctx.currentTime + batDau);
  g.gain.setValueAtTime(amLuong, ctx.currentTime + batDau);
  g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + batDau + doDai);
  o.connect(g); g.connect(ctx.destination);
  o.start(ctx.currentTime + batDau);
  o.stop(ctx.currentTime + batDau + doDai);
}

function phatMoCua() {
  nhac(880, 0, 0.5, 0.8);
  nhac(660, 0.5, 0.5, 0.8);
}

function phatBaoDong() {
  const o = ctx.createOscillator(), g = ctx.createGain();
  o.type = "sawtooth";
  g.gain.value = 1;
  o.frequency.setValueAtTime(600, ctx.currentTime);
  for (let i = 0; i < 6; i++) {
    o.frequency.linearRampToValueAtTime(1200, ctx.currentTime + i * 0.5 + 0.25);
    o.frequency.linearRampToValueAtTime(600, ctx.currentTime + i * 0.5 + 0.5);
  }
  o.connect(g); g.connect(ctx.destination);
  o.start();
  o.stop(ctx.currentTime + 3);
}

function hienThi(sk) {
  clearTimeout(hen);
  tt.textContent = sk.noi_dung;
  document.body.className = sk.loai === "mo_cua" ? "mo" : "bao";
  hen = setTimeout(() => {
    document.body.className = "";
    tt.textContent = "DANG CHO";
  }, sk.loai === "mo_cua" ? 7000 : 5000);
}

async function hoi() {
  try {
    const sk = await (await fetch("/su_kien")).json();
    document.getElementById("yeu_cau").textContent = sk.yeu_cau;
    const ck = document.getElementById("cua_khoa");
    ck.textContent = sk.chu_cua_khoa;
    ck.className = sk.mau_cua_khoa;
    const tb = document.getElementById("thong_bao_esp");
    tb.textContent = sk.thong_bao_esp;
    tb.className = sk.thong_bao_loi ? "loi" : "";
    document.getElementById("lich_su").textContent = sk.lich_su.join("\n");
    if (idCu === null) idCu = sk.id;
    if (sk.id !== idCu) {
      idCu = sk.id;
      hienThi(sk);
      if (ctx) {
        if (sk.loai === "mo_cua") phatMoCua();
        else if (sk.loai === "bao_dong") phatBaoDong();
      }
    }
  } catch (e) {}
}
setInterval(hoi, 300);
</script>
</body>
</html>"""


@app.route("/")
def trang_chu():
    return TRANG_WEB


@app.route("/su_kien")
def lay_su_kien():
    chu, mau = chu_cua_khoa()
    with khoa_tt:
        thong_bao, la_loi = thong_bao_cuoi, thong_bao_la_loi
        gan_day = [f"{gio} {noi_dung}" for gio, noi_dung in reversed(lich_su)]
    ten_mau = {(0, 255, 0): "xanh", (0, 255, 255): "vang", (0, 0, 255): "do"}[mau]
    return jsonify({**su_kien, "chu_cua_khoa": chu, "mau_cua_khoa": ten_mau,
                    "thong_bao_esp": thong_bao, "esp32": trang_thai_esp, "thong_bao_loi": la_loi, "lich_su": gan_day})


def chu_cua_khoa():
    with khoa_tt:
        khoa, dang_bao = trang_thai_khoa, time.time() < het_bao_dong
    chu = f"Khoa: {khoa}"
    if dang_bao:
        return chu, (0, 0, 255)
    if khoa == "KHOA":
        return chu, (0, 255, 0)
    return chu, (0, 255, 255)


def ip_laptop():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def chay_web():
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    print(f"Mo tren dien thoai: http://{ip_laptop()}:{CONG_WEB}")
    app.run(host="0.0.0.0", port=CONG_WEB, threaded=True, use_reloader=False)


def chuan_hoa(hand_landmarks):
    pts = [(lm.x, lm.y) for lm in hand_landmarks.landmark]
    x0, y0 = pts[0]
    pts = [(x - x0, y - y0) for x, y in pts]
    m = max(max(abs(x), abs(y)) for x, y in pts) or 1
    return [v / m for p in pts for v in p]


def on_connect(client, userdata, flags, ma_loi, thuoc_tinh):
    if ma_loi.is_failure:
        print("Ket noi MQTT loi:", ma_loi)
        return
    print("Da ket noi MQTT broker")
    client.subscribe([(CHU_DE_SU_KIEN, 1), (CHU_DE_TRANG_THAI, 1)])


def on_disconnect(client, userdata, co_ngat, ma_loi, thuoc_tinh):
    print("Mat ket noi MQTT broker - dang thu lai")


def on_message(client, userdata, tin):
    global trang_thai_esp
    chuoi = tin.payload.decode("utf-8", errors="ignore").strip()
    if tin.topic == CHU_DE_TRANG_THAI:
        print("[ESP32]", chuoi)
        trang_thai_esp = chuoi
        if chuoi == "OFFLINE":
            them_su_kien("Mat ket noi khoa cua")
            if duoc_gui("esp_offline"):
                gui_mo_cua("Mat ket noi khoa cua")
        return
    if not chuoi:
        return
    print("[ESP32]", chuoi)
    if chuoi.startswith("UID:"):
        return
    khoa, dau, gia_tri = chuoi.partition(":")
    if not dau or not khoa or not gia_tri:
        return
    try:
        xu_ly_esp32(khoa.strip(), gia_tri.strip())
    except Exception as e:
        print("[ESP32] Loi xu ly:", chuoi, "-", e)


def ket_noi_mqtt():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="laptop_ai")
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    try:
        socket.create_connection((MQTT_MAY_CHU, MQTT_CONG), timeout=2).close()
    except OSError:
        print("Chua bat Docker EMQX")
    client.connect_async(MQTT_MAY_CHU, MQTT_CONG, keepalive=15)
    client.loop_start()
    return client


def them_su_kien(noi_dung):
    with khoa_tt:
        lich_su.append((time.strftime("%H:%M"), noi_dung))


def gui_lenh(lenh, ten="", frame_goc=None):
    global lan_gui_telegram, thoi_gui_mo
    if lenh == "O" and not client_mqtt.is_connected():
        print("Chua ket noi MQTT - khong mo duoc khoa")
        return False
    print("Gui lenh:", lenh)
    if PHAT_AM_LAPTOP:
        phat_am("chuong_cua.wav" if lenh == "O" else "bao_dong.wav")
    if lenh == "X":
        them_su_kien("Canh bao nguoi la")
        if frame_goc is not None and time.time() - lan_gui_telegram > THOI_GIAN_CHO_BAO_DONG:
            lan_gui_telegram = time.time()
            gui_bao_dong(frame_goc)
    su_kien["loai"] = "mo_cua" if lenh == "O" else "bao_dong"
    su_kien["noi_dung"] = f"Chao mung {ten}" if lenh == "O" else "CANH BAO NGUOI LA"
    su_kien["id"] += 1
    if lenh == "O":
        with khoa_tt:
            thoi_gui_mo = time.time()
    client_mqtt.publish(CHU_DE_LENH, lenh, qos=1)
    return True


def bao_dong(frame_goc):
    global lan_bao_dong
    if time.time() - lan_bao_dong < THOI_GIAN_CHO_BAO_DONG:
        return
    gui_lenh("X", frame_goc=frame_goc)
    lan_bao_dong = time.time()


def duoc_gui(loai):
    with khoa_tt:
        if time.time() - lan_gui_canh_bao.get(loai, 0) < THOI_GIAN_CHONG_SPAM:
            return False
        lan_gui_canh_bao[loai] = time.time()
        return True


def canh_bao_the_la():
    global het_bao_dong
    with khoa_tt:
        het_bao_dong = time.time() + THOI_GIAN_HIEN_BAO_DONG_ESP
        anh = frame_hien_tai
    if PHAT_AM_LAPTOP:
        phat_am("bao_dong.wav")
    them_su_kien("Canh bao the la")
    if anh is not None and duoc_gui("the_la_3_lan"):
        gui_the_la(anh)
    su_kien["loai"] = "bao_dong"
    su_kien["noi_dung"] = "PHAT HIEN THE LA"
    su_kien["id"] += 1


def xu_ly_esp32(khoa, gia_tri):
    global trang_thai_khoa, thong_bao_cuoi, thong_bao_la_loi, thoi_nhan_khoa_mo, het_bao_dong, thong_bao_the
    with khoa_tt:
        thong_bao_cuoi = f"{khoa}:{gia_tri}"
        thong_bao_la_loi = khoa == "LOI"
    if khoa == "ESP32" and gia_tri == "SAN_SANG":
        with khoa_tt:
            thong_bao_cuoi = "ESP32 san sang"
    elif khoa == "KHOA" and gia_tri == "MO":
        with khoa_tt:
            trang_thai_khoa = "MO"
            thoi_nhan_khoa_mo = time.time()
    elif khoa == "KHOA" and gia_tri == "DA_KHOA":
        with khoa_tt:
            trang_thai_khoa = "KHOA"
            het_bao_dong = 0
    elif khoa == "THE" and gia_tri == "LA":
        with khoa_tt:
            thong_bao_the = ("The khong hop le", (0, 165, 255), time.time() + THOI_GIAN_HIEN_THE_LA)
    elif khoa == "THE":
        with khoa_tt:
            thong_bao_the = (f"Mo bang the: {gia_tri}", (0, 255, 0), time.time() + THOI_GIAN_HIEN_THE)
        them_su_kien(f"{gia_tri} mo bang the")
        if duoc_gui(f"mo_the_{gia_tri}"):
            gui_mo_cua(f"{gia_tri} da mo cua bang the")
    elif khoa == "CANH_BAO" and gia_tri == "THE_LA":
        canh_bao_the_la()
    elif khoa == "LOI":
        print(f"[91m[ESP32] LOI: {gia_tri}[0m")


def viet(frame, chu, dong, mau=(0, 255, 255), co=0.7):
    cv2.putText(frame, chu, (10, 30 * dong), cv2.FONT_HERSHEY_SIMPLEX, co, mau, 2)


def doc_nhan(nhan):
    return nhan.replace("_", " ")


def tao_thu_thach(cac_nhan):
    if len(cac_nhan) < 2:
        return [CU_CHI_MO_KHOA]
    chuoi = [random.choice(cac_nhan)]
    while len(chuoi) < DO_DAI_THU_THACH:
        chuoi.append(random.choice([n for n in cac_nhan if n != chuoi[-1]]))
    return chuoi


def nhan_dien_mat(frame, embeddings):
    detector.setInputSize((frame.shape[1], frame.shape[0]))
    _, mats = detector.detect(frame)
    if mats is None:
        return False, None, False

    mat = max(mats, key=lambda m: m[2] * m[3])
    ti_le = mat[2] / frame.shape[1]
    cv2.putText(frame, f"Mat: {ti_le:.2f}", (frame.shape[1] - 110, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    if ti_le < TI_LE_MAT_GAN:
        x, y, w, h = mat[:4].astype(int)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (128, 128, 128), 2)
        cv2.putText(frame, "Lai gan hon", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (128, 128, 128), 1)
        return False, None, True
    dac_trung = recognizer.feature(recognizer.alignCrop(frame, mat))
    diem_max, ten = -1.0, None
    for ten_dk, ds in embeddings.items():
        for emb in ds:
            diem = recognizer.match(dac_trung, emb.reshape(1, -1), cv2.FaceRecognizerSF_FR_COSINE)
            if diem > diem_max:
                diem_max, ten = diem, ten_dk
    if diem_max < NGUONG_COSINE:
        ten = None

    x, y, w, h = mat[:4].astype(int)
    mau = (0, 255, 0) if ten else (0, 0, 255)
    cv2.rectangle(frame, (x, y), (x + w, y + h), mau, 2)
    cv2.putText(frame, f"{ten or 'Nguoi la'} ({diem_max:.2f}) w={w}", (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, mau, 2)
    return True, ten, False


def main():
    global frame_hien_tai, het_bao_dong
    with open("models/face_embeddings.pkl", "rb") as f:
        embeddings = pickle.load(f)
    with open("models/gesture_model.pkl", "rb") as f:
        gesture_model = pickle.load(f)

    cac_nhan = [n for n in CAC_CU_CHI_THU_THACH if n in gesture_model.classes_]
    thieu = [n for n in CAC_CU_CHI_THU_THACH if n not in cac_nhan]
    if CHE_DO_CU_CHI == "co_dinh":
        if any(n not in gesture_model.classes_ for n in MAT_KHAU_CU_CHI):
            print("Thieu du lieu cu chi cho mat khau - hay chay thu_thap_dataset.py")
    else:
        if thieu:
            print("Thieu du lieu cu chi:", ", ".join(thieu), "- hay chay thu_thap_dataset.py")
        if len(cac_nhan) < 2:
            print(f"Chi co {len(cac_nhan)} cu chi - dung 1 cu chi co dinh {CU_CHI_MO_KHOA}")

    global client_mqtt
    client_mqtt = ket_noi_mqtt()
    hands = mp.solutions.hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.5)
    ve = mp.solutions.drawing_utils
    threading.Thread(target=chay_web, daemon=True).start()
    kiem_tra_token()
    if not kiem_tra_camera():
        print(f"Khong ket noi duoc camera {NGUON_CAMERA} - kiem tra IP Webcam va laptop cung mang wifi")
        client_mqtt.loop_stop()
        return
    camera = LuongCamera()

    trang_thai = "QUET"
    dem_dung = dem_sai = dem_cu_chi = 0
    nguoi = ""
    moc = 0
    thu_thach = []
    buoc = 0
    han_buoc_ok = 0
    so_khung_cu = 0
    bat_dau_la = lan_thay_la = 0
    da_bao_khach = False
    bat_dau_tay = lan_thay_tay = 0
    dem_lan_sai = 0
    da_bao_khong_phan_hoi = da_bao_mo = False
    thong_bao_sai = ""
    mau_sai = (0, 165, 255)
    han_thong_bao = 0

    while True:
        so_khung_cu, frame = camera.lay_moi(so_khung_cu)
        if frame is None:
            if cv2.waitKey(10) & 0xFF == ord("q"):
                break
            continue
        frame_goc = frame.copy()
        with khoa_tt:
            frame_hien_tai = frame_goc
        bay_gio = time.time()

        if trang_thai == "QUET":
            thay_mat, ten_hien, _ = nhan_dien_mat(frame, embeddings)

            la_gan = thay_mat and not ten_hien
            if not thay_mat:
                dem_dung = 0
            elif ten_hien:
                dem_dung += 1
            else:
                dem_dung = 0

            viet(frame, "Dang quet khuon mat...", 1)
            if bay_gio < han_thong_bao:
                viet(frame, thong_bao_sai, 2, mau_sai)

            if la_gan:
                if not bat_dau_la:
                    bat_dau_la = bay_gio
                lan_thay_la = bay_gio
            elif bat_dau_la and bay_gio - lan_thay_la > THOI_GIAN_MAT_DAU:
                bat_dau_la = 0
                da_bao_khach = False
                bat_dau_tay = 0

            if dem_dung >= SO_KHUNG_XAC_NHAN:
                nguoi = ten_hien
                trang_thai = "CHO_CU_CHI"
                moc = bay_gio
                buoc = 0
                if CHE_DO_CU_CHI == "co_dinh":
                    thu_thach = list(MAT_KHAU_CU_CHI)
                else:
                    thu_thach = tao_thu_thach(cac_nhan)
                    print("Thu thach:", " -> ".join(thu_thach))
                dem_dung = dem_cu_chi = dem_sai = 0
                bat_dau_la = bat_dau_tay = 0
                da_bao_khach = False
            elif bat_dau_la:
                dung_la = bay_gio - bat_dau_la
                viet(frame, f"CO KHACH - cua dang khoa ({dung_la:.0f}s)", 3, (0, 0, 255))

                kq = hands.process(cv2.cvtColor(frame_goc, cv2.COLOR_BGR2RGB))
                if kq.multi_hand_landmarks:
                    if not bat_dau_tay:
                        bat_dau_tay = bay_gio
                    lan_thay_tay = bay_gio
                elif bat_dau_tay and bay_gio - lan_thay_tay > THOI_GIAN_MAT_TAY:
                    bat_dau_tay = 0

                if dung_la >= THOI_GIAN_LA_KHACH and not da_bao_khach:
                    da_bao_khach = True
                    gui_co_khach(frame_goc)
                if dung_la >= THOI_GIAN_BAO_DONG or (bat_dau_tay and bay_gio - bat_dau_tay >= THOI_GIAN_TAY_BAO_DONG):
                    bao_dong(frame_goc)
                    bat_dau_tay = 0

        elif trang_thai == "CHO_CU_CHI":
            con_lai = THOI_GIAN_MOI_BUOC - (bay_gio - moc)
            can_gio = thu_thach[buoc]
            co_dinh = CHE_DO_CU_CHI == "co_dinh"
            if co_dinh:
                yeu_cau = f"Nhap mat khau cu chi {buoc + 1}/{len(thu_thach)}"
            else:
                yeu_cau = f"Gio {doc_nhan(can_gio)}"
            su_kien["yeu_cau"] = yeu_cau
            thay_mat, ten_hien, qua_xa = nhan_dien_mat(frame, embeddings)
            dung_nguoi = ten_hien == nguoi
            if qua_xa:
                dem_sai = 0
            elif thay_mat and not dung_nguoi:
                dem_sai += 1
            elif dung_nguoi:
                dem_sai = 0

            kq =hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            cu_chi = "Khong thay tay"

            if kq.multi_hand_landmarks:
                lm = kq.multi_hand_landmarks[0]
                ve.draw_landmarks(frame, lm, mp.solutions.hands.HAND_CONNECTIONS)
                xac_suat = gesture_model.predict_proba([chuan_hoa(lm)])[0]
                i = xac_suat.argmax()
                cu_chi = gesture_model.classes_[i] if xac_suat[i] >= NGUONG_TIN_CAY_CU_CHI else "Khong ro"

            dem_cu_chi = dem_cu_chi + 1 if cu_chi == can_gio and dung_nguoi else 0

            if co_dinh:
                viet(frame, f"Nhap mat khau cu chi - Buoc {buoc + 1}/{len(thu_thach)}", 1, (0, 255, 0), 0.9)
                if bay_gio < han_buoc_ok:
                    viet(frame, f"Buoc {buoc}/{len(thu_thach)}: OK", 3, (0, 255, 0))
            else:
                viet(frame, f"Buoc {buoc + 1}/{len(thu_thach)}: {yeu_cau}", 1, (0, 255, 0), 1.0)
                viet(frame, f"Cu chi: {doc_nhan(cu_chi)}", 3)
            viet(frame, f"Xin chao {nguoi}", 2, (0, 255, 0))
            viet(frame, f"Con lai: {max(con_lai, 0):.0f}s", 4)

            if dem_sai >= SO_KHUNG_NGUOI_LA:
                bao_dong(frame_goc)
                trang_thai = "QUET"
                dem_dung = dem_sai = dem_cu_chi = 0
            elif dem_cu_chi >= SO_KHUNG_CU_CHI:
                buoc += 1
                dem_cu_chi = 0
                moc = bay_gio
                han_buoc_ok = bay_gio + 1.5
                if co_dinh:
                    print(f"Buoc {buoc} dung")
                if buoc >= len(thu_thach):
                    dem_lan_sai = 0
                    if gui_lenh("O", nguoi):
                        da_bao_khong_phan_hoi = da_bao_mo = False
                        trang_thai = "DA_MO"
                    else:
                        thong_bao_sai = "Khong mo duoc khoa"
                        mau_sai = (0, 0, 255)
                        han_thong_bao = bay_gio + THOI_GIAN_HIEN_SAI
                        trang_thai = "QUET"
            elif con_lai <= 0:
                print("Sai mat khau" if co_dinh else f"Het gio o buoc {buoc + 1}/{len(thu_thach)}")
                dem_lan_sai += 1
                thong_bao_sai = f"Sai cu chi ({dem_lan_sai}/{SO_LAN_SAI_TOI_DA})"
                mau_sai = (0, 165, 255)
                han_thong_bao = bay_gio + THOI_GIAN_HIEN_SAI
                if dem_lan_sai >= SO_LAN_SAI_TOI_DA:
                    bao_dong(frame_goc)
                    dem_lan_sai = 0
                trang_thai = "QUET"
                dem_dung = dem_sai = dem_cu_chi = 0

        elif trang_thai == "DA_MO":
            with khoa_tt:
                da_nhan = thoi_nhan_khoa_mo > thoi_gui_mo
                cho_lau = bay_gio - thoi_gui_mo > THOI_GIAN_CHO_KHOA_MO
            if da_nhan:
                viet(frame, "DA MO KHOA", 1, (0, 255, 0))
                if not da_bao_mo:
                    da_bao_mo = True
                    them_su_kien(f"{nguoi} mo bang khuon mat + cu chi")
                    if duoc_gui(f"mo_cu_chi_{nguoi}"):
                        gui_mo_cua(f"{nguoi} da mo cua bang khuon mat + cu chi")
            elif cho_lau:
                viet(frame, "ESP32 KHONG PHAN HOI", 1, (0, 0, 255))
                if not da_bao_khong_phan_hoi:
                    da_bao_khong_phan_hoi = True
                    print("ESP32 khong phan hoi - relay chua chay")
            else:
                viet(frame, "Dang mo khoa...", 1, (0, 255, 255))
            if bay_gio - moc > THOI_GIAN_MO_CUA:
                trang_thai = "QUET"

        if trang_thai != "CHO_CU_CHI":
            su_kien["yeu_cau"] = ""

        chu, mau = chu_cua_khoa()
        cao = frame.shape[0]
        with khoa_tt:
            thong_bao, la_loi = thong_bao_cuoi, thong_bao_la_loi
        with khoa_tt:
            chu_the, mau_the, het_the = thong_bao_the
        if bay_gio < het_the:
            viet(frame, chu_the, 5, mau_the)
        if trang_thai_esp != "ONLINE":
            cv2.putText(frame, "CHUA KET NOI ESP32", (10, cao - 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        cv2.putText(frame, chu, (10, cao - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, mau, 2)
        cv2.putText(frame, thong_bao, (10, cao - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (0, 0, 255) if la_loi else (255, 255, 255), 2)

        cv2.imshow("Camera khoa chong trom", frame)
        phim = cv2.waitKey(1) & 0xFF
        if phim == ord("q"):
            break
        if phim == ord("s"):
            dung_am()
            with khoa_tt:
                het_bao_dong = 0
            client_mqtt.publish(CHU_DE_LENH, "S", qos=1)
            print("Gui lenh: S")

    camera.dung()
    cv2.destroyAllWindows()
    client_mqtt.loop_stop()
    client_mqtt.disconnect()


if __name__ == "__main__":
    main()
