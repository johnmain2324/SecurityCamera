import threading
import time
import cv2
from cau_hinh_bi_mat import TOKEN_BAO_DONG, TOKEN_CHUONG, CHAT_ID

NGUON_CAMERA = "http://192.168.1.3:8080/video"
THOI_GIAN_MO_CAMERA = 8
LAT_ANH = False
XOAY_ANH = None

THOI_GIAN_CHO_BAO_DONG = 15
PHAT_AM_LAPTOP = True
TI_LE_MAT_GAN = 0.18
THOI_GIAN_LA_KHACH = 3
THOI_GIAN_BAO_DONG = 15
SO_LAN_SAI_TOI_DA = 3
THOI_GIAN_MAT_DAU = 2
MAT_KHAU_CU_CHI = ["so_2", "nam_tay"]
CHE_DO_CU_CHI = "co_dinh"
CAC_CU_CHI_THU_THACH = ["so_1", "so_2", "so_3", "so_4", "so_5"]
DO_DAI_THU_THACH = 2
THOI_GIAN_MOI_BUOC = 8
NGUONG_TIN_CAY_CU_CHI = 0.8


def xu_ly_khung(frame):
    if LAT_ANH:
        frame = cv2.flip(frame, 1)
    if XOAY_ANH is not None:
        frame = cv2.rotate(frame, XOAY_ANH)
    return frame


def kiem_tra_camera(nguon=NGUON_CAMERA):
    ket_qua = []

    def thu_mo():
        cap = cv2.VideoCapture(nguon)
        ket_qua.append(cap.isOpened() and cap.read()[0])
        cap.release()

    threading.Thread(target=thu_mo, daemon=True).start()
    for _ in range(THOI_GIAN_MO_CAMERA * 10):
        if ket_qua:
            break
        time.sleep(0.1)
    return bool(ket_qua and ket_qua[0])


class LuongCamera:
    def __init__(self, nguon=NGUON_CAMERA):
        self.nguon = nguon
        self.khung = None
        self.so_khung = 0
        self.khoa = threading.Lock()
        self.chay = True
        threading.Thread(target=self.doc, daemon=True).start()

    def doc(self):
        while self.chay:
            cap = cv2.VideoCapture(self.nguon)
            while self.chay:
                ok, khung = cap.read()
                if not ok:
                    break
                with self.khoa:
                    self.khung = khung
                    self.so_khung += 1
            cap.release()
            if self.chay:
                print("Mat ket noi camera - thu ket noi lai sau 2 giay")
                time.sleep(2)

    def lay_moi(self, so_cu):
        with self.khoa:
            if self.khung is None or self.so_khung == so_cu:
                return so_cu, None
            return self.so_khung, xu_ly_khung(self.khung.copy())

    def dung(self):
        self.chay = False
