import serial
import numpy as np
import joblib # Library สำหรับโหลดโมเดล
import os
from collections import deque

# ---!!! ตั้งค่าที่สำคัญ !!!---
SERIAL_PORT = 'COM10'  # <--- แก้ไข Port ของคุณตรงนี้
BAUD_RATE = 115200
MODEL_FILENAME = 'csi_knn_model.joblib' # ชื่อไฟล์โมเดลที่บันทึกไว้

# ค่าสำหรับ Smoothing ผลลัพธ์ (ทำให้ค่าพิกัดนิ่งขึ้น)
SMOOTHING_WINDOW_SIZE = 5
prediction_history = deque(maxlen=SMOOTHING_WINDOW_SIZE)

def predict_location_realtime():
    """ฟังก์ชันหลักสำหรับทำนายตำแหน่งแบบ Real-time"""
    
    # 1. โหลดโมเดลที่ฝึกสอนไว้แล้ว
    print(f"Loading model from '{MODEL_FILENAME}'...")
    if not os.path.exists(MODEL_FILENAME):
        print(f"Error: Model file '{MODEL_FILENAME}' not found.")
        print("Please run train_model.py to create the model first.")
        return
        
    try:
        model = joblib.load(MODEL_FILENAME)
        print("Model loaded successfully!")
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    # 2. เปิดการเชื่อมต่อ Serial Port
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
        ser.flushInput()
        print(f"Connected to {SERIAL_PORT}. Waiting for CSI data...")
    except serial.SerialException as e:
        print(f"Error: Could not open serial port {SERIAL_PORT}. {e}")
        return

    # 3. วนลูปเพื่ออ่านข้อมูลและทำนายตำแหน่ง
    try:
        while True:
            line = ser.readline().decode('utf-8').strip()
            
            if line.startswith('CSI_DATA,'):
                # เตรียมข้อมูล CSI ให้อยู่ในรูปแบบที่โมเดลต้องการ
                parts = line.split(',')[1:]
                csi_values_str = [p for p in parts if p]
                
                # ตรวจสอบว่าจำนวน Feature ตรงกับที่โมเดลเคยเรียนรู้มาหรือไม่
                if len(csi_values_str) >= model.n_features_in_:
                    csi_features = np.array(csi_values_str[:model.n_features_in_], dtype=float).reshape(1, -1)
                    
                    # --- การทำนายตำแหน่ง ---
                    predicted_xy = model.predict(csi_features)[0]
                    prediction_history.append(predicted_xy)
                    
                    # --- Smoothing ผลลัพธ์ ---
                    # นำค่าที่ทำนายได้ย้อนหลังมาหาค่าเฉลี่ยเพื่อให้ตำแหน่งนิ่งขึ้น
                    smoothed_prediction = np.mean(prediction_history, axis=0)
                    
                    pos_x = smoothed_prediction[0]
                    pos_y = smoothed_prediction[1]
                    
                    # แสดงผลลัพธ์ (ใช้ \r เพื่อให้แสดงผลทับบรรทัดเดิม)
                    print(f"Predicted Location -> X: {pos_x:.2f}, Y: {pos_y:.2f}   ", end='\r')
                
    except KeyboardInterrupt:
        print("\nStopping prediction.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("\nSerial port closed.")

if __name__ == "__main__":
    predict_location_realtime()