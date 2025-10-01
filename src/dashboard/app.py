# src/dashboard/app.py

import streamlit as st
import pandas as pd
import requests
import json
import base64

# --- 服務設定 ---
import os
API_URL = os.getenv("API_URL", "http://fraud_api:8000/predict")
MLFLOW_BASE_URI = os.getenv("MLFLOW_BASE_URI", "http://mlflow_server:5000/api/2.0/")
MLFLOW_EXP_NAME = "Fraud Detection Baseline" # 使用實驗名稱來查找 ID


st.set_page_config(page_title="詐欺偵測儀表板", layout="wide")


# --- 核心函式 1: 動態獲取實驗 ID ---
@st.cache_data(ttl=60)  # 緩存 60 秒後自動更新
def get_experiment_id():
    """動態地從 MLflow 獲取實驗 ID。"""
    try:
        response = requests.get(f"{MLFLOW_BASE_URI}mlflow/experiments/search?max_results=100", timeout=5)
        response.raise_for_status()
        experiments = response.json().get('experiments', [])
        
        for exp in experiments:
            if exp['name'] == MLFLOW_EXP_NAME:
                return exp['experiment_id']
        
        return None
    except Exception:
        return None


# --- 核心函式 2: 從 MLflow 讀取數據 ---
@st.cache_data(ttl=60)  # 緩存 60 秒後自動更新
def get_mlflow_runs(experiment_id):
    """從 MLflow Tracking API 獲取所有實驗運行結果 (使用 runs/search)。"""
    
    if not experiment_id:
        return pd.DataFrame()

    payload = {
        "experiment_ids": [experiment_id],
        "order_by": ["attributes.start_time DESC"]
    }
    
    try:
        full_url = f"{MLFLOW_BASE_URI}mlflow/runs/search"
        response = requests.post(full_url, json=payload, timeout=5) 
        response.raise_for_status() 

        json_data = response.json()
        if isinstance(json_data, dict) and 'runs' in json_data:
            run_data = json_data['runs']
        elif isinstance(json_data, list):
            run_data = json_data
        else:
            return pd.DataFrame()
        
        # 解析數據並返回 DataFrame
        records = []
        for run in run_data:
            # 解析metrics列表為字典
            metrics_dict = {}
            for metric in run.get('data', {}).get('metrics', []):
                metrics_dict[metric['key']] = metric['value']
            
            # 解析params列表為字典
            params_dict = {}
            for param in run.get('data', {}).get('params', []):
                params_dict[param['key']] = param['value']
            
            # 解析tags列表為字典
            tags_dict = {}
            for tag in run.get('data', {}).get('tags', []):
                tags_dict[tag['key']] = tag['value']
            
            records.append({
                'name': run.get('info', {}).get('run_name', 'N/A'),
                'f1': metrics_dict.get('f1_score', None),
                'precision': metrics_dict.get('precision_score', None),
                'recall': metrics_dict.get('recall_score', None),
                'auc': metrics_dict.get('roc_auc_score', None),
                'class_weight': params_dict.get('class_weight', '-'),
                'model_type': tags_dict.get('model_type', 'Unknown'),
            })
            
        df = pd.DataFrame(records).dropna(subset=['f1'])
        if not df.empty:
            df = df.sort_values(by='f1', ascending=False).reset_index(drop=True)
            df['f1'] = df['f1'].map(lambda x: f'{x:.4f}')
            df['precision'] = df['precision'].map(lambda x: f'{x:.4f}')
            df['recall'] = df['recall'].map(lambda x: f'{x:.4f}')
            df['auc'] = df['auc'].map(lambda x: f'{x:.4f}')
        
        return df

    except Exception as e:
        print(f"MLflow API 調用失敗: {e}")
        return pd.DataFrame()


# --- 介面呈現 (主邏輯) ---

st.title("💸 端到端詐欺交易偵測 Dashboard")
st.markdown("---")

# 1. 動態獲取 ID
EXP_ID = get_experiment_id()

# 2. 使用動態 ID 獲取數據
mlflow_df = get_mlflow_runs(EXP_ID)

st.header("📈 模型訓練歷史與性能比較")

if not mlflow_df.empty:
    st.dataframe(mlflow_df, use_container_width=True)
    
    # 顯示最佳模型信息
    best_model = mlflow_df.iloc[0] if len(mlflow_df) > 0 else None
    if best_model is not None:
        st.success(f"🏆 **最佳模型**: {best_model['name']} (F1 Score: {best_model['f1']})")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("F1 Score", best_model['f1'])
        with col2:
            st.metric("Precision", best_model['precision'])
        with col3:
            st.metric("Recall", best_model['recall'])
        with col4:
            st.metric("AUC", best_model['auc'])
else:
    st.info("無法載入 MLflow 數據，請確認服務已運行且模型已訓練。")


st.markdown("---")

# --- 2. 實時預測區 ---
st.header("🔍 實時單筆交易預測 (由 XGBoost 模型驅動)")

# 核心交易特徵輸入
with st.form("transaction_form"):
    col1, col2 = st.columns(2)
    with col1:
        time = st.number_input("時間 (Time)", value=45000.0, step=1.0)
        v1 = st.number_input("V1", value=-0.96, step=0.01)
        v3 = st.number_input("V3", value=-1.0, step=0.01)
        v5 = st.number_input("V5", value=-0.1, step=0.01)
        v7 = st.number_input("V7", value=0.0, step=0.01)
        v9 = st.number_input("V9", value=0.5, step=0.01)
        v11 = st.number_input("V11", value=0.0, step=0.01)
        v13 = st.number_input("V13", value=0.0, step=0.01)
        v15 = st.number_input("V15", value=0.0, step=0.01)
        v17 = st.number_input("V17", value=0.0, step=0.01)
        v19 = st.number_input("V19", value=0.0, step=0.01)
        v21 = st.number_input("V21", value=0.0, step=0.01)
        v23 = st.number_input("V23", value=0.0, step=0.01)
        v25 = st.number_input("V25", value=0.0, step=0.01)
        v27 = st.number_input("V27", value=0.0, step=0.01)
    
    with col2:
        amount = st.number_input("金額 (Amount)", value=120.50, step=0.01)
        v2 = st.number_input("V2", value=1.24, step=0.01)
        v4 = st.number_input("V4", value=0.0, step=0.01)
        v6 = st.number_input("V6", value=0.0, step=0.01)
        v8 = st.number_input("V8", value=0.0, step=0.01)
        v10 = st.number_input("V10", value=0.0, step=0.01)
        v12 = st.number_input("V12", value=0.0, step=0.01)
        v14 = st.number_input("V14", value=0.0, step=0.01)
        v16 = st.number_input("V16", value=0.0, step=0.01)
        v18 = st.number_input("V18", value=0.0, step=0.01)
        v20 = st.number_input("V20", value=0.0, step=0.01)
        v22 = st.number_input("V22", value=0.0, step=0.01)
        v24 = st.number_input("V24", value=0.0, step=0.01)
        v26 = st.number_input("V26", value=0.0, step=0.01)
        v28 = st.number_input("V28", value=0.0, step=0.01)

    submitted = st.form_submit_button("預測")

if submitted:
    # 將所有輸入包裝成 FastAPI 需要的 JSON 格式
    data_dict = {
        'time': time, 'amount': amount, 
        'v1': v1, 'v2': v2, 'v3': v3, 'v4': v4, 'v5': v5, 'v6': v6, 'v7': v7, 'v8': v8, 'v9': v9, 
        'v10': v10, 'v11': v11, 'v12': v12, 'v13': v13, 'v14': v14, 'v15': v15, 'v16': v16, 'v17': v17, 
        'v18': v18, 'v19': v19, 'v20': v20, 'v21': v21, 'v22': v22, 'v23': v23, 'v24': v24, 'v25': v25, 
        'v26': v26, 'v27': v27, 'v28': v28
    }

    try:
        # 呼叫 FastAPI 服務 (現在運行的是 XGBoost)
        response = requests.post(API_URL, json=data_dict)
        response.raise_for_status()
        result = response.json()
        
        st.subheader("💡 預測結果")
        
        if result['is_fraud'] == 1:
            st.error(f"🚨 **詐欺警報**：交易被判斷為 **詐欺 (Fraud)**")
        else:
            st.success(f"✅ **交易正常**：交易被判斷為 **正常 (Normal)**")

        st.metric("詐欺機率", f"{result['fraud_probability']:.4f}")
        st.json(result) # 顯示完整的 API 回傳結果
            
    except requests.exceptions.ConnectionError:
        st.error(f"無法連線到 FastAPI 服務 ({API_URL})。請檢查 fraud_api 容器是否運行。")
    except Exception as e:
        st.error(f"API 呼叫失敗，錯誤訊息: {e}。請檢查 API logs。")
        try:
            if 'response' in locals():
                st.json(response.json())
        except:
            pass