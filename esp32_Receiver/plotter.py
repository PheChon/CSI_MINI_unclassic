import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import time
import threading

# --- การตั้งค่า (CONFIGURATION) ---
# TODO: แก้ไขให้ตรงกับ Port ของ ESP32 Gateway Node ของคุณ
SERIAL_PORT = 'COM3'  
BAUD_RATE = 115200

# ## ปรับแก้ที่นี่ ##
# จำนวนจุดข้อมูลล่าสุดที่จะแสดงบนกราฟ
# ยิ่งค่ามาก จุดยิ่งค้างอยู่บนกราฟนานขึ้น
POINTS_TO_SHOW = 100000

# --- ตัวแปรสำหรับเก็บข้อมูล ---
times = deque(maxlen=POINTS_TO_SHOW)
distances = deque(maxlen=POINTS_TO_SHOW)
start_time = time.time()

# --- ตั้งค่ากราฟ ---
fig, ax = plt.subplots()
line, = ax.plot([], [], 'r-o', markersize=3, label="Distance")

def setup_plot():
    """ตั้งค่าเริ่มต้นของกราฟ"""
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 10) 
    ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("Distance (meters)")
    ax.set_title("Real-time Distance Measurement")
    ax.legend()
    ax.grid(True)
    fig.tight_layout()
    return line,

def update_plot(frame):
    """ฟังก์ชันสำหรับอัปเดตกราฟในแต่ละเฟรม"""
    if times:
        # ปรับปรุงขอบเขตแกน X ให้เป็นหน้าต่างที่เลื่อนตามเวลา
        time_window = max(20, times[-1]) # ให้หน้าต่างกว้างอย่างน้อย 20 วินาที
        ax.set_xlim(max(0, time_window - 20), time_window + 2)
    
        # ปรับปรุงขอบเขตแกน Y อัตโนมัติ
        min_dist = min(distances)
        max_dist = max(distances)
        ax.set_ylim(min_dist - 1, max_dist + 1)

    # วาดข้อมูลทั้งหมดที่อยู่ใน deque (ซึ่งมีจำนวนไม่เกิน POINTS_TO_SHOW)
    line.set_data(list(times), list(distances))
    return line,

def serial_reader_thread(ser):
    """ฟังก์ชันสำหรับอ่านข้อมูลจาก Serial Port ใน Thread แยก"""
    while True:
        try:
            if not ser.is_open:
                break
            line_str = ser.readline().decode('utf-8').strip()
            if line_str.startswith("Distance:"):
                try:
                    dist_val = float(line_str.split(':')[1])
                    current_time = time.time() - start_time
                    times.append(current_time)
                    distances.append(dist_val)
                except (ValueError, IndexError):
                    pass
        except (serial.SerialException, TypeError, OSError):
            print("Serial port closed or error. Exiting thread.")
            break

# --- ส่วนการทำงานหลัก ---
if __name__ == '__main__':
    ser = None
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} bps.")

        reader_thread = threading.Thread(target=serial_reader_thread, args=(ser,), daemon=True)
        reader_thread.start()

        ani = animation.FuncAnimation(fig, update_plot, init_func=setup_plot, blit=False, interval=100)
        
        plt.show()

    except serial.SerialException as e:
        print(f"Error: Could not open serial port {SERIAL_PORT}. Please check the port name.")
    except KeyboardInterrupt:
        print("Program terminated by user.")
    finally:
        if ser and ser.is_open:
            ser.close()
            print("Serial port closed.")