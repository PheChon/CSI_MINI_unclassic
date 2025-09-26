import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from collections import deque

# ---!!! ตั้งค่าที่สำคัญ !!!---
SERIAL_PORT = 'COM10'  # <--- แก้ไข Port ของคุณตรงนี้
BAUD_RATE = 115200
NUM_SUBcarriers = 64

# ---!!! ค่าสำหรับปรับความนิ่ง (Smoothing) !!!---
# ยิ่งค่าสูง กราฟจะยิ่งนิ่งแต่จะตอบสนองช้าลง (แนะนำ: 3-10)
SMOOTHING_WINDOW_SIZE = 5

# --- ตัวแปรสำหรับเก็บข้อมูล ---
ser = None
# ใช้ deque เพื่อเก็บข้อมูล CSI ย้อนหลังตามขนาดของ window
csi_history = deque(maxlen=SMOOTHING_WINDOW_SIZE) 
latest_smoothed_csi = np.zeros(NUM_SUBcarriers)

# --- ตั้งค่ากราฟ (ปรับขนาดให้กว้างขึ้น) ---
# figsize=(width, height) หน่วยเป็นนิ้ว
fig, ax = plt.subplots(figsize=(12, 6)) # <--- ปรับขนาดกราฟตรงนี้
bars = ax.bar(range(NUM_SUBcarriers), latest_smoothed_csi)

ax.set_ylim(0, 40)
ax.set_xlabel('Subcarrier Index')
ax.set_ylabel('Amplitude')
ax.set_title(f'Real-time CSI Amplitude (Smoothed over {SMOOTHING_WINDOW_SIZE} frames)')

def init_serial():
    global ser
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        # เคลียร์ buffer เก่าที่อาจค้างอยู่
        ser.flushInput()
        print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} bps.")
        return True
    except serial.SerialException as e:
        print(f"Error: Could not open serial port {SERIAL_PORT}. {e}")
        return False

# --- ฟังก์ชันสำหรับอัปเดตกราฟ ---
def update_graph(frame):
    global latest_smoothed_csi
    if ser and ser.is_open:
        try:
            line = ser.readline().decode('utf-8').strip()
            
            if line.startswith('CSI_DATA,'):
                parts = line.split(',')[1:]
                csi_values = np.array([float(p) for p in parts if p], dtype=float)
                
                # เพิ่มข้อมูลใหม่เข้าไปใน history
                if len(csi_values) > 0:
                    full_csi_frame = np.zeros(NUM_SUBcarriers)
                    num_received = len(csi_values)
                    full_csi_frame[:num_received] = csi_values
                    csi_history.append(full_csi_frame)

                # --- ส่วนของการทำ Smoothing ---
                # คำนวณค่าเฉลี่ยจากข้อมูลใน history
                if len(csi_history) > 0:
                    latest_smoothed_csi = np.mean(csi_history, axis=0)
                
                # อัปเดตความสูงของแท่งกราฟ
                for bar, height in zip(bars, latest_smoothed_csi):
                    bar.set_height(height)

        except Exception as e:
            pass
    return bars

# --- เริ่มการทำงาน ---
if init_serial():
    ani = animation.FuncAnimation(fig, update_graph, blit=True, interval=20, save_count=0)
    plt.show()
    ser.close()
    print("Serial port closed.")