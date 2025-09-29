import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import mean_absolute_error
import joblib
import os
import glob

# ---!!! ตั้งค่าที่สำคัญ !!!---
DATA_FOLDER = r'C:\Users\user\Documents\GitHub\CSI_MINI_unclassic\ESP32s3_Study'
MODEL_FILENAME = 'csi_knn_model.joblib'

def load_and_combine_data(folder_path):
    """ฟังก์ชันสำหรับอ่านและรวมไฟล์ CSV ทั้งหมด"""
    csv_files = glob.glob(os.path.join(folder_path, 'csi_data_x*.csv'))
    if not csv_files:
        print(f"Error: No data files found in '{folder_path}'.")
        return None
    
    df_list = []
    for file in csv_files:
        try:
            df = pd.read_csv(file, on_bad_lines='skip')
            df_list.append(df)
        except Exception as e:
            print(f"Could not read file {file} due to error: {e}")

    if not df_list:
        print("No data could be loaded.")
        return None

    full_df = pd.concat(df_list, ignore_index=True)
    
    print(f"Data loaded successfully!")
    print(f" - Found {len(csv_files)} data files.")
    print(f" - Total valid samples: {len(full_df)}")
    
    if 'pos_x' not in full_df.columns or 'pos_y' not in full_df.columns:
        print("Error: 'pos_x' or 'pos_y' columns not found in the data.")
        return None

    return full_df

def train_and_save_model():
    """ฟังก์ชันหลักสำหรับฝึกสอนและบันทึกโมเดล"""
    
    # 1. โหลดข้อมูล
    dataset = load_and_combine_data(DATA_FOLDER)
    if dataset is None:
        return

    # --- BUG FIX #1: จัดการค่าว่างใน Feature (X) ---
    feature_columns = [col for col in dataset.columns if col not in ['pos_x', 'pos_y']]
    dataset[feature_columns] = dataset[feature_columns].apply(pd.to_numeric, errors='coerce')
    dataset.fillna(0, inplace=True)
    print("\nCleaned feature data (X): Filled missing values with 0.")
    
    # --- BUG FIX #2: ลบแถวที่ค่าพิกัด (y) เป็นค่าว่าง ---
    initial_rows = len(dataset)
    dataset.dropna(subset=['pos_x', 'pos_y'], inplace=True)
    rows_dropped = initial_rows - len(dataset)
    if rows_dropped > 0:
        print(f"Cleaned label data (y): Dropped {rows_dropped} rows with missing coordinates.")

    # 2. แยก Features (X) และ Labels (y)
    X = dataset.drop(columns=['pos_x', 'pos_y']) 
    y = dataset[['pos_x', 'pos_y']]
    
    # 3. แบ่งข้อมูลสำหรับ Train และ Test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"Data split into training ({len(X_train)} samples) and testing ({len(X_test)} samples).")
    
    # 4. สร้างและฝึกสอนโมเดล k-NN
    print("\nTraining k-NN model...")
    knn_model = KNeighborsRegressor(n_neighbors=5)
    knn_model.fit(X_train, y_train)
    print("Model training complete!")
    
    # 5. ประเมินผลโมเดล
    y_pred = knn_model.predict(X_test)
    avg_error_distance = np.mean(np.sqrt(np.sum((y_test.values - y_pred)**2, axis=1)))

    print("\n--- Model Evaluation ---")
    print(f"Average Error Distance on Test Set: {avg_error_distance:.2f} meters")
    
    # 6. บันทึกโมเดลที่ฝึกสอนแล้วลงไฟล์
    joblib.dump(knn_model, MODEL_FILENAME)
    print(f"\nModel has been saved to '{MODEL_FILENAME}'")
    print("This file is your ready-to-use model!")

if __name__ == "__main__":
    train_and_save_model()