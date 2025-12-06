# coding: utf-8
import os
import sys
import json
import re
from ReactAgent import LLM  # 导入 LLM 用于评测函数

# --- 核心组件：双向日志记录器 ---
class DualLogger:
    """
    劫持 sys.stdout，将所有 print 输出同时发送到终端和日志文件
    """
    def __init__(self, filepath):
        self.terminal = sys.stdout
        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        # 使用 line buffering (buffering=1) 确保日志实时写入
        self.log = open(filepath, "w", encoding="utf-8", buffering=1)

    def write(self, message):
        try:
            self.terminal.write(message)
            self.log.write(message)
        except Exception:
            pass

    def flush(self):
        self.terminal.flush()
        self.log.flush()
    
    def close(self):
        self.log.close()

# --- 文件与数据处理辅助函数 ---

def ensure_dataset_exists(filepath):
    """确保数据集文件存在，不存在则创建一个 dummy 文件"""
    if not os.path.exists(filepath):
        print(f"⚠️ Dataset {filepath} not found. Creating dummy.")
        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump([{"id":1, "question":"Test?", "gold_keywords":["Test"], "gold_answer":"Test"}], f)

def normalize_text(text):
    """文本标准化：转小写，去标点"""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text

def get_safe_name(path):
    """将路径转换为安全的文件名"""
    name = os.path.basename(path)
    if name.endswith('.json'):
        name = name[:-5]
    return name.replace("/", "_").replace("\\", "_")

# --- 评测相关辅助函数 ---

def evaluate_trace(trace_history, consensus, gold_answer, tools, question):
    """
    调用 LLM 对 Agent 的推理轨迹进行打分
    """
    prompt = f"""
You are an expert evaluator. Score 1-5 based on how well the agent used the available tools to answer the question. Your reason should be concise.
Question: {question}
Gold: {gold_answer}
Trace: {trace_history}
Answer: {consensus}
Format: Score: [N] Reason: [Text]
"""
    # 使用 LLM 模块调用
    try:
        res = LLM.local_llm_call(prompt, temperature=0.5)
        if 'Score:' in res:
            res = 'Score:' + res.split('Score:')[-1]
        return res.strip()
    except Exception as e:
        return f"Eval Error: {str(e)}"