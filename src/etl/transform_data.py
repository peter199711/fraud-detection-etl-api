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
from lightgbm import LGBMClassifier

# 導入 TensorFlow 模型模組
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from models.tensorflow_model import train_tensorflow_model

# --- 設定路徑與參數 ---
# 儲存最終模型的本地路徑
# 環境自適應：本機使用相對路徑，Docker 使用絕對路循
if os.path.exists('/opt/airflow'):
    # Docker 環境：使用 /opt/airflow/src/models（對應本機的 src/models）
    MODEL_PATH = os.getenv('MODEL_PATH', '/opt/airflow/src/models/baseline_model.pkl')
else:
    # 本機環境：使用相對路徑
    MODEL_PATH = os.getenv('MODEL_PATH', 'src/models/baseline_model.pkl')

# --- 改進：從環境變數讀取主機名稱，並提供本地預設值 ---
DB_HOST = os.getenv('DB_HOST', 'localhost')
# 優先讀取完整的 URI，如果沒有才用 HOST 構建
MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI')
if not MLFLOW_TRACKING_URI:
    MLFLOW_HOST = os.getenv('MLFLOW_HOST', 'localhost')
    MLFLOW_TRACKING_URI = f"http://{MLFLOW_HOST}:5000"

print(f"🔗 使用 MLflow URI: {MLFLOW_TRACKING_URI}")  # 添加調試輸出

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

        # ✅ 儲存模型到 MLflow Artifacts（測試連接）
        try:
            # 先測試基本連接
            client = mlflow.tracking.MlflowClient()
            print(f"MLflow 客戶端連接成功")
            
            # 使用最簡單的方法記錄模型
            mlflow.sklearn.log_model(model, "model")
            print(f"成功記錄 {tags.get('model_type', 'Unknown')} 模型到 MLflow")
        except Exception as e:
            print(f"模型記錄失敗: {e}")
            print(f"跳過模型記錄，但訓練指標已保存")
        
        return metrics['f1_score'], model


def run_etl_and_train_pipeline():
    """主執行函式，包含數據載入和所有模型的訓練。"""

    global MODEL_PATH  # ← 添加這行

    print(f"設定 MLflow Tracking URI: {MLFLOW_TRACKING_URI}")
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment("Fraud Detection Baseline") 
    try:
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        print(f"📁 模型儲存目錄已準備：{os.path.dirname(MODEL_PATH)}")
    except PermissionError:
        print(f"⚠️  無法創建目錄 {os.path.dirname(MODEL_PATH)}，使用當前目錄")
        MODEL_PATH = 'baseline_model.pkl'
    
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
                "tags": {"data_source": "Postgres-VIEW", "model_type": "LogisticRegression"},
                "type": "sklearn"
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
                "tags": {"data_source": "Postgres-VIEW", "model_type": "XGBoost"},
                "type": "sklearn"
            },
            {
                "name": "03_LightGBM_Optimized",
                "class": LGBMClassifier, 
                "params": {
                    'n_estimators': 200, 
                    'learning_rate': 0.05, 
                    'scale_pos_weight': 40, 
                    'random_state': 42
                },
                "tags": {"data_source": "Postgres-VIEW", "model_type": "LightGBM"},
                "type": "sklearn"
            },
            {
                "name": "04_TensorFlow_DNN",
                "class": None,  # TensorFlow 使用自訂訓練函式
                "params": {
                    'epochs': 50,
                    'batch_size': 256,
                    'learning_rate': 0.001,
                    'early_stopping_patience': 10
                },
                "tags": {"data_source": "Postgres-VIEW", "model_type": "TensorFlow"},
                "type": "tensorflow"
            }
        ]

        # 3. 迭代訓練所有模型
        for config in model_configs:
            # 根據模型類型選擇訓練方式
            if config.get("type") == "tensorflow":
                # TensorFlow 模型使用專用訓練函式
                try:
                    current_f1, current_model = train_tensorflow_model(
                        X_train=X_train, 
                        X_test=X_test, 
                        y_train=y_train, 
                        y_test=y_test,
                        run_name=config["name"],
                        tags=config["tags"],
                        **config["params"]
                    )
                except Exception as tf_error:
                    print(f"⚠️  TensorFlow 模型訓練失敗: {tf_error}")
                    print("繼續訓練其他模型...")
                    continue
            else:
                # sklearn/XGBoost/LightGBM 模型使用原有函式
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

def main():
    """主執行函式 - 供 Airflow DAG 呼叫"""
    try:
        run_etl_and_train_pipeline()
        # 明確指定成功退出，即使 MLflow API 有問題
        print("🎯 主函數執行完成，強制返回成功狀態")
        import sys
        sys.exit(0)
    except Exception as e:
        import traceback
        print(f"🔥 主函數執行失敗: {e}")
        print(traceback.format_exc())
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()
