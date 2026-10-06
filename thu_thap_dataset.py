import os
import csv
import math
import time
import cv2
import mediapipe as mp
import train_dataset
from cau_hinh import LuongCamera, MAT_KHAU_CU_CHI

FACE_DIR = "dataset/faces"
GESTURE_DIR = "dataset/gestures"
SO_ANH_MAT = 100
SO_MAU_CU_CHI = 200
SO_MAU_MOI_CU_CHI = 100
THOI_GIAN_DEM_NGUOC = 3

detector = cv2.FaceDetectorYN.create("models/face_detection_yunet_2023mar.onnx", "", (320, 320), 0.8)
recognizer = cv2.FaceRecognizerSF.create("models/face_recognition_sface_2021dec.onnx", "")


def chuan_hoa(hand_landmarks):
    pts = [(lm.x, lm.y) for lm in hand_landmarks.landmark]
    x0, y0 = pts[0]
    pts = [(x - x0, y - y0) for x, y in pts]
    m = max(max(abs(x), abs(y)) for x, y in pts) or 1
    return [v / m for p in pts for v in p]


def thu_khuon_mat():
    ten = input("Nhap ten nguoi (khong dau, vd: tin): ").strip()
    thu_muc = os.path.join(FACE_DIR, ten)
    os.makedirs(thu_muc, exist_ok=True)
    bat_dau = len(os.listdir(thu_muc))

    camera = LuongCamera()
    so_khung_cu = 0
    dem = 0
    khung = 0
    dang_chup = False

    while dem < SO_ANH_MAT:
        so_khung_cu, frame = camera.lay_moi(so_khung_cu)
        if frame is None:
            if cv2.waitKey(10) & 0xFF == ord("q"):
                break
            continue
        detector.setInputSize((frame.shape[1], frame.shape[0]))
        _, mats = detector.detect(frame)
        mats = [] if mats is None else mats

        khung += 1
        if dang_chup and len(mats) == 1 and khung % 3 == 0:
            mat = recognizer.alignCrop(frame, mats[0])
            cv2.imwrite(os.path.join(thu_muc, f"{bat_dau + dem}.jpg"), mat)
            dem += 1

        for m in mats:
            x, y, w, h = m[:4].astype(int)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        trang_thai = "DANG CHUP - xoay nhe dau" if dang_chup else "Nhan S de bat dau chup"
        cv2.putText(frame, trang_thai, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, f"Anh: {dem}/{SO_ANH_MAT}  (Q: thoat)", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.imshow("Thu thap khuon mat", frame)

        phim = cv2.waitKey(1) & 0xFF
        if phim == ord("s"):
            dang_chup = not dang_chup
        elif phim == ord("q"):
            break

    camera.dung()
    cv2.destroyAllWindows()
    print(f"Da luu {dem} anh vao {thu_muc}")


def thu_cu_chi():
    nhan = input("Nhap ten cu chi (vd: so_2 hoac khac): ").strip()
    os.makedirs(GESTURE_DIR, exist_ok=True)
    duong_dan = os.path.join(GESTURE_DIR, f"{nhan}.csv")

    hands = mp.solutions.hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
    ve = mp.solutions.drawing_utils
    camera = LuongCamera()
    so_khung_cu = 0
    dem = 0
    dang_ghi = False

    with open(duong_dan, "a", newline="") as f:
        writer = csv.writer(f)
        while dem < SO_MAU_CU_CHI:
            so_khung_cu, frame = camera.lay_moi(so_khung_cu)
            if frame is None:
                if cv2.waitKey(10) & 0xFF == ord("q"):
                    break
                continue
            kq = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            if kq.multi_hand_landmarks:
                lm = kq.multi_hand_landmarks[0]
                ve.draw_landmarks(frame, lm, mp.solutions.hands.HAND_CONNECTIONS)
                if dang_ghi:
                    writer.writerow(chuan_hoa(lm))
                    dem += 1

            trang_thai = "DANG GHI - di chuyen tay nhe" if dang_ghi else "Nhan S de bat dau ghi"
            cv2.putText(frame, f"Cu chi: {nhan}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(frame, trang_thai, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(frame, f"Mau: {dem}/{SO_MAU_CU_CHI}  (Q: thoat)", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.imshow("Thu thap cu chi", frame)

            phim = cv2.waitKey(1) & 0xFF
            if phim == ord("s"):
                dang_ghi = not dang_ghi
            elif phim == ord("q"):
                break

    camera.dung()
    cv2.destroyAllWindows()
    print(f"Da luu {dem} mau vao {duong_dan}")


def thu_mat_khau():
    cac_nhan = MAT_KHAU_CU_CHI
    so_cu_chi = len(cac_nhan)
    xoa = input("Xoa du lieu cu cua cac cu chi mat khau? (y/n): ").strip().lower() == "y"
    os.makedirs(GESTURE_DIR, exist_ok=True)

    hands = mp.solutions.hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
    ve = mp.solutions.drawing_utils
    camera = LuongCamera()
    so_khung_cu = 0
    tat_ca = {}
    huy = False

    for i, nhan in enumerate(cac_nhan):
        mau = []
        pha = "cho" if i == 0 else "dem"
        moc = time.time()
        while len(mau) < SO_MAU_MOI_CU_CHI and not huy:
            so_khung_cu, frame = camera.lay_moi(so_khung_cu)
            if frame is None:
                if cv2.waitKey(10) & 0xFF == ord("q"):
                    huy = True
                continue
            kq = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            if kq.multi_hand_landmarks:
                lm = kq.multi_hand_landmarks[0]
                ve.draw_landmarks(frame, lm, mp.solutions.hands.HAND_CONNECTIONS)
                if pha == "ghi":
                    mau.append(chuan_hoa(lm))

            if pha == "dem":
                con_lai = THOI_GIAN_DEM_NGUOC - (time.time() - moc)
                if con_lai <= 0:
                    pha = "ghi"
                else:
                    chu = f"DOI CU CHI - bat dau sau {math.ceil(con_lai)} giay"
            if pha == "cho":
                chu = f"Cu chi {i + 1}/{so_cu_chi} - nhan S de bat dau"
            elif pha == "ghi":
                chu = f"Cu chi {i + 1}/{so_cu_chi} - Mau: {len(mau)}/{SO_MAU_MOI_CU_CHI}"
            cv2.putText(frame, chu, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(frame, "(Q: huy)", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.imshow("Thu mat khau cu chi", frame)

            phim = cv2.waitKey(1) & 0xFF
            if phim == ord("s") and pha == "cho":
                pha = "ghi"
            elif phim == ord("q"):
                huy = True
        if huy:
            break
        tat_ca[nhan] = mau

    camera.dung()
    cv2.destroyAllWindows()
    if huy:
        print("Da huy - khong luu gi")
        return

    for nhan, mau in tat_ca.items():
        with open(os.path.join(GESTURE_DIR, f"{nhan}.csv"), "w" if xoa else "a", newline="") as f:
            csv.writer(f).writerows(mau)
    print(f"Da luu {SO_MAU_MOI_CU_CHI} mau cho moi cu chi trong {so_cu_chi} cu chi mat khau")

    if input("Train luon? (y/n): ").strip().lower() == "y":
        train_dataset.train_cu_chi()


def main():
    while True:
        print("\n===== THU THAP DATASET =====")
        print("1. Thu khuon mat")
        print("2. Thu cu chi ban tay")
        print("3. Thu mat khau cu chi (2 cu chi lien tiep)")
        print("0. Thoat")
        chon = input("Chon: ").strip()
        if chon == "1":
            thu_khuon_mat()
        elif chon == "2":
            thu_cu_chi()
        elif chon == "3":
            thu_mat_khau()
        elif chon == "0":
            break


if __name__ == "__main__":
    main()
