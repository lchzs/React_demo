#!/bin/bash

# =================配置区域=================

# 1. 定义要测试的温度列表
TEMPERATURES=(0.5)

# 2. 定义要测试的 K 值列表
K_VALUES=(1 3)

# 3. 定义要测试的数据集列表
DATASETS=(
    #"./data/easy_eval_dataset.json"
    #"./data/hard_eval_dataset.json"
    "./data/median_eval_dataset.json"
)

# 4. 模型路径
MODEL_PATH="Qwen/Qwen2.5-7B-Instruct"

# =================主循环=================

echo "========================================"
echo "开始批量评测任务"
echo "Model: $MODEL_PATH"
echo "时间: $(date)"
echo "========================================"

for dataset in "${DATASETS[@]}"; do
    
    for temp in "${TEMPERATURES[@]}"; do
        
        for k in "${K_VALUES[@]}"; do
            
            echo ""
            echo ">>> 启动任务: Data=$(basename "$dataset") | Temp=$temp | K=$k"
            
            # 直接运行 Python
            # 注意：不再需要 | tee，因为 Python 内部 DualLogger 已经处理了文件写入
            python main.py \
                --run_mode evaluate \
                --dataset_path "$dataset" \
                --temperature "$temp" \
                --k_value "$k" \
                --model_path "$MODEL_PATH"
            
            # 检查 Python 是否报错退出
            if [ $? -eq 0 ]; then
                echo "✅ 任务完成"
            else
                echo "❌ 任务出错"
            fi
            
        done
    done
done

echo "========================================"
echo "所有评测任务已结束"
echo "========================================"