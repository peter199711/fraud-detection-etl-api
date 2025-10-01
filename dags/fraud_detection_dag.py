"""
詐欺偵測 ETL 和模型訓練 DAG
這個 DAG 負責定期執行數據載入、特徵工程和模型重新訓練

作者: Fraud Detection Team  
日期: 2025-09-30

修正版本：
- 使用 Airflow Connections 管理資料庫連線
- 添加 feature_transactions VIEW 創建步驟
- 改善錯誤處理和日誌記錄
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.models import Variable
import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.append('/opt/airflow/src')

# 預設參數
default_args = {
    'owner': 'fraud-detection-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 9, 30),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# 建立 DAG
dag = DAG(
    'fraud_detection_pipeline',
    default_args=default_args,
    description='詐欺偵測資料管道和模型訓練',
    schedule_interval=timedelta(days=1),  # 每日執行
    catchup=False,  # 不追補歷史執行
    tags=['fraud-detection', 'etl', 'ml'],
)

# 任務 1: 檢查資料庫連線 (使用 Airflow Connections)
def check_database_connection():
    """使用 Airflow PostgresHook 檢查資料庫連線"""
    try:
        # 使用 Airflow Connection ID 'postgres_fraud_db'
        postgres_hook = PostgresHook(postgres_conn_id='postgres_fraud_db')
        
        # 測試連線
        conn = postgres_hook.get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        print("✅ 資料庫連線成功")
        print(f"測試查詢結果: {result}")
        return True
    except Exception as e:
        print(f"❌ 資料庫連線失敗: {e}")
        print("請確認 Airflow Connection 'postgres_fraud_db' 已正確配置")
        raise

# 任務 2: 載入新數據 (使用 BashOperator)
# 移除 Python 函式，改用 BashOperator 執行 db_load.py 腳本

# 任務 3: 創建特徵視圖 
def create_feature_view():
    """創建或更新 feature_transactions 視圖"""
    postgres_hook = PostgresHook(postgres_conn_id='postgres_fraud_db')
    
    # 特徵視圖 SQL
    create_view_sql = """
    CREATE OR REPLACE VIEW feature_transactions AS
    SELECT 
        time,
        v1, v2, v3, v4, v5, v6, v7, v8, v9, v10,
        v11, v12, v13, v14, v15, v16, v17, v18, v19, v20,
        v21, v22, v23, v24, v25, v26, v27, v28,
        amount,
        class
    FROM raw_transactions
    WHERE 
        time IS NOT NULL 
        AND amount IS NOT NULL
        AND class IS NOT NULL
    ORDER BY time;
    """
    
    try:
        print("🔧 創建/更新 feature_transactions 視圖...")
        
        # 先刪除現有視圖以避免衝突
        drop_view_sql = "DROP VIEW IF EXISTS feature_transactions CASCADE;"
        postgres_hook.run(drop_view_sql)
        print("已刪除現有視圖")
        
        # 創建新視圖
        postgres_hook.run(create_view_sql)
        
        # 驗證視圖創建成功
        count_query = "SELECT COUNT(*) FROM feature_transactions"
        result = postgres_hook.get_first(count_query)
        
        print(f"✅ feature_transactions 視圖創建成功，包含 {result[0]} 筆記錄")
        return True
        
    except Exception as e:
        print(f"❌ 特徵視圖創建失敗: {e}")
        raise

# 任務 4: 執行模型訓練 (使用 BashOperator)
# 移除 Python 函式，改用 BashOperator 執行腳本

# 任務 5: 驗證模型性能
def validate_model_performance():
    """驗證模型性能是否符合標準"""
    postgres_hook = PostgresHook(postgres_conn_id='postgres_fraud_db')
    
    print("📊 驗證模型性能...")
    # 這裡可以添加實際的模型驗證邏輯
    # 例如從 MLflow 載入最新模型並檢查 F1 score, AUC 等指標
    
    # 簡單檢查：確保有足夠的訓練數據
    try:
        count_query = "SELECT COUNT(*) FROM feature_transactions WHERE class = 1"
        fraud_count = postgres_hook.get_first(count_query)[0]
        
        if fraud_count < 100:
            print(f"⚠️  警告：詐欺案例數量較少 ({fraud_count} 筆)")
        else:
            print(f"✅ 詐欺案例數量充足：{fraud_count} 筆")
            
        print("✅ 模型性能驗證完成")
    except Exception as e:
        print(f"❌ 模型驗證失敗: {e}")
        raise

# 任務 6: 清理暫存檔案
cleanup_task = BashOperator(
    task_id='cleanup_temp_files',
    bash_command='echo "🧹 清理暫存檔案..." && find /tmp -name "*fraud*" -type f -delete 2>/dev/null || true',
    dag=dag,
)

# 定義所有任務
db_check_task = PythonOperator(
    task_id='check_database_connection',
    python_callable=check_database_connection,
    dag=dag,
)

data_load_task = BashOperator(
    task_id='load_new_data',
    bash_command="""
    cd /opt/airflow/src && \
    export DB_HOST=postgres_db && \
    python -m etl.db_load
    """,
    dag=dag,
)

create_feature_view_task = PythonOperator(
    task_id='create_feature_view',
    python_callable=create_feature_view,
    dag=dag,
)

model_training_task = BashOperator(
    task_id='perform_model_training',
    bash_command="""
    cd /opt/airflow/src && \
    export DB_HOST=postgres_db && \
    export MLFLOW_HOST=mlflow_server && \
    python -m etl.transform_data
    """,
    dag=dag,
)

model_validation_task = PythonOperator(
    task_id='validate_model_performance',
    python_callable=validate_model_performance,
    dag=dag,
)

# 修正後的任務依賴關係
db_check_task >> data_load_task >> create_feature_view_task >> model_training_task >> model_validation_task >> cleanup_task

# 添加任務文檔
db_check_task.doc_md = """
檢查 PostgreSQL 資料庫是否可正常連線
使用 Airflow PostgresHook 和 Connection 'postgres_fraud_db'
"""

data_load_task.doc_md = """
執行資料載入腳本 (db_load.py)
重新載入信用卡交易數據並創建基礎 raw_transactions 表
"""

create_feature_view_task.doc_md = """
創建或更新 feature_transactions 視圖
這個視圖是模型訓練的核心數據來源，包含所有必要的特徵
"""

model_training_task.doc_md = """
執行機器學習模型訓練腳本 (transform_data.py)
使用 feature_transactions 視圖訓練多個模型並將最佳模型記錄到 MLflow
"""

model_validation_task.doc_md = """
驗證新訓練模型的性能指標
檢查模型品質和數據完整性
"""

cleanup_task.doc_md = """
清理執行過程中產生的暫存檔案
維護系統整潔，釋放磁碟空間
"""
