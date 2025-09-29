# src/etl/transform_data.py (新增 MLflow 追蹤)
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score
from sqlalchemy import create_engine
import joblib
import os

# --- 新增 MLflow 導入 ---
import mlflow
import mlflow.sklearn

# --- 設定路徑 ---
MODEL_PATH = '../src/models/baseline_model.pkl'

# --- 資料庫連線參數 ---
DB_HOST = 'localhost' # 本機執行腳本
DB_NAME = 'fraud_db'
DB_USER = 'user'
DB_PASSWORD = 'password'
DB_PORT = '5432'
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
FEATURE_VIEW_NAME = 'feature_transactions'

# --- MLflow 設定 ---
# 指向 Docker Compose 中的 MLflow 服務（由於是本機執行，使用 localhost:5000）
MLFLOW_TRACKING_URI = "http://localhost:5000" 

def run_etl_and_train():
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    
    # --- 啟動 MLflow 實驗追蹤 ---
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment("Fraud Detection Baseline") 
    
    with mlflow.start_run(run_name="DB_Driven_Logistic_Regression") as run:
        try:
            engine = create_engine(DATABASE_URL)
            print(f"--- 1. 從資料庫載入特徵：{FEATURE_VIEW_NAME} ---")

            sql_query = f"SELECT * FROM {FEATURE_VIEW_NAME}"
            df = pd.read_sql(sql_query, engine)
            
            print(f"成功載入 {len(df)} 筆特徵數據。")

            X = df.drop('class', axis=1)
            y = df['class']

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )

            print("--- 2. 訓練 Baseline 模型 ---")
            
            # 1. 定義模型實際使用的參數 (給 LogisticRegression)
            model_params = {
                "solver": 'liblinear', 
                "random_state": 42, 
                "class_weight": 'balanced',
            }
            # 2. 定義 MLflow 追蹤用的自定義標籤 (給 MLflow)
            mlflow_tags = {
                "data_source": "Postgres-VIEW", # 記錄資料來源
                "model_type": "baseline",        # 記錄模型類型
                "author": "Peter"                # 記錄作者
            }
            
            # 記錄模型參數
            mlflow.log_params(model_params) 
            # 記錄自定義標籤（使用 set_tags 而不是 log_params）
            mlflow.set_tags(mlflow_tags) 

            # 使用正確的參數建構模型
            model = LogisticRegression(**model_params) 
            model.fit(X_train, y_train)
            
            # 3. 評估模型並記錄指標
            y_proba = model.predict_proba(X_test)[:, 1]
            y_pred = model.predict(X_test)
            
            metrics = {
                "roc_auc_score": roc_auc_score(y_test, y_proba),
                "f1_score": f1_score(y_test, y_pred),
                "precision_score": precision_score(y_test, y_pred),
                "recall_score": recall_score(y_test, y_pred)
            }
            mlflow.log_metrics(metrics) # 記錄指標

            print(f"--- 評估結果：AUC={metrics['roc_auc_score']:.4f} ---")

            # 4. 儲存模型 (MLflow Artifacts)
            mlflow.sklearn.log_model(model, "model")
            
            # 5. 儲存模型到本地供 API 使用
            joblib.dump(model, MODEL_PATH)
            print(f"模型儲存至本地: {MODEL_PATH}")
            
        except ImportError:
            print("錯誤：請確認已安裝 MLflow, psycopg2-binary, sqlalchemy。")
        except Exception as e:
            print(f"訓練流程失敗。錯誤訊息: {e}")
            print("請確認 MLflow Server (localhost:5000) 和 PostgreSQL 容器 (postgres_db) 正在運行。")

if __name__ == "__main__":
    run_etl_and_train()