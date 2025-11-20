# TensorFlow 模型快速入門指南

## ✅ 整合完成清單

- ✅ **新增模型模組:** `src/models/tensorflow_model.py`
- ✅ **實驗 Notebook:** `notebooks/tensorflow_model_training.ipynb`
- ✅ **更新依賴:** `src/api/requirements.txt` (+tensorflow)
- ✅ **整合 ETL:** `src/etl/transform_data.py` (支援 TensorFlow 訓練)
- ✅ **整合 API:** `src/api/main.py` (支援 TensorFlow 載入)
- ✅ **測試腳本:** `test_tensorflow_integration.py`
- ✅ **完整文檔:** `TENSORFLOW_INTEGRATION.md`
- ✅ **Keras 3.0+ 兼容:** 已更新為新版 API (`.keras` 格式)

---

## 🚀 快速開始（3 步驟）

### 步驟 1: 安裝 TensorFlow

```bash
# Windows (PowerShell) - API 環境
.\venv_api\Scripts\Activate.ps1
pip install tensorflow>=2.15.0

# 如果也使用 Airflow
.\venv_airflow_wsl\Scripts\Activate.ps1
pip install tensorflow>=2.15.0
```

### 步驟 2: 執行測試驗證整合

```bash
python test_tensorflow_integration.py
```

**預期結果:** 所有 6 項測試通過 ✅

### 步驟 3: 訓練模型（選擇其一）

#### 選項 A: 使用 Notebook（推薦用於實驗）
```bash
jupyter notebook notebooks/tensorflow_model_training.ipynb
```

#### 選項 B: 使用 ETL Pipeline（推薦用於生產）
```bash
# 確保 PostgreSQL 和 MLflow 正在運行
python -m src.etl.transform_data
```

#### 選項 C: 使用 Airflow DAG（自動化）
啟動 Airflow，執行 `fraud_detection_pipeline` DAG

---

## 📊 查看訓練結果

### 在 MLflow UI 查看
```bash
# 訪問 http://localhost:5000
# 查看實驗: "Fraud Detection Baseline"
# 比較 TensorFlow 與其他模型的性能
```

### 關鍵指標
- **AUC:** 模型區分能力
- **F1 Score:** 精確率與召回率的平衡
- **Recall:** 詐欺偵測率（最重要）
- **Precision:** 誤報率

---

## 🔧 如何調整模型

### 修改架構
編輯 `src/models/tensorflow_model.py` 的 `build_fraud_detection_model()` 函式

### 修改超參數
編輯 `src/etl/transform_data.py` 的模型配置：
```python
{
    "name": "04_TensorFlow_DNN",
    "params": {
        'epochs': 50,              # 調整這裡
        'batch_size': 256,          # 調整這裡
        'learning_rate': 0.001,     # 調整這裡
        'early_stopping_patience': 10
    },
    ...
}
```

### 📌 重要提示：Keras 3.0+ API
如果遇到模型保存錯誤，請查看 `KERAS_3_MIGRATION_NOTES.md`：
- ✅ 使用 `.keras` 格式（不要用 `.h5`）
- ✅ SavedModel 使用 `model.export()`（不要用 `model.save()`）

---

## 🎯 常見問題

### Q: TensorFlow 模型會自動被 API 使用嗎？
**A:** 是的！如果 TensorFlow 模型的 F1 Score 最高，API 會自動載入它。

### Q: 可以同時保留所有模型嗎？
**A:** 可以，所有模型都會記錄到 MLflow，你可以隨時切換。

### Q: 訓練需要多久？
**A:** 
- Notebook: ~5-10 分鐘（取決於 CPU/GPU）
- ETL Pipeline: ~15-20 分鐘（訓練所有模型）

### Q: 如何使用 GPU 加速？
**A:** 
```bash
pip install tensorflow[and-cuda]>=2.15.0
python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
```

---

## 📁 專案結構（更新後）

```
fraud-detection-etl-api/
├── src/
│   ├── models/
│   │   ├── baseline_model.pkl
│   │   ├── scaler.pkl
│   │   └── tensorflow_model.py          ✨ 新增
│   ├── api/
│   │   ├── main.py                      🔧 已更新
│   │   └── requirements.txt             🔧 已更新 (+tensorflow)
│   └── etl/
│       └── transform_data.py            🔧 已更新
├── notebooks/
│   └── tensorflow_model_training.ipynb  ✨ 新增
├── test_tensorflow_integration.py       ✨ 新增
├── TENSORFLOW_INTEGRATION.md            ✨ 新增（完整文檔）
└── TENSORFLOW_QUICK_START.md            ✨ 新增（本文件）
```

---

## 🎓 下一步建議

1. **執行測試:** 確保整合正常
   ```bash
   python test_tensorflow_integration.py
   ```

2. **訓練模型:** 使用 Notebook 進行首次訓練
   ```bash
   jupyter notebook notebooks/tensorflow_model_training.ipynb
   ```

3. **比較性能:** 在 MLflow UI 比較所有模型

4. **調整優化:** 根據結果調整超參數

5. **生產部署:** 將最佳模型整合到 API

---

## 📚 詳細資訊

請參閱 `TENSORFLOW_INTEGRATION.md` 獲取：
- 完整的架構說明
- 詳細的使用方式
- 故障排除指南
- 性能比較分析
- 未來改進方向

---

**祝訓練順利！🚀**

如有問題，請參考完整文檔或測試腳本的錯誤訊息。

