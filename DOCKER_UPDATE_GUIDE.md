# Docker 系統更新指南

## 📦 TensorFlow 整合的 Docker 更新步驟

---

## ⚠️ 重要說明

**單純 `docker compose down` 和 `docker compose up` 不夠！**

因為你新增了 TensorFlow 依賴，需要：
1. ✅ 更新 Dockerfile（已完成）
2. ✅ **重新構建 Docker images**（必須）
3. ✅ 重啟容器

---

## 🚀 完整更新步驟

### 步驟 1: 停止所有容器

```bash
cd docker
docker compose down
```

**預期輸出:**
```
[+] Running 9/9
 ✔ Container airflow_scheduler      Removed
 ✔ Container airflow_webserver      Removed
 ✔ Container fraud-dashboard        Removed
 ✔ Container fraud-api              Removed
 ✔ Container mlflow_server          Removed
 ✔ Container adminer                Removed
 ✔ Container airflow_init           Removed
 ✔ Container postgres_db            Removed
```

---

### 步驟 2: 重新構建 Images（重要！）

```bash
# 重新構建所有 images（包含 TensorFlow）
docker compose build --no-cache

# 或者只構建特定服務
docker compose build --no-cache fraud_api airflow-webserver airflow-scheduler
```

**⏱️ 預計時間:** 5-15 分鐘（取決於網路速度）

**預期輸出:**
```
[+] Building 450.2s (12/12) FINISHED
 => [fraud_api internal] load build definition
 => => transferring dockerfile: 1.05kB
 => [fraud_api internal] load .dockerignore
 ...
 => [fraud_api] => RUN pip install tensorflow>=2.15.0
 ...
 => [fraud_api] exporting to image
 ✔ fraud_api
 ✔ airflow-webserver
 ✔ airflow-scheduler
```

---

### 步驟 3: 啟動容器

```bash
docker compose up -d
```

**預期輸出:**
```
[+] Running 9/9
 ✔ Container postgres_db            Started
 ✔ Container mlflow_server          Started
 ✔ Container adminer                Started
 ✔ Container airflow_init           Started
 ✔ Container airflow_webserver      Started
 ✔ Container airflow_scheduler      Started
 ✔ Container fraud-api              Started
 ✔ Container fraud-dashboard        Started
```

---

### 步驟 4: 驗證 TensorFlow 安裝

#### 驗證 API 容器
```bash
docker exec -it fraud-api python -c "import tensorflow as tf; print(f'TensorFlow 版本: {tf.__version__}')"
```

**預期輸出:**
```
TensorFlow 版本: 2.15.0
```

#### 驗證 Airflow 容器
```bash
docker exec -it airflow_webserver python -c "import tensorflow as tf; print(f'TensorFlow 版本: {tf.__version__}')"
```

**預期輸出:**
```
TensorFlow 版本: 2.15.0
```

---

## 🔍 檢查服務狀態

### 查看所有容器狀態
```bash
docker compose ps
```

**預期輸出（所有服務 State 為 running）:**
```
NAME                  IMAGE                      STATUS         PORTS
postgres_db           postgres:16-alpine         Up 2 minutes   0.0.0.0:5432->5432/tcp
mlflow_server         fraud-detection-mlflow     Up 2 minutes   0.0.0.0:5000->5000/tcp
airflow_webserver     fraud-detection-airflow    Up 2 minutes   0.0.0.0:8080->8080/tcp
airflow_scheduler     fraud-detection-airflow    Up 2 minutes   
fraud-api             fraud-detection-api        Up 2 minutes   0.0.0.0:8000->8000/tcp
fraud-dashboard       fraud-detection-dashboard  Up 2 minutes   0.0.0.0:8501->8501/tcp
adminer               adminer:4.8.1              Up 2 minutes   0.0.0.0:8088->8080/tcp
```

### 查看 API 日誌
```bash
docker compose logs -f fraud_api
```

**尋找以下訊息（表示成功）:**
```
✅ 成功從 MLflow 載入最佳模型！
  模型類型: TensorFlow_DNN
  F1 Score: 0.XXXX
```

---

## 🎯 測試 TensorFlow 整合

### 測試 1: 從本機呼叫 API
```bash
# 在專案根目錄執行
python test_tensorflow_integration.py
```

### 測試 2: 執行 Airflow DAG
1. 訪問 http://localhost:8080
2. 登入（admin/admin）
3. 啟動 `fraud_detection_pipeline` DAG
4. 等待 `perform_model_training` 任務完成
5. 檢查日誌是否有 "訓練: TensorFlow_DNN"

### 測試 3: 查看 MLflow
1. 訪問 http://localhost:5000
2. 查看 "Fraud Detection Baseline" 實驗
3. 確認有 "04_TensorFlow_DNN" 的 run

---

## 📊 已更新的檔案

### Docker 相關
- ✅ `docker/Dockerfile.api` (+tensorflow)
- ✅ `docker/Dockerfile.airflow` (+tensorflow)

### Python 代碼
- ✅ `src/models/tensorflow_model.py` (新增)
- ✅ `src/etl/transform_data.py` (整合 TF 訓練)
- ✅ `src/api/main.py` (支援 TF 載入)
- ✅ `src/api/requirements.txt` (+tensorflow)

### 文檔
- ✅ `TENSORFLOW_INTEGRATION.md`
- ✅ `TENSORFLOW_QUICK_START.md`
- ✅ `KERAS_3_MIGRATION_NOTES.md`
- ✅ `DOCKER_UPDATE_GUIDE.md` (本文件)

---

## ⚡ 快速指令摘要

```bash
# 完整更新流程（一次性執行）
cd docker
docker compose down
docker compose build --no-cache
docker compose up -d

# 驗證安裝
docker exec -it fraud-api python -c "import tensorflow as tf; print(tf.__version__)"

# 查看日誌
docker compose logs -f fraud_api
```

---

## ❓ 常見問題

### Q1: 為什麼需要 `--no-cache`？
**A:** 確保 Docker 不使用舊的 cache，重新安裝 TensorFlow。

### Q2: 構建太慢怎麼辦？
**A:** 
```bash
# 只構建需要 TensorFlow 的服務
docker compose build --no-cache fraud_api airflow-webserver airflow-scheduler
```

### Q3: 如果構建失敗怎麼辦？
**A:** 檢查錯誤訊息，常見原因：
- 網路問題（下載 TensorFlow 太慢）
- 磁碟空間不足
- 解決方法：清理舊 images
  ```bash
  docker system prune -a
  ```

### Q4: 需要刪除 volumes 嗎？
**A:** 通常不需要，除非你想清空所有數據：
```bash
# ⚠️ 警告：這會刪除所有數據！
docker compose down -v
```

### Q5: 舊模型還能用嗎？
**A:** 可以！新系統向後兼容：
- Logistic Regression, XGBoost, LightGBM 正常運行
- TensorFlow 模型會被自動添加到比較清單

---

## 🐛 故障排除

### 問題 1: TensorFlow 導入失敗
```bash
# 進入容器檢查
docker exec -it fraud-api bash
pip list | grep tensorflow
```

**解決:** 如果沒有 tensorflow，重新構建：
```bash
docker compose build --no-cache fraud_api
```

### 問題 2: 容器啟動失敗
```bash
# 查看詳細日誌
docker compose logs fraud_api
```

**解決:** 通常是依賴衝突，檢查日誌中的錯誤訊息。

### 問題 3: 模型訓練失敗
```bash
# 查看 Airflow 日誌
docker compose logs airflow_scheduler
```

**解決:** 確認 Airflow 容器也安裝了 TensorFlow：
```bash
docker exec -it airflow_scheduler python -c "import tensorflow as tf; print(tf.__version__)"
```

---

## 📈 性能考量

### TensorFlow 對 Image 大小的影響
- **API Image:** ~2GB → ~3.5GB (+1.5GB)
- **Airflow Image:** ~2.5GB → ~4GB (+1.5GB)

### 首次構建時間
- **無 TensorFlow:** ~3-5 分鐘
- **含 TensorFlow:** ~10-15 分鐘

### 運行時資源使用
- **記憶體:** 建議至少 8GB RAM
- **CPU:** TensorFlow 訓練會使用更多 CPU
- **磁碟:** 需要額外 3-4GB 空間

---

## 🎓 進階：選擇性更新

如果你只想在本機測試，不想更新 Docker：

```bash
# 本機環境測試
source venv_api/bin/activate  # Linux/WSL
# 或
.\venv_api\Scripts\Activate.ps1  # Windows

pip install tensorflow>=2.15.0
python -m src.etl.transform_data  # 本機訓練
uvicorn src.api.main:app --reload  # 本機 API
```

---

## ✅ 更新檢查清單

完成以下步驟確保更新成功：

- [ ] `docker compose down` 停止所有容器
- [ ] `docker compose build --no-cache` 重新構建
- [ ] `docker compose up -d` 啟動容器
- [ ] 驗證 API 容器有 TensorFlow
- [ ] 驗證 Airflow 容器有 TensorFlow
- [ ] 執行測試腳本通過
- [ ] Airflow DAG 可以訓練 TensorFlow 模型
- [ ] MLflow 可以記錄 TensorFlow 模型
- [ ] API 可以載入 TensorFlow 模型

---

**更新完成後，你的整個系統就支援 TensorFlow 了！** 🎉

有任何問題，請查看日誌或參考故障排除章節。

