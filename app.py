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

st.markdown("""
<style>
header,[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu,.stDeployButton,[data-testid="stStatusWidget"],[data-testid="stBottomBlock"],footer,.streamlit-footer,[data-testid="stFooter"],.stActionButton,[data-testid="stActionButton"],.stAppToolbar,[data-testid="stAppToolbar"],button[kind="header"],.stApp>header,.stApp>div:first-child>div:first-child>div:first-child,a[href*="fork"],a[href*="github.com/streamlit"],button:contains("Deploy"),button:contains("Share"),button:contains("Fork"),button:contains("Manage app"),[data-testid="manage-app-button"],.manage-app-btn,.stAppToolbar_actions,.stAppToolbar_actionIcon{display:none!important;visibility:hidden!important;opacity:0!important;height:0!important;width:0!important;position:absolute!important;pointer-events:none!important;margin:0!important;padding:0!important;border:none!important;overflow:hidden!important}
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
.streamlit-expanderHeader{background:rgba(30,41,59,0.5)!important;border-radius:12px!important;border:1px solid rgba(148,163,184,0.1)!important;color:#e2e8f0!important}
hr{border-color:rgba(148,163,184,0.1)!important}
::-webkit-scrollbar{width:6px}
::-webkit-scrollbar-track{background:rgba(15,23,42,0.5)}
::-webkit-scrollbar-thumb{background:rgba(148,163,184,0.2);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:rgba(148,163,184,0.4)}
</style>
""", unsafe_allow_html=True)

# Nuclear JS to remove any remaining chrome
st.components.v1.html("""
<script>
setInterval(function(){
    document.querySelectorAll('header,[data-testid="stHeader"],[data-testid="stToolbar"],#MainMenu,.stDeployButton,[data-testid="stStatusWidget"],footer,.stAppToolbar,a[href*="fork"],a[href*="github.com/streamlit"]').forEach(function(el){el.remove();});
},500);
</script>
""", height=0)

# ============================================================
# SIDEBAR — INSTRUCTIONS ONLY
# ============================================================
with st.sidebar:
    st.markdown("## 📖 Instructions")
    st.markdown("""
    <div style="color:#94a3b8;line-height:1.9;font-size:0.92rem;">
    <b style="color:#e2e8f0;">How to use this agent:</b><br><br>
    1️⃣ <b style="color:#e2e8f0;">Select Provider</b><br>
    &nbsp;&nbsp;&nbsp;&nbsp;Choose Groq or Google AI Studio<br><br>
    2️⃣ <b style="color:#e2e8f0;">Enter API Key</b><br>
    &nbsp;&nbsp;&nbsp;&nbsp;Get free keys from provider console<br><br>
    3️⃣ <b style="color:#e2e8f0;">Load Models</b><br>
    &nbsp;&nbsp;&nbsp;&nbsp;Click button to fetch available models<br><br>
    4️⃣ <b style="color:#e2e8f0;">Select Model</b><br>
    &nbsp;&nbsp;&nbsp;&nbsp;Pick one from the dropdown<br><br>
    5️⃣ <b style="color:#e2e8f0;">Enter Tool Keys</b><br>
    &nbsp;&nbsp;&nbsp;&nbsp;SerpAPI (search) + WeatherAPI (weather)<br><br>
    6️⃣ <b style="color:#e2e8f0;">Start Chatting!</b><br>
    &nbsp;&nbsp;&nbsp;&nbsp;Ask anything — agent will think and act
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    st.markdown("### 🔧 Capabilities")
    st.markdown("""
    <div style="color:#94a3b8;font-size:0.92rem;line-height:1.9;">
    🔍 <b style="color:#e2e8f0;">Web Search</b> — Find current information<br>
    🌤️ <b style="color:#e2e8f0;">Weather</b> — Check any city's weather<br>
    🧠 <b style="color:#e2e8f0;">Reasoning</b> — Multi-step problem solving
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    st.markdown("### ℹ️ About")
    st.markdown("""
    <div style="color:#64748b;font-size:0.82rem;line-height:1.7;">
    Built by <b style="color:#94a3b8;">Saad Maqbool</b><br>
    Bano Qabil Agentic AI<br>
    Batch BQL6-LR, Lytton Road
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# HERO
# ============================================================
st.markdown('<div class="hero-box"><div class="hero-title">🤖 AI Agent Playground</div><div class="hero-subtitle">ReAct Agent powered by Groq OR Google AI Studio — you choose the brain</div></div>', unsafe_allow_html=True)

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
if "agent_ready" not in st.session_state:
    st.session_state.agent_ready = False

# ============================================================
# CONFIGURATION CARD
# ============================================================
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown('<div class="card-header">⚙️ Configuration</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    provider = st.radio("Select LLM Provider", ["Groq", "Google AI Studio"], horizontal=True, help="Choose one provider. Enter its API key below.")
    
    if provider == "Groq":
        st.markdown('<p style="color:#64748b;font-size:0.82rem;margin-top:-0.5rem;">Get free key: console.groq.com | $200 credits</p>', unsafe_allow_html=True)
        provider_key_input = st.text_input("Groq API Key", type="password", key="groq_key", placeholder="gsk_...", help="Your key stays in this browser only.")
        load_btn_label = "🔍 Load Groq Models"
    else:
        st.markdown('<p style="color:#64748b;font-size:0.82rem;margin-top:-0.5rem;">Get free key: aistudio.google.com</p>', unsafe_allow_html=True)
        provider_key_input = st.text_input("Google AI Studio API Key", type="password", key="google_key", placeholder="Paste your key here", help="Your key stays in this browser only.")
        load_btn_label = "🔍 Load Gemini Models"
    
    if st.button(load_btn_label, use_container_width=True):
        if not provider_key_input:
            st.error("❌ Please enter an API key first.")
        else:
            with st.spinner("Fetching models..."):
                try:
                    if provider == "Groq":
                        resp = requests.get("https://api.groq.com/openai/v1/models", headers={"Authorization": f"Bearer {provider_key_input}"}, timeout=15)
                        if resp.status_code == 200:
                            data = resp.json()
                            models = [m["id"] for m in data.get("data", [])]
                            chat_models = [m for m in models if any(x in m.lower() for x in ["gpt-oss", "llama", "mixtral", "gemma", "qwen"])]
                            st.session_state.available_models = chat_models if chat_models else models
                        else:
                            st.error(f"❌ Failed: HTTP {resp.status_code}")
                    else:
                        resp = requests.get("https://generativelanguage.googleapis.com/v1beta/models", headers={"x-goog-api-key": provider_key_input}, timeout=15)
                        if resp.status_code == 200:
                            data = resp.json()
                            models = [m["name"].replace("models/", "") for m in data.get("models", []) if "generateContent" in m.get("supportedGenerationMethods", [])]
                            st.session_state.available_models = models
                        else:
                            st.error(f"❌ Failed: HTTP {resp.status_code}")
                    
                    if resp.status_code == 200:
                        st.session_state.provider_key = provider_key_input
                        st.session_state.provider_confirmed = True
                        st.success(f"✅ Loaded {len(st.session_state.available_models)} models!")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

with col2:
    if st.session_state.provider_confirmed and st.session_state.available_models:
        selected_model = st.selectbox("Select Model", st.session_state.available_models, key="model_select")
        st.session_state.selected_model = selected_model
        st.markdown(f'<span class="badge badge-ready">✅ Model Ready</span>', unsafe_allow_html=True)
    else:
        st.selectbox("Select Model", ["Load models first..."], disabled=True, key="model_select_disabled")
        st.markdown(f'<span class="badge badge-locked">🔒 Locked</span>', unsafe_allow_html=True)
    
    st.divider()
    
    serp_key = st.text_input("SerpAPI Key", type="password", key="serp_key_input", placeholder="tvly-...", help="serpapi.com | 100 searches/month free")
    weather_key = st.text_input("WeatherAPI Key", type="password", key="weather_key_input", placeholder="Paste key", help="weatherapi.com | 1M calls/month free")
    
    if serp_key and weather_key:
        st.markdown(f'<span class="badge badge-ready">✅ Tools Ready</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="badge badge-warn">⚠️ Tools Incomplete</span>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# CHECK READINESS
# ============================================================
missing = []
if not st.session_state.provider_confirmed:
    missing.append("Select provider and load models")
if not st.session_state.selected_model:
    missing.append("Select a model from dropdown")
if not serp_key:
    missing.append("Enter SerpAPI key")
if not weather_key:
    missing.append("Enter WeatherAPI key")

is_ready = len(missing) == 0

# ============================================================
# BUILD AGENT
# ============================================================
agent_executor = None

if is_ready:
    def build_llm(provider, model, api_key):
        if provider == "Groq":
            return ChatGroq(model=model, temperature=0, api_key=api_key, max_tokens=1024, request_timeout=60)
        elif provider == "Google AI Studio":
            return ChatGoogleGenerativeAI(model=model, temperature=0, google_api_key=api_key, max_output_tokens=1024, request_timeout=60)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    @st.cache_resource(show_spinner=False)
    def build_agent(provider, model, provider_key, serp_key, weather_key):
        os.environ["SERPAPI_API_KEY"] = serp_key
        llm = build_llm(provider, model, provider_key)
        
        search_wrapper = SerpAPIWrapper(serpapi_api_key=serp_key)
        search_tool = Tool(name="web_search", func=search_wrapper.run, description="Useful for searching the internet for current information, facts, news, and data.")
        
        def get_weather(city):
            url = f"https://api.weatherapi.com/v1/current.json?key={weather_key}&q={city}"
            try:
                resp = requests.get(url, timeout=10)
                data = resp.json()
                if "current" not in data:
                    return f"Could not fetch weather for {city}."
                c = data["current"]
                return f"City: {city}\nTemp: {c['temp_c']}°C\nCondition: {c['condition']['text']}\nHumidity: {c['humidity']}%"
            except Exception as e:
                return f"Error: {str(e)}"
        
        weather_tool = Tool(name="get_weather", func=get_weather, description="Useful for getting current weather information for any city.")
        
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
        with st.spinner(f"🛠️ Building agent with {provider} / {html.escape(st.session_state.selected_model)}..."):
            agent_executor = build_agent(provider, st.session_state.selected_model, st.session_state.provider_key, serp_key, weather_key)
        st.success(f"✅ Agent ready! Using {provider} | {html.escape(st.session_state.selected_model)}")
        st.session_state.agent_ready = True
    except Exception as e:
        st.error(f"❌ Failed to build agent: {e}")
        st.session_state.agent_ready = False

# ============================================================
# CHAT CARD
# ============================================================
st.markdown('<div class="glass-card">', unsafe_allow_html=True)

if is_ready and st.session_state.agent_ready and agent_executor is not None:
    st.markdown('<div class="card-header">💬 Chat with your AI Agent</div>', unsafe_allow_html=True)
    
    # Show status
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        st.markdown(f'<span class="badge badge-ready">🟢 {provider}</span>', unsafe_allow_html=True)
    with c2:
        model_short = st.session_state.selected_model.split("/")[-1] if "/" in st.session_state.selected_model else st.session_state.selected_model
        st.markdown(f'<span class="badge badge-ready">🧠 {html.escape(model_short[:25])}</span>', unsafe_allow_html=True)
    with c3:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    st.divider()
    
    # Messages
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-user"><b>👤 You:</b><br>{html.escape(msg["content"])}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-assistant"><b>🤖 Agent:</b><br>{html.escape(msg["content"])}</div>', unsafe_allow_html=True)
    
    # Chat input
    user_query = st.chat_input("Ask the agent anything...")
    
    if user_query:
        if len(user_query) > 1000:
            st.error("❌ Query too long. Max 1000 characters.")
        else:
            current_time = time.time()
            if current_time - st.session_state.last_query_time < 3:
                st.warning("⏳ Please wait 3 seconds between queries.")
            else:
                st.session_state.last_query_time = current_time
                st.session_state.messages.append({"role": "user", "content": user_query})
                
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
                            with st.expander("🔍 View Agent's Thought Process"):
                                st.text(verbose_output)
                        
                        final_answer = response.get("output", "No answer generated.")
                        st.markdown(f'<div class="chat-assistant"><b>🤖 Agent:</b><br>{html.escape(final_answer)}</div>', unsafe_allow_html=True)
                        st.session_state.messages.append({"role": "assistant", "content": final_answer})
                        
                    except Exception as e:
                        st.error(f"❌ Agent error: {e}")
                        st.info("💡 Try rephrasing your question or check your API keys.")
else:
    st.markdown('<div class="card-header">💬 Chat</div>', unsafe_allow_html=True)
    st.markdown('''
    <div class="locked-box">
        <div class="locked-icon">🔐</div>
        <div class="locked-title">Agent is Locked</div>
        <div class="locked-text">Complete the configuration above to unlock the chat</div>
    </div>
    ''', unsafe_allow_html=True)
    
    for item in missing:
        st.markdown(f'<div class="locked-item">❌ {item}</div>', unsafe_allow_html=True)
    
    st.markdown('<div style="text-align:center;color:#64748b;font-size:0.85rem;margin-top:1rem;">All services offer free tiers. No credit card required.</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# FOOTER
# ============================================================
st.markdown('<div style="text-align:center;color:#475569;font-size:0.78rem;margin-top:2rem;padding-bottom:2rem;">🤖 Built with LangChain + Streamlit | BYOK Design | Free Tier Friendly</div>', unsafe_allow_html=True)
