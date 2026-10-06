import cv2

# IP Webcam (Android): dùng http, đường dẫn /video là luồng MJPEG
URL = "http://192.168.1.133:8080/video"

cap = cv2.VideoCapture(URL)
if not cap.isOpened():
    raise SystemExit(f"Không kết nối được tới {URL}")

while True:
    ok, frame = cap.read()
    if not ok:
        print("Mất khung hình, thoát.")
        break
    cv2.imshow("IP Webcam", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
