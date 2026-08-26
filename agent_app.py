import streamlit as st
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import SerpAPIWrapper
from langchain.tools import Tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
import requests
import os
import html
import time

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="AI Agent - Multi-Provider",
    page_icon="🤖",
    layout="centered"
)

# ============================================================
# CUSTOM CSS
# ============================================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .provider-box {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #1f77b4;
    }
    .instruction {
        background-color: #f0f8ff;
        padding: 1rem;
        border-left: 4px solid #1f77b4;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    .final-answer {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #28a745;
        margin-top: 1rem;
    }
    .stButton>button {
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.5rem 2rem;
    }
    .stButton>button:hover {
        background-color: #1565a8;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# MAIN HEADER
# ============================================================
st.markdown('<div class="main-header">🤖 AI Agent Playground</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">ReAct Agent powered by Groq OR Google AI Studio — you choose the brain</div>', unsafe_allow_html=True)

# ============================================================
# SIDEBAR — LLM PROVIDER SELECTION
# ============================================================
st.sidebar.markdown("## 🧠 Select LLM Provider")

provider = st.sidebar.radio(
    "Choose your provider:",
    ["Groq", "Google AI Studio"],
    help="Select one provider. Enter its API key. The other is disabled."
)

st.sidebar.markdown("---")

# ---- Initialize session state for models ----
if "available_models" not in st.session_state:
    st.session_state.available_models = []
if "selected_model" not in st.session_state:
    st.session_state.selected_model = None
if "provider_key" not in st.session_state:
    st.session_state.provider_key = ""
if "provider_confirmed" not in st.session_state:
    st.session_state.provider_confirmed = False
if "last_query_time" not in st.session_state:
    st.session_state.last_query_time = 0

# ============================================================
# PROVIDER-SPECIFIC API KEY INPUT
# ============================================================
if provider == "Groq":
    st.sidebar.markdown("### 🔐 Groq API Key")
    st.sidebar.markdown("<small>Get free key: console.groq.com | $200 free credits</small>", unsafe_allow_html=True)
    groq_key = st.sidebar.text_input(
        "Enter Groq API Key",
        type="password",
        key="groq_key_input",
        help="Your key stays in this browser session only."
    )
    
    if st.sidebar.button("🔍 Load Groq Models", key="load_groq"):
        if not groq_key:
            st.sidebar.error("Please enter your Groq API key first.")
        else:
            with st.spinner("Fetching Groq models..."):
                try:
                    resp = requests.get(
                        "https://api.groq.com/openai/v1/models",
                        headers={"Authorization": f"Bearer {groq_key}"},
                        timeout=15
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        models = [m["id"] for m in data.get("data", [])]
                        chat_models = [m for m in models if any(x in m.lower() for x in ["gpt-oss", "llama", "mixtral", "gemma", "qwen"])]
                        st.session_state.available_models = chat_models if chat_models else models
                        st.session_state.provider_key = groq_key
                        st.session_state.provider_confirmed = True
                        st.sidebar.success(f"Loaded {len(st.session_state.available_models)} models")
                    else:
                        st.sidebar.error(f"Failed: HTTP {resp.status_code}. Check your key.")
                except Exception as e:
                    st.sidebar.error(f"Error: {e}")

elif provider == "Google AI Studio":
    st.sidebar.markdown("### 🔐 Google AI Studio API Key")
    st.sidebar.markdown("<small>Get free key: aistudio.google.com | Generous free tier</small>", unsafe_allow_html=True)
    google_key = st.sidebar.text_input(
        "Enter Google AI Studio API Key",
        type="password",
        key="google_key_input",
        help="Your key stays in this browser session only."
    )
    
    if st.sidebar.button("🔍 Load Gemini Models", key="load_google"):
        if not google_key:
            st.sidebar.error("Please enter your Google AI Studio API key first.")
        else:
            with st.spinner("Fetching Gemini models..."):
                try:
                    # SECURITY FIX: Use header-based auth instead of URL parameter
                    resp = requests.get(
                        "https://generativelanguage.googleapis.com/v1beta/models",
                        headers={"x-goog-api-key": google_key},
                        timeout=15
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        models = [m["name"].replace("models/", "") for m in data.get("models", []) if "generateContent" in m.get("supportedGenerationMethods", [])]
                        st.session_state.available_models = models
                        st.session_state.provider_key = google_key
                        st.session_state.provider_confirmed = True
                        st.sidebar.success(f"Loaded {len(st.session_state.available_models)} models")
                    else:
                        st.sidebar.error(f"Failed: HTTP {resp.status_code}. Check your key.")
                except Exception as e:
                    st.sidebar.error(f"Error: {e}")

# ============================================================
# MODEL SELECTION DROPDOWN
# ============================================================
if st.session_state.provider_confirmed and st.session_state.available_models:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎯 Select Model")
    selected_model = st.sidebar.selectbox(
        "Choose a model:",
        st.session_state.available_models,
        key="model_select"
    )
    # SECURITY FIX: Escape model name to prevent XSS if API returns malicious string
    safe_model = html.escape(selected_model)
    st.session_state.selected_model = selected_model
    st.sidebar.markdown(f"Selected: **{safe_model}**")

# ============================================================
# TOOL API KEYS (SerpAPI + WeatherAPI)
# ============================================================
st.sidebar.markdown("---")
st.sidebar.markdown("## 🔧 Tool API Keys")

serp_key = st.sidebar.text_input(
    "SerpAPI Key",
    type="password",
    help="serpapi.com | 100 searches/month free"
)

weather_key = st.sidebar.text_input(
    "WeatherAPI Key",
    type="password",
    help="weatherapi.com | 1M calls/month free"
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Built by:** Saad Maqbool")
st.sidebar.markdown("**Course:** Bano Qabil Agentic AI")

# ============================================================
# MAIN AREA — INSTRUCTIONS
# ============================================================
with st.expander("📖 How to Use (Click to Expand)", expanded=False):
    st.markdown("""
    <div class="instruction">
    <b>Step 1:</b> Select <b>Groq</b> or <b>Google AI Studio</b> in the sidebar.<br>
    <b>Step 2:</b> Enter that provider's API key and click <b>Load Models</b>.<br>
    <b>Step 3:</b> Pick a model from the dropdown that appears.<br>
    <b>Step 4:</b> Enter <b>SerpAPI</b> and <b>WeatherAPI</b> keys.<br>
    <b>Step 5:</b> Type your question and watch the agent work!<br><br>
    
    <b>What the agent can do:</b><br>
    🔍 <b>Web Search</b> — Find current information from the internet<br>
    🌤️ <b>Weather Lookup</b> — Get real-time weather for any city<br>
    🧠 <b>Reasoning</b> — Combine tools to answer complex questions<br><br>
    
    <b>Example questions:</b><br>
    • "Find the capital of India and then find its current weather."<br>
    • "What is the weather in Lahore right now?"<br>
    • "Search for the latest news about AI and summarize it."
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# VALIDATE ALL INPUTS
# ============================================================
missing = []
if not st.session_state.provider_confirmed:
    missing.append("LLM Provider API Key (select provider → enter key → Load Models)")
if not st.session_state.selected_model:
    missing.append("A model from the dropdown")
if not serp_key:
    missing.append("SerpAPI Key")
if not weather_key:
    missing.append("WeatherAPI Key")

if missing:
    st.warning("⚠️ Please complete the setup in the sidebar:")
    for item in missing:
        st.markdown(f"• {item}")
    st.info("💡 All services offer free tiers. No credit card required.")
    st.stop()

# ============================================================
# BUILD LLM BASED ON SELECTED PROVIDER
# ============================================================
def build_llm(provider: str, model: str, api_key: str):
    """Build the LLM based on selected provider and model."""
    if provider == "Groq":
        return ChatGroq(
            model=model,
            temperature=0,
            api_key=api_key,
            max_tokens=1024,
            request_timeout=60
        )
    elif provider == "Google AI Studio":
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=0,
            google_api_key=api_key,
            max_output_tokens=1024,
            request_timeout=60
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")

# ============================================================
# SETUP AGENT (cached)
# ============================================================
@st.cache_resource(show_spinner=False)
def build_agent(provider: str, model: str, provider_key: str, serp_key: str, weather_key: str):
    """Build the ReAct agent with selected LLM + tools."""
    
    os.environ["SERPAPI_API_KEY"] = serp_key
    
    # ---- LLM ----
    llm = build_llm(provider, model, provider_key)
    
    # ---- TOOL 1: Web Search via SerpAPI ----
    search_wrapper = SerpAPIWrapper(serpapi_api_key=serp_key)
    search_tool = Tool(
        name="web_search",
        func=search_wrapper.run,
        description="Useful for searching the internet for current information, facts, news, and data."
    )
    
    # ---- TOOL 2: Weather Lookup via WeatherAPI ----
    # SECURITY FIX: Use HTTPS instead of HTTP
    def get_weather(city: str) -> str:
        """Fetch current weather for a given city."""
        url = f"https://api.weatherapi.com/v1/current.json?key={weather_key}&q={city}"
        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()
            if "current" not in data:
                return f"Could not fetch weather for {city}. Please check the city name."
            current = data["current"]
            return (
                f"City: {city}\n"
                f"Temperature: {current['temp_c']}°C\n"
                f"Condition: {current['condition']['text']}\n"
                f"Humidity: {current['humidity']}%\n"
                f"Wind: {current['wind_kph']} km/h"
            )
        except Exception as e:
            return f"Error fetching weather: {str(e)}"
    
    weather_tool = Tool(
        name="get_weather",
        func=get_weather,
        description="Useful for getting current weather information for any city in the world."
    )
    
    # ---- PROMPT: ReAct template ----
    template = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""
    
    prompt = PromptTemplate.from_template(template)
    
    # ---- AGENT & EXECUTOR ----
    tools = [search_tool, weather_tool]
    agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=10
    )
    
    return agent_executor

# Build the agent
try:
    with st.spinner(f"🛠️ Building your AI Agent with {provider} / {st.session_state.selected_model}..."):
        agent_executor = build_agent(
            provider,
            st.session_state.selected_model,
            st.session_state.provider_key,
            serp_key,
            weather_key
        )
    st.success(f"✅ Agent ready! Provider: **{provider}** | Model: **{html.escape(st.session_state.selected_model)}**")
except Exception as e:
    st.error(f"❌ Failed to build agent: {e}")
    st.info("Please check your API keys and selected model, then try again.")
    st.stop()

# ============================================================
# CHAT INTERFACE
# ============================================================
st.markdown("---")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_query = st.chat_input("Ask the agent anything...")

if user_query:
    # SECURITY FIX: Input length validation
    if len(user_query) > 1000:
        st.error("❌ Query too long. Please keep it under 1000 characters.")
        st.stop()
    
    # SECURITY FIX: Rate limiting — 3 second cooldown between queries
    current_time = time.time()
    if current_time - st.session_state.last_query_time < 3:
        st.warning("⏳ Please wait a few seconds between queries.")
        st.stop()
    st.session_state.last_query_time = current_time
    
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)
    
    with st.chat_message("assistant"):
        with st.spinner("🧠 Agent is thinking..."):
            try:
                import sys
                from io import StringIO
                
                old_stdout = sys.stdout
                sys.stdout = mystdout = StringIO()
                
                response = agent_executor.invoke({"input": user_query})
                
                sys.stdout = old_stdout
                verbose_output = mystdout.getvalue()
                
                if verbose_output:
                    with st.expander("🔍 View Agent's Thought Process", expanded=False):
                        st.text(verbose_output)
                
                final_answer = response.get("output", "No answer generated.")
                # SECURITY FIX: Escape HTML in agent output to prevent XSS
                safe_answer = html.escape(final_answer)
                st.markdown(f'<div class="final-answer"><b>📝 Final Answer:</b><br>{safe_answer}</div>', unsafe_allow_html=True)
                
                st.session_state.messages.append({"role": "assistant", "content": final_answer})
                
            except Exception as e:
                st.error(f"❌ Agent error: {e}")
                st.info("Try rephrasing your question or check your API keys.")

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888; font-size: 0.85rem;">
    🤖 Built with LangChain + Groq/Google AI Studio + Streamlit | BYOK | Free tier friendly
</div>
""", unsafe_allow_html=True)
