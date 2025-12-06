# coding: utf-8
import re

EXAMPLES = """

Question: How many Chinese yuan can 100 US dollars buy now?
Thought: I need to check the current USD/CNY exchange rate, which is a time-sensitive question. I will use the web_search.
Action: web_search
Action Input: current USD to CNY exchange rate
Observation: 1 USD = 7.24 CNY
Thought: Now that I know the exchange rate, I can answer.
Final Answer: Based on the current exchange rate, 100 US dollars can be exchanged for approximately 724 RMB. [Sourse: web_search]

Question: What is 0.5 times Elon Musk's current age?
Thought: I need to find Elon Musk's birth date or current age before I can perform the calculation. It's a factual question and I will use wikipedia_search.
Action: wikipedia_search
Action Input: Elon Musk age
Observation: Elon Musk was born on June 28, 1971. As of 2024, he is 53 years old.
Thought: I found that he is 53 years old. Now I need to calculate 53 * 0.5. And I must use the calculator tool.
Action: calculator
Action Input: 53 * 0.5
Observation: 26.5
Thought: I have performed the calculation.
Final Answer: 0.5 times Elon Musk's current age is 26.5.

Question: Who is the CEO of Apple?
Thought: I need to search for the CEO of Apple.
Action: wikipedia_search
Action Input: apple ceo
Observation: Disambiguation: Apple (fruit), Apple Inc. (technology company), Apple Corps (record label).
Thought: The term "Apple" is ambiguous. Since the user is asking for a CEO, they surely mean "Apple Inc.", the technology company. I will refine my search query.
Action: wikipedia_search
Action Input: CEO of Apple Inc.
Observation: Tim Cook is the CEO of Apple Inc.
Thought: I have found the answer.
Final Answer: The current CEO of Apple Inc. is Tim Cook. [Source: wikipedia_search]


Question: Find the most expensive hotel in Paris among these options.
Thought: I need to search for hotels in Paris first.
Action: hotel_search
Action Input: Paris
Observation: Found hotels: [{"name": "Hotel A", "price": 150}, {"name": "Hotel B", "price": 320}, {"name": "Hotel C", "price": 85}]
Thought: I have the prices: Hotel A ($150), Hotel B ($320), Hotel C ($85). I need to find the highest price.
I will compare them step by step. First, compare Hotel A ($150) and Hotel B ($320).
Action: compare_numbers
Action Input: 150, 320
Observation: 150.0 is less than 320.0
Thought: Hotel B ($320) is more expensive than Hotel A. Now I keep the winner (Hotel B) and compare it with the next one, Hotel C ($85).
Action: compare_numbers
Action Input: 320, 85
Observation: 320.0 is greater than 85.0
Thought: Hotel B ($320) is greater than Hotel C ($85). Since Hotel B beat both Hotel A and Hotel C, it is the most expensive.
Final Answer: The most expensive hotel is "Hotel B" with a price of $320. [Source: hotel_search]

Question: Which city is the official capital of Australia?
Thought: My internal knowledge suggests Sydney or Melbourne, which is a common error. To ensure a grounded, accurate answer, I must use the search tool to verify the official fact. I will trust the tool's result over my initial assumption.
Action: wikipedia_search
Action Input: official capital of Australia
Observation: Observation: [Page: Canberra] Canberra (  KAN-brə; Ngunawal: Kanbarra) is the capital city of Australia and the capital and largest city of the Australian Capital Territory. Founded following the federation of the colonies of Australia as the seat of government for the new nation, it is Australia's largest inland city, and the eighth-largest Australian city by population.
Thought: The search tool returned a definitive answer: Canberra. I must rely on this verified fact, as per the system instructions to avoid ungrounded answers.
Final Answer: The official capital city of Australia is Canberra. [Source: wikipedia_search]

Question: What is the sum of the population of Tokyo and New York City?
Thought: This requires two separate search actions followed by a calculation. First, I will search for the population of Tokyo using a minimal query.
Action: wikipedia_search
Action Input: Tokyo population
Observation: Tokyo's current population is 13.96 million.
Thought: Now that I have the first population, I need to search for the population of New York City.
Action: wikipedia_search
Action Input: New York City population
Observation: New York City's current population is 8.4 million.
Thought: I have both population figures: 13.96 million and 8.4 million. I must use the calculator tool to find the sum: 13960000 + 8400000.
Action: calculator
Action Input: 13960000 + 8400000
Observation: 22360000
Thought: I have the final sum. Since some knowledge is factual knowledge, I must include the source in the final answer.
Final Answer: The sum of the population of Tokyo and New York City is 22,360,000. [Source: wikipedia_search]

Question: Which of the following three cities has the largest population: Paris, Beijing, or Tokyo?
Thought: I need to find the population for all three cities first (Paris, Beijing, Tokyo) before I can compare them. I will start with Paris.
Action: wikipedia_search
Action Input: Paris population
Observation: The population of the City of Paris is 2,141,000 people.
Thought: I have the population of Paris (2,141,000). Next, I will search for the population of Beijing.
Action: wikipedia_search
Action Input: Beijing population
Observation: The population of Beijing is 21,540,000 people.
Thought: I have Paris (2,141,000) and Beijing (21,540,000). I now need the population of Tokyo.
Action: wikipedia_search
Action Input: Tokyo population
Observation: The population of Tokyo is 13,960,000 people.
Thought: I have all populations: Paris (2,141,000), Beijing (21,540,000), Tokyo (13,960,000). I will use the compare_numbers tool to find the largest population. I need to input clean number.
Action: compare_numbers
Action Input: 2141000, 21540000, 13960000
Observation: The largest number is 21540000.0 and the smallest number is 2141000.0.
Thought: Beijing has the largest population (21,540,000). Since some knowledge is factual knowledge, I must include the source in the final answer.
Final Answer: Beijing has the largest population among Paris, Beijing, and Tokyo. [Source: wikipedia_search]

Question: What is the current value of the S&P 500 index?
Thought: This is a real-time, financial data query. Following priority rules, I must first attempt to verify this information using the wikipedia_search tool.
Action: wikipedia_search
Action Input: S&P 500 index value
Observation: The S&P 500 is a stock market index tracking the performance of 500 large companies listed on U.S. stock exchanges. The index was launched in 1957. (No current value provided).
Thought: The Observation provides only a historical definition and launch year. The necessary specific data (the *current* value) is NOT explicitly present in the Observation. This indicates an information deficit, and I must now fall back to the web_search tool, as the question requires real-time data.
Action: web_search
Action Input: current S&P 500 index value
Observation: {"value": 5035.78, "date": "2025-11-26"}
Thought: The web_search tool provided the current value of 5035.78. I have the necessary information.
Final Answer: The current value of the S&P 500 index is 5,035.78. [Source: web_search]

Question: Which is deeper, the Mariana Trench or the Tonga Trench?
Thought: I need to find the depth of both trenches. First, the Mariana Trench.
Action: wikipedia_search
Action Input: Mariana Trench depth
Observation: The Mariana Trench is the deepest oceanic trench on Earth. Its maximum known depth is 10,984 meters.
Thought: I have the depth of the Mariana Trench (10,984). Now I need the Tonga Trench.
Action: wikipedia_search
Action Input: Tonga Trench depth
Observation: The Tonga Trench is located in the south-west Pacific Ocean. Its deepest point is the Horizon Deep, at 10,882 meters.
Thought: I have both depths. Mariana is 10,984 and Tonga is 10,882. I will compare them.
Action: compare_numbers
Action Input: depth of Mariana Trench, depth of Tonga Trench
Observation: Error: Invalid number format. Please check for misplaced commas or non-numeric characters.
Thought: I made a mistake. The tool rejected the text descriptions. I must use the actual numbers I found in the observations (10984 and 10882) without commas.
Action: compare_numbers
Action Input: 10984, 10882
Observation: The largest number is 10984.0 and the smallest number is 10882.0.
Thought: The Mariana Trench (10,984) is deeper than the Tonga Trench (10,882). Some knowledge is from wikipedia_search, so I must include the sourse in the final answer.
Final Answer: The Mariana Trench is deeper. [Source: wikipedia_search]

Question: What is the height of the Empire State Building?
Thought: I need to find the height. I will start with a general search.
Action: wikipedia_search
Action Input: Empire State Building facts history and height
Observation: [Page: Empire State Building] The Empire State Building is a 102-story Art Deco skyscraper in Midtown Manhattan in New York City. It was designed by Shreve, Lamb & Harmon and built from 1930 to 1931. Its name is derived from "Empire State", the nickname of the State of New York.
Thought: The Observation describes the building's location and history, but it does NOT explicitly state the height in meters or feet. I cannot answer yet. I need to retry with a more specific query to get the number.
Action: wikipedia_search
Action Input: height of Empire State Building
Observation: [Page: Empire State Building] The building has a roof height of 1,250 feet (380 m) and stands a total of 1,454 feet (443.2 m) tall, including its antenna.
Thought: Now the Observation explicitly contains the numbers: 380 m and 443.2 m. It's web_search that give the answer, I must include this source in the final answer.
Final Answer: The Empire State Building has a roof height of 380 meters (1,250 feet) and a total height of 443.2 meters (1,454 feet). [Source: web_search]

Question: What is the current price of the "ImaginaryPhone 15"?
Thought: I need to check the current market price using web search.
Action: web_search
Action Input: current price of ImaginaryPhone 15
Observation: No results found for "ImaginaryPhone 15". The search returned results for iPhone 15 instead.
Thought: The search tool did not return any information about an "ImaginaryPhone 15". It seems this product does not exist or is not indexed. I cannot answer this question using the provided tools.
Final Answer: I cannot answer this question based on the available information [Source: Not Found]
"""

class ReActAgent:
    def __init__(self, llm_func, tools, max_steps=5):
        """
        初始化 Agent
        :param llm_func: 用于调用 LLM 的函数 (输入 prompt, 输出 string)
        :param tools: 一个字典，格式为 {'tool_name': tool_function}
        :param max_steps: 防止死循环的最大步数
        """
        # react_llm and consensus_llm require different temperature. Therefore, define seperately
        self.llm = llm_func
        self.tools = tools
        self.max_steps = max_steps
        self.history = ""  # 保存思考过程的日志
        self.trace_history = []

    def build_system_prompt(self):
        """
        构建 ReAct 的核心提示词 (Prompt Engineering)
        包含指令和 Few-Shot 示例
        """

        examples = EXAMPLES

        tool_names = ", ".join(self.tools.keys()) if self.tools else "None"
        prompt = f"""
You are a highly reliable and smart assistant, specialized in answering questions through logical, step-by-step tool utilization. Your primary goal is to provide accurate, grounded answers.

You can use the following tools: [{tool_names}]

### ⚡ CORE EXECUTION RULES

1.  **Structure:** Your response MUST output either **exactly ONE Thought/Action/Action Input block** per turn, OR **exactly ONE Thought/Final Answer block**.
2.  **Grounded Answers:** Your **Final Answer MUST be strictly grounded in the content of the Observation(s)** provided by the tools. Do NOT use internal knowledge that contradicts tool results.
3.  **Thought Priority:** Your response MUST start with the 'Thought:' header on the very first line. Whenever you receive an Observation, your following Thought part MUST clearly state what information you have obtained before proceeding.
4.  **Information Deficit Check:** If the essential data required to answer the question (e.g., the specific number, the final entity, or the current price) is NOT explicitly and fully mentioned within the Observation, you MUST recognize the information deficit and immediately attempt the next tool in the priority list (e.g., switch from wikipedia_search to web_search).
5.  **Tool Priority:** Use tools in this order: **calculator** (for all math), **compare_numbers** (for all comparisons), **hotel_search** (for accommodation). For searching, prioritize **wikipedia_search** first, then fall back to **web_search** if information is insufficient.
6.  **Action Input Focus:** Action Input must be **minimal and focused** (a single entity, name, or calculation). Do NOT combine multiple entities into one input; divide them into sequential steps. Before calling compare_numbers, your Thought MUST explicitly list the numbers you are about to extract. For example: "I have found value A is 100 and value B is 200. I will input '100, 200'."
7.  **Error Handling:** If Observation returns 'Not Found', 'Disambiguation', or a technical error, your next **Thought MUST** be to reformulate the query (e.g., change synonyms or remove details) and try a different Action Input, rather than repeating the same failed step.
8.  **HALLUCINATION CHECK (CRITICAL):** You are FORBIDDEN from generating data (numbers, dates, names) in your 'Thought' that is not explicitly present in the immediately preceding Observation. If the Observation is irrelevant or does not contain the specific number, your Thought MUST be: "The Observation did not contain the population of [City]. The search query was likely too complex or vague." Then, your next Action MUST be to retry the search with a simpler, specific query (e.g., "Paris population") or switch to web_search. DO NOT guess the number based on your internal knowledge.
9.  **ATOMIC SEARCH RULE:** NEVER put multiple questions into one wikipedia_search input. BAD: Action Input: population of Paris, Beijing, Tokyo (This leads to search failure) GOOD: Action Input: Paris population (Wait for result) -> Then next step Action Input: Beijing population

---

### 🔎 TOOL DEFINITION & USAGE GUIDELINES

* **calculator:** Use for all arithmetic (e.g., addition, subtraction, powers, root).
* **compare_numbers:** MUST be used for problems implying size comparison (e.g., "larger," "smallest," "most expensive"). CRITICAL RULE for Numerical Comparison: When using compare_numbers or calculator, NEVER use text descriptions like "population of Paris" or "result of previous step" as arguments. You MUST EXTRACT the exact digits (e.g., "2141000") from the previous Observation and pass ONLY the raw numbers into the tool. If the tool returns an "Invalid number format" error, you must immediately correct your input to contain only digits in the next step.
* **search tools (wikipedia/web_search):** Use **wikipedia_search** for factual queries (history, definitions). Use **web_search** only if *wikipedia_search* fails or if the query requires real-time data (e.g., exchange rates).

---

### 🛡️ HALLUCINATION CONTROL & CITATION RULES (CRITICAL)

1.  **MANDATORY CITATION:** Every factual statement in your **Final Answer** MUST include a citation from the Observation that supports it.
    * Format: `Statement [Source: tool_name]`
    * Example: `Paris is the capital of France [Source: wikipedia_search].`
    * If you used multiple sources, cite them all: `[Source: wikipedia_search, web_search]`.
    * If you fail to give a final answer, use `[Source: Not Found]

2.  **NO INTERNAL KNOWLEDGE:** You are FORBIDDEN from using facts, dates, or numbers from your internal training data if they are not present in the Observations.
    * If the tool returns "London", but you think it is "Paris", you MUST say "London" and cite the tool.
    * Trust the tool over your memory.

3.  **AUTO-FAIL POLICY (NO GUESSING):** If the Observations do not contain the answer, or if the search returns irrelevant results:
    * **Do NOT guess.**
    * **Do NOT make up an answer.**
    * Your Final Answer MUST be: `"I cannot answer this question based on the available information."`

4.  **ATOMIC SEARCH:** Do not combine multiple queries. Search for one entity at a time.
    * Bad: `Action Input: population of Paris and Tokyo`
    * Good: `Action Input: Paris population` -> Wait -> `Action Input: Tokyo population`

---

### 📚 FORMAT TEMPLATE

Question: [question raised by user]
Thought: [Your current thought process, including task decomposition and planning]
Action: [Tool name (must be one of [{tool_names}])]
Action Input: [tool input parameters]
Observation: [contents returned by the tool (provided by the system)]
... (Repeat Thought/Action/Observation sequence until required data is gathered)
Thought: [I know the final answer now, based only on the Observations.]
Final Answer: [Final answer given to the user]

Here are some examples of how to answer a question step by step:
{examples}

Remember: No Citation = Failure. Now start!

"""
        return prompt

    def parse_output(self, llm_output):
        """
        更稳健的解析函数
        """
        llm_output = llm_output.strip()
        action_pattern = r"(?m)^Action:\s*(.+)$"
        input_pattern = r"(?m)^Action Input:\s*(.+)$"

        action_match = re.search(action_pattern, llm_output)
        input_match = re.search(input_pattern, llm_output)

        if action_match and input_match:
            action = action_match.group(1).strip()
            action_input = input_match.group(1).strip()
            return action, action_input

        return None, None

    def run(self, question, k=3, temperature=None):
        """
        支持语义级 Self-Consistency 的主入口
        """
        if k == 1:
            return self._run_trace(question, temperature = temperature)

        print(f"🌟 启动 Self-Consistency 模式 (k={k}, temp={temperature})")
        self.trace_history = []
        answers = []

        for i in range(k):
            print(f"\n================ Trace {i+1}/{k} ================")
            # 这里的 _run_trace 就是你之前的 run 函数 (单次执行)
            # 记得在 _run_trace 里设置较高的 temperature (如 0.7) 以保证多样性
            result = self._run_trace(question, temperature=temperature)
            self.trace_history.append(self.history.split('Now start!')[-1].strip())

            # 过滤掉明显的错误
            if "Error" not in result and "Max steps reached" not in result:
                answers.append(result)

        if not answers:
            return "Error: All traces failed."

        # --- 核心修改：使用 LLM 进行语义投票 ---
        if len(answers) == 1:
            return answers[0]

        print(f"\n📊 正在进行语义投票 (共 {len(answers)} 个有效回答)...")
        print(f"   候选答案: {answers}")

        final_consensus = self.get_consensus_answer(question, answers)

        print(f"🏆 语义一致性结果: {final_consensus}")
        return final_consensus

    def get_consensus_answer(self, question, answers):
        """
        使用 LLM 作为裁判，从多个候选答案中找出最一致的答案。
        """
        candidates_str = ""
        for i, ans in enumerate(answers, 1):
            candidates_str += f"Candidate {i}: {ans}\n"

        prompt = f"""
You are a consensus verifier.

Your task is to identify the "Majority Consensus" answer and preserve its citation.
1. Identify the core answer agreed upon by the majority.
2. Ignore minor phrasing differences (e.g., "The answer is 5" == "5").
3. **CRITICAL:** You MUST include the citation tag (e.g., [Source: ...]) in your final output. If candidates have different citations, prioritize the most frequent one.
4. If the answers are completely different or contradictory, output "Uncertain".

Example Question: "What is the capital of France?"

Example Input:
Candidate 1: Paris is the capital. [Source: wikipedia]
Candidate 2: The capital is Paris [Source: wikipedia]
Candidate 3: Paris [Source: web_search]

Consensus Answer: Paris [Source: wikipedia]

Output ONLY the final consensus answer text combined with the citation, without any explanation.

Now start!

User Question: "{question}"

Here are {len(answers)} candidate answers generated by an AI agent:
{candidates_str}

Consensus Answer:"""
        try:
            # 裁判通常需要低温度，保持客观
            consensus = self.llm(prompt, temperature=0.1).strip()

            if "Consensus:" in consensus:
                consensus = consensus.split("Consensus:")[-1].strip()

            consensus = consensus.split('\n')[0].strip()

            return consensus
        except Exception as e:
            print(f"⚠️ 裁判模型出错: {e}")
            return answers[0]


    def _run_trace(self, question, temperature = 0.2):
        """
        执行 ReAct 主循环
        """
        print(f"🚀 Start processing question: {question} (temp={temperature})\n")

        # 初始化 Prompt
        self.history = self.build_system_prompt()
        self.history += f"\nQuestion: {question}\n"

        step = 0
        while step < self.max_steps:
            print(f"--- Step {step+1} ---")

            # 1. 调用 LLM (Thought & Action 生成)
            # 这里我们将完整的 history 发给 LLM，并传入 temperature
            response = self.llm(self.history, temperature=temperature)
            response = response.strip()

            # 记录 LLM 的输出并打印
            print(f"\033[94mLLM Output:\033[0m\n{response}")  # 蓝色打印
            self.history += response + "\n"

            # 2. 检查是否包含 Final Answer
            if "Final Answer:" in response:
                final_answer = response.split("Final Answer:")[-1].strip()
                final_answer = final_answer.split("\n")[0].strip()
                # --- 进阶: 自动检查引用 ---
                if "[Source:" not in final_answer and "[Sources:" not in final_answer:
                    # 如果没有引用，强行把这个回答视为错误，塞回 History 让 LLM 重写
                    error_msg = "Observation: SYSTEM ALERT: You failed to provide a citation in your Final Answer. You MUST cite the source (e.g., [Source: wikipedia_search]). Please rewrite the Final Answer."
                    print(f"\033[31m{error_msg}\033[0m\n")
                    correction_thought = "Thought: I received a system alert that I missed the citation. I must rewrite the Final Answer to include the correct source immediately."
                    self.history += f"{response}\n{error_msg}\n" + correction_thought + "\nFinal Answers: "
                    continue
                print(f"\n✅ Task completed! Final answer: {final_answer}")
                return final_answer

            # 3. 解析 Action
            action, action_input = self.parse_output(response)

            if not action:
                # 错误处理: 如果 LLM 没遵循格式，让它重试
                print("⚠️ No valid action detected, Ask LLM to correct...")
                observation = "Observation: invalid format. Please strictly use 'Action:', 'Action Input:' format."

            elif action not in self.tools:
                # 错误处理: 调用了不存在的工具
                print(f"⚠️ Tool '{action}' does not exist.")
                observation = f"Observation: tool {action} does not exist. Please select from {list(self.tools.keys())}."

            else:
                # 4. 执行工具 (Execution)
                print(f"🛠️ Tool execution: {action}. Parameter: {action_input}.")
                try:
                    tool_result = self.execute_tool(action, action_input)
                    observation = tool_result
                except Exception as e:
                    observation = f"Observation: RuntimeError: {str(e)}"

            # 5. 将 Observation 反馈回历史 (Feedback Loop)
            print(f"\033[92m{observation}\033[0m\n")  # 绿色打印
            self.history += observation + "\nThought: "
            step += 1

        print("❌ Max steps reached. Task failed.")
        return "Error: Max steps reached."

    def execute_tool(self, action, action_input_str):
        tool_func = self.tools.get(action)

        if action == "calculator":
            return tool_func(action_input_str)

        if action == "plot_chart":
            try:
                import json
                params = json.loads(action_input_str)
                return tool_func(**params)
            except:
                return "Observation: Error. Please use JSON for this tool."

        return tool_func(action_input_str)