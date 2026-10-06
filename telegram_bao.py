import threading
import time
import cv2
import requests
from cau_hinh import TOKEN_BAO_DONG, TOKEN_CHUONG, CHAT_ID

TIMEOUT = 10


def bay_gio_chu():
    return time.strftime("%H:%M:%S %d/%m/%Y")


def chay_nen(ham, *tham_so):
    threading.Thread(target=ham, args=tham_so, daemon=True).start()


def gui_anh(token, frame, noi_dung):
    try:
        ok, jpg = cv2.imencode(".jpg", frame)
        if not ok:
            return
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendPhoto",
            data={"chat_id": CHAT_ID, "caption": noi_dung},
            files={"photo": ("canh_bao.jpg", jpg.tobytes(), "image/jpeg")},
            timeout=TIMEOUT,
        )
        if not r.ok:
            print("Telegram bao dong loi:", r.text)
    except requests.RequestException as e:
        print("Telegram bao dong loi mang:", e)


def gui_tin(noi_dung):
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TOKEN_CHUONG}/sendMessage",
            data={"chat_id": CHAT_ID, "text": noi_dung},
            timeout=TIMEOUT,
        )
        if not r.ok:
            print("Telegram chuong loi:", r.text)
    except requests.RequestException as e:
        print("Telegram chuong loi mang:", e)


def gui_bao_dong(frame):
    chay_nen(gui_anh, TOKEN_BAO_DONG, frame.copy(), f"CANH BAO: Phat hien nguoi la luc {bay_gio_chu()}")


def gui_co_khach(frame):
    chay_nen(gui_anh, TOKEN_CHUONG, frame.copy(), f"Co nguoi truoc cua luc {time.strftime('%H:%M:%S')}")


def gui_mo_cua(noi_dung):
    chay_nen(gui_tin, noi_dung)


def gui_the_la(frame):
    chay_nen(gui_anh, TOKEN_BAO_DONG, frame.copy(), "CANH BAO: quet the la 3 lan o cua")


def kiem_tra_token():
    ok = True
    for ten, token in (("TOKEN_BAO_DONG", TOKEN_BAO_DONG), ("TOKEN_CHUONG", TOKEN_CHUONG)):
        try:
            if not requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=TIMEOUT).ok:
                print("Telegram: sai", ten)
                ok = False
        except requests.RequestException as e:
            print("Telegram: loi mang khi kiem tra", ten, "-", e)
            ok = False
    if ok:
        print("Telegram: OK")
