#!/usr/bin/env python
# coding: utf-8

import json
import time
import os
import sys
import traceback
import datetime
import argparse

# 1. 导入配置模块
import config

# 2. 导入 Agent 模块
from ReactAgent.tool import MY_TOOLS
from ReactAgent.Agent import ReActAgent
from ReactAgent import LLM

# 3. 导入工具函数 (从 utils.py)
from utils import (
    DualLogger, 
    ensure_dataset_exists, 
    normalize_text, 
    evaluate_trace
)

# --- 主程序逻辑 ---

def run_evaluation_loop(agent):
    """执行批量评估模式"""
    
    # 1. 获取配置
    eval_config = config.EVALUATE_CONFIG
    dataset_path = eval_config.get("dataset_path", "./data/easy_eval_dataset.json")
    k_values = eval_config.get("k_values_to_test", [1])
    temperature = eval_config.get("temperature", 0.1)
    model_path = config.MODEL_CONFIG.get("model_path", "unknown")

    # 确保数据存在
    ensure_dataset_exists(dataset_path)

    # 2. 提取名称用于文件名
    safe_model_name = model_path.replace("/", "_").replace("\\", "_")
    dataset_name = os.path.splitext(os.path.basename(dataset_path))[0]

    # 保存原始 stdout，以便后续恢复
    original_stdout = sys.stdout

    print("\n" + "="*60)
    print("🚀 MODE: BATCH EVALUATION")
    print(f"🧠 Model: {safe_model_name}")
    print(f"📂 Dataset: {dataset_name}")
    print("="*60)

    for k in k_values:
        # ==========================================
        # 3. 构造统一的文件名 (模型_数据集_T_K)
        # ==========================================
        base_filename = f"{safe_model_name}_{dataset_name}_T{temperature}_K{k}"
        
        log_filepath = os.path.join("./logs", f"{base_filename}.log")
        result_filepath = os.path.join("./results", f"{base_filename}.json")
        
        # 确保目录存在
        os.makedirs("./logs", exist_ok=True)
        os.makedirs("./results", exist_ok=True)

        # 开启日志记录 (使用 utils 中的 DualLogger)
        sys.stdout = DualLogger(log_filepath)

        try:
            print(f"\n--- Evaluation Run: K={k}, Temp={temperature} ---")
            print(f"📝 Log: {log_filepath}")
            print(f"💾 Res: {result_filepath}")
            
            with open(dataset_path, 'r', encoding='utf-8') as f:
                test_cases = json.load(f)

            passed = 0
            results = []
            total = len(test_cases)

            for i, case in enumerate(test_cases):
                q = case["question"]
                print(f"\n[{i+1}/{total}] Q: {q}")

                try:
                    t0 = time.time()
                    # 运行 Agent
                    output = agent.run(q, k=k, temperature=temperature)
                    duration = round(time.time() - t0, 2)

                    # 简单匹配准确率 (使用 utils 中的 normalize_text)
                    is_correct = False
                    norm_out = normalize_text(output)
                    for kw in case["gold_keywords"]:
                        if normalize_text(kw) in norm_out:
                            is_correct = True
                            break
                    
                    status = "✅ PASS" if is_correct else "❌ FAIL"
                    if is_correct: passed += 1
                    
                    print(f"   -> Out: {output}")
                    print(f"   -> Sta: {status} ({duration}s)")
                    
                    # LLM 评分 (使用 utils 中的 evaluate_trace)
                    eval_res = evaluate_trace(agent.trace_history, output, case["gold_answer"], agent.tools, q)

                    results.append({
                        "id": case["id"],
                        "k": k,
                        "temperature": temperature,
                        "question": q,
                        "actual": output,
                        "status": status,
                        "eval_report": eval_res,
                        "trace": agent.trace_history
                    })

                except Exception as e:
                    print(f"   -> Error: {e}")
                    traceback.print_exc()

            acc = (passed / total) * 100
            print(f"\n📈 Result for K={k}: {acc:.2f}% ({passed}/{total})")
            
            # 保存 JSON 结果
            with open(result_filepath, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"Json saved to {result_filepath}")

        except Exception as e:
            print(f"❌ Critical Error: {e}")
            traceback.print_exc()
        
        finally:
            # 关闭日志，切回终端
            if isinstance(sys.stdout, DualLogger):
                sys.stdout.close()
                sys.stdout = original_stdout

    print("\n🎉 All Done.")

def run_debug_mode(agent):
    """执行调试模式"""
    # 调试模式简单处理，也生成个日志
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = f"./logs/debug_{timestamp}.log"
    # 确保目录存在
    os.makedirs("./logs", exist_ok=True)
    
    # 开启日志
    sys.stdout = DualLogger(log_path)
    
    try:
        conf = config.DEBUG_CONFIG
        q = conf.get("question", "Test?")
        k = conf.get("k_value", 1)
        temp = conf.get("temperature", 0.1)
        
        print(f"🛠️ DEBUG MODE")
        print(f"Question: {q}")
        print(f"Params: K={k}, Temp={temp}")
        
        res = agent.run(q, k=k, temperature=temp)
        print(f"\n🏆 Final Result: {res}")
        
    finally:
        sys.stdout.close()
        sys.stdout = sys.__stdout__

if __name__ == "__main__":
    # ================= 命令行参数解析 =================
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_mode", type=str, choices=["debug", "evaluate"])
    parser.add_argument("--dataset_path", type=str)
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--k_value", type=int)
    parser.add_argument("--model_path", type=str)
    
    args = parser.parse_args()

    # 1. 覆盖 Config
    if args.run_mode: config.RUN_MODE = args.run_mode
    if args.model_path: config.MODEL_CONFIG["model_path"] = args.model_path

    if config.RUN_MODE == "evaluate":
        if args.dataset_path: config.EVALUATE_CONFIG["dataset_path"] = args.dataset_path
        if args.temperature is not None: config.EVALUATE_CONFIG["temperature"] = args.temperature
        if args.k_value is not None: config.EVALUATE_CONFIG["k_values_to_test"] = [args.k_value]

    # 2. 初始化模型 (调用 LLM 模块)
    LLM.init_model(config)

    # 3. 初始化 Agent (将 LLM.local_llm_call 传进去)
    agent = ReActAgent(llm_func=LLM.local_llm_call, tools=MY_TOOLS, max_steps=10)

    # 4. 运行
    if config.RUN_MODE == "evaluate":
        run_evaluation_loop(agent)
    else:
        run_debug_mode(agent)