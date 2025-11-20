# TensorFlow 模型整合文檔

> **完成日期:** 2025-11-20  
> **作者:** Fraud Detection Team  
> **版本:** 1.0

## 📋 概述

本文檔記錄了 TensorFlow 深度學習模型整合到詐欺偵測系統的完整過程。整合遵循**最小侵入原則**，不影響現有的機器學習模型（Logistic Regression, XGBoost, LightGBM）。

---

## 🎯 整合目標

- ✅ 添加 TensorFlow/Keras 深度神經網路模型
- ✅ 與現有 MLflow 追蹤系統整合
- ✅ 保持與其他模型的公平比較基準
- ✅ 支援 API 自動載入最佳模型（無論類型）
- ✅ 整合到 Airflow ETL Pipeline

---

## 📁 新增檔案

### 1. **模型定義模組**
```
src/models/tensorflow_model.py
```
**功能:**
- `build_fraud_detection_model()`: 建構深度神經網路
- `train_tensorflow_model()`: 訓練模型並記錄到 MLflow
- `create_class_weights()`: 計算類別權重處理不平衡數據
- `predict_with_tensorflow_model()`: 預測函式

**模型架構:**
```
Input (30 features)
    ↓
Dense(128) + BatchNorm + Dropout(0.3)
    ↓
Dense(64) + BatchNorm + Dropout(0.2)
    ↓
Dense(32) + Dropout(0.1)
    ↓
Dense(1, sigmoid) [輸出]
```

### 2. **實驗 Notebook**
```
notebooks/tensorflow_model_training.ipynb
```
**內容:**
- 完整的資料載入與預處理流程
- 模型訓練與評估
- 訓練歷史視覺化
- ROC 曲線與 Precision-Recall 曲線
- 模型儲存

### 3. **整合測試腳本**
```
test_tensorflow_integration.py
```
**測試項目:**
- TensorFlow 模組導入
- 自訂模型模組導入
- 模型建構
- ETL Pipeline 整合
- API 整合
- 模型預測功能

---

## 🔧 修改的檔案

### 1. **依賴管理**
**檔案:** `src/api/requirements.txt`

**變更:**
```diff
+ tensorflow>=2.15.0
```

### 2. **ETL 訓練腳本**
**檔案:** `src/etl/transform_data.py`

**變更:**

#### a) 導入 TensorFlow 模組
```python
# 新增導入
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from models.tensorflow_model import train_tensorflow_model
```

#### b) 模型配置列表新增 TensorFlow
```python
{
    "name": "04_TensorFlow_DNN",
    "class": None,
    "params": {
        'epochs': 50,
        'batch_size': 256,
        'learning_rate': 0.001,
        'early_stopping_patience': 10
    },
    "tags": {"data_source": "Postgres-VIEW", "model_type": "TensorFlow"},
    "type": "tensorflow"
}
```

#### c) 訓練循環支援 TensorFlow
```python
# 根據模型類型選擇訓練方式
if config.get("type") == "tensorflow":
    current_f1, current_model = train_tensorflow_model(...)
else:
    current_f1, current_model = train_model_and_log_mlflow(...)
```

### 3. **API 服務**
**檔案:** `src/api/main.py`

**變更:**

#### a) 導入 TensorFlow 模組
```python
import mlflow.tensorflow  # 新增
```

#### b) 模型載入邏輯
```python
if model_name in ['TensorFlow', 'TensorFlow_DNN']:
    model = mlflow.tensorflow.load_model(model_uri)
```

#### c) 預測邏輯
```python
elif hasattr(model, 'predict') and hasattr(model, 'layers'):
    # TensorFlow/Keras 模型
    proba = model.predict(df.values).flatten()
```

---

## 🚀 使用方式

### 方式 1: 使用 Notebook 獨立訓練

```bash
# 啟動 Jupyter Notebook
jupyter notebook notebooks/tensorflow_model_training.ipynb
```

按順序執行所有 cell，模型會自動儲存到 `src/models/` 目錄。

### 方式 2: 透過 ETL Pipeline 訓練

```bash
# 確保資料庫和 MLflow 服務正在運行
# 執行 ETL 腳本
python -m src.etl.transform_data
```

**注意:** 
- TensorFlow 模型會與其他模型一起訓練
- 所有模型的性能指標會記錄到 MLflow
- 最佳模型（基於 F1 Score）會被自動選擇

### 方式 3: 透過 Airflow DAG 自動訓練

啟動 Airflow DAG `fraud_detection_pipeline`，TensorFlow 模型會作為訓練流程的一部分自動執行。

---

## 📊 模型性能監控

### MLflow Tracking

所有 TensorFlow 模型訓練會記錄以下資訊：

**參數 (Parameters):**
- `model_type`: "TensorFlow_DNN"
- `epochs`: 訓練輪數
- `batch_size`: 批次大小
- `learning_rate`: 學習率
- `early_stopping_patience`: Early Stopping 耐心值

**指標 (Metrics):**
- `roc_auc_score`: ROC AUC 分數
- `f1_score`: F1 分數
- `precision_score`: 精確率
- `recall_score`: 召回率
- `train_loss`: 訓練損失（每個 epoch）
- `train_auc`: 訓練 AUC（每個 epoch）

**模型檔案 (Artifacts):**
- TensorFlow SavedModel 格式

### 查看實驗結果

```bash
# 訪問 MLflow UI
http://localhost:5000

# 查看實驗: "Fraud Detection Baseline"
# 比較所有模型（包括 TensorFlow）的性能
```

---

## 🔍 測試驗證

執行整合測試腳本：

```bash
python test_tensorflow_integration.py
```

**預期輸出:**
```
╔==========================================================╗
║          TensorFlow 整合測試套件                          ║
╚==========================================================╝

============================================================
測試 1: TensorFlow 模組導入
============================================================
✅ TensorFlow 版本: 2.15.0
✅ GPU 可用: 0 個

============================================================
測試 2: 自訂模型模組導入
============================================================
✅ 成功導入 tensorflow_model 模組
✅ 可用函式: build_fraud_detection_model, train_tensorflow_model, create_class_weights

... (其他測試) ...

============================================================
測試總結
============================================================
通過: 6/6
失敗: 0/6

🎉 所有測試通過！TensorFlow 整合成功！
```

---

## ⚙️ 環境設定

### 安裝依賴

#### Windows (PowerShell)
```powershell
# API 環境
.\venv_api\Scripts\Activate.ps1
pip install tensorflow>=2.15.0

# Airflow 環境（如果使用 Airflow）
.\venv_airflow_wsl\Scripts\Activate.ps1
pip install tensorflow>=2.15.0
```

#### Linux/WSL
```bash
# API 環境
source venv_api/bin/activate
pip install tensorflow>=2.15.0

# Airflow 環境
source venv_airflow_wsl/bin/activate
pip install tensorflow>=2.15.0
```

### GPU 支援（選用）

如果要啟用 GPU 加速：

```bash
# 安裝 CUDA 版本的 TensorFlow
pip install tensorflow[and-cuda]>=2.15.0

# 驗證 GPU 可用性
python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
```

---

## 🎯 超參數調整建議

### 當前配置（Baseline）
```python
epochs = 50
batch_size = 256
learning_rate = 0.001
early_stopping_patience = 10
```

### 優化方向

**提高 Recall（捕捉更多詐欺）:**
- 增加 `class_weight[1]` 的權重
- 調整 threshold < 0.5（如 0.3）
- 使用 Focal Loss 取代 binary_crossentropy

**提高 Precision（減少誤報）:**
- 增加 Dropout rate
- 減少模型複雜度
- 使用 L2 正則化

**加速訓練:**
- 增加 `batch_size` (512, 1024)
- 增加 `learning_rate` (0.01)
- 減少網路層數

---

## 📈 與其他模型的比較

### 預期性能範圍

| 模型 | AUC | F1 | Precision | Recall | 訓練時間 |
|------|-----|----|-----------| -------|---------|
| Logistic Regression | ~0.97 | ~0.11 | 低 | 高 | 最快 |
| XGBoost | ~0.98 | ~0.15 | 中 | 中 | 中等 |
| LightGBM | ~0.98 | ~0.14 | 中 | 中 | 快 |
| **TensorFlow DNN** | ~0.97 | ~0.12 | 中 | 高 | 較慢 |

### TensorFlow 的優勢
- 🔹 更好的非線性模式捕捉能力
- 🔹 架構靈活，易於添加自訂層
- 🔹 可整合 Embedding 層處理類別特徵
- 🔹 支援 Transfer Learning
- 🔹 易於部署到 TensorFlow Serving

### TensorFlow 的限制
- ⚠️ 訓練時間較長
- ⚠️ 需要更多超參數調整
- ⚠️ 對小數據集可能過擬合
- ⚠️ 解釋性不如樹模型

---

## 🛠️ 故障排除

### 問題 1: TensorFlow 導入失敗

**錯誤訊息:**
```
ModuleNotFoundError: No module named 'tensorflow'
```

**解決方法:**
```bash
pip install tensorflow>=2.15.0
```

### 問題 2: MLflow 記錄失敗

**錯誤訊息:**
```
模型記錄失敗: Connection refused
```

**解決方法:**
```bash
# 確認 MLflow Server 正在運行
mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri sqlite:///mlflow.db
```

### 問題 3: API 載入 TensorFlow 模型失敗

**錯誤訊息:**
```
AttributeError: 'PyfuncModel' object has no attribute 'predict_proba'
```

**解決方法:**  
已在 `main.py` 中處理，會自動檢測模型類型並使用正確的預測方法。

### 問題 4: GPU 記憶體不足

**錯誤訊息:**
```
ResourceExhaustedError: OOM when allocating tensor
```

**解決方法:**
```python
# 在訓練前添加
import tensorflow as tf
gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    tf.config.experimental.set_memory_growth(gpus[0], True)
```

---

## 📚 相關資源

- [TensorFlow 官方文檔](https://www.tensorflow.org/)
- [Keras API 參考](https://keras.io/api/)
- [MLflow TensorFlow 整合](https://mlflow.org/docs/latest/python_api/mlflow.tensorflow.html)
- [不平衡數據處理](https://www.tensorflow.org/tutorials/structured_data/imbalanced_data)

---

## 🔄 未來改進方向

### 短期（1-2 週）
- [ ] 超參數自動調整（Keras Tuner）
- [ ] 添加更多評估指標（PR-AUC, Matthews Correlation）
- [ ] 模型解釋性分析（SHAP, LIME）

### 中期（1-2 月）
- [ ] 嘗試其他架構（CNN, Attention）
- [ ] 集成學習（與 XGBoost 組合）
- [ ] 實時模型更新機制

### 長期（3-6 月）
- [ ] 部署到 TensorFlow Serving
- [ ] A/B 測試框架
- [ ] 模型版本管理與回滾機制

---

## 📝 更新日誌

### v1.0 (2025-11-20)
- ✅ 初始整合完成
- ✅ 基礎 DNN 架構實現
- ✅ MLflow 追蹤整合
- ✅ API 自動載入支援
- ✅ 測試腳本與文檔

---

## 💬 聯絡方式

如有問題或建議，請聯繫：
- **團隊:** Fraud Detection Team
- **專案:** fraud-detection-etl-api

---

**© 2025 Fraud Detection Team. All rights reserved.**

