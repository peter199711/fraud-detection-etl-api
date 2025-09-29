## 📌 Fraud Detection ETL & API Deployment
### 🔍 專案簡介
本專案實作端到端詐欺交易偵測系統，涵蓋資料 ETL → 模型訓練 → API 部署 → Dashboard，模擬銀行如何以機器學習防範詐欺交易。核心重點是將資料科學模型產品化，而非停留在 Notebook 階段。

### 📂 專案架構
```text
fraud-detection-etl-api/
│── data/               # 原始與處理後的資料
│── notebooks/          # EDA 與模型實驗
│── src/
│   ├── etl/            # ETL 腳本
│   ├── models/         # 訓練與推論程式
│   ├── api/            # FastAPI 服務
│   └── dashboard/      # Streamlit Dashboard
│── docker/
│   ├── Dockerfile.api
│   ├── Dockerfile.dashboard
│   └── docker-compose.yml
│── README.md
```

### 🛠 技術棧
- **資料庫**: MySQL / Postgres（Docker Compose）
- **ETL**: Python（pandas），可升級為 Airflow / dbt
- **機器學習**: scikit-learn、XGBoost
- **API 部署**: FastAPI + Uvicorn
- **容器化**: Docker、Docker Compose
- **視覺化**: Streamlit Dashboard

### ⚙️ 安裝與執行
#### 1) 環境需求
- Docker / Docker Compose
- Python 3.12+

#### 2) 啟動專案
```bash
# Clone 專案
git clone https://github.com/yourname/fraud-detection-etl-api.git
cd fraud-detection-etl-api

# 啟動整個系統 (DB + API + Dashboard)
docker-compose up --build
```

#### 3) 服務位置
- **FastAPI (API)**: [Swagger UI](http://localhost:8000/docs)
- **Streamlit Dashboard**: [Dashboard](http://localhost:8501)
- **MySQL Adminer / pgAdmin**: [管理介面](http://localhost:8080)

### 📊 系統流程架構圖
```text
[Dataset] → [ETL Pipeline] → [Database] → [ML Model] → [FastAPI Service] → [Dashboard]
```
（之後可加上 Mermaid 流程圖或 draw.io 架構圖）

### 🚀 功能展示
#### ETL Pipeline
- 自動清理 Kaggle 信用卡詐欺資料
- 導入 MySQL，產生特徵表

#### 模型訓練
- Logistic Regression、XGBoost
- 指標：Confusion Matrix、ROC、AUC、Precision/Recall

#### API 部署
- `POST /predict`：輸入交易 JSON，回傳是否詐欺（0/1 + 機率）
示例：
```json
{
  "amount": 1200.5,
  "time": 34567,
  "feature_v1": -1.23,
  "feature_v2": 2.14
}
```

#### Dashboard
- 模型表現視覺化
- 輸入交易樣本，立即獲取預測結果

### 📈 商業價值模擬
- 每降低 1% 假陽性（False Positive），可減少誤攔交易導致的客戶流失
- 每降低 1% 假陰性（False Negative），可直接降低金錢損失

本專案展示如何透過數據驅動決策，協助金融機構更有效控管風險。

### ✅ 未來改進方向
- 加入 Airflow pipeline 自動化 ETL
- 導入模型版本管理（MLflow）
- API 加上 JWT 驗證
- 部署至雲端（AWS / GCP / Azure / Railway）