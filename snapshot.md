# fraud-detection-etl-api 專案快照
> 自動生成於: 2025-10-02 08:48:56

## 專案目錄結構
```
fraud-detection-etl-api/
├── README.md
└── SERVICES_GUIDE.md
│   ├── dags/
│   └── fraud_detection_dag.py
│   ├── data/
│   └── creditcard.csv
│   ├── docker/
│   ├── Dockerfile.airflow
│   ├── Dockerfile.api
│   ├── Dockerfile.dashboard
│   ├── Dockerfile.mlflow
│   └── docker-compose.yml
│   │   ├── dags/
│   └── src/
│   ├── notebooks/
│   ├── baseline_model_training.ipynb
│   └── eda_and_baseline.ipynb
└── src/
│   │   ├── api/
│   │   ├── main.py
│   │   └── requirements.txt
│   │   ├── dashboard/
│   │   └── app.py
│   │   ├── etl/
│   │   ├── db_load.py
│   │   └── transform_data.py
│   └── models/
│   │       ├── baseline_model.pkl
│   │       └── scaler.pkl
```

## 函式清單
### `dags\fraud_detection_dag.py`
```
// 任務 1: 檢查資料庫連線 (使用 Airflow Connections)
check_database_connection()
// 任務 3: 創建特徵視圖
create_feature_view()
```
### `src\api\main.py`
```
// --- 2. 載入模型與 Scaler ---
load_model_from_mlflow()
home()
predict_fraud(transaction: Transaction)
```
### `src\dashboard\app.py`
```
get_experiment_id()
get_mlflow_runs(experiment_id)
```
### `src\etl\db_load.py`
```
connect_and_load_data()
create_feature_view(engine)
```
### `src\etl\transform_data.py`
```
load_data(engine)
train_model_and_log_mlflow(model_class, run_name, params, tags, X_train, X_test, y_train, y_test)
run_etl_and_train_pipeline()
main()
```

## 依賴清單
未在本專案中找到 `package.json` 檔案。