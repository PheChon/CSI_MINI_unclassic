import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import time
import threading

# --- การตั้งค่า (CONFIGURATION) ---
SERIAL_PORT = 'COM10' # TODO: แก้ไข Port ให้ถูกต้อง
BAUD_RATE = 115200
POINTS_TO_SHOW = 100000 # แสดง 100 จุดล่าสุด

# --- ตัวแปรสำหรับเก็บข้อมูล ---
times = deque(maxlen=POINTS_TO_SHOW)
distances = deque(maxlen=POINTS_TO_SHOW)
start_time = time.time()
ser = None

# --- ตั้งค่ากราฟ ---
plt.style.use('seaborn-v0_8-darkgrid')
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
        time_window = max(20, times[-1])
        ax.set_xlim(max(0, time_window - 20), time_window + 2)
    
        min_dist = min(distances)
        max_dist = max(distances)
        ax.set_ylim(min_dist - 1, max_dist + 1)

    line.set_data(list(times), list(distances))
    return line,

def serial_reader_thread():
    """ฟังก์ชันสำหรับอ่านข้อมูลจาก Serial และดึงเฉพาะค่า Distance"""
    global ser
    while True:
        try:
            if not ser or not ser.is_open: break
            line_str = ser.readline().decode('utf-8').strip()
            
            # --- Logic การอ่านข้อมูลที่แก้ไขแล้ว ---
            if "Distance:" in line_str:
                # แยกข้อมูลด้วย ',' ก่อน แล้วเอาส่วนท้ายมาทำงานต่อ
                dist_part = line_str.split(',')[-1]
                # แยกด้วย ':' แล้วเอาค่าตัวเลข
                dist_val = float(dist_part.split(':')[1])
                
                current_time = time.time() - start_time
                
                times.append(current_time)
                distances.append(dist_val)
            # ----------------------------------------
        except (serial.SerialException, TypeError, OSError, ValueError, IndexError):
            break

# --- ส่วนการทำงานหลัก ---
if __name__ == '__main__':
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} bps.")

        reader_thread = threading.Thread(target=serial_reader_thread, args=(), daemon=True)
        reader_thread.start()

        ani = animation.FuncAnimation(fig, update_plot, init_func=setup_plot, blit=False, interval=100)
        plt.show()

    except serial.SerialException as e:
        print(f"Error: Could not open port {SERIAL_PORT}. Please check the port name.")
    finally:
        if ser and ser.is_open:
            ser.close()
            print("Serial port closed.")