# src/etl/transform_data.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sqlalchemy import create_engine
import joblib
import os

# --- 設定路徑 (保持與你的專案架構一致) ---
MODEL_PATH = '../src/models/baseline_model.pkl'

# --- 資料庫連線參數 (與 docker-compose.yml 保持一致) ---
# 注意：這裡使用 'localhost' 是因為你是在 Docker 容器之外的本機執行此腳本
DB_HOST = 'localhost' 
DB_NAME = 'fraud_db'
DB_USER = 'user'
DB_PASSWORD = 'password'
DB_PORT = '5432'
DB_TYPE = 'postgresql' 
DATABASE_URL = f"{DB_TYPE}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

FEATURE_VIEW_NAME = 'feature_transactions'

def run_etl_and_train():
    """
    從 PostgreSQL 特徵視圖載入數據，訓練模型並儲存。
    """
    # 確保 models 資料夾存在
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    
    try:
        # 建立連線引擎
        engine = create_engine(DATABASE_URL)
        print(f"成功連線到資料庫：{DB_NAME}")

        print(f"--- 1. 從資料庫載入特徵：{FEATURE_VIEW_NAME} ---")

        # 1.1 使用 SQL 查詢從視圖中載入數據
        sql_query = f"SELECT * FROM {FEATURE_VIEW_NAME}"
        # pandas.read_sql 會自動從 SQL 查詢中讀取數據到 DataFrame
        df = pd.read_sql(sql_query, engine)
        
        print(f"成功載入 {len(df)} 筆特徵數據。")

        # 1.2 定義特徵 (X) 和目標 (y)
        # 數據來自 VIEW，已經包含 scaled_amount 和 scaled_time
        X = df.drop('class', axis=1) # 'class' 欄位在 DB 中是小寫
        y = df['class']

        # 1.3 分割訓練集與訓練模型
        X_train, _, y_train, _ = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        print("--- 2. 訓練 Baseline 模型 ---")
        model = LogisticRegression(solver='liblinear', random_state=42, class_weight='balanced')
        model.fit(X_train, y_train)

        # 1.4 儲存模型
        joblib.dump(model, MODEL_PATH)
        print(f"模型儲存至: {MODEL_PATH}")
        
    except ImportError:
        print("錯誤：請確認已安裝 psycopg2-binary 和 sqlalchemy: pip install psycopg2-binary sqlalchemy")
    except Exception as e:
        print(f"訓練流程失敗。錯誤訊息: {e}")
        print("請確認 PostgreSQL 容器 (postgres_db) 正在運行，且 'feature_transactions' VIEW 已被創建。")


if __name__ == "__main__":
    run_etl_and_train()