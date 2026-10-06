import os
import csv
import pickle
import cv2
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split

FACE_DIR = "dataset/faces"
GESTURE_DIR = "dataset/gestures"
MODEL_DIR = "models"


def train_khuon_mat():
    recognizer = cv2.FaceRecognizerSF.create(os.path.join(MODEL_DIR, "face_recognition_sface_2021dec.onnx"), "")
    embeddings = {}
    if os.path.isdir(FACE_DIR):
        for ten in sorted(os.listdir(FACE_DIR)):
            thu_muc = os.path.join(FACE_DIR, ten)
            if not os.path.isdir(thu_muc):
                continue
            ds = []
            for file in os.listdir(thu_muc):
                img = cv2.imread(os.path.join(thu_muc, file))
                if img is not None:
                    ds.append(recognizer.feature(cv2.resize(img, (112, 112))).flatten())
            if ds:
                embeddings[ten] = np.array(ds)

    if not embeddings:
        print("Chua co anh khuon mat. Hay chay thu_thap_dataset.py truoc.")
        return

    with open(os.path.join(MODEL_DIR, "face_embeddings.pkl"), "wb") as f:
        pickle.dump(embeddings, f)
    tong = sum(len(v) for v in embeddings.values())
    print(f"Train khuon mat xong: {tong} anh, {len(embeddings)} nguoi: {list(embeddings)}")


def train_cu_chi():
    X, y = [], []
    for file in os.listdir(GESTURE_DIR):
        if not file.endswith(".csv"):
            continue
        nhan = file[:-4]
        with open(os.path.join(GESTURE_DIR, file)) as f:
            for dong in csv.reader(f):
                if len(dong) == 42:
                    X.append([float(v) for v in dong])
                    y.append(nhan)

    if len(set(y)) < 2:
        print("Can it nhat 2 cu chi (vd: so_2 va khac). Hay thu them.")
        return

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    model = KNeighborsClassifier(n_neighbors=5)
    model.fit(X_train, y_train)
    print(f"Do chinh xac tren tap test: {model.score(X_test, y_test) * 100:.1f}%")

    model.fit(X, y)
    with open(os.path.join(MODEL_DIR, "gesture_model.pkl"), "wb") as f:
        pickle.dump(model, f)
    print(f"Train cu chi xong: {len(X)} mau, cac lop: {sorted(set(y))}")


def main():
    os.makedirs(MODEL_DIR, exist_ok=True)
    train_khuon_mat()
    train_cu_chi()


if __name__ == "__main__":
    main()
