import serial
import time

# ---!!! ตั้งค่าที่สำคัญ !!!---
SERIAL_PORT = 'COM10'  # <--- แก้ไข Port ของคุณตรงนี้
BAUD_RATE = 115200
COLLECTION_DURATION_SEC = 60 # ระยะเวลาในการเก็บข้อมูลต่อ 1 จุด (วินาที)
NUM_SUBcarriers = 64 # จำนวน subcarrier สูงสุดที่จะสร้าง header

def collect_data(pos_x, pos_y):
    """ฟังก์ชันสำหรับเก็บข้อมูล ณ พิกัดที่กำหนด"""
    
    # สร้างชื่อไฟล์อัตโนมัติจากพิกัด
    filename = f"csi_data_x{pos_x}_y{pos_y}.csv"
    print(f"\nPreparing to collect data for position ({pos_x}, {pos_y})")
    print(f"Data will be saved to: {filename}")
    
    # รอให้ผู้ใช้พร้อม
    input("Place the device at the correct position and press Enter to start...")
    
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        ser.flushInput()
        
        print(f"--- Starting data collection for {COLLECTION_DURATION_SEC} seconds ---")
        
        sample_count = 0
        start_time = time.time()
        
        # สร้าง Header สำหรับไฟล์ CSV
        header = ",".join([f"sc_{i}" for i in range(NUM_SUBcarriers)]) + ",pos_x,pos_y\n"
        
        with open(filename, 'w') as f:
            f.write(header) # เขียน Header ลงไฟล์
            
            while time.time() - start_time < COLLECTION_DURATION_SEC:
                line = ser.readline().decode('utf-8').strip()
                
                if line.startswith('CSI_DATA,'):
                    # เพิ่มพิกัด (Label) ต่อท้ายข้อมูล CSI
                    data_row = line.split(',', 1)[1] + f",{pos_x},{pos_y}\n"
                    f.write(data_row)
                    sample_count += 1
            
        print(f"--- Collection complete! ---")
        print(f"Saved {sample_count} samples to {filename}")

    except serial.SerialException as e:
        print(f"Error: Could not open serial port {SERIAL_PORT}. {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    while True:
        print("\n--- New Data Collection Cycle ---")
        try:
            # รับค่าพิกัดจากผู้ใช้
            px_str = input("Enter X coordinate (or 'q' to quit): ")
            if px_str.lower() == 'q':
                break
            
            py_str = input("Enter Y coordinate: ")
            
            pos_x = float(px_str)
            pos_y = float(py_str)
            
            collect_data(pos_x, pos_y)
            
        except ValueError:
            print("Invalid input. Please enter numbers for coordinates.")
        except KeyboardInterrupt:
            print("\nExiting program.")
            break