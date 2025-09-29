# src/etl/db_load.py
import pandas as pd
from sqlalchemy import create_engine, text
import os

# --- 資料庫連線參數 ---
DB_HOST = 'localhost' # 在本機執行腳本時，使用 localhost
DB_NAME = 'fraud_db'
DB_USER = 'user'
DB_PASSWORD = 'password'
DB_PORT = '5432'
DB_TYPE = 'postgresql' # 資料庫類型

# SQLAlchemy 連線字串
DATABASE_URL = f"{DB_TYPE}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

RAW_DATA_PATH = 'data/creditcard.csv'
RAW_TABLE_NAME = 'raw_transactions'

def connect_and_load_data():
    """連線到 Postgres 並將原始 CSV 載入到 raw_transactions 表中。"""
    try:
        # 建立連線引擎
        engine = create_engine(DATABASE_URL)
        print(f"成功連線到資料庫：{DB_NAME}")

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
        
    except Exception as e:
        print(f"資料庫連線或載入失敗，錯誤訊息：{e}")
        # 如果在本機執行失敗，可以嘗試將 DB_HOST 改為 'localhost'

if __name__ == "__main__":
    connect_and_load_data()