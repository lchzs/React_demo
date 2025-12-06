# coding: utf-8
import json
import wikipedia
import threading
import random
import math
import re
from ddgs import DDGS

# --- 数学工具定义 ---

MATH_FUNCTIONS = {
    'sqrt': math.sqrt,
    'pow': math.pow,   
    'log': math.log,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'pi': math.pi,     
    'e': math.e,       
}

def calculator_tool(expression):
    """
    现在支持 sqrt(), pow(), log() 等高级数学函数。
    """
    try:
        # 1. 清理输入 (处理逗号和空格)
        clean_expression = expression.replace(",", "").replace(" ", "")

        # 2. 安全执行计算
        result = eval(
            clean_expression,
            {"__builtins__": None},
            MATH_FUNCTIONS
        )

        # 检查是否是整数或是否需要浮点数精度
        if result == int(result):
             return "Observation: " + str(int(result))
        else:
             return "Observation: " + str(result)

    except NameError:
        return "Observation: Error, function not supported (e.g., maybe you tried to use 'sqr' instead of 'sqrt')."
    except SyntaxError:
        return "Observation: Error, invalid calculation formula. Check operators or parenthesis."
    except Exception as e:
        return f"Observation: Calculation Error: {str(e)}"


# --- Wikipedia 搜索工具 ---

class TimeoutException(Exception):
    pass

def _search_worker(query, result_container):
    """
    执行搜索任务的“工人”。
    """
    try:
        search_results = wikipedia.search(query)

        if not search_results:
            result_container['result'] = "Observation: No relevant results were found. Please try simpler keywords (e.g., search only for entity names)."
            return

        suggested_pages = search_results[:3]
        
        summaries = []
        for page in suggested_pages:
            summaries.append(wikipedia.summary(page, sentences=1, auto_suggest=False))
        
        observation = "Observation: "
        for i in range(len(suggested_pages)):
            observation += f"[Page: {suggested_pages[i]}] {summaries[i]} "
        
        result_container['result'] = observation.strip()

    except Exception as e:
        result_container['exception'] = e

def wikipedia_search_tool(query: str, timeout_seconds: int = 5):
    """
    增强版 Wikipedia 搜索工具，带有超时功能。
    """
    query = query.strip().strip('"').strip("'")
    result_container = {} 
    
    worker_thread = threading.Thread(
        target=_search_worker, 
        args=(query, result_container)
    )
    worker_thread.daemon = True
    worker_thread.start()

    worker_thread.join(timeout=timeout_seconds)

    if worker_thread.is_alive():
        return f"Observation: Search timed out after {timeout_seconds} seconds."

    if 'exception' in result_container:
        e = result_container['exception']
        if isinstance(e, wikipedia.exceptions.DisambiguationError):
            options = ", ".join(e.options[:3])
            return f"Observation: The search term is ambiguous and may refer to: {options}. Please try again depending on the context."
        elif isinstance(e, wikipedia.exceptions.PageError):
            return f"Observation: Unable to load page '{query}', please try other keywords."
        else:
            return f"Observation: Search tool error: {str(e)}"

    return result_container.get('result', "Observation: An unknown error occurred in the search worker.")


# --- Web 搜索工具 ---

def web_search_tool(query, max_results=3):
    """
    通用网页搜索工具 (基于 DuckDuckGo)
    """
    print(f"🔍 Searching: {query} ...")

    try:
        results = []
        # 使用 DDGS 上下文管理器
        with DDGS() as ddgs:
            search_gen = ddgs.text(query, max_results=max_results)
            for r in search_gen:
                results.append(r)

        if not results:
            return "Observation: No relevant web page results found. Please try changing your keywords."

        return f"Observation: The search results are as follows:\n{json.dumps(results)}"

    except Exception as e:
        return f"Observation: Search Error: {str(e)}"


# --- 酒店搜索工具 ---

def hotel_search_tool(city_name):
    """
    模拟的酒店查询 API。
    """
    city = city_name.replace("Action Input:", "").strip()

    mock_db = {
        "Paris": [
            {"name": "Hotel Eiffel View", "price": 150, "currency": "USD", "rating": 4.5},
            {"name": "Le Grand Paris", "price": 320, "currency": "USD", "rating": 5.0},
            {"name": "Budget Inn Paris", "price": 85, "currency": "USD", "rating": 3.2}
        ],
        "Tokyo": [
            {"name": "Shinjuku Prince Hotel", "price": 120, "currency": "USD", "rating": 4.3},
            {"name": "Tokyo Station Hotel", "price": 400, "currency": "USD", "rating": 4.9}
        ],
        "New York": [
            {"name": "Times Square Suites", "price": 250, "currency": "USD", "rating": 4.1}
        ]
    }

    found_city = None
    for k in mock_db.keys():
        if k.lower() in city.lower():
            found_city = k
            break

    if found_city:
        hotels = mock_db[found_city]
        return f"Observation: Found hotels in {found_city}: {json.dumps(hotels)}"
    else:
        return f"Observation: Found standard hotels in {city}: " + json.dumps([
            {"name": f"{city} City Center Hotel", "price": random.randint(100, 200), "currency": "USD"},
            {"name": f"{city} Grand Hotel", "price": random.randint(250, 400), "currency": "USD"}
        ])


# --- 数字比较工具 ---

def compare_numbers_tool(input_str):
    """
    比较多个数字的大小，返回最大值和最小值。
    """
    try:
        clean_input = input_str.replace("$", "").strip()
        list_separators = r',\s+|\s+'
        parts_with_commas = re.split(list_separators, clean_input)

        numbers = []
        for p in parts_with_commas:
            if not p: continue 

            clean_part = p.replace(',', '')
            if clean_part.count('.') > 1:
                 raise ValueError("Too many decimal points in a number.")

            numbers.append(float(clean_part))

        if len(numbers) < 2:
            return "Observation: Error: Please provide at least two numbers for comparison."

        largest = max(numbers)
        smallest = min(numbers)

        return f"Observation: The largest number is {largest} and the smallest number is {smallest}."

    except ValueError:
        return "Observation: Error: Invalid number format. Please check for misplaced commas or non-numeric characters."
    except Exception as e:
        return f"Observation: Comparison Error: {str(e)}"

# 导出工具字典
MY_TOOLS = {
    "wikipedia_search": web_search_tool,
    "web_search": web_search_tool,
    "hotel_search": hotel_search_tool,
    "calculator": calculator_tool,
    "compare_numbers": compare_numbers_tool
}