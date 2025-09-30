# src/etl/db_load.py
import pandas as pd
from sqlalchemy import create_engine, text
import os

# --- 資料庫連線參數 ---
# 從環境變數讀取，提供本地預設值
DB_HOST = os.getenv('DB_HOST', 'localhost')  # Docker中使用postgres_db，本機使用localhost
DB_NAME = os.getenv('DB_NAME', 'fraud_db')
DB_USER = os.getenv('DB_USER', 'user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
DB_PORT = '5432'
DB_TYPE = 'postgresql' # 資料庫類型

# SQLAlchemy 連線字串
DATABASE_URL = f"{DB_TYPE}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

RAW_DATA_PATH = '/app/data/creditcard.csv'  # 使用容器內的絕對路徑
RAW_TABLE_NAME = 'raw_transactions'
FEATURE_VIEW_NAME = 'feature_transactions' 

def connect_and_load_data():
    """連線到 Postgres 並將原始 CSV 載入到 raw_transactions 表中。"""
    try:
        # 建立連線引擎
        engine = create_engine(DATABASE_URL)
        print(f"成功連線到資料庫：{DB_NAME}")

        with engine.connect() as connection:
            # 使用 IF EXISTS 確保即使 VIEW 不存在也不會報錯
            drop_view_sql = text(f"DROP VIEW IF EXISTS {FEATURE_VIEW_NAME} CASCADE;")
            connection.execute(drop_view_sql)
            connection.commit()
            print(f"已清理舊的 {FEATURE_VIEW_NAME} 視圖依賴。")

        # 1. 載入 CSV 數據
        print(f"正在載入原始數據：{RAW_DATA_PATH}")
        df_raw = pd.read_csv(RAW_DATA_PATH)
        
        # 為了 SQL 方便，將欄位名稱轉為小寫
        df_raw.columns = [col.lower() for col in df_raw.columns]

        # 2. 寫入資料庫
        print(f"正在將 {len(df_raw)} 筆數據寫入 {RAW_TABLE_NAME} 表...")
        
        # 使用 if_exists='replace' 每次執行時都重新創建表
        df_raw.to_sql(RAW_TABLE_NAME, engine, if_exists='replace', index=False)

        print(f"資料成功寫入 {RAW_TABLE_NAME} 表。")
        
        # 3. 創建特徵視圖
        print(f"正在創建 {FEATURE_VIEW_NAME} 視圖...")
        create_feature_view(engine)
        
    except Exception as e:
        print(f"資料庫連線或載入失敗，錯誤訊息：{e}")
        # 如果在本機執行失敗，可以嘗試將 DB_HOST 改為 'localhost'

def create_feature_view(engine):
    """創建 feature_transactions 視圖，包含基本特徵工程"""
    create_view_sql = f"""
    CREATE OR REPLACE VIEW {FEATURE_VIEW_NAME} AS
    SELECT 
        -- 保留所有V特徵
        v1, v2, v3, v4, v5, v6, v7, v8, v9, v10,
        v11, v12, v13, v14, v15, v16, v17, v18, v19, v20,
        v21, v22, v23, v24, v25, v26, v27, v28,
        
        -- 添加標準化的時間和金額特徵 (這裡只是原始值，實際標準化在Python中進行)
        time,
        amount,
        
        -- 目標變數
        class
    FROM {RAW_TABLE_NAME}
    WHERE time IS NOT NULL 
    AND amount IS NOT NULL;
    """
    
    try:
        with engine.connect() as connection:
            connection.execute(text(create_view_sql))
            connection.commit()
            print(f"成功創建 {FEATURE_VIEW_NAME} 視圖。")
    except Exception as e:
        print(f"創建視圖失敗：{e}")

if __name__ == "__main__":
    connect_and_load_data()