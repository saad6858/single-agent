# 🤖 AI Agent Playground — Custom Lightweight Agent

Built by **Saad Maqbool** | Bano Qabil Agentic AI BQL6-LR | Lytton Road, Lahore

A multi-provider AI agent that works with **ANY model** — no ReAct compatibility required.

---

## 🎯 Why Custom Agent?

LangChain's ReAct agent requires models specifically trained on the ReAct text pattern (Thought → Action → Observation). Most free-tier models don't support this.

Our custom agent uses a **simple regex-based tool calling format** that ANY instruction-tuned model can follow:

This means the app works with:
- ✅ Groq (compound, gpt-oss, qwen, etc.)
- ✅ Google AI Studio (Gemini 3.x, etc.)
- ✅ Cerebras (gemma, gpt-oss, etc.)
- ✅ Any future provider — just add 10 lines of code

---

## 🚀 Setup

### 1. Get API Keys (Free Tiers)

| Provider | Where | Free Tier |
|----------|-------|-----------|
| **Groq** | console.groq.com | Available models on your account |
| **Google AI Studio** | aistudio.google.com | Generous free tier |
| **Cerebras** | cloud.cerebras.ai | 5 RPM free tier |

### 2. Search & Weather Keys (Optional)

| Tool | Where | Free Tier |
|------|-------|-----------|
| DuckDuckGo | — | Free, no key |
| SerpAPI | serpapi.com | 100 searches/month |
| Tavily | tavily.com | 1,000 calls/month |
| WeatherAPI | weatherapi.com | 1M calls/month |
| OpenWeatherMap | openweathermap.org | 1M calls/month |

### 3. Deploy

1. Create GitHub repo `saad6858/single-agent`
2. Upload `app.py`, `requirements.txt`, `README.md`
3. Go to share.streamlit.io → Deploy
4. Enter your API keys in the sidebar
5. Click "Load Models" → Select model → Chat

---

## 🧠 How It Works

1. User asks a question
2. LLM receives a short system prompt + the question
3. LLM decides if it needs a tool (search/weather)
4. If yes, LLM outputs `TOOL: name` + `INPUT: query`
5. App parses this with regex, executes the tool
6. Tool result sent back to LLM
7. LLM outputs final answer

**Max 3 tool calls per query.** Simple. Fast. Reliable.

---

## 🎓 Course Context

- **Course:** Bano Qabil Agentic AI (BQ-023/BQ-024)
- **Batch:** BQL6-LR
- **Campus:** Lytton Road, Lahore
- **Instructor:** Shan Ali (Sir Shan)

