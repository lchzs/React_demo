# coding: utf-8

# =====================================================
# 1. 运行模式设置
# =====================================================
RUN_MODE = "debug"  # "debug" or "evaluate"

# =====================================================
# 2. 调试模式配置
# =====================================================
DEBUG_CONFIG = {
    "question": "How many years older is Trump than Musk?",
    "k_value": 1,
    "show_history": True,
    "temperature": 0.1
}

# =====================================================
# 3. 评估模式配置
# =====================================================
EVALUATE_CONFIG = {
    "dataset_path": "./data/easy_eval_dataset.json",
    "k_values_to_test": [3, 5],
    "temperature": 0.3
}

# =====================================================
# 4. 模型加载配置
# =====================================================
MODEL_CONFIG = {
    "model_path": "Qwen/Qwen2.5-7B-Instruct",
    "hf_endpoint": "https://hf-mirror.com",
    "cuda_visible_devices": "0,1",
    "default_temperature": 0.1
}