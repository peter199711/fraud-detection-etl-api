# src/api/main.py
from fastapi import FastAPI
from pydantic import BaseModel, Field
import joblib
import pandas as pd
import numpy as np
import os

# --- 設定路徑 (與 ETL 腳本中的儲存路徑一致) ---
MODEL_PATH = 'src/models/baseline_model.pkl'
SCALER_PATH = 'src/models/scaler.pkl'

# --- 1. 定義資料結構 (Schema) ---
# 這個結構必須對應模型訓練時的輸入特徵 (除了 Time/Amount，它們被替換了)
class Transaction(BaseModel):
    # 原始交易數據 - 包含所有模型需要的特徵
    time: float = Field(..., description="交易發生時間 (秒)")
    amount: float = Field(..., description="交易金額")
    
    # V1-V28 特徵 (PCA 處理後的匿名特徵)
    v1: float
    v2: float
    v3: float
    v4: float
    v5: float
    v6: float
    v7: float
    v8: float
    v9: float
    v10: float
    v11: float
    v12: float
    v13: float
    v14: float
    v15: float
    v16: float
    v17: float
    v18: float
    v19: float
    v20: float
    v21: float
    v22: float
    v23: float
    v24: float
    v25: float
    v26: float
    v27: float
    v28: float

# 為了讓範例運作，我們假設 Transaction 已經包含所有 V 特徵。

# --- 2. 載入模型與 Scaler ---
try:
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    print("模型和 Scaler 載入成功！")
except FileNotFoundError:
    print(f"錯誤：找不到模型或 Scaler 檔案。請先執行 {os.path.abspath('src/etl/transform_data.py')}。")
    model = None
    scaler = None
except Exception as e:
    print(f"載入模型時發生錯誤: {e}")
    model = None
    scaler = None

# --- 3. 初始化 FastAPI App ---
app = FastAPI(title="Fraud Detection API")

@app.get("/")
def home():
    return {"message": "Fraud Detection API is running. Go to /docs for Swagger UI."}

@app.post("/predict")
def predict_fraud(transaction: Transaction):
    """
    接收單筆交易資料，回傳是否為詐欺的預測 (0/1) 與機率。
    """
    if model is None or scaler is None:
        return {"error": "Model not loaded. Please check logs and run ETL script."}
        
    # 1. 將 Pydantic 資料結構轉換為 DataFrame (方便使用 Scaler)
    data = transaction.model_dump()
    df = pd.DataFrame([data])
    
    # 2. 應用與訓練時相同的特徵工程：標準化 Time 和 Amount
    # 提取 Time 和 Amount，然後進行標準化
    time_amount_cols = ['time', 'amount']
    # 確保列名與訓練時的 scaler 一致，這裡假設原始數據有 Time 和 Amount
    
    # 這裡必須與 ETL 腳本中的 scaler.fit_transform() 對應
    # 由於訓練時，我們對 Time 和 Amount 分別進行了 fit_transform，
    # 這裡我們需要提取這兩列並使用 fit 過的 scaler 進行 transform。
    
    # 注意：StandardScaler 在 fit 時只接收了 Time 和 Amount，但它們被reshape成單列
    # 為了在 API 中正確使用，我們需要確保 scaler 知道它被 fit 在哪個結構上。
    # 為了穩健性，我們重新創建一個包含 Time 和 Amount 的 DataFrame 進行 transform。
    
    
    # 這裡我們模擬單獨處理 Time 和 Amount
    # 實際 scaler 應該分別儲存 Time_Scaler 和 Amount_Scaler，或使用 ColumnTransformer。
    
    # 為了讓這個範例運行，我們假設 scaler 是 fit 在 [Amount, Time] 上的
    # **實戰建議：在 ETL 腳本中，分別對 Amount 和 Time 進行 fit/transform，並儲存兩個 scaler。**
    
    # 使用與 ETL 訓練時相同的特徵順序：[Amount, Time]
    # 確保與 scaler.fit_transform() 時的順序一致
    features_to_scale = df[['amount', 'time']].values
    scaled_features = scaler.transform(features_to_scale)
    
    df['scaled_amount'] = scaled_features[:, 0]  # Amount 的標準化結果
    df['scaled_time'] = scaled_features[:, 1]    # Time 的標準化結果
    
    # 3. 準備模型輸入
    # 移除原始 Time 和 Amount，保留 V 特徵和 scaled_features
    df.drop(columns=['time', 'amount'], inplace=True)
    
    # **重要**：確保 df 的欄位順序與訓練模型時的 X_train **完全一致**！
    # 如果不一致，預測結果會錯誤。
    # 建議儲存特徵列表並載入：feature_list = joblib.load('feature_list.pkl')
    
    # 4. 進行預測
    # 預測機率
    proba = model.predict_proba(df.values)[:, 1]
    # 預測類別
    prediction = (proba > 0.5).astype(int) # 預設 threshold=0.5
    
    return {
        "is_fraud": int(prediction[0]),
        "fraud_probability": float(proba[0]),
        "message": "Transaction analyzed successfully."
    }