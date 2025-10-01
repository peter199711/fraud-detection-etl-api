# 🚀 詐欺偵測系統完整服務指南

## 📋 服務概覽

本系統包含以下9個核心服務，完整實現MLOps生產級架構：

| 服務名稱 | 容器名稱 | 端口 | 描述 |
|---------|---------|------|------|
| **PostgreSQL資料庫** | `postgres_db` | 5432 | 主要資料庫，存儲交易數據和特徵 |
| **Apache Airflow (初始化)** | `airflow_init` | - | 一次性執行的Airflow初始化服務 |
| **Apache Airflow UI** | `airflow_webserver` | 8080 | Airflow Web界面，管理工作流程 |
| **Apache Airflow 排程器** | `airflow_scheduler` | - | DAG任務排程和執行引擎 |
| **MLflow追蹤服務** | `mlflow_server` | 5000 | 機器學習實驗追蹤和模型版本管理 |
| **詐欺偵測API** | `fraud-api` | 8000 | FastAPI服務，提供詐欺預測功能 |
| **Streamlit Dashboard** | `fraud-dashboard` | 8501 | 互動式儀表板，模型監控和預測 |
| **Adminer** | `adminer` | 8088 | 資料庫管理介面 |

## 🎯 新版本架構亮點

### ✨ Apache Airflow整合
- 🔄 **自動化ETL管道**: 完整的數據處理和模型訓練工作流程
- 📅 **定期排程執行**: 每日自動重訓練和模型更新
- 🎛️ **可視化管理**: Web UI監控所有任務狀態
- 🔧 **錯誤恢復**: 智能重試機制和失敗通知

### 🔧 主要改進項目

**1. 工作流程自動化**
✅ 完整的Airflow DAG實現：
- 數據庫連線檢查
- 自動數據載入
- 特徵視圖創建
- 模型訓練和比較
- 性能驗證
- 清理作業

**2. 容器化優化**
✅ 全面Docker架構：
- 專用Airflow容器 (`Dockerfile.airflow`)
- 統一網路配置
- 環境變數管理
- Volume持久化

**3. 端口重新配置**
✅ 避免服務衝突：
- Airflow UI: `8080`
- Adminer: `8088` (原8080改至8088)
- 所有其他端口維持不變

**4. 模型載入策略優化**
✅ 智能模型選擇：
- 優先從MLflow載入最佳模型
- 本地備份機制
- 自動F1 Score比較

## 🚀 快速啟動

### 方法1：完整自動化啟動 (推薦)

```bash
cd docker

# 1. 啟動基礎服務
docker-compose up -d postgres_db mlflow_server

# 2. 初始化Airflow
docker-compose up -d airflow-init

# 3. 啟動Airflow核心服務
docker-compose up -d airflow-webserver airflow-scheduler

# 4. 等待2-3分鐘讓服務完全啟動，然後啟動應用服務
docker-compose up -d fraud_api fraud_dashboard adminer
```

### 方法2：分步驟手動執行

```bash
cd docker

# 1. 基礎設施服務
docker-compose up -d postgres_db mlflow_server

# 2. 等待資料庫就緒 (約10秒)
sleep 10

# 3. Airflow服務 (按順序啟動)
docker-compose up -d airflow-init
docker-compose up -d airflow-webserver airflow-scheduler

# 4. 手動執行ETL (可選，或等待Airflow DAG執行)
# docker run --rm --network docker_default \
#   -v $(pwd)/../src:/opt/airflow/src \
#   -v $(pwd)/../data:/opt/airflow/data \
#   fraud-detection-etl-api_airflow-webserver \
#   python -m etl.db_load

# docker run --rm --network docker_default \
#   -v $(pwd)/../src:/opt/airflow/src \
#   fraud-detection-etl-api_airflow-webserver \
#   python -m etl.transform_data

# 5. 應用層服務
docker-compose up -d fraud_api fraud_dashboard adminer
```

## 🌐 服務訪問

| 服務 | URL | 用途 | 登入資訊 |
|------|-----|------|----------|
| **API服務** | http://localhost:8000 | REST API端點 | - |
| **API文檔** | http://localhost:8000/docs | Swagger互動文檔 | - |
| **Dashboard** | http://localhost:8501 | 模型監控和預測介面 | - |
| **MLflow** | http://localhost:5000 | 實驗追蹤和模型管理 | - |
| **Airflow UI** | http://localhost:8080 | 工作流程管理和監控 | admin/admin |
| **Adminer** | http://localhost:8088 | 資料庫管理 | 見下方 |

### Airflow登入資訊
- **使用者名稱**: admin
- **密碼**: admin

### Adminer登入資訊
- **系統**: PostgreSQL
- **伺服器**: postgres_db
- **使用者名稱**: user
- **密碼**: password
- **資料庫**: fraud_db

## 🔍 服務測試與驗證

### 1. 系統狀態檢查
```bash
cd docker
docker-compose ps
```

### 2. 服務健康檢查
```bash
# PostgreSQL
curl -f http://localhost:8088 || echo "Adminer無法訪問"

# MLflow
curl -f http://localhost:5000 || echo "MLflow無法訪問"

# Airflow
curl -f http://localhost:8080 || echo "Airflow UI無法訪問"

# API
curl http://localhost:8000/ || echo "API無法訪問"

# Dashboard
curl -f http://localhost:8501 || echo "Dashboard無法訪問"
```

### 3. API功能測試
```bash
# 詐欺預測測試
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "time": 45000.0,
    "amount": 120.50,
    "v1": -0.96, "v2": 1.24, "v3": -1.0, "v4": 0.0, "v5": -0.1,
    "v6": 0.0, "v7": 0.0, "v8": 0.0, "v9": 0.5, "v10": 0.0,
    "v11": 0.0, "v12": 0.0, "v13": 0.0, "v14": 0.0, "v15": 0.0,
    "v16": 0.0, "v17": 0.0, "v18": 0.0, "v19": 0.0, "v20": 0.0,
    "v21": 0.0, "v22": 0.0, "v23": 0.0, "v24": 0.0, "v25": 0.0,
    "v26": 0.0, "v27": 0.0, "v28": 0.0
  }'
```

**預期回應**:
```json
{
  "is_fraud": 0,
  "fraud_probability": 0.1234,
  "message": "Transaction analyzed successfully."
}
```

## ⚡ Airflow DAG操作指南

### DAG功能說明
`fraud_detection_pipeline` DAG包含以下任務：

1. **check_database_connection** - 驗證資料庫連線
2. **load_new_data** - 載入原始交易數據
3. **create_feature_view** - 創建特徵工程視圖
4. **perform_model_training** - 執行模型訓練
5. **validate_model_performance** - 驗證模型性能
6. **cleanup_temp_files** - 清理暫存檔案

### 手動觸發DAG
1. 開啟 http://localhost:8080
2. 使用 admin/admin 登入
3. 找到 `fraud_detection_pipeline`
4. 點擊 ▶️ 按鈕觸發執行

### 查看DAG執行狀態
- **Graph View**: 查看任務依賴圖
- **Tree View**: 查看歷史執行記錄
- **Logs**: 查看各任務詳細日誌

## 🛠️ 疑難排解

### 常見問題與解決方案

**1. Airflow初始化失敗**
```
airflow_init容器異常退出
```
✅ **解決方案**: 確保PostgreSQL先啟動
```bash
docker-compose up -d postgres_db
sleep 10  # 等待資料庫就緒
docker-compose up -d airflow-init
```

**2. 端口衝突問題**
```
Port 8080 already in use
```
✅ **解決方案**: 檢查其他使用8080的服務
```bash
# Windows
netstat -ano | findstr :8080

# Linux/Mac
lsof -i :8080

# 終止佔用程序或修改docker-compose.yml端口配置
```

**3. Airflow Web UI無法訪問**
```
Connection refused
```
✅ **解決方案**: 確認服務啟動順序
```bash
docker-compose logs airflow-webserver
docker-compose ps airflow-webserver
```

**4. 模型載入失敗**
```
Model not loaded. Please check logs and run ETL script.
```
✅ **解決方案**: 確保模型訓練已完成
```bash
# 方法1: 透過Airflow執行
# 在Airflow UI中手動觸發 fraud_detection_pipeline

# 方法2: 手動執行ETL
docker-compose exec airflow-webserver python -m etl.db_load
docker-compose exec airflow-webserver python -m etl.transform_data
```

**5. MLflow連線問題**
```
MLflow Server unreachable
```
✅ **解決方案**: 檢查MLflow容器狀態
```bash
docker-compose logs mlflow_server
curl http://localhost:5000
```

**6. 資料庫連線失敗**
```
Connection to PostgreSQL failed
```
✅ **解決方案**: 檢查資料庫容器
```bash
docker-compose logs postgres_db
docker-compose exec postgres_db pg_isready -U user -d fraud_db
```

### 檢查所有服務狀態
```bash
cd docker

# 檢查容器狀態
docker-compose ps

# 檢查特定服務日誌
docker-compose logs [service_name]

# 檢查網路連線
docker network ls
docker network inspect docker_default
```

### 完全重置系統
```bash
cd docker

# 停止所有服務
docker-compose down -v

# 清理Docker資源
docker system prune -f

# 重新構建並啟動
docker-compose build --no-cache
docker-compose up -d
```

## 📊 系統架構圖

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Dashboard     │    │      API        │    │    MLflow       │
│   (Streamlit)   │◄──►│   (FastAPI)     │◄──►│   Tracking      │
│   Port: 8501    │    │   Port: 8000    │    │   Port: 5000    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Airflow Web    │    │   PostgreSQL    │    │    Adminer      │
│     (UI)        │◄──►│   (Database)    │◄──►│  (DB Manager)   │
│   Port: 8080    │    │   Port: 5432    │    │   Port: 8088    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         │                       │
┌─────────────────┐              │
│ Airflow Scheduler│              │
│   (Background)   │──────────────┘
│    No Port       │
└─────────────────┘
```

## 🎯 最佳實踐建議

### 1. 開發環境
- 使用 `docker-compose logs -f [service_name]` 即時監控日誌
- 定期備份PostgreSQL數據 (`docker-compose exec postgres_db pg_dump...`)
- 監控磁碟空間，MLflow artifacts會持續增長

### 2. 生產部署
- 修改預設密碼和API密鑰
- 設定外部數據庫 (非Docker容器)
- 配置反向代理 (Nginx/Apache)
- 實施SSL/TLS加密
- 設定監控告警

### 3. Airflow管理
- 定期清理舊的DAG runs
- 監控任務執行時間
- 設定適當的重試次數
- 使用Airflow Variables管理配置

### 4. 模型管理
- 定期檢查模型性能
- 設定模型性能閾值告警
- 保留模型版本歷史
- 實施A/B測試機制

---

**✅ 系統已完全配置為自動化MLOps管道，具備生產級可靠性！**