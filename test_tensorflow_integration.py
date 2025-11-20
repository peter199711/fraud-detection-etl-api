"""
TensorFlow 模型整合測試腳本

測試 TensorFlow 模型是否能正確整合到現有的 ETL pipeline 中

作者: Fraud Detection Team
日期: 2025-11-20
"""

import sys
import os

# 添加專案路徑
sys.path.append('src')
sys.path.append('src/models')

def test_tensorflow_module_import():
    """測試 TensorFlow 模組導入"""
    print("=" * 60)
    print("測試 1: TensorFlow 模組導入")
    print("=" * 60)
    
    try:
        import tensorflow as tf
        print(f"✅ TensorFlow 版本: {tf.__version__}")
        print(f"✅ GPU 可用: {len(tf.config.list_physical_devices('GPU'))} 個")
        return True
    except Exception as e:
        print(f"❌ TensorFlow 導入失敗: {e}")
        return False


def test_model_module_import():
    """測試自訂模型模組導入"""
    print("\n" + "=" * 60)
    print("測試 2: 自訂模型模組導入")
    print("=" * 60)
    
    try:
        from models.tensorflow_model import (
            build_fraud_detection_model,
            train_tensorflow_model,
            create_class_weights
        )
        print("✅ 成功導入 tensorflow_model 模組")
        print("✅ 可用函式: build_fraud_detection_model, train_tensorflow_model, create_class_weights")
        return True
    except Exception as e:
        print(f"❌ 模組導入失敗: {e}")
        return False


def test_model_building():
    """測試模型建構"""
    print("\n" + "=" * 60)
    print("測試 3: 模型建構")
    print("=" * 60)
    
    try:
        from models.tensorflow_model import build_fraud_detection_model
        
        # 建構測試模型
        model = build_fraud_detection_model(input_dim=30, learning_rate=0.001)
        print(f"✅ 模型建構成功")
        print(f"✅ 模型名稱: {model.name}")
        print(f"✅ 參數數量: {model.count_params():,}")
        print(f"✅ 層數: {len(model.layers)}")
        
        return True
    except Exception as e:
        print(f"❌ 模型建構失敗: {e}")
        return False


def test_transform_data_integration():
    """測試 transform_data.py 整合"""
    print("\n" + "=" * 60)
    print("測試 4: ETL Pipeline 整合")
    print("=" * 60)
    
    try:
        # 嘗試導入 transform_data 模組
        from etl import transform_data
        
        # 檢查是否有 TensorFlow 導入
        if hasattr(transform_data, 'train_tensorflow_model'):
            print("✅ transform_data.py 已整合 TensorFlow 訓練函式")
        else:
            print("⚠️  transform_data.py 未直接暴露 TensorFlow 函式（使用動態導入）")
        
        print("✅ ETL Pipeline 模組載入成功")
        return True
    except Exception as e:
        print(f"❌ ETL Pipeline 整合測試失敗: {e}")
        return False


def test_api_integration():
    """測試 API 整合"""
    print("\n" + "=" * 60)
    print("測試 5: API 整合")
    print("=" * 60)
    
    try:
        # 檢查 API requirements
        with open('src/api/requirements.txt', 'r') as f:
            requirements = f.read()
        
        if 'tensorflow' in requirements:
            print("✅ requirements.txt 包含 tensorflow")
        else:
            print("❌ requirements.txt 缺少 tensorflow")
            return False
        
        # 嘗試導入 API 模組（不啟動服務器）
        from api import main
        
        # 檢查是否有 TensorFlow 導入
        import inspect
        source = inspect.getsource(main)
        
        if 'mlflow.tensorflow' in source:
            print("✅ API main.py 已整合 TensorFlow 模型載入")
        else:
            print("⚠️  API main.py 未明確導入 mlflow.tensorflow")
        
        print("✅ API 模組載入成功")
        return True
    except Exception as e:
        print(f"❌ API 整合測試失敗: {e}")
        return False


def test_model_prediction():
    """測試模型預測功能"""
    print("\n" + "=" * 60)
    print("測試 6: 模型預測功能")
    print("=" * 60)
    
    try:
        import numpy as np
        from models.tensorflow_model import build_fraud_detection_model
        
        # 建立模型
        model = build_fraud_detection_model(input_dim=30)
        
        # 創建測試數據
        test_data = np.random.randn(5, 30).astype(np.float32)
        
        # 進行預測
        predictions = model.predict(test_data, verbose=0)
        
        print(f"✅ 預測成功")
        print(f"✅ 輸入形狀: {test_data.shape}")
        print(f"✅ 輸出形狀: {predictions.shape}")
        print(f"✅ 預測範圍: [{predictions.min():.4f}, {predictions.max():.4f}]")
        
        return True
    except Exception as e:
        print(f"❌ 預測測試失敗: {e}")
        return False


def main():
    """執行所有測試"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "TensorFlow 整合測試套件" + " " * 24 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    tests = [
        test_tensorflow_module_import,
        test_model_module_import,
        test_model_building,
        test_transform_data_integration,
        test_api_integration,
        test_model_prediction
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"\n❌ 測試執行異常: {e}")
            results.append(False)
    
    # 總結
    print("\n" + "=" * 60)
    print("測試總結")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    
    print(f"通過: {passed}/{total}")
    print(f"失敗: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 所有測試通過！TensorFlow 整合成功！")
        return 0
    else:
        print("\n⚠️  部分測試失敗，請檢查錯誤訊息")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

