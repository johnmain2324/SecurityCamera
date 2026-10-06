import time
import serial
import serial.tools.list_ports

for p in serial.tools.list_ports.comports():
    print("Cong:", p.device, "|", p.description, "| VID:", hex(p.vid or 0))

CONG = "COM4"

for dtr, rts in [(True, True), (True, False), (False, False)]:
    print(f"\n--- Thu DTR={dtr} RTS={rts} ---")
    s = serial.Serial()
    s.port = CONG
    s.baudrate = 115200
    s.timeout = 1
    s.dtr = dtr
    s.rts = rts
    s.open()
    time.sleep(2)
    print("ESP32 noi:", s.read(200))
    s.write(b"O")
    s.flush()
    time.sleep(1)
    print("Phan hoi:", s.read(200))
    s.close()
    time.sleep(7)