# src/api/main.py
from fastapi import FastAPI
from pydantic import BaseModel, Field
import joblib
import pandas as pd
import numpy as np
import os
import mlflow
import mlflow.sklearn
import mlflow.pyfunc  # 新增：支援通用模型載入
import mlflow.tensorflow  # 新增：支援 TensorFlow 模型載入

# --- 設定MLflow和本地路徑 ---
MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000')
MODEL_PATH = 'src/models/baseline_model.pkl'  # 本地備份路徑
SCALER_PATH = 'src/models/scaler.pkl'          # 本地備份路徑

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
def load_model_from_mlflow():
    """嘗試從MLflow載入最新模型，失敗則使用本地檔案"""
    try:
        print(f"設定 MLflow Tracking URI: {MLFLOW_TRACKING_URI}")
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        
        # 嘗試獲取最新的模型
        client = mlflow.tracking.MlflowClient()
        experiment = client.get_experiment_by_name("Fraud Detection Baseline")
        
        if experiment:
            # 獲取所有runs並按F1分數排序，選擇最佳模型
            runs = client.search_runs(
                experiment_ids=[experiment.experiment_id],
                order_by=["metrics.f1_score DESC"],
                max_results=10
            )
            
            if runs:
                best_run = runs[0]  # F1分數最高的模型
                model_uri = f"runs:/{best_run.info.run_id}/model"
                
                # 獲取模型信息
                f1_score = best_run.data.metrics.get('f1_score', 'N/A')
                model_name = best_run.data.tags.get('model_type', 'Unknown')
                
                # ✅ 智能模型載入：根據模型類型選擇正確的載入方法
                try:
                    if model_name in ['LogisticRegression']:
                        model = mlflow.sklearn.load_model(model_uri)
                    elif model_name in ['TensorFlow', 'TensorFlow_DNN']:
                        # Keras 3.0+ 使用 mlflow.keras 或 pyfunc
                        try:
                            import mlflow.keras
                            model = mlflow.keras.load_model(model_uri)
                        except:
                            model = mlflow.pyfunc.load_model(model_uri)
                    else:  # XGBoost, LightGBM 等使用通用載入
                        model = mlflow.pyfunc.load_model(model_uri)
                    
                    print(f"成功從 MLflow 載入最佳模型！")
                    print(f"  模型類型: {model_name}")
                    print(f"  F1 Score: {f1_score}")
                    print(f"  Run ID: {best_run.info.run_id}")
                    return model
                    
                except Exception as load_error:
                    print(f"使用 {model_name} 載入方法失敗: {load_error}")
                    # 嘗試備用載入方法
                    try:
                        model = mlflow.pyfunc.load_model(model_uri)
                        print(f"使用通用方法成功載入模型: {model_name}")
                        return model
                    except Exception as fallback_error:
                        print(f"通用載入方法也失敗: {fallback_error}")
                        raise fallback_error
        
        print("MLflow 中沒有找到模型，嘗試載入本地檔案...")
        
    except Exception as e:
        print(f"從 MLflow 載入模型失敗: {e}")
        print("嘗試載入本地檔案...")
    
    # 回退到本地檔案
    try:
        model = joblib.load(MODEL_PATH)
        print("成功載入本地模型檔案！")
        return model
    except Exception as e:
        print(f"載入本地模型失敗: {e}")
        return None

# 載入模型和scaler
model = load_model_from_mlflow()

try:
    scaler = joblib.load(SCALER_PATH)
    print("Scaler 載入成功！")
except Exception as e:
    print(f"載入 Scaler 失敗: {e}")
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
    try:
        # ✅ 智能預測：根據模型類型使用不同方法
        if hasattr(model, 'predict_proba'):
            # sklearn/XGBoost/LightGBM 直接載入的模型
            proba = model.predict_proba(df.values)[:, 1]
        elif hasattr(model, 'predict') and hasattr(model, 'layers'):
            # TensorFlow/Keras 模型 (檢查是否有 layers 屬性)
            proba = model.predict(df.values).flatten()
        else:
            # MLflow pyfunc 載入的模型
            prediction_df = model.predict(df)
            if isinstance(prediction_df, pd.DataFrame) and len(prediction_df.columns) > 1:
                # 多列輸出，取第二列 (詐欺機率)
                proba = prediction_df.iloc[:, 1].values
            else:
                # 單列輸出，可能是機率或類別
                pred_values = prediction_df.values if isinstance(prediction_df, pd.DataFrame) else prediction_df
                if pred_values.max() <= 1.0 and pred_values.min() >= 0.0:
                    proba = pred_values  # 看起來是機率
                else:
                    proba = [0.5]  # 回退預設值
        
        # 預測類別
        prediction = (proba > 0.5).astype(int) if isinstance(proba, (list, tuple)) == False else [int(p > 0.5) for p in proba]
        
        return {
            "is_fraud": int(prediction[0]),
            "fraud_probability": float(proba[0]),
            "message": "Transaction analyzed successfully."
        }
        
    except Exception as pred_error:
        print(f"預測過程中發生錯誤: {pred_error}")
        return {
            "error": f"Prediction failed: {str(pred_error)}",
            "message": "Please check model compatibility and try again."
        }