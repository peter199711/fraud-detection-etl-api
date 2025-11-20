# Keras 3.0+ API 遷移說明

## 🔄 問題說明

如果你在運行 TensorFlow Notebook 時看到以下錯誤：

```
ValueError: Invalid filepath extension for saving. 
Please add either a `.keras` extension for the native Keras format...
```

這是因為 **Keras 3.0+** 改變了模型保存的 API。

---

## ✅ 已修正的變更

### 1. **模型保存格式**

#### ❌ 舊版 (已棄用)
```python
model.save('model.h5')  # HDF5 格式
```

#### ✅ 新版 (推薦)
```python
model.save('model.keras')  # Keras 原生格式
```

### 2. **SavedModel 格式**

#### ❌ 舊版 API
```python
model.save('saved_model_dir')  # 會報錯
```

#### ✅ 新版 API
```python
model.export('saved_model_dir')  # Keras 3.0+
# 或
tf.saved_model.save(model, 'saved_model_dir')  # 通用方法
```

---

## 📝 修改的檔案

### 1. `notebooks/tensorflow_model_training.ipynb`
**Cell 20（儲存模型）已更新:**

```python
# ✅ 使用 .keras 格式
model_path = os.path.join(model_dir, 'tensorflow_fraud_model.keras')
model.save(model_path)

# ✅ SavedModel 使用 export()
saved_model_dir = os.path.join(model_dir, 'tensorflow_fraud_model')
if hasattr(model, 'export'):
    model.export(saved_model_dir)  # Keras 3.0+
else:
    tf.saved_model.save(model, saved_model_dir)  # 備用
```

### 2. `src/models/tensorflow_model.py`
**MLflow 記錄邏輯已更新:**

```python
# 使用 mlflow.keras 而非 mlflow.tensorflow
mlflow.keras.log_model(model, "model")
```

### 3. `src/api/main.py`
**模型載入邏輯已更新:**

```python
# 支援 Keras 3.0+ 格式
import mlflow.keras
model = mlflow.keras.load_model(model_uri)
```

---

## 🚀 如何使用

### 選項 1: 重新執行 Notebook
直接執行更新後的 Notebook，所有問題已修正：

```bash
jupyter notebook notebooks/tensorflow_model_training.ipynb
```

### 選項 2: 手動修正現有代碼
如果你有自己的修改版本，只需要改這兩處：

```python
# 1. 改變保存格式
model.save('model.keras')  # 不要用 .h5

# 2. SavedModel 使用 export
model.export('saved_model_dir')  # 不要用 save()
```

---

## 🔍 兼容性說明

### Keras 版本檢測
```python
import keras
print(f"Keras 版本: {keras.__version__}")

# Keras 3.0+ 才有 export() 方法
if hasattr(model, 'export'):
    print("使用 Keras 3.0+ API")
else:
    print("使用舊版 API")
```

### 向後兼容
代碼已添加兼容性檢查，支援：
- ✅ Keras 3.0+ (推薦)
- ✅ Keras 2.x (備用)
- ✅ TensorFlow 2.15+ (任何版本)

---

## 📊 格式比較

| 格式 | 副檔名 | 支援版本 | 推薦度 | 用途 |
|------|--------|----------|--------|------|
| Keras 原生 | `.keras` | Keras 3.0+ | ⭐⭐⭐⭐⭐ | 推薦用於所有場景 |
| HDF5 | `.h5` | 所有版本 | ⭐⭐ | 舊專案，已棄用 |
| SavedModel | 目錄 | 所有版本 | ⭐⭐⭐⭐ | TF Serving, 生產部署 |

---

## ⚠️ 常見問題

### Q1: 我需要重新訓練模型嗎？
**A:** 不需要。只需要重新執行保存的 cell。

### Q2: 舊的 .h5 模型還能用嗎？
**A:** 可以，但建議轉換為 .keras 格式：
```python
# 載入舊模型
old_model = keras.models.load_model('old_model.h5')
# 保存為新格式
old_model.save('new_model.keras')
```

### Q3: MLflow 支援 .keras 格式嗎？
**A:** 完全支援。使用 `mlflow.keras.log_model()` 即可。

### Q4: 影響現有的 sklearn 模型嗎？
**A:** 不影響。這些修改只針對 TensorFlow/Keras 模型。

---

## 📚 參考資料

- [Keras 3.0 Release Notes](https://keras.io/keras_3/)
- [TensorFlow SavedModel Guide](https://www.tensorflow.org/guide/saved_model)
- [MLflow Keras Integration](https://mlflow.org/docs/latest/python_api/mlflow.keras.html)

---

## 🔄 更新日誌

### v1.1 (2025-11-20)
- ✅ 修正 Keras 3.0+ 兼容性問題
- ✅ 更新模型保存邏輯（.keras 格式）
- ✅ 更新 SavedModel 導出（使用 export()）
- ✅ 更新 MLflow 記錄（使用 mlflow.keras）
- ✅ 添加向後兼容性檢查

---

**修正完成！現在可以正常執行 Notebook 了。** 🎉

