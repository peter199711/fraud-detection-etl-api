# src/dashboard/app.py

import streamlit as st
import pandas as pd
import requests
import json

# FastAPI 服務的 URL (從容器內或主機上訪問)
# 如果在同一個 docker-compose 網路中，可以直接使用服務名稱 'fraud_api'
# 但在本地測試和簡單部署中，使用 'http://fraud_api:8000' 或 'http://localhost:8000'
API_URL = "http://fraud_api:8000/predict" 

st.set_page_config(page_title="詐欺偵測儀表板", layout="wide")

st.title("💸 實時詐欺交易預測")
st.markdown("---")

# 1. 交易輸入介面 (讓用戶輸入一筆交易數據)
st.header("輸入交易樣本")

# 為了簡潔，我們只讓用戶輸入幾個重要的特徵
with st.form("transaction_form"):
    # 這裡的欄位名稱必須與 FastAPI 的 Transaction Pydantic 結構中的欄位名稱一致
    time = st.number_input("時間 (Time)", value=45000.0, step=1.0)
    amount = st.number_input("金額 (Amount)", value=120.50, step=0.01)
    
    # V 特徵，為了簡化，我們只讓用戶輸入 V1 和 V2
    # 實際上需要所有 V1-V28
    v1 = st.number_input("V1", value=-0.96, step=0.01)
    v2 = st.number_input("V2", value=1.24, step=0.01)
    
    # 由於模型需要 V3-V28，我們必須補齊這些欄位，這裡使用一個平均/預設值
    # 最佳實踐是讓 API 處理缺失值，但這裡我們在 Dashboard 中補齊
    
    data_dict = {
        "time": time,
        "amount": amount,
        "v1": v1,
        "v2": v2,
        # **重要：補齊所有 V3-V28 的欄位，使用任何代表「正常」的值，例如 0.0 或 -1.0**
        # 由於我不知道你的模型訓練數據，這裡假設 V3-V28 為 0.0
    }
    for i in range(3, 29):
        data_dict[f'v{i}'] = 0.0 # 補齊 V3 到 V28
        
    submitted = st.form_submit_button("預測")

if submitted:
    try:
        # 呼叫 FastAPI 服務
        response = requests.post(API_URL, json=data_dict)
        
        if response.status_code == 200:
            result = response.json()
            st.subheader("💡 預測結果")
            
            if result['is_fraud'] == 1:
                st.error(f"🚨 **詐欺警報**：交易被判斷為 **詐欺 (Fraud)**")
            else:
                st.success(f"✅ **交易正常**：交易被判斷為 **正常 (Normal)**")

            st.metric("詐欺機率", f"{result['fraud_probability']:.4f}")
            
        else:
            st.error(f"API 呼叫失敗，狀態碼: {response.status_code}")
            st.json(response.json())
            
    except requests.exceptions.ConnectionError:
        st.error(f"無法連線到 FastAPI 服務 ({API_URL})。請檢查 fraud_api 容器是否運行。")
    except Exception as e:
        st.error(f"發生未知錯誤: {e}")