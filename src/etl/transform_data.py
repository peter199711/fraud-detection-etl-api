import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score
from sqlalchemy import create_engine
import joblib
import os
import mlflow
import mlflow.sklearn
from xgboost import XGBClassifier

# --- 設定路徑與參數 ---
# 儲存最終模型的本地路徑
MODEL_PATH = '/app/src/models/baseline_model.pkl' # 使用容器內的絕對路徑

# --- 改進：從環境變數讀取主機名稱，並提供本地預設值 ---
DB_HOST = os.getenv('DB_HOST', 'localhost')
MLFLOW_HOST = os.getenv('MLFLOW_HOST', 'localhost')

# MLflow 追蹤服務的 URI
MLFLOW_TRACKING_URI = f"http://{MLFLOW_HOST}:5000" 

# 資料庫連線參數
DB_NAME = os.getenv('DB_NAME', 'fraud_db')
DB_USER = os.getenv('DB_USER', 'user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
DB_PORT = '5432'
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
FEATURE_VIEW_NAME = 'feature_transactions'


def load_data(engine):
    """從 PostgreSQL feature_transactions 視圖載入數據並分割。"""
    
    print(f"--- 1. 從資料庫載入特徵：{FEATURE_VIEW_NAME} ---")
    
    sql_query = f"SELECT * FROM {FEATURE_VIEW_NAME}"
    df = pd.read_sql(sql_query, engine)
    
    print(f"成功載入 {len(df)} 筆特徵數據。")

    X = df.drop('class', axis=1)
    y = df['class']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    return X_train, X_test, y_train, y_test

def train_model_and_log_mlflow(model_class, run_name, params, tags, X_train, X_test, y_train, y_test):
    """訓練單一模型、評估並將結果記錄到 MLflow。"""
    
    with mlflow.start_run(run_name=run_name) as run:
        print(f"\n--- 訓練: {run_name} ---")

        # 記錄參數和標籤
        mlflow.log_params(params)
        mlflow.set_tags(tags) 
        
        # 訓練模型
        model = model_class(**params) 
        model.fit(X_train, y_train)
        
        # 評估模型
        y_proba = model.predict_proba(X_test)[:, 1]
        y_pred = (y_proba > 0.5).astype(int) 
        
        metrics = {
            "roc_auc_score": roc_auc_score(y_test, y_proba),
            "f1_score": f1_score(y_test, y_pred),
            "precision_score": precision_score(y_test, y_pred),
            "recall_score": recall_score(y_test, y_pred)
        }
        mlflow.log_metrics(metrics)

        print(f"   AUC: {metrics['roc_auc_score']:.4f}, F1: {metrics['f1_score']:.4f}, Precision: {metrics['precision_score']:.4f}")

        # 儲存模型到 MLflow Artifacts
        mlflow.sklearn.log_model(model, "model")
        
        return metrics['f1_score'], model


def run_etl_and_train_pipeline():
    """主執行函式，包含數據載入和所有模型的訓練。"""
    
    print(f"設定 MLflow Tracking URI: {MLFLOW_TRACKING_URI}")
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment("Fraud Detection Baseline") 
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    
    try:
        engine = create_engine(DATABASE_URL)
        # 測試連線
        connection = engine.connect()
        print(f"成功連線到資料庫：{DB_HOST}/{DB_NAME}")
        connection.close()

        # 1. 載入和分割數據
        X_train, X_test, y_train, y_test = load_data(engine)

        best_f1_score = -1
        best_model = None
        best_model_name = ""

        # 2. 模型配置清單
        model_configs = [
            {
                "name": "01_Logistic_Regression_Baseline",
                "class": LogisticRegression,
                "params": {"solver": 'liblinear', "random_state": 42, "class_weight": 'balanced'},
                "tags": {"data_source": "Postgres-VIEW", "model_type": "LogisticRegression"}
            },
            {
                "name": "02_XGBoost_Optimized",
                "class": XGBClassifier,
                "params": {
                    'n_estimators': 100, 
                    'learning_rate': 0.1, 
                    'scale_pos_weight': 50,
                    'random_state': 42,
                    'use_label_encoder': False,
                    'eval_metric': 'logloss'
                },
                "tags": {"data_source": "Postgres-VIEW", "model_type": "XGBoost"}
            }
        ]

        # 3. 迭代訓練所有模型
        for config in model_configs:
            current_f1, current_model = train_model_and_log_mlflow(
                model_class=config["class"],
                run_name=config["name"],
                params=config["params"],
                tags=config["tags"],
                X_train=X_train, X_test=X_test, y_train=y_train, y_test=y_test
            )
            
            # 4. 選擇並儲存最佳模型
            if current_f1 > best_f1_score:
                best_f1_score = current_f1
                best_model = current_model
                best_model_name = config["name"]
                print(f"-> 新的最佳模型: {best_model_name} (F1={best_f1_score:.4f})")

        if best_model:
            # 這裡我們不再需要儲存到本地，因為 API 將會從 MLflow 載入模型
            # joblib.dump(best_model, MODEL_PATH) 
            print(f"\n✅ 訓練流程完成。最佳模型 '{best_model_name}' 已記錄至 MLflow。")
            print("API 服務現在應該能夠從 MLflow 載入此模型。")

    except Exception as e:
        import traceback
        print(f"\n🔥 訓練流程失敗。錯誤訊息: {e}")
        print(traceback.format_exc())
        print("請確認 MLflow Server (mlflow_server) 和 PostgreSQL (postgres_db) 容器正在運行。")

if __name__ == "__main__":
    run_etl_and_train_pipeline()
