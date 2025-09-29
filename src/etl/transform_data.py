# src/etl/transform_data.py
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
import joblib
import os

# --- 設定路徑 ---
RAW_DATA_PATH = 'data/creditcard.csv'
MODEL_PATH = 'src/models/baseline_model.pkl'
SCALER_PATH = 'src/models/scaler.pkl' # 儲存Scaler，供API推論時使用
PROCESSED_DATA_PATH = 'data/processed_data.csv' # 訓練完成後，儲存處理過的資料供備用

def run_etl_and_train(raw_data_path: str, model_path: str, scaler_path: str):
    """
    執行資料清理、特徵工程、模型訓練並儲存模型與 Scaler。
    """
    print("--- 1. 載入資料 ---")
    df = pd.read_csv(raw_data_path)

    # 1.1 核心前處理邏輯 (與 EDA Notebook 保持一致！)
    scaler = StandardScaler()
    
    # 標準化 'Amount' 和 'Time' - 一起 fit，確保 scaler 知道兩個特徵
    features_to_scale = df[['Amount', 'Time']].values
    scaled_features = scaler.fit_transform(features_to_scale)
    
    df['scaled_amount'] = scaled_features[:, 0]  # Amount 的標準化結果
    df['scaled_time'] = scaled_features[:, 1]    # Time 的標準化結果
    
    # 儲存 Scaler 供 API 推論時對單筆資料進行標準化
    joblib.dump(scaler, scaler_path)
    print(f"Scaler 儲存至: {scaler_path}")
    
    df.drop(['Time', 'Amount'], axis=1, inplace=True)

    # 1.2 定義特徵 (X) 和目標 (y)
    X = df.drop('Class', axis=1)
    y = df['Class']

    # 1.3 分割訓練集與測試集
    # 這裡我們使用所有數據進行訓練，因為 ETL 的重點是資料準備，
    # 測試集用於 Dashboard 展示即可。
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("--- 2. 訓練 Baseline 模型 ---")
    # 採用 class_weight='balanced' 處理不平衡資料
    model = LogisticRegression(solver='liblinear', random_state=42, class_weight='balanced')
    model.fit(X_train, y_train)

    print("--- 3. 儲存模型 ---")
    # 儲存模型
    joblib.dump(model, model_path)
    print(f"模型儲存至: {model_path}")
    
    # (可選) 儲存處理後的資料以供 Dashboard/測試使用
    X_test.assign(Class=y_test).to_csv(PROCESSED_DATA_PATH, index=False)
    
    print("\nETL 和訓練流程完成！")

if __name__ == "__main__":
    # 確保 models 資料夾存在
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(PROCESSED_DATA_PATH), exist_ok=True)
    run_etl_and_train(RAW_DATA_PATH, MODEL_PATH, SCALER_PATH)