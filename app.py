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

st.set_page_config(page_title="AI Agent Playground", page_icon="🤖", layout="wide", initial_sidebar_state="expanded")

# ============================================================
# SIR SHAN'S CHROME-HIDING CSS — VERIFIED WORKING
# ============================================================
_HIDE_ALL_STREAMLIT_CHROME = """
<style>
    #MainMenu {visibility: hidden !important; display: none !important;}
    [data-testid="stMainMenu"] {display: none !important;}
    button[kind="headerNoPadding"] {display: none !important;}

    .stDeployButton {display: none !important;}
    [data-testid="stDeployButton"] {display: none !important;}
    a[href*="/fork"] {display: none !important;}

    a[title="View source"] {display: none !important;}
    a[href*="github.com"] svg {display: none !important;}
    [data-testid="stHeaderActionElements"] {display: none !important;}

    [data-testid="stToolbar"] {display: none !important;}
    header [data-testid="stHeader"] {display: none !important;}
    .stApp > header {display: none !important;}

    footer {display: none !important;}
    .stApp > footer {display: none !important;}
    [data-testid="stFooter"] {display: none !important;}
    [data-testid="stFooterV2"] {display: none !important;}

    [data-testid="stDecoration"] {display: none !important;}
    .stDecoration {display: none !important;}
    img[alt*="Streamlit"] {display: none !important;}
    img[alt*="streamlit"] {display: none !important;}
    img[src*="streamlit"] {display: none !important;}

    a[href*="streamlit.io"] {display: none !important;}

    .stApp {padding-bottom: 0 !important;}
    .reportview-container {padding-bottom: 0 !important;}
</style>
"""
st.markdown(_HIDE_ALL_STREAMLIT_CHROME, unsafe_allow_html=True)

# ============================================================
# CUSTOM THEME CSS
# ============================================================
st.markdown("""
<style>
.stApp{background:linear-gradient(135deg,#0a0e27 0%,#1a1f3a 50%,#0f172a 100%)!important}
.main .block-container{padding-top:0.5rem!important;padding-bottom:2rem!important;max-width:1000px!important}

.hero-box{text-align:center;padding:1.5rem 1rem 1rem 1rem;margin-bottom:1.5rem}
.hero-title{font-size:2.8rem;font-weight:900;background:linear-gradient(135deg,#00d4ff 0%,#00ff88 50%,#00d4ff 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;letter-spacing:-2px;margin-bottom:0.3rem;line-height:1.1}
.hero-subtitle{color:#94a3b8;font-size:1.05rem;font-weight:400}

.glass-card{background:rgba(30,41,59,0.6)!important;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border:1px solid rgba(148,163,184,0.12);border-radius:20px;padding:1.5rem;margin-bottom:1.2rem;box-shadow:0 8px 32px rgba(0,0,0,0.2)}
.card-header{color:#f1f5f9;font-size:1.15rem;font-weight:700;margin-bottom:1.2rem;display:flex;align-items:center;gap:0.6rem;padding-bottom:0.8rem;border-bottom:1px solid rgba(148,163,184,0.1)}

.badge{display:inline-block;padding:0.3rem 0.9rem;border-radius:999px;font-size:0.75rem;font-weight:700;letter-spacing:0.5px;text-transform:uppercase}
.badge-locked{background:rgba(239,68,68,0.15);color:#f87171;border:1px solid rgba(239,68,68,0.25)}
.badge-ready{background:rgba(34,197,94,0.15);color:#4ade80;border:1px solid rgba(34,197,94,0.25)}
.badge-warn{background:rgba(234,179,8,0.15);color:#facc15;border:1px solid rgba(234,179,8,0.25)}

.stButton>button{background:linear-gradient(135deg,#0ea5e9 0%,#06b6d4 100%)!important;color:white!important;font-weight:700!important;border:none!important;border-radius:12px!important;padding:0.65rem 1.5rem!important;font-size:0.95rem!important;transition:all 0.2s ease!important;box-shadow:0 4px 15px rgba(14,165,233,0.25)!important}
.stButton>button:hover{transform:translateY(-2px)!important;box-shadow:0 8px 25px rgba(14,165,233,0.4)!important}
.stButton>button:active{transform:translateY(0)!important}

div[data-testid="stTextInput"] input{background:rgba(15,23,42,0.8)!important;border:1.5px solid rgba(148,163,184,0.15)!important;border-radius:12px!important;color:#e2e8f0!important;padding:0.7rem 1rem!important;font-size:0.9rem!important}
div[data-testid="stTextInput"] input:focus{border-color:#0ea5e9!important;box-shadow:0 0 0 4px rgba(14,165,233,0.1)!important;outline:none!important}

div[data-testid="stRadio"]>div{background:rgba(15,23,42,0.5);border-radius:14px;padding:0.6rem;border:1px solid rgba(148,163,184,0.1)}
div[data-testid="stRadio"] label{color:#cbd5e1!important;font-weight:500!important}

div[data-testid="stSelectbox"]>div>div{background:rgba(15,23,42,0.8)!important;border:1.5px solid rgba(148,163,184,0.15)!important;border-radius:12px!important;color:#e2e8f0!important}

.chat-user{background:linear-gradient(135deg,rgba(14,165,233,0.15) 0%,rgba(6,182,212,0.1) 100%);border-left:3px solid #0ea5e9;padding:1rem 1.2rem;border-radius:0 16px 16px 0;margin-bottom:0.8rem;color:#e2e8f0}
.chat-assistant{background:linear-gradient(135deg,rgba(34,197,94,0.1) 0%,rgba(16,185,129,0.05) 100%);border-left:3px solid #22c55e;padding:1rem 1.2rem;border-radius:0 16px 16px 0;margin-bottom:0.8rem;color:#e2e8f0}

.locked-box{background:rgba(15,23,42,0.5);border:2px dashed rgba(148,163,184,0.15);border-radius:20px;padding:3rem 2rem;text-align:center}
.locked-icon{font-size:3.5rem;margin-bottom:1rem;opacity:0.8}
.locked-title{font-size:1.3rem;font-weight:700;color:#e2e8f0;margin-bottom:0.5rem}
.locked-text{color:#94a3b8;margin-bottom:1.5rem}
.locked-item{display:flex;align-items:center;justify-content:center;gap:0.5rem;color:#cbd5e1;padding:0.4rem 0;font-size:0.95rem}

[data-testid="stSidebar"]{background:rgba(10,14,39,0.95)!important;border-right:1px solid rgba(148,163,184,0.08)}
[data-testid="stSidebar"] .block-container{padding-top:1.5rem!important}
[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3{color:#f1f5f9!important}
[data-testid="stSidebar"] p,[data-testid="stSidebar"] li{color:#94a3b8!important}

hr{border-color:rgba(148,163,184,0.1)!important}
::-webkit-scrollbar{width:6px}
::-webkit-scrollbar-track{background:rgba(15,23,42,0.5)}
::-webkit-scrollbar-thumb{background:rgba(148,163,184,0.2);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:rgba(148,163,184,0.4)}
</style>
""", unsafe_allow_html=True)

# ============================================================
# JS MUTATIONOBSERVER — NUCLEAR BACKUP
# ============================================================
st.components.v1.html("""
<script>
(function(){
    function nuke(){
        document.querySelectorAll('header,#MainMenu,.stDeployButton,[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"],footer,[data-testid="stFooter"],[data-testid="stFooterV2"],.stAppToolbar,[data-testid="stAppToolbar"],.stActionButton,[data-testid="manage-app-button"],.manage-app-btn').forEach(function(el){el.remove();});
        document.querySelectorAll('a,button,div,span').forEach(function(el){
            var t=el.textContent?el.textContent.trim():'';
            if(t==='Fork'||t==='Deploy'||t==='Share'||t==='Manage app'){el.remove();}
        });
        document.querySelectorAll('a[href*="/fork"],a[href*="github.com"] svg,a[title="View source"],a[href*="streamlit.io"]').forEach(function(el){el.remove();});
    }
    nuke();
    var obs=new MutationObserver(function(muts){nuke();});
    obs.observe(document.body,{childList:true,subtree:true});
    setInterval(nuke,300);
})();
</script>
""", height=0)

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
if "serp_key" not in st.session_state:
    st.session_state.serp_key = ""
if "weather_key" not in st.session_state:
    st.session_state.weather_key = ""

# ============================================================
# SIDEBAR — INSTRUCTIONS ONLY
# ============================================================
st.sidebar.markdown("## 📖 Instructions")
st.sidebar.markdown("""
<div style="color:#94a3b8;font-size:0.9rem;line-height:1.7">
<b style="color:#f1f5f9">How to use this agent:</b><br>
1. Select <b>Groq</b> or <b>Google AI Studio</b><br>
2. Enter the API key for your chosen provider<br>
3. Click <b>Load Models</b> to fetch available models<br>
4. Pick a model from the dropdown<br>
5. Enter <b>SerpAPI</b> and <b>WeatherAPI</b> keys<br>
6. Start chatting with your AI agent!<br><br>

<b style="color:#f1f5f9">What the agent can do:</b><br>
🔍 <b>Web Search</b> — Find current info from the internet<br>
🌤️ <b>Weather Lookup</b> — Get real-time weather for any city<br>
🧠 <b>Reasoning</b> — Combine tools to answer complex questions<br><br>

<b style="color:#f1f5f9">Example questions:</b><br>
• "Find the capital of India and then find its current weather."<br>
• "What is the weather in Lahore right now?"<br>
• "Search for the latest news about AI and summarize it."
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="text-align:center;color:#64748b;font-size:0.8rem">
    🤖 Built by <b style="color:#94a3b8">Saad Maqbool</b><br>
    🎓 Bano Qabil Agentic AI<br>
    📍 Lytton Road, Lahore
</div>
""", unsafe_allow_html=True)

# ============================================================
# MAIN AREA — HERO
# ============================================================
st.markdown("""
<div class="hero-box">
    <div class="hero-title">🤖 AI Agent Playground</div>
    <div class="hero-subtitle">ReAct Agent powered by Groq or Google AI Studio — you choose the brain</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# MAIN AREA — CONFIG CARD
# ============================================================
with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-header">⚙️ Configuration</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        provider = st.radio("Select LLM Provider", ["Groq", "Google AI Studio"], horizontal=True, key="provider_radio")
        st.session_state.provider = provider

        if provider == "Groq":
            st.markdown("<small style='color:#94a3b8'>Get free key: console.groq.com | $200 free credits</small>", unsafe_allow_html=True)
            api_key_input = st.text_input("🔐 Groq API Key", type="password", key="groq_key_input", help="Your key stays in this browser session only.")
            load_btn_label = "🔍 Load Groq Models"
            load_btn_key = "load_groq"
        else:
            st.markdown("<small style='color:#94a3b8'>Get free key: aistudio.google.com | Generous free tier</small>", unsafe_allow_html=True)
            api_key_input = st.text_input("🔐 Google AI Studio API Key", type="password", key="google_key_input", help="Your key stays in this browser session only.")
            load_btn_label = "🔍 Load Gemini Models"
            load_btn_key = "load_google"

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
                                chat_models = [m for m in models if any(x in m.lower() for x in ["gpt-oss", "llama", "mixtral", "gemma", "qwen"])]
                                st.session_state.available_models = chat_models if chat_models else models
                                st.session_state.provider_key = api_key_input
                                st.session_state.provider_confirmed = True
                                st.success(f"✅ Loaded {len(st.session_state.available_models)} models")
                            else:
                                st.error(f"❌ Failed: HTTP {resp.status_code}. Check your key.")
                        else:
                            resp = requests.get(
                                "https://generativelanguage.googleapis.com/v1beta/models",
                                headers={"x-goog-api-key": api_key_input},
                                timeout=15
                            )
                            if resp.status_code == 200:
                                data = resp.json()
                                models = [m["name"].replace("models/", "") for m in data.get("models", []) if "generateContent" in m.get("supportedGenerationMethods", [])]
                                st.session_state.available_models = models
                                st.session_state.provider_key = api_key_input
                                st.session_state.provider_confirmed = True
                                st.success(f"✅ Loaded {len(st.session_state.available_models)} models")
                            else:
                                st.error(f"❌ Failed: HTTP {resp.status_code}. Check your key.")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

    with col2:
        if st.session_state.provider_confirmed and st.session_state.available_models:
            st.markdown("<div style='margin-top:0.3rem'></div>", unsafe_allow_html=True)
            selected_model = st.selectbox("🎯 Select Model", st.session_state.available_models, key="model_select")
            safe_model = html.escape(selected_model)
            st.session_state.selected_model = selected_model
            st.markdown(f"<span class='badge badge-ready'>Ready</span> &nbsp; <b style='color:#e2e8f0'>{safe_model}</b>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='margin-top:0.3rem'></div>", unsafe_allow_html=True)
            st.selectbox("🎯 Select Model", ["Load models first"], disabled=True, key="model_select_disabled")
            st.markdown("<span class='badge badge-locked'>Locked</span> &nbsp; <span style='color:#94a3b8'>Load models to unlock</span>", unsafe_allow_html=True)

        st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)
        serp_key_input = st.text_input("🔧 SerpAPI Key", type="password", key="serp_key", help="serpapi.com | 100 searches/month free")
        weather_key_input = st.text_input("🔧 WeatherAPI Key", type="password", key="weather_key", help="weatherapi.com | 1M calls/month free")
        st.session_state.serp_key = serp_key_input
        st.session_state.weather_key = weather_key_input

    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# CHECK CONFIG STATUS
# ============================================================
missing = []
if not st.session_state.provider_confirmed:
    missing.append("LLM Provider API Key (select provider → enter key → Load Models)")
if not st.session_state.selected_model:
    missing.append("A model from the dropdown")
if not st.session_state.serp_key:
    missing.append("SerpAPI Key")
if not st.session_state.weather_key:
    missing.append("WeatherAPI Key")

is_ready = len(missing) == 0

# ============================================================
# MAIN AREA — CHAT CARD
# ============================================================
with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    if is_ready:
        st.markdown('<div class="card-header">💬 Chat with your AI Agent</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:0.8rem;margin-bottom:1rem;flex-wrap:wrap">
            <span class="badge badge-ready">Active</span>
            <span style="color:#94a3b8;font-size:0.9rem">Provider: <b style="color:#e2e8f0">{html.escape(st.session_state.provider)}</b></span>
            <span style="color:#94a3b8;font-size:0.9rem">|</span>
            <span style="color:#94a3b8;font-size:0.9rem">Model: <b style="color:#e2e8f0">{html.escape(st.session_state.selected_model)}</b></span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="card-header">💬 Chat</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="locked-box">
            <div class="locked-icon">🔐</div>
            <div class="locked-title">Agent is Locked</div>
            <div class="locked-text">Complete the configuration above to unlock the chat</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom:0.8rem'></div>", unsafe_allow_html=True)
        for item in missing:
            st.markdown(f"<div class='locked-item'>❌ {item}</div>", unsafe_allow_html=True)
        st.markdown("<div style='margin-top:0.8rem;color:#64748b;font-size:0.85rem;text-align:center'>All services offer free tiers. No credit card required.</div>", unsafe_allow_html=True)

    # ---- Chat history ----
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-user"><b>👤 You:</b><br>{html.escape(msg["content"])}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-assistant"><b>🤖 Agent:</b><br>{html.escape(msg["content"])}</div>', unsafe_allow_html=True)

    # ---- Chat input ----
    user_query = st.chat_input("Ask the agent anything..." if is_ready else "Complete setup to chat...", disabled=not is_ready)

    if user_query and is_ready:
        # SECURITY FIX: Input length validation
        if len(user_query) > 1000:
            st.error("❌ Query too long. Please keep it under 1000 characters.")
        else:
            # SECURITY FIX: Rate limiting — 3 second cooldown
            current_time = time.time()
            if current_time - st.session_state.last_query_time < 3:
                st.warning("⏳ Please wait a few seconds between queries.")
            else:
                st.session_state.last_query_time = current_time
                st.session_state.messages.append({"role": "user", "content": user_query})

                # ---- Build agent if not cached ----
                @st.cache_resource(show_spinner=False)
                def build_agent(provider: str, model: str, provider_key: str, serp_key: str, weather_key: str):
                    os.environ["SERPAPI_API_KEY"] = serp_key

                    if provider == "Groq":
                        llm = ChatGroq(model=model, temperature=0, api_key=provider_key, max_tokens=1024, request_timeout=60)
                    else:
                        llm = ChatGoogleGenerativeAI(model=model, temperature=0, google_api_key=provider_key, max_output_tokens=1024, request_timeout=60)

                    search_wrapper = SerpAPIWrapper(serpapi_api_key=serp_key)
                    search_tool = Tool(
                        name="web_search",
                        func=search_wrapper.run,
                        description="Useful for searching the internet for current information, facts, news, and data."
                    )

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

                    prompt = PromptTemplate.from_template(template)
                    tools = [search_tool, weather_tool]
                    agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
                    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True, max_iterations=10)
                    return agent_executor

                try:
                    with st.spinner("🧠 Agent is thinking..."):
                        agent_executor = build_agent(
                            st.session_state.provider,
                            st.session_state.selected_model,
                            st.session_state.provider_key,
                            st.session_state.serp_key,
                            st.session_state.weather_key
                        )

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
                        safe_answer = html.escape(final_answer)
                        st.markdown(f'<div class="chat-assistant"><b>🤖 Agent:</b><br>{safe_answer}</div>', unsafe_allow_html=True)
                        st.session_state.messages.append({"role": "assistant", "content": final_answer})

                except Exception as e:
                    st.error(f"❌ Agent error: {e}")
                    st.info("Try rephrasing your question or check your API keys.")

    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# FOOTER
# ============================================================
st.markdown("""
<div style="text-align:center;color:#64748b;font-size:0.8rem;margin-top:2rem">
    🤖 Built with LangChain + Groq/Google AI Studio + Streamlit | BYOK | Free tier friendly
</div>
""", unsafe_allow_html=True)
