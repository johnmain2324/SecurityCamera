import os
import winsound

THU_MUC = os.path.dirname(os.path.abspath(__file__))


def phat_am(ten_file):
    duong_dan = os.path.join(THU_MUC, ten_file)
    if not os.path.isfile(duong_dan):
        print("Khong tim thay file am thanh:", duong_dan)
        return
    winsound.PlaySound(duong_dan, winsound.SND_FILENAME | winsound.SND_ASYNC)


def dung_am():
    winsound.PlaySound(None, winsound.SND_PURGE)
