"""
AI Agent Playground — Custom Lightweight Agent
Built by Saad Maqbool | Bano Qabil Agentic AI BQL6-LR
Multi-provider: Groq / Google AI Studio / Cerebras
Custom agent loop — works with ANY model, no ReAct compatibility needed
"""

import os
import re
import time
import traceback

import requests
import streamlit as st
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.utilities.openweathermap import OpenWeatherMapAPIWrapper
from langchain_community.utilities.serpapi import SerpAPIWrapper
from langchain_community.utilities.weatherapi import WeatherAPIWrapper

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Agent Playground",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── HIDE STREAMLIT CHROME ────────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none !important;}
[data-testid="stToolbar"] {display: none !important;}
.block-container {padding-top: 1rem !important;}
.chat-user {background: #1e3a5f; color: white; padding: 12px 16px;
            border-radius: 12px 12px 0 12px; margin: 8px 0;
            max-width: 80%; margin-left: auto;}
.chat-assistant {background: #2d2d2d; color: #e0e0e0; padding: 12px 16px;
                 border-radius: 12px 12px 12px 0; margin: 8px 0;
                 max-width: 80%; border-left: 3px solid #4CAF50;}
.chat-error {background: #2d2d2d; color: #ff6b6b; padding: 12px 16px;
             border-radius: 12px 12px 12px 0; margin: 8px 0;
             max-width: 80%; border-left: 3px solid #ff6b6b;}
.chat-tool {background: #1a1a2e; color: #a0d2eb; padding: 10px 14px;
            border-radius: 8px; margin: 6px 0; font-size: 0.85rem;
            border-left: 3px solid #a0d2eb;}
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ────────────────────────────────────────────────────────────
for key in ["messages", "last_query_time", "selected_model", "available_models"]:
    if key not in st.session_state:
        if key == "messages":
            st.session_state[key] = []
        elif key == "last_query_time":
            st.session_state[key] = 0
        elif key == "available_models":
            st.session_state[key] = []
        else:
            st.session_state[key] = None

# ── FRIENDLY ERROR MAPPER ────────────────────────────────────────────────────
def friendly_error(exc, provider=None):
    tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
    combined = " ".join(tb).lower()
    msg = str(exc).lower()

    if provider == "Groq":
        if "401" in combined or "403" in combined or "invalid api key" in msg:
            return "Groq API key is invalid. Get a new one at console.groq.com."
        if "429" in combined or "rate limit" in combined:
            return "Groq rate limit hit. Wait 30 seconds and try again."
        if "413" in combined or "too large" in combined:
            return "This model's context window is too small. Try a different model."
        if "not found" in combined or "does not exist" in combined:
            return "This model is not available. Try another from the list."

    if provider == "Google AI Studio":
        if "401" in combined or "403" in combined or "not valid" in msg:
            return "Google key is invalid. Get one at aistudio.google.com."
        if "429" in combined or "quota" in combined:
            return "Google quota exceeded. Wait a minute and try again."
        if "safety" in combined or "blocked" in combined:
            return "Google blocked this due to safety settings. Try rephrasing."

    if provider == "Cerebras":
        if "401" in combined or "403" in combined:
            return "Cerebras key is invalid. Get one at cloud.cerebras.ai."
        if "429" in combined or "rate limit" in combined:
            return "Cerebras rate limit hit (5 RPM free tier). Wait 12 seconds."
        if "not found" in combined or "unsupported" in combined:
            return "Model not available. Try another from the list."

    if "timeout" in combined or "timed out" in msg:
        return "Request timed out. Try again or pick a faster model."
    if "connection" in combined or "network" in combined:
        return "Network error. Check your internet and try again."
    if "no module named" in combined:
        return "Library missing. Wait 2 minutes for install, then refresh."

    return f"Error: {str(exc)[:150]}. Try again or pick a different model."

# ── HERO ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 20px 0;">
    <h1 style="font-size: 2.5rem; margin-bottom: 0.2rem;">🤖 AI Agent Playground</h1>
    <p style="color: #888; font-size: 1.05rem;">
        Custom Lightweight Agent • Works with ANY Model • Search + Weather • Built by Saad Maqbool
    </p>
</div>
""", unsafe_allow_html=True)

# ── TOOL SELECTION ───────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    search_tool_name = st.radio(
        "🔍 Search Tool",
        ["DuckDuckGo (Free)", "SerpAPI", "Tavily"],
        index=0,
        help="DuckDuckGo needs no API key. SerpAPI and Tavily need keys.",
    )
with col2:
    weather_tool_name = st.radio(
        "🌤️ Weather Tool",
        ["WeatherAPI", "OpenWeatherMap"],
        index=1,
        help="Both need free API keys.",
    )

# ── API KEYS ─────────────────────────────────────────────────────────────────
st.markdown("---")
key_col1, key_col2, key_col3 = st.columns(3)

with key_col1:
    st.markdown("**🔐 LLM Provider**")
    provider = st.radio(
        "Select Provider",
        ["Groq", "Google AI Studio", "Cerebras"],
        index=0,
        help="Pick the provider whose API key you have.",
    )
    if provider == "Groq":
        provider_key = st.text_input("Groq API Key", type="password", help="console.groq.com")
    elif provider == "Google AI Studio":
        provider_key = st.text_input("Google AI Studio Key", type="password", help="aistudio.google.com")
    else:
        provider_key = st.text_input("Cerebras API Key", type="password", help="cloud.cerebras.ai")

with key_col2:
    st.markdown("**🔐 Search Key (if needed)**")
    if search_tool_name == "DuckDuckGo (Free)":
        st.info("✅ No key needed")
        search_key = ""
    elif search_tool_name == "SerpAPI":
        search_key = st.text_input("SerpAPI Key", type="password")
    else:
        search_key = st.text_input("Tavily Key", type="password")

with key_col3:
    st.markdown("**🔐 Weather Key**")
    if weather_tool_name == "WeatherAPI":
        weather_key = st.text_input("WeatherAPI Key", type="password")
    else:
        weather_key = st.text_input("OpenWeatherMap Key", type="password")

# ── MODEL LOADING ────────────────────────────────────────────────────────────
st.markdown("---")
model_col1, model_col2 = st.columns([2, 1])

with model_col1:
    if st.button("🔍 Load Models", use_container_width=True) and provider_key:
        with st.spinner(f"Fetching {provider} models..."):
            try:
                models = []
                if provider == "Groq":
                    resp = requests.get(
                        "https://api.groq.com/openai/v1/models",
                        headers={"Authorization": f"Bearer {provider_key}"},
                        timeout=15,
                    )
                    if resp.status_code == 200:
                        models = [m["id"] for m in resp.json().get("data", []) if "id" in m]

                elif provider == "Google AI Studio":
                    resp = requests.get(
                        f"https://generativelanguage.googleapis.com/v1beta/models?key={provider_key}",
                        timeout=15,
                    )
                    if resp.status_code == 200:
                        raw = resp.json().get("models", [])
                        models = [m["name"].replace("models/", "") for m in raw if "name" in m]

                elif provider == "Cerebras":
                    resp = requests.get(
                        "https://api.cerebras.ai/v1/models",
                        headers={"Authorization": f"Bearer {provider_key}"},
                        timeout=15,
                    )
                    if resp.status_code == 200:
                        models = [m["id"] for m in resp.json().get("data", []) if "id" in m]

                st.session_state.available_models = models
                if models:
                    st.success(f"✅ Loaded {len(models)} models")
                else:
                    st.warning("No models returned. Check your API key.")
            except Exception as e:
                st.error(friendly_error(e, provider))

    if st.session_state.available_models:
        selected_model = st.selectbox(
            "🧠 Select Model",
            st.session_state.available_models,
            index=0,
        )
        st.session_state.selected_model = selected_model
        st.markdown(f"<span style='color:#4CAF50;font-size:0.9rem;'>✅ Ready: `{selected_model}`</span>", unsafe_allow_html=True)
    else:
        st.info("Enter your API key and click 'Load Models' above.")

with model_col2:
    st.markdown("""
    <div style="font-size:0.85rem; color:#aaa; padding-top:8px;">
        <b>How this works:</b><br>
        This app uses a <b>custom lightweight agent</b> — not LangChain ReAct. It works with ANY model, even ones that don't support ReAct. The model just needs to follow simple instructions.<br><br>
        <b>Tip:</b> If one model fails, try another from the same provider.
    </div>
    """, unsafe_allow_html=True)

# ── INSTRUCTIONS ─────────────────────────────────────────────────────────────
with st.expander("📖 How to use this app"):
    st.markdown("""
    1. **Pick a provider** and enter its API key.
    2. **Click "Load Models"** to see all available models.
    3. **Select a model** from the dropdown.
    4. **Enter search/weather keys** if needed (DuckDuckGo is free).
    5. **Ask anything** — the agent will use search or weather tools if needed.

    **Why custom agent?** LangChain ReAct requires models trained on the ReAct text pattern. Many free-tier models don't support this. Our custom agent uses a simpler format that ANY instruction-tuned model can follow.
    """)

# ── CLEAR CHAT ───────────────────────────────────────────────────────────────
if st.session_state.messages:
    if st.button("🗑️ Clear Chat", type="secondary"):
        st.session_state.messages = []
        st.session_state.selected_model = None
        st.session_state.available_models = []
        st.rerun()

# ── CHAT HISTORY ─────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-user">{msg["content"]}</div>', unsafe_allow_html=True)
    elif msg["role"] == "error":
        st.markdown(f'<div class="chat-error">⚠️ {msg["content"]}</div>', unsafe_allow_html=True)
    elif msg["role"] == "tool":
        st.markdown(f'<div class="chat-tool">🔧 {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-assistant">{msg["content"]}</div>', unsafe_allow_html=True)

# ── TOOL INITIALIZATION ────────────────────────────────────────────────────
def init_search_tool(tool_name, api_key):
    if tool_name == "DuckDuckGo (Free)":
        return DuckDuckGoSearchRun()
    elif tool_name == "SerpAPI":
        if not api_key:
            raise ValueError("SerpAPI key is required.")
        os.environ["SERPAPI_API_KEY"] = api_key
        return SerpAPIWrapper()
    elif tool_name == "Tavily":
        if not api_key:
            raise ValueError("Tavily key is required.")
        return TavilySearchResults(tavily_api_key=api_key, max_results=3)
    return DuckDuckGoSearchRun()

def init_weather_tool(tool_name, api_key):
    if tool_name == "WeatherAPI":
        if not api_key:
            raise ValueError("WeatherAPI key is required.")
        os.environ["WEATHERAPI_API_KEY"] = api_key
        return WeatherAPIWrapper()
    else:
        if not api_key:
            raise ValueError("OpenWeatherMap key is required.")
        os.environ["OPENWEATHERMAP_API_KEY"] = api_key
        return OpenWeatherMapAPIWrapper()

# ── LLM INITIALIZATION ───────────────────────────────────────────────────────
def init_llm(provider, model, api_key):
    if provider == "Groq":
        return ChatGroq(model=model, api_key=api_key, temperature=0, max_tokens=1024)
    elif provider == "Google AI Studio":
        return ChatGoogleGenerativeAI(model=model, google_api_key=api_key, temperature=0, max_output_tokens=1024)
    elif provider == "Cerebras":
        return ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            openai_api_base="https://api.cerebras.ai/v1",
            temperature=0,
            max_tokens=1024,
        )
    raise ValueError(f"Unknown provider: {provider}")

# ── CUSTOM AGENT LOOP ─────────────────────────────────────────────────────────
TOOL_PATTERN = re.compile(r"TOOL:[ \t]*(\w+)[ \t]*INPUT:[ \t]*(.+)", re.IGNORECASE)

SYSTEM_PROMPT = """You are a helpful AI assistant with access to tools.

Available tools:
- search: Search the internet for current information. Input: a search query.
- weather: Get current weather for a city. Input: a city name.

To use a tool, respond EXACTLY in this format on its own line:
TOOL: <tool_name>
INPUT: <tool_input>

Example:
TOOL: search
INPUT: current Pakistan test cricket captain

If you can answer directly without tools, just respond normally. Do not make up information. Use the search tool if you need current facts."""

MAX_ITERATIONS = 3

def run_agent(query, llm, search_tool, weather_tool):
    """Custom lightweight agent loop. Works with ANY model."""
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"User question: {query}"),
    ]

    for i in range(MAX_ITERATIONS):
        try:
            response = llm.invoke(messages)
            content = response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            raise RuntimeError(f"LLM error: {e}")

        # Check for tool call
        match = TOOL_PATTERN.search(content)
        if not match:
            return content, messages

        tool_name = match.group(1).strip().lower()
        tool_input = match.group(2).strip()

        # Execute tool
        try:
            if tool_name == "search":
                observation = search_tool.run(tool_input)
            elif tool_name == "weather":
                observation = weather_tool.run(tool_input)
            else:
                observation = f"Error: Unknown tool '{tool_name}'. Available: search, weather."
        except Exception as e:
            observation = f"Error running {tool_name}: {str(e)[:200]}"

        # Add tool call and observation to conversation
        messages.append(AIMessage(content=content))
        messages.append(HumanMessage(content=f"Observation from {tool_name}: {observation}\n\nNow answer the user's original question: {query}"))

    return "I used the available tools but couldn't find a definitive answer. Try rephrasing your question.", messages

# ── CHAT INPUT ───────────────────────────────────────────────────────────────
st.markdown("---")
query = st.chat_input("Ask your agent anything...")

if query:
    if not provider_key:
        st.session_state.messages.append({"role": "error", "content": f"Enter your {provider} API key first."})
        st.rerun()
    if not st.session_state.selected_model:
        st.session_state.messages.append({"role": "error", "content": "Load models and select one first."})
        st.rerun()
    if len(query) > 1000:
        st.session_state.messages.append({"role": "error", "content": "Question too long (max 1000 chars)."})
        st.rerun()

    now = time.time()
    if now - st.session_state.last_query_time < 3:
        st.session_state.messages.append({"role": "error", "content": "Please wait 3 seconds between queries."})
        st.rerun()
    st.session_state.last_query_time = now

    st.session_state.messages.append({"role": "user", "content": query})

    with st.spinner(f"🧠 {st.session_state.selected_model} is thinking..."):
        try:
            search = init_search_tool(search_tool_name, search_key)
            weather = init_weather_tool(weather_tool_name, weather_key)
            llm = init_llm(provider, st.session_state.selected_model, provider_key)

            answer, _ = run_agent(query, llm, search, weather)

            if not answer or not answer.strip():
                st.session_state.messages.append({"role": "error", "content": "The agent returned an empty response. Try rephrasing."})
            else:
                st.session_state.messages.append({"role": "assistant", "content": answer})

        except Exception as e:
            err_msg = friendly_error(e, provider)
            st.session_state.messages.append({"role": "error", "content": err_msg})

    st.rerun()

# ── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 30px 0 10px; color:#666; font-size:0.85rem;">
    Built by <b>Saad Maqbool</b> • Bano Qabil Agentic AI BQL6-LR • Lytton Road, Lahore<br>
    Custom Lightweight Agent — Works with ANY model from Groq, Google AI Studio, or Cerebras
</div>
""", unsafe_allow_html=True)
