import streamlit as st
import json
import time
import os
import pandas as pd
import traceback

# 1. Import Config
import config

# 2. Import Core Modules
from ReactAgent import LLM
from ReactAgent.tool import MY_TOOLS
from ReactAgent.Agent import ReActAgent

# 3. Import Utility Functions
from utils import evaluate_trace, ensure_dataset_exists

# ==========================================
# 1. Page Config & CSS Styles
# ==========================================
st.set_page_config(
    page_title="ReactAgent Dashboard",
    page_icon="🧠",
    layout="wide"
)

st.markdown("""
<style>
    /* Thought Block */
    .st-thought {
        background-color: #f0f7ff;
        border-left: 4px solid #0068c9;
        padding: 10px;
        margin: 5px 0;
        border-radius: 4px;
        font-size: 0.95em;
        color: #002b55;
    }
    /* Action Block */
    .st-action {
        background-color: #fff8f0;
        border-left: 4px solid #ff9f36;
        padding: 10px;
        margin: 5px 0;
        border-radius: 4px;
        font-family: monospace;
        font-size: 0.9em;
        color: #663300;
    }
    /* Observation Block */
    .st-observation {
        background-color: #f0fff4;
        border-left: 4px solid #28a745;
        padding: 10px;
        margin: 5px 0;
        border-radius: 4px;
        font-size: 0.95em;
        color: #155724;
        white-space: pre-wrap;
    }
    /* Final Answer */
    .st-final {
        background-color: #e8fdf5;
        border: 1px solid #28a745;
        padding: 15px;
        border-radius: 8px;
        font-weight: bold;
        color: #155724;
        margin-top: 10px;
    }
    /* Error Alert */
    .st-error {
        background-color: #fff0f0;
        border-left: 4px solid #ff4b4b;
        padding: 10px;
    }
    /* Divider */
    .st-divider {
        border-top: 1px dashed #ccc;
        margin: 10px 0;
        text-align: center;
        color: #888;
        font-size: 0.8em;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. Streamlit Specific Agent
# ==========================================
class StreamlitReActAgent(ReActAgent):
    def __init__(self, llm_func, tools, max_steps=10, st_container=None):
        super().__init__(llm_func, tools, max_steps)
        self.st_container = st_container

    def _log_ui(self, type_name, content):
        """
        Core modification: Use st_container.markdown to write.
        If using st.container() or st.status(), this appends content instead of overwriting.
        """
        if not self.st_container: return
        
        if type_name == "Thought":
            self.st_container.markdown(f'<div class="st-thought">🤔 <b>Thought:</b> {content}</div>', unsafe_allow_html=True)
        elif type_name == "Action":
            self.st_container.markdown(f'<div class="st-action">⚙️ <b>Action:</b> {content}</div>', unsafe_allow_html=True)
        elif type_name == "Observation":
            disp = content[:1000] + "..." if len(content) > 1000 else content
            self.st_container.markdown(f'<div class="st-observation">👁️ <b>Observation:</b> {disp}</div>', unsafe_allow_html=True)
        elif type_name == "Error":
            self.st_container.markdown(f'<div class="st-error">❌ <b>Error:</b> {content}</div>', unsafe_allow_html=True)
        elif type_name == "Divider":
            self.st_container.markdown(f'<div class="st-divider">{content}</div>', unsafe_allow_html=True)

    def run(self, question, k=1, temperature=0.1):
        """
        Override run method to distinguish different Paths in UI when K > 1
        """
        if k == 1:
            return self._run_trace(question, temperature=temperature)
        
        # If Self-Consistency mode
        self.trace_history = []
        answers = []
        
        for i in range(k):
            # Print separator in UI to distinguish paths
            self._log_ui("Divider", f"🚀 Start Trace {i+1}/{k}")
            
            # Call parent logic for single trace
            result = self._run_trace(question, temperature=temperature)
            
            # Record history
            self.trace_history.append(self.history.split('Now start!')[-1].strip())
            
            if "Error" not in result and "Max steps reached" not in result:
                answers.append(result)
        
        if not answers:
            return "Error: All traces failed."
            
        if len(answers) == 1:
            return answers[0]
            
        # Semantic Voting Display
        self._log_ui("Divider", f"📊 Performing Semantic Consensus Vote on {len(answers)} answers...")
        final_consensus = self.get_consensus_answer(question, answers)
        return final_consensus

    def _run_trace(self, question, temperature=0.2):
        self.history = self.build_system_prompt()
        self.history += f"\nQuestion: {question}\n"

        step = 0
        while step < self.max_steps:
            response = self.llm(self.history, temperature=temperature).strip()
            
            # 1. Real-time Thought / Action display
            if "Action:" in response:
                parts = response.split("Action:")
                thought_part = parts[0].replace("Thought:", "").strip()
                action_part = "Action:" + parts[1]
                if thought_part: self._log_ui("Thought", thought_part)
                self._log_ui("Action", action_part)
            else:
                if "Final Answer:" not in response:
                    clean_resp = response.replace("Thought:", "").strip()
                    self._log_ui("Thought", clean_resp)

            self.history += response + "\n"

            # 2. Check Final Answer
            if "Final Answer:" in response:
                final_answer = response.split("Final Answer:")[-1].strip().split("\n")[0]
                if "[Source:" not in final_answer and "[Sources:" not in final_answer:
                     err = "Observation: SYSTEM ALERT: Missing citation."
                     self._log_ui("Observation", err)
                     self.history += f"{response}\n{err}\nThought: Adding citation.\nFinal Answers: "
                     continue
                return final_answer

            # 3. Execute Tool
            action, action_input = self.parse_output(response)

            if not action or action not in self.tools:
                self._log_ui("Error", f"Tool '{action}' not found.")
            else:
                try:
                    tool_result = self.execute_tool(action, action_input)
                    clean_obs = tool_result.replace("Observation:", "").strip()
                    # Real-time Observation display (append)
                    self._log_ui("Observation", clean_obs)
                    obs = tool_result 
                except Exception as e:
                    obs = f"Observation: Error: {str(e)}"
                    self._log_ui("Error", str(e))
            
            self.history += obs + "\nThought: "
            step += 1
        return "Error: Max steps reached."

# ==========================================
# 3. Model Loading
# ==========================================
@st.cache_resource
def load_llm_once():
    """Initialize Model"""
    try:
        print("⏳ Streamlit: Loading Model...")
        LLM.init_model(config)
        print("✅ Streamlit: Model Loaded!")
        return True
    except Exception as e:
        print(f"❌ Load Error: {e}")
        raise e

# ==========================================
# 4. Helper Functions
# ==========================================
def get_dataset_files():
    data_dir = "./data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        ensure_dataset_exists(os.path.join(data_dir, "easy_eval_dataset.json"))
    return [f for f in os.listdir(data_dir) if f.endswith(".json")]

# ==========================================
# 5. Sidebar & Main Logic
# ==========================================
if "model_ready" not in st.session_state:
    with st.spinner("Initializing Model..."):
        try:
            load_llm_once()
            st.session_state.model_ready = True
        except Exception as e:
            st.error(f"Model Load Failed: {e}")
            st.stop()

with st.sidebar:
    st.title("🤖 TinyAgent Console")
    # Translated radio options
    run_mode = st.radio("🛠️ Mode Selection", ["💬 Chat", "📊 Batch Evaluation"])
    temp = st.slider("Temperature", 0.0, 1.0, 0.1)
    k_val = st.number_input("Self-Consistency K", 1, 5, 1)
    
    st.divider()
    enable_eval = st.checkbox("Enable LLM Auto-Eval", value=True, help="If checked, the model will score the agent's reasoning path.")

# --- Mode A: Chat Debug ---
if run_mode == "💬 Chat":
    st.header("💬 Agent Interactive ")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if "trace_html" in msg:
                with st.expander(f"View Thought Process ({msg.get('status', 'Done')})", expanded=False):
                    st.markdown(msg["trace_html"], unsafe_allow_html=True)
            st.markdown(msg["content"])
            if "eval_score" in msg:
                 st.caption(f"📝 Score: {msg['eval_score']}")

    if prompt := st.chat_input("Enter your question..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            trace_container = st.container()
            
            # Use status to show current thinking state
            with trace_container.status("🔄 Thinking...", expanded=True) as status_box:
                # [Key Change]
                # Pass status_box as the container to the Agent.
                
                agent = StreamlitReActAgent(LLM.local_llm_call, MY_TOOLS, st_container=status_box)
                
                try:
                    start_t = time.time()
                    if k_val > 1:
                        status_box.markdown(f"**ℹ️ Performing {k_val} votes...**")
                        final_ans = agent.run(prompt, k=k_val, temperature=temp)
                    else:
                        final_ans = agent.run(prompt, k=1, temperature=temp)
                    
                    duration = time.time() - start_t
                    
                    status_box.update(label=f"✅ Thinking Complete ({duration:.2f}s)", state="complete", expanded=False)
                    
                    st.markdown(f'<div class="st-final">{final_ans}</div>', unsafe_allow_html=True)

                    if k_val > 1:
                        trace_text = "\n\n".join([f"--- Path {i+1} ---\n{t}" for i, t in enumerate(agent.trace_history)])
                    else:
                        trace_text = agent.history
                    
                    hist_html = f"<pre style='white-space: pre-wrap;'>{trace_text}</pre>"
                    
                    msg_data = {
                        "role": "assistant",
                        "content": final_ans,
                        "trace_html": hist_html,
                        "status": f"K={k_val}"
                    }

                    if enable_eval:
                        with st.spinner("Scoring automatically..."):
                            score = evaluate_trace(trace_text, final_ans, "Unknown", MY_TOOLS, prompt)
                            msg_data["eval_score"] = score
                            st.success(f"Evaluation Complete: {score}")

                    st.session_state.messages.append(msg_data)

                except Exception as e:
                    status_box.update(label="❌ Error Occurred", state="error")
                    st.error(f"Runtime Error: {e}")
                    st.write(traceback.format_exc())

# --- Mode B: Batch Evaluation ---
else:
    st.header("📊 Batch Evaluation Mode")
    datasets = get_dataset_files()
    selected_file = st.selectbox("Select Dataset", datasets)
    
    if st.button("🚀 Start Evaluation", type="primary"):
        if not selected_file:
            st.warning("Please select a dataset")
            st.stop()
            
        file_path = os.path.join("./data", selected_file)
        with open(file_path, "r", encoding="utf-8") as f:
            test_cases = json.load(f)
            
        eval_status_text = 'On' if enable_eval else 'Off'
        st.info(f"Evaluating {len(test_cases)} items | K={k_val} | Temp={temp} | Auto-Eval: {eval_status_text}")
        
        progress_bar = st.progress(0)
        result_table = st.empty()
        results_list = []
        passed_count = 0
        
        eval_agent = ReActAgent(LLM.local_llm_call, MY_TOOLS)
        
        for i, case in enumerate(test_cases):
            q = case.get("question")
            gold_ans = case.get("gold_answer", "")
            gold_kws = case.get("gold_keywords", [])
            
            try:
                output = eval_agent.run(q, k=k_val, temperature=temp)
                
                is_correct = any(kw.lower() in output.lower() for kw in gold_kws)
                if is_correct: passed_count += 1
                
                if enable_eval:
                    trace_for_eval = str(eval_agent.trace_history) if k_val > 1 else eval_agent.history
                    llm_score = evaluate_trace(trace_for_eval, output, gold_ans, MY_TOOLS, q)
                else:
                    llm_score = "Skipped"

                results_list.append({
                    "ID": case.get("id", i+1),
                    "Question": q,
                    "Answer": output,
                    "Pass": "✅" if is_correct else "❌",
                    "Score": llm_score
                })
            except Exception as e:
                results_list.append({"ID": i+1, "Question": q, "Answer": f"Error: {e}", "Pass": "⚠️", "Score": "Error"})
            
            progress_bar.progress((i + 1) / len(test_cases))
            result_table.dataframe(pd.DataFrame(results_list), use_container_width=True)
        
        acc = (passed_count / len(test_cases)) * 100
        st.success(f"Evaluation Complete! Accuracy: {acc:.2f}%")
        
        if results_list:
            csv = pd.DataFrame(results_list).to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download CSV", csv, "eval_result.csv", "text/csv")