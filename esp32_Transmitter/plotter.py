import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import time
import threading

# --- ตั้งค่า ---
# TODO: แก้ไขให้ตรงกับ Port ของ ESP32 Gateway Node ของคุณ
# Windows: 'COM3', 'COM4', ...
# macOS: '/dev/cu.usbserial-xxxx'
# Linux: '/dev/ttyUSB0', '/dev/ttyACM0', ...
SERIAL_PORT = 'COM7'  
BAUD_RATE = 115200
MAX_POINTS = 50  # จำนวนจุดสูงสุดที่จะแสดงบนกราฟ

# --- ตัวแปรสำหรับเก็บข้อมูล ---
times = deque(maxlen=MAX_POINTS)
distances = deque(maxlen=MAX_POINTS)
start_time = time.time()

# --- ตั้งค่ากราฟ ---
fig, ax = plt.subplots()
line, = ax.plot([], [], 'r-o', markersize=4, label="Distance")

def setup_plot():
    """ตั้งค่าเริ่มต้นของกราฟ"""
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 10) # ตั้งค่าแกน Y เริ่มต้น (จะปรับอัตโนมัติ)
    ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("Distance (meters)")
    ax.set_title("Real-time Distance Measurement (RSSI-based)")
    ax.legend()
    ax.grid(True)
    return line,

def update_plot(frame):
    """ฟังก์ชันสำหรับอัปเดตกราฟในแต่ละเฟรม"""
    # ปรับปรุงขอบเขตแกน X ให้เลื่อนตามเวลา
    if times:
        last_time = times[-1]
        if last_time > ax.get_xlim()[1]:
             ax.set_xlim(last_time - (MAX_POINTS * 1.1), last_time + 5)
    
    # ปรับปรุงขอบเขตแกน Y อัตโนมัติ
    if distances:
        min_dist = min(distances)
        max_dist = max(distances)
        ax.set_ylim(min_dist - 1, max_dist + 1)

    line.set_data(list(times), list(distances))
    return line,

def serial_reader_thread(ser):
    """ฟังก์ชันสำหรับอ่านข้อมูลจาก Serial Port ใน Thread แยก"""
    while ser.is_open:
        try:
            line_str = ser.readline().decode('utf-8').strip()
            if line_str.startswith("Distance:"):
                try:
                    dist_val = float(line_str.split(':')[1])
                    current_time = time.time() - start_time
                    
                    # เพิ่มข้อมูลใหม่เข้าไปใน Deque
                    times.append(current_time)
                    distances.append(dist_val)
                    
                    print(f"Time: {current_time:.2f}s, Distance: {dist_val:.2f}m")
                except (ValueError, IndexError):
                    # ข้ามบรรทัดที่ข้อมูลไม่สมบูรณ์
                    pass
        except serial.SerialException:
            print("Serial port disconnected. Exiting thread.")
            break
        except Exception as e:
            print(f"An error occurred in serial thread: {e}")
            break


if __name__ == '__main__':
    try:
        # เริ่มการเชื่อมต่อ Serial
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} bps.")

        # เริ่ม Thread สำหรับการอ่านข้อมูล Serial
        reader_thread = threading.Thread(target=serial_reader_thread, args=(ser,), daemon=True)
        reader_thread.start()

        # ใช้ animation เพื่ออัปเดตกราฟแบบ real-time
        ani = animation.FuncAnimation(fig, update_plot, init_func=setup_plot, blit=False, interval=200, save_count=10)
        
        plt.show()

    except serial.SerialException as e:
        print(f"Error: Could not open serial port {SERIAL_PORT}. Please check the port name and permissions.")
        print(f"Details: {e}")
    except KeyboardInterrupt:
        print("Program terminated by user.")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Serial port closed.")