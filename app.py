import streamlit as st
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SerpAPIWrapper
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.tools import Tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
import requests
import os
import html
import time
import traceback
import sys
from io import StringIO

# ============================================================
# ERROR HANDLING — SENIOR DEV: NEVER SHOW RAW TRACEBACK TO USER
# ============================================================

def friendly_error(err: Exception, search_tool: str = "", weather_tool: str = "") -> str:
    """Map any exception to a human-friendly, actionable message.
    
    search_tool and weather_tool prevent false positives — e.g. blaming DuckDuckGo
    when Tavily is actually selected (the traceback contains ALL import names).
    """
    s = str(err).lower()
    tb = traceback.format_exc().lower()

    # === HIGH CONFIDENCE: check error message FIRST ===
    # timedelta.format is a secondary error triggered when an incompatible model
    # (e.g. gpt-oss, qwen on Groq) tries to use tools. The primary error is model
    # incompatibility, but LangChain's internal retry/timeout code crashes with
    # timedelta.format before the real error surfaces. We detect BOTH patterns.
    if "unsupported format string" in s and "timedelta" in s:
        return "This model does not support tool calling. Try a different model like llama-3.1-8b-instant, mixtral-8x7b, or gemma-7b-it."
    if "deadline exceeded" in s:
        return "The LLM took too long to respond. Try a simpler question or check your connection."
    if any(x in s for x in ["401", "unauthorized", "invalid api key"]):
        return "API key is invalid or expired. Please check your key and try again."
    if any(x in s for x in ["403", "forbidden", "permission denied"]):
        return "API access denied. Your key may not have permission for this model."
    if any(x in s for x in ["429", "rate limit", "too many requests", "quota exceeded"]):
        return "Rate limit hit. Too many requests. Wait 30 seconds and try again."
    if any(x in s for x in ["timeout", "timed out", "connecttimeout"]):
        return "Request timed out. The server or tool took too long. Try a simpler question."
    if any(x in s for x in ["connection error", "connection refused", "name resolution", "dns", "network"]):
        return "Network error. Please check your internet connection and try again."
    if "model not found" in s or "not found" in s:
        return "The selected model is not available. Try loading models again or pick a different one."

    # === TOOL ERRORS — only blame the tool that is ACTUALLY selected ===
    # (traceback contains ALL import names, so we must NOT check tb for these)
    if search_tool == "DuckDuckGo (Free)" and ("duckduckgo" in s or "ddg" in s):
        return "DuckDuckGo search failed (rate limit or blocked). Try again in a few seconds or switch to SerpAPI/Tavily."
    if search_tool == "SerpAPI" and ("serpapi" in s or "serp_api" in s):
        return "SerpAPI search failed. Check your SerpAPI key or try DuckDuckGo (free, no key)."
    if search_tool == "Tavily" and "tavily" in s:
        return "Tavily search failed. Check your Tavily API key or try DuckDuckGo (free, no key)."
    if weather_tool == "WeatherAPI" and ("weatherapi" in s or "weather api" in s):
        return "WeatherAPI failed. Check your key or the city name. Try OpenWeatherMap as alternative."
    if weather_tool == "OpenWeatherMap" and ("openweathermap" in s or "open weather" in s):
        return "OpenWeatherMap failed. Check your key or the city name. Try WeatherAPI as alternative."

    # === FALLBACK: check combined (error + traceback) for remaining patterns ===
    combined = s + " " + tb

    if "iteration" in combined or "max iteration" in combined or "time limit" in combined:
        return "The agent took too many steps without finding an answer. Try a more specific question."
    if "parsing" in combined or "could not parse" in combined or "output parser" in combined:
        return "The agent could not understand the LLM response. Try rephrasing your question."
    if "action input" in combined or "invalid action" in combined:
        return "The agent made an invalid tool call. Try rephrasing your question."
    if "tool choice" in combined or "model called a tool" in combined:
        return "This model does not support tool calling. Try a different model like llama-3.1-8b-instant, mixtral-8x7b, or gemini-1.5-flash."

    # Generic fallback
    return f"Something went wrong: {str(err)[:200]}. Try rephrasing or check your API keys."


# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(page_title="AI Agent Playground", page_icon="🤖", layout="wide")

# ============================================================
# HIDE STREAMLIT CLOUD CHROME + SIDEBAR — CSS ONLY
# ============================================================
st.markdown("""
<style>
    header {display: none !important;}
    [data-testid="stHeader"] {display: none !important;}
    [data-testid="stHeaderActionElements"] {display: none !important;}
    button[kind="headerNoPadding"] {display: none !important;}
    [data-testid="stSidebar"] {display: none !important;}
    [data-testid="stSidebarCollapsedControl"] {display: none !important;}
    .stDeployButton {display: none !important;}
    [data-testid="stDeployButton"] {display: none !important;}
    [data-testid="manage-app-button"] {display: none !important;}
    a[href*="/fork"] {display: none !important;}
    a[title="View source"] {display: none !important;}
    a[href*="github.com"] svg {display: none !important;}
    footer {display: none !important;}
    .stApp > footer {display: none !important;}
    [data-testid="stFooter"] {display: none !important;}
    [data-testid="stFooterV2"] {display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}
    img[alt*="Streamlit"] {display: none !important;}
    img[alt*="streamlit"] {display: none !important;}
    img[src*="streamlit"] {display: none !important;}
    a[href*="streamlit.io"] {display: none !important;}

    .stApp{background:linear-gradient(135deg,#0a0e27 0%,#1a1f3a 50%,#0f172a 100%)!important}
    .main .block-container{padding-top:0.5rem!important;padding-bottom:2rem!important;max-width:1000px!important}

    .hero-box{text-align:center;padding:1.2rem 1rem 0.5rem 1rem;margin-bottom:0.3rem}
    .hero-title{font-size:2.6rem;font-weight:900;background:linear-gradient(135deg,#00d4ff 0%,#00ff88 50%,#00d4ff 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;letter-spacing:-2px;margin-bottom:0.3rem;line-height:1.1}
    .hero-subtitle{color:#94a3b8;font-size:1rem;font-weight:400}

    .section-header{color:#f1f5f9;font-size:1.2rem;font-weight:700;margin-bottom:0.8rem;display:flex;align-items:center;gap:0.5rem;padding-bottom:0.5rem;border-bottom:1px solid rgba(148,163,184,0.15)}

    .badge{display:inline-block;padding:0.25rem 0.8rem;border-radius:999px;font-size:0.7rem;font-weight:700;letter-spacing:0.5px;text-transform:uppercase}
    .badge-locked{background:rgba(239,68,68,0.15);color:#f87171;border:1px solid rgba(239,68,68,0.25)}
    .badge-ready{background:rgba(34,197,94,0.15);color:#4ade80;border:1px solid rgba(34,197,94,0.25)}
    .badge-free{background:rgba(59,130,246,0.15);color:#60a5fa;border:1px solid rgba(59,130,246,0.25)}
    .badge-error{background:rgba(239,68,68,0.15);color:#f87171;border:1px solid rgba(239,68,68,0.25)}

    .stButton>button{background:linear-gradient(135deg,#0ea5e9 0%,#06b6d4 100%)!important;color:white!important;font-weight:700!important;border:none!important;border-radius:12px!important;padding:0.6rem 1.4rem!important;font-size:0.9rem!important;transition:all 0.2s ease!important;box-shadow:0 4px 15px rgba(14,165,233,0.25)!important}
    .stButton>button:hover{transform:translateY(-2px)!important;box-shadow:0 8px 25px rgba(14,165,233,0.4)!important}

    div[data-testid="stTextInput"] input{background:rgba(15,23,42,0.8)!important;border:1.5px solid rgba(148,163,184,0.15)!important;border-radius:12px!important;color:#e2e8f0!important;padding:0.65rem 0.9rem!important;font-size:0.88rem!important}
    div[data-testid="stTextInput"] input:focus{border-color:#0ea5e9!important;box-shadow:0 0 0 4px rgba(14,165,233,0.1)!important;outline:none!important}

    div[data-testid="stRadio"]>div{background:rgba(15,23,42,0.5);border-radius:14px;padding:0.5rem;border:1px solid rgba(148,163,184,0.1)}
    div[data-testid="stRadio"] label{color:#cbd5e1!important;font-weight:500!important}

    div[data-testid="stSelectbox"]>div>div{background:rgba(15,23,42,0.8)!important;border:1.5px solid rgba(148,163,184,0.15)!important;border-radius:12px!important;color:#e2e8f0!important}

    .chat-user{background:linear-gradient(135deg,rgba(14,165,233,0.15) 0%,rgba(6,182,212,0.1) 100%);border-left:3px solid #0ea5e9;padding:0.9rem 1.1rem;border-radius:0 14px 14px 0;margin-bottom:0.7rem;color:#e2e8f0}
    .chat-assistant{background:linear-gradient(135deg,rgba(34,197,94,0.1) 0%,rgba(16,185,129,0.05) 100%);border-left:3px solid #22c55e;padding:0.9rem 1.1rem;border-radius:0 14px 14px 0;margin-bottom:0.7rem;color:#e2e8f0}
    .chat-error{background:linear-gradient(135deg,rgba(239,68,68,0.15) 0%,rgba(220,38,38,0.05) 100%);border-left:3px solid #ef4444;padding:0.9rem 1.1rem;border-radius:0 14px 14px 0;margin-bottom:0.7rem;color:#e2e8f0}

    .locked-box{background:rgba(15,23,42,0.5);border:2px dashed rgba(148,163,184,0.15);border-radius:18px;padding:1.5rem 1rem;text-align:center;margin:0.5rem 0}
    .locked-icon{font-size:2.5rem;margin-bottom:0.5rem;opacity:0.8}
    .locked-title{font-size:1.1rem;font-weight:700;color:#e2e8f0;margin-bottom:0.3rem}
    .locked-text{color:#94a3b8;margin-bottom:0.8rem;font-size:0.85rem}
    .locked-item{display:flex;align-items:center;justify-content:center;gap:0.4rem;color:#cbd5e1;padding:0.25rem 0;font-size:0.85rem}

    hr{border-color:rgba(148,163,184,0.1)!important;margin:1rem 0!important}
    ::-webkit-scrollbar{width:6px}
    ::-webkit-scrollbar-track{background:rgba(15,23,42,0.5)}
    ::-webkit-scrollbar-thumb{background:rgba(148,163,184,0.2);border-radius:3px}

    .stExpander{border:1px solid rgba(148,163,184,0.1)!important;border-radius:12px!important;background:rgba(15,23,42,0.4)!important}
    .stExpander > details > summary{color:#e2e8f0!important;font-weight:600!important}
</style>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE
# ============================================================
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
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent_executor" not in st.session_state:
    st.session_state.agent_executor = None
if "provider" not in st.session_state:
    st.session_state.provider = "Groq"
if "show_instructions" not in st.session_state:
    st.session_state.show_instructions = False
if "build_error" not in st.session_state:
    st.session_state.build_error = None

# ============================================================
# MAIN AREA — HERO
# ============================================================
st.markdown("""
<div class="hero-box">
    <div class="hero-title">🤖 AI Agent Playground</div>
    <div class="hero-subtitle">ReAct Agent powered by Groq, Google AI Studio, Alibaba Qwen, or OpenRouter — you choose the brain</div>
    <div style="color:#64748b;font-size:0.85rem;margin-top:0.5rem">👨‍💻 Built by <b style="color:#94a3b8">Saad Maqbool</b> | 🎓 Bano Qabil Agentic AI | 📍 Lytton Road, Lahore</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# INSTRUCTIONS TOGGLE
# ============================================================
if st.button("📖 View Instructions", key="btn_instructions"):
    st.session_state.show_instructions = not st.session_state.show_instructions

if st.session_state.show_instructions:
    with st.expander("📖 How to Use", expanded=True):
        st.markdown("""
        <div style="color:#94a3b8;font-size:0.9rem;line-height:1.7">
        <b style="color:#f1f5f9">Step-by-step setup:</b><br>
        1. Select your LLM provider (Groq, Google AI Studio, Alibaba Qwen, or OpenRouter)<br>
        2. Select your Search tool (SerpAPI, DuckDuckGo, or Tavily)<br>
        3. Select your Weather tool (WeatherAPI or OpenWeatherMap)<br>
        4. Paste your API keys and click <b>Load Models</b><br>
        5. Choose a model from the dropdown that appears<br>
        6. Type your question and let the agent work!<br><br>

        <b style="color:#f1f5f9">Compatible models:</b><br>
        • <b>Groq</b> — llama, mixtral, gemma families (avoid gpt-oss and qwen, they do not support ReAct)<br>
        • <b>Google AI Studio</b> — gemini-1.5-flash, gemini-1.5-pro (avoid embedding models)<br>
        • <b>Alibaba Qwen</b> — qwen-turbo, qwen-plus, qwen-max (avoid embedding models)<br>
        • <b>OpenRouter</b> — stealth/ox-alpha (free, 1M context, agentic) | meta-llama/llama-3.1-8b-instruct | mistralai/mixtral-8x7b-instruct<br><br>

        <b style="color:#f1f5f9">Available tools:</b><br>
        🔍 <b>Web Search</b> — SerpAPI | DuckDuckGo (completely free) | Tavily<br>
        🌤️ <b>Weather Lookup</b> — WeatherAPI | OpenWeatherMap<br>
        🧠 <b>Chain-of-Thought</b> — The agent reasons step-by-step using ReAct pattern<br><br>

        <b style="color:#f1f5f9">Try these:</b><br>
        • "What is the weather in Dubai right now?"<br>
        • "Find the capital of France and tell me its weather"<br>
        • "Search latest AI news and summarize in 3 bullet points"
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# MAIN AREA — CONFIG SECTION
# ============================================================
st.markdown('<div class="section-header">⚙️ Configuration</div>', unsafe_allow_html=True)

# --- LLM Provider ---
provider = st.radio("Select LLM Provider", ["Groq", "Google AI Studio", "Alibaba Qwen", "OpenRouter"], horizontal=True, key="provider_radio")
st.session_state.provider = provider

# --- Search Tool ---
search_tool_choice = st.radio("Select Search Tool", ["SerpAPI", "DuckDuckGo (Free)", "Tavily"], horizontal=True, key="search_radio")

# --- Weather Tool ---
weather_tool_choice = st.radio("Select Weather Tool", ["WeatherAPI", "OpenWeatherMap"], horizontal=True, key="weather_radio")

col1, col2 = st.columns([1, 1])

with col1:
    if provider == "Groq":
        st.markdown("<small style='color:#94a3b8'>Get key: console.groq.com | Free tier available</small>", unsafe_allow_html=True)
        api_key_input = st.text_input("🔐 Groq API Key", type="password", key="groq_key_input", help="Your key stays in this browser session only.")
        load_btn_label = "🔍 Load Groq Models"
        load_btn_key = "load_groq"
    elif provider == "Google AI Studio":
        st.markdown("<small style='color:#94a3b8'>Get key: aistudio.google.com | Generous free tier</small>", unsafe_allow_html=True)
        api_key_input = st.text_input("🔐 Google AI Studio API Key", type="password", key="google_key_input", help="Your key stays in this browser session only.")
        load_btn_label = "🔍 Load Gemini Models"
        load_btn_key = "load_google"
    elif provider == "Alibaba Qwen":
        st.markdown("<small style='color:#94a3b8'>Get key: dashscope.aliyun.com | Sir Shan has credits</small>", unsafe_allow_html=True)
        api_key_input = st.text_input("🔐 Alibaba DashScope API Key", type="password", key="qwen_key_input", help="Your key stays in this browser session only.")
        load_btn_label = "🔍 Load Qwen Models"
        load_btn_key = "load_qwen"
    else:  # OpenRouter
        st.markdown("<small style='color:#94a3b8'>Get key: openrouter.ai | Free tier available (ox-alpha currently free)</small>", unsafe_allow_html=True)
        api_key_input = st.text_input("🔐 OpenRouter API Key", type="password", key="openrouter_key_input", help="Your key stays in this browser session only.")
        load_btn_label = "🔍 Load OpenRouter Models"
        load_btn_key = "load_openrouter"

    if st.button(load_btn_label, key=load_btn_key):
        if not api_key_input:
            st.error("❌ Please enter your API key first.")
        else:
            with st.spinner("Fetching models..."):
                try:
                    if provider == "Groq":
                        resp = requests.get(
                            "https://api.groq.com/openai/v1/models",
                            headers={"Authorization": f"Bearer {api_key_input}"},
                            timeout=15
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            models = [m["id"] for m in data.get("data", [])]
                            chat_models = [m for m in models if any(x in m.lower() for x in ["llama", "mixtral", "gemma"])]
                            st.session_state.available_models = chat_models if chat_models else models
                            st.session_state.provider_key = api_key_input
                            st.session_state.provider_confirmed = True
                            st.session_state.build_error = None
                            st.success(f"✅ Loaded {len(st.session_state.available_models)} models")
                        else:
                            st.error(f"❌ Failed: HTTP {resp.status_code}. Check your key.")
                    elif provider == "Alibaba Qwen":
                        try:
                            resp = requests.get(
                                "https://dashscope.aliyuncs.com/api/v1/models",
                                headers={"Authorization": f"Bearer {api_key_input}"},
                                timeout=15
                            )
                            if resp.status_code == 200:
                                data = resp.json()
                                models = [m.get("id", m.get("name", "")) for m in data.get("data", [])]
                                # Only include Qwen chat models, exclude embedding
                                qwen_models = [m for m in models if m and "qwen" in m.lower() and "embedding" not in m.lower()]
                                st.session_state.available_models = qwen_models if qwen_models else models
                            else:
                                st.session_state.available_models = ["qwen-turbo", "qwen-plus", "qwen-max", "qwen-max-longcontext"]
                        except Exception:
                            st.session_state.available_models = ["qwen-turbo", "qwen-plus", "qwen-max", "qwen-max-longcontext"]
                        st.session_state.provider_key = api_key_input
                        st.session_state.provider_confirmed = True
                        st.session_state.build_error = None
                        st.success(f"✅ Loaded {len(st.session_state.available_models)} Qwen models")
                    elif provider == "Google AI Studio":
                        resp = requests.get(
                            "https://generativelanguage.googleapis.com/v1beta/models",
                            headers={"x-goog-api-key": api_key_input},
                            timeout=15
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            models = [m["name"].replace("models/", "") for m in data.get("models", []) if "generateContent" in m.get("supportedGenerationMethods", [])]
                            # Only include Gemini chat models, exclude embedding/vision-only
                            chat_models = [m for m in models if "gemini" in m.lower() and "embedding" not in m.lower()]
                            st.session_state.available_models = chat_models if chat_models else models
                            st.session_state.provider_key = api_key_input
                            st.session_state.provider_confirmed = True
                            st.session_state.build_error = None
                            st.success(f"✅ Loaded {len(st.session_state.available_models)} models")
                        else:
                            st.error(f"❌ Failed: HTTP {resp.status_code}. Check your key.")
                    else:  # OpenRouter
                        resp = requests.get(
                            "https://openrouter.ai/api/v1/models",
                            headers={"Authorization": f"Bearer {api_key_input}"},
                            timeout=15
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            models = [m["id"] for m in data.get("data", []) if m.get("id")]
                            # Pin stealth/ox-alpha to top, then filter for chat models
                            ox_first = []
                            chat_models = []
                            for m in models:
                                if "stealth/ox-alpha" in m:
                                    ox_first.append(m)
                                elif any(x in m.lower() for x in ["llama", "mixtral", "mistral", "gemma", "qwen", "claude", "gpt"]):
                                    chat_models.append(m)
                            st.session_state.available_models = ox_first + chat_models if (ox_first or chat_models) else models
                            st.session_state.provider_key = api_key_input
                            st.session_state.provider_confirmed = True
                            st.session_state.build_error = None
                            st.success(f"✅ Loaded {len(st.session_state.available_models)} OpenRouter models")
                        else:
                            st.error(f"❌ Failed: HTTP {resp.status_code}. Check your key.")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

with col2:
    if st.session_state.provider_confirmed and st.session_state.available_models:
        selected_model = st.selectbox("🎯 Select Model", st.session_state.available_models, key="model_select")
        safe_model = html.escape(selected_model)
        st.session_state.selected_model = selected_model
        st.markdown(f"<span class='badge badge-ready'>Ready</span> &nbsp; <b style='color:#e2e8f0'>{safe_model}</b>", unsafe_allow_html=True)
    else:
        st.selectbox("🎯 Select Model", ["Load models first"], disabled=True, key="model_select_disabled")
        st.markdown("<span class='badge badge-locked'>Locked</span> &nbsp; <span style='color:#94a3b8'>Load models to unlock</span>", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:0.8rem'></div>", unsafe_allow_html=True)

    serp_key_input = ""
    tavily_key_input = ""
    weather_key_input = ""
    owm_key_input = ""

    if search_tool_choice == "SerpAPI":
        serp_key_input = st.text_input("🔧 SerpAPI Key", type="password", key="serp_key_widget", help="serpapi.com | 100 searches/month free")
    elif search_tool_choice == "Tavily":
        tavily_key_input = st.text_input("🔧 Tavily API Key", type="password", key="tavily_key_widget", help="tavily.com | 1,000 searches/month free")
    else:
        st.markdown("<span class='badge badge-free'>Free</span> &nbsp; <span style='color:#94a3b8'>DuckDuckGo requires no API key</span>", unsafe_allow_html=True)

    if weather_tool_choice == "WeatherAPI":
        weather_key_input = st.text_input("🔧 WeatherAPI Key", type="password", key="weather_key_widget", help="weatherapi.com | 1M calls/month free")
    else:
        owm_key_input = st.text_input("🔧 OpenWeatherMap Key", type="password", key="owm_key_widget", help="openweathermap.org | 1,000 calls/day free")

st.markdown("<hr>", unsafe_allow_html=True)

# ============================================================
# CHECK CONFIG STATUS
# ============================================================
missing = []
if not st.session_state.provider_confirmed:
    missing.append("LLM Provider API Key (select provider → enter key → Load Models)")
if not st.session_state.selected_model:
    missing.append("A model from the dropdown")
if search_tool_choice == "SerpAPI" and not serp_key_input:
    missing.append("SerpAPI Key (or switch to DuckDuckGo/Tavily)")
if search_tool_choice == "Tavily" and not tavily_key_input:
    missing.append("Tavily Key (or switch to SerpAPI/DuckDuckGo)")
if weather_tool_choice == "WeatherAPI" and not weather_key_input:
    missing.append("WeatherAPI Key (or switch to OpenWeatherMap)")
if weather_tool_choice == "OpenWeatherMap" and not owm_key_input:
    missing.append("OpenWeatherMap Key (or switch to WeatherAPI)")

is_ready = len(missing) == 0

# ============================================================
# MAIN AREA — CHAT SECTION
# ============================================================
st.markdown('<div class="section-header">💬 Chat with your AI Agent</div>', unsafe_allow_html=True)

# --- Clear chat button ---
if st.session_state.messages:
    if st.button("🗑️ Clear Chat", key="btn_clear_chat"):
        st.session_state.messages = []
        st.session_state.agent_executor = None
        st.session_state.build_error = None
        st.rerun()

if is_ready:
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:0.7rem;margin-bottom:0.8rem;flex-wrap:wrap">
        <span class="badge badge-ready">Active</span>
        <span style="color:#94a3b8;font-size:0.85rem">Provider: <b style="color:#e2e8f0">{html.escape(st.session_state.provider)}</b></span>
        <span style="color:#94a3b8;font-size:0.85rem">|</span>
        <span style="color:#94a3b8;font-size:0.85rem">Model: <b style="color:#e2e8f0">{html.escape(st.session_state.selected_model)}</b></span>
        <span style="color:#94a3b8;font-size:0.85rem">|</span>
        <span style="color:#94a3b8;font-size:0.85rem">Search: <b style="color:#e2e8f0">{html.escape(search_tool_choice)}</b></span>
        <span style="color:#94a3b8;font-size:0.85rem">|</span>
        <span style="color:#94a3b8;font-size:0.85rem">Weather: <b style="color:#e2e8f0">{html.escape(weather_tool_choice)}</b></span>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="locked-box">
        <div class="locked-icon">🔐</div>
        <div class="locked-title">Agent is Locked</div>
        <div class="locked-text">Complete the configuration above to unlock the chat</div>
    </div>
    """, unsafe_allow_html=True)
    for item in missing:
        st.markdown(f"<div class='locked-item'>❌ {item}</div>", unsafe_allow_html=True)
    st.markdown("<div style='margin-top:0.6rem;color:#64748b;font-size:0.8rem;text-align:center'>All services offer free tiers. No credit card required.</div>", unsafe_allow_html=True)

# ---- Chat history ----
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-user"><b>👤 You:</b><br>{html.escape(msg["content"])}</div>', unsafe_allow_html=True)
    elif msg["role"] == "error":
        st.markdown(f'<div class="chat-error"><b>⚠️ Error:</b><br>{html.escape(msg["content"])}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-assistant"><b>🤖 Agent:</b><br>{html.escape(msg["content"])}</div>', unsafe_allow_html=True)

# ---- Chat input only when ready ----
if is_ready:
    user_query = st.chat_input("Ask the agent anything...")

    if user_query:
        if len(user_query) > 1000:
            st.session_state.messages.append({"role": "error", "content": "Query too long. Please keep it under 1000 characters."})
            st.rerun()
        else:
            current_time = time.time()
            if current_time - st.session_state.last_query_time < 3:
                st.session_state.messages.append({"role": "error", "content": "Please wait a few seconds between queries."})
                st.rerun()
            else:
                st.session_state.last_query_time = current_time
                st.session_state.messages.append({"role": "user", "content": user_query})

                # ============================================================
                # BUILD AGENT — WITH COMPREHENSIVE ERROR HANDLING
                # ============================================================
                @st.cache_resource(show_spinner=False)
                def build_agent(provider: str, model: str, provider_key: str, search_tool_choice: str, weather_tool_choice: str, serp_key: str, tavily_key: str, weather_key: str, owm_key: str):
                    try:
                        # --- LLM — NO request_timeout (causes timedelta.format crash) ---
                        if provider == "Groq":
                            llm = ChatGroq(
                                model=model,
                                temperature=0,
                                api_key=provider_key,
                                max_tokens=1024
                            )
                        elif provider == "Alibaba Qwen":
                            llm = ChatTongyi(
                                model=model,
                                dashscope_api_key=provider_key,
                                temperature=0
                            )
                        elif provider == "OpenRouter":
                            llm = ChatOpenAI(
                                model=model,
                                openai_api_key=provider_key,
                                openai_api_base="https://openrouter.ai/api/v1",
                                temperature=0,
                                max_tokens=1024,
                                default_headers={
                                    "HTTP-Referer": "https://single-agent.streamlit.app",
                                    "X-Title": "AI Agent Playground"
                                }
                            )
                        else:
                            llm = ChatGoogleGenerativeAI(
                                model=model,
                                temperature=0,
                                google_api_key=provider_key,
                                max_output_tokens=1024
                            )
                    except Exception as e:
                        raise RuntimeError(f"Failed to initialize LLM: {friendly_error(e, search_tool_choice, weather_tool_choice)}") from e

                    # --- Search Tool — wrapped in try-except ---
                    try:
                        if search_tool_choice == "SerpAPI":
                            if not serp_key:
                                raise ValueError("SerpAPI key is empty.")
                            os.environ["SERPAPI_API_KEY"] = serp_key
                            search_wrapper = SerpAPIWrapper(serpapi_api_key=serp_key)
                            search_tool = Tool(
                                name="web_search",
                                func=search_wrapper.run,
                                description="Useful for searching the internet for current information, facts, news, and data."
                            )
                        elif search_tool_choice == "Tavily":
                            if not tavily_key:
                                raise ValueError("Tavily key is empty.")
                            search_tool = TavilySearchResults(tavily_api_key=tavily_key, max_results=3)
                        else:
                            search_tool = DuckDuckGoSearchRun()
                    except Exception as e:
                        raise RuntimeError(f"Search tool failed: {friendly_error(e, search_tool_choice, weather_tool_choice)}") from e

                    # --- Weather Tool — wrapped in try-except ---
                    try:
                        if weather_tool_choice == "WeatherAPI":
                            if not weather_key:
                                raise ValueError("WeatherAPI key is empty.")
                            def get_weather(city: str) -> str:
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
                        else:
                            if not owm_key:
                                raise ValueError("OpenWeatherMap key is empty.")
                            def get_weather(city: str) -> str:
                                url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={owm_key}&units=metric"
                                try:
                                    resp = requests.get(url, timeout=10)
                                    data = resp.json()
                                    if data.get("cod") != 200:
                                        return f"Could not fetch weather for {city}. {data.get('message', 'Check city name or API key.')}"
                                    main = data["main"]
                                    weather = data["weather"][0]
                                    wind = data["wind"]
                                    return (
                                        f"City: {city}, {data['sys']['country']}\n"
                                        f"Temperature: {main['temp']}°C (feels like {main['feels_like']}°C)\n"
                                        f"Condition: {weather['main']} — {weather['description']}\n"
                                        f"Humidity: {main['humidity']}%\n"
                                        f"Wind: {wind['speed']} m/s"
                                    )
                                except Exception as e:
                                    return f"Error fetching weather: {str(e)}"
                    except Exception as e:
                        raise RuntimeError(f"Weather tool failed: {friendly_error(e, search_tool_choice, weather_tool_choice)}") from e

                    weather_tool = Tool(
                        name="get_weather",
                        func=get_weather,
                        description="Useful for getting current weather information for any city in the world."
                    )

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

                    try:
                        prompt = PromptTemplate.from_template(template)
                        tools = [search_tool, weather_tool]
                        agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
                        agent_executor = AgentExecutor(
                            agent=agent,
                            tools=tools,
                            verbose=True,
                            handle_parsing_errors=True,
                            max_iterations=10
                        )
                    except Exception as e:
                        raise RuntimeError(f"Agent assembly failed: {friendly_error(e, search_tool_choice, weather_tool_choice)}") from e

                    return agent_executor

                # ============================================================
                # EXECUTE QUERY — WITH COMPREHENSIVE ERROR HANDLING
                # ============================================================
                try:
                    with st.spinner("🧠 Agent is thinking..."):
                        agent_executor = build_agent(
                            st.session_state.provider,
                            st.session_state.selected_model,
                            st.session_state.provider_key,
                            search_tool_choice,
                            weather_tool_choice,
                            serp_key_input,
                            tavily_key_input,
                            weather_key_input,
                            owm_key_input
                        )

                        # Capture verbose output
                        old_stdout = sys.stdout
                        sys.stdout = mystdout = StringIO()

                        try:
                            response = agent_executor.invoke({"input": user_query})
                        finally:
                            sys.stdout = old_stdout

                        verbose_output = mystdout.getvalue()

                        if verbose_output:
                            with st.expander("🔍 View Agent's Thought Process", expanded=False):
                                st.text(verbose_output)

                        final_answer = response.get("output", "No answer generated.")
                        if not final_answer or not final_answer.strip():
                            final_answer = "The agent returned an empty response. Try rephrasing your question."

                        safe_answer = html.escape(final_answer)
                        st.session_state.messages.append({"role": "assistant", "content": final_answer})

                except Exception as e:
                    error_msg = friendly_error(e, search_tool_choice, weather_tool_choice)
                    st.session_state.messages.append({"role": "error", "content": error_msg})
                    # Clear cache so next attempt rebuilds fresh
                    try:
                        build_agent.clear()
                    except Exception:
                        pass

                st.rerun()

# ============================================================
# FOOTER
# ============================================================
st.markdown("""
<div style="text-align:center;color:#64748b;font-size:0.78rem;margin-top:1.5rem">
    👨‍💻 <b style="color:#94a3b8">Saad Maqbool</b> | 🎓 Bano Qabil Agentic AI | 📍 Lytton Road, Lahore<br>
    🤖 Built with LangChain + Groq/Google AI Studio/Qwen + Streamlit | BYOK | Free tier friendly
</div>
""", unsafe_allow_html=True)
