# 🤖 AI Agent Playground — Multi-Provider ReAct Agent

**Built by:** Saad Maqbool  
**Course:** Bano Qabil Agentic AI (Batch BQL6-LR, Lytton Road, Lahore)  
**Instructor:** Shan Ali

---

## What This Is

A fully functional **ReAct Agent** built with **LangChain + Streamlit** that supports **three LLM providers**, **three search tools**, and **two weather APIs**.

Users pick their provider, enter their own API key, load available models dynamically, select one, and chat. No keys are hardcoded. All keys stay in the browser session only.

---

## Supported Providers & Tools

### LLM Providers

| Provider | Models | Key Source |
|----------|--------|------------|
| **Groq** | Llama, Mixtral, Gemma, Qwen, GPT-OSS | console.groq.com |
| **Google AI Studio** | Gemini 1.5 Flash, Pro, etc. | aistudio.google.com |
| **Alibaba Qwen** | qwen-turbo, qwen-plus, qwen-max | dashscope.aliyun.com |

### Search Tools

| Tool | Key Required | Source |
|------|--------------|--------|
| **SerpAPI** | Yes | serpapi.com |
| **DuckDuckGo** | **No** — completely free | No signup needed |
| **Tavily** | Yes | tavily.com |

### Weather Tools

| Tool | Key Required | Source |
|------|--------------|--------|
| **WeatherAPI** | Yes | weatherapi.com |
| **OpenWeatherMap** | Yes | openweathermap.org |

---

## What the Agent Can Do

| Capability | Example Query |
|------------|---------------|
| 🔍 **Web Search** | "What is the latest news about AI?" |
| 🌤️ **Weather Lookup** | "What is the weather in Lahore?" |
| 🧠 **Multi-step Reasoning** | "Find the capital of India and then find its weather" |

The agent uses the **ReAct pattern** (Reason + Act):

```
Thought → Action → Observation → Thought → ... → Final Answer
```

---

## How to Run Locally

### 1. Clone or Download

```bash
git clone https://github.com/saad6858/single-agent.git
cd single-agent
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the App

```bash
streamlit run app.py
```

### 4. Setup (on the main page)

1. **Select LLM Provider** — Groq, Google AI Studio, or Alibaba Qwen
2. **Select Search Tool** — SerpAPI, DuckDuckGo (free), or Tavily
3. **Select Weather Tool** — WeatherAPI or OpenWeatherMap
4. **Enter API Keys** for the services you selected
5. **Click "Load Models"** — models are fetched dynamically from the provider
6. **Select a Model** from the dropdown
7. **Ask away!**

> **Note:** DuckDuckGo requires no API key. If you choose it, you only need the LLM and weather keys.

---

## How to Deploy to Streamlit Cloud

### 1. Push to GitHub

```bash
git add app.py requirements.txt README.md
git commit -m "AI Agent Playground — multi-provider ReAct agent"
git push origin main
```

### 2. Deploy

1. Go to **share.streamlit.io**
2. Connect your GitHub repo `saad6858/single-agent`
3. Select `app.py` as the main file
4. Click **Deploy**

### 3. Share

Send the deployed URL to anyone. They use their own API keys. Nothing is stored server-side.

---

## API Key Setup

| Service | Free Tier | Sign Up Link |
|---------|-----------|--------------|
| Groq | Free tier available | console.groq.com |
| Google AI Studio | Generous free tier | aistudio.google.com |
| Alibaba Qwen (DashScope) | Free trial credits | dashscope.aliyun.com |
| SerpAPI | 100 searches/month | serpapi.com |
| Tavily | 1,000 searches/month | tavily.com |
| WeatherAPI | 1M calls/month | weatherapi.com |
| OpenWeatherMap | 1,000 calls/day | openweathermap.org |
| DuckDuckGo | Unlimited, no key | No signup required |

---

## Architecture

```
User Query
    ↓
Provider Selection (Groq / Google AI Studio / Alibaba Qwen)
    ↓
Search Tool Selection (SerpAPI / DuckDuckGo / Tavily)
    ↓
Weather Tool Selection (WeatherAPI / OpenWeatherMap)
    ↓
Dynamic Model Fetch → Model Selection
    ↓
LangChain ReAct Agent
    ↓
Selected LLM (Reasoning Engine)
    ↓
Tools: [Web Search, Weather Lookup]
    ↓
Final Answer
```

---

## Files

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit application |
| `requirements.txt` | Python dependencies |
| `README.md` | This file |

---

## Notes

- **Bring Your Own Key (BYOK).** Users enter their own API keys. No keys are hardcoded.
- **API keys are never stored.** They exist only in the browser session.
- **Dynamic model loading.** The app fetches live model lists from provider APIs.
- **Works on mobile.** Responsive UI for Android/iPhone browsers.
- **Provider-agnostic.** Switch between Groq, Google, and Qwen without changing code.
- **DuckDuckGo is free.** No API key, no signup, no rate limits for casual use.

---

*"AI is not replacing humans — but humans who use AI are replacing those who don't."* — Shan Ali
