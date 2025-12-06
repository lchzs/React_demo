# coding: utf-8
import os
import torch
import traceback
from transformers import AutoModelForCausalLM, AutoTokenizer

# 全局变量
tokenizer = None
model = None
model_config_cache = {}

def init_model(config):
    """
    初始化模型和分词器
    :param config: 接收 config.py 模块对象或字典配置
    """
    global tokenizer, model, model_config_cache
    
    # 1. 解析配置
    if isinstance(config, dict):
        model_conf = config.get('MODEL_CONFIG', {})
    else:
        model_conf = getattr(config, 'MODEL_CONFIG', {})
    
    model_config_cache = model_conf

    # 2. 设置环境变量
    # 建议: CUDA_VISIBLE_DEVICES 最好在脚本最顶层设置，此处设置在某些环境下可能滞后
    os.environ['HF_ENDPOINT'] = model_conf.get('hf_endpoint', 'https://hf-mirror.com')
    os.environ["CUDA_VISIBLE_DEVICES"] = model_conf.get('cuda_visible_devices', "0")
    
    model_path = model_conf.get('model_path', "Qwen/Qwen2.5-7B-Instruct")
    print("已换源")
    print(f"⏳ 正在加载模型: {model_path}")

    try:
        # 3. 加载分词器
        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )

        # 4. 加载模型
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            device_map="auto",
            dtype="auto",
            trust_remote_code=True
        )
        print("✅ 模型加载完成!")

    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        traceback.print_exc()
        exit(1)

def local_llm_call(prompt, temperature=None, stop=None, **kwargs):
    """
    调用模型进行推理，适配 ReAct Agent
    :param prompt: 提示词
    :param temperature: 采样温度 (优先级: 函数入参 > 缓存配置 > 默认0.1)
    :param stop: 停止词列表 (例如 ['Observation:', '\n'])
    :param kwargs: 接收其他可能的参数 (如 max_tokens)，防止报错
    :return: 生成的文本
    """
    global tokenizer, model, model_config_cache
    
    if model is None or tokenizer is None:
        raise RuntimeError("Model not initialized. Call init_model() first.")

    # --- 1. 确定温度参数 ---
    if temperature is None:
        temperature = model_config_cache.get("default_temperature", 0.1)
    
    # 确保 temperature 是浮点数
    temperature = float(temperature)

    # --- 2. 构造生成参数 ---
    # 允许通过 kwargs 覆盖 max_new_tokens
    max_new_tokens = kwargs.get("max_tokens", kwargs.get("max_new_tokens", 512))

    try:
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        generate_kwargs = {
            "max_new_tokens": max_new_tokens,
            "pad_token_id": tokenizer.eos_token_id
        }

        # 采样逻辑
        if temperature > 1e-5:
            generate_kwargs["temperature"] = temperature
            generate_kwargs["top_p"] = kwargs.get("top_p", 0.9)
            generate_kwargs["do_sample"] = True
        else:
            generate_kwargs["do_sample"] = False

        # --- 3. 执行推理 ---
        with torch.no_grad():
            outputs = model.generate(**inputs, **generate_kwargs)

        # --- 4. 解码输出 ---
        generated_ids = outputs[0][inputs.input_ids.shape[1]:]
        response = tokenizer.decode(generated_ids, skip_special_tokens=True)

        # --- 5. 后处理：截断 (ReAct 核心逻辑) ---
        
        # 5.1 处理传入的 stop 列表 (如果有)
        if stop and isinstance(stop, list):
            for s in stop:
                if s in response:
                    response = response.split(s)[0]
        
        # 5.2 硬编码兜底截断 (防止 Agent 没传 stop 但模型自己吐出了 Observation)
        if "Observation:" in response:
            response = response.split("Observation:")[0]
            
        # 5.3 优化 Final Answer 格式
        if "Final Answer:" in response:
            parts = response.split("Final Answer:")
            # 只取 Final Answer 后的一行，防止生成多余内容
            answer_part = parts[-1].split("\n")[0].strip()
            # 重新拼接，丢弃 Final Answer 之后可能产生的幻觉
            response = parts[0] + "Final Answer: " + answer_part

        return response.strip()

    except Exception as e:
        error_msg = f"Error: 本地推理失败 - {str(e)}"
        print(f"❌ {error_msg}")
        return error_msg