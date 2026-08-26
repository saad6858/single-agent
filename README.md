# 🤖 AI Agent — Multi-Provider (Groq + Google AI Studio)

**Built by:** Saad Maqbool  
**Course:** Bano Qabil Agentic AI (Batch BQL6-LR)  
**Instructor:** Shan Ali

---

## What This Is

A fully functional **ReAct Agent** built with **LangChain + Streamlit** that supports **TWO LLM providers**:

| Provider | Why Use It | Free Tier |
|----------|-----------|-----------|
| **Groq** | Blazing fast inference, open-source models | $200 credits |
| **Google AI Studio** | Generous TPM limits, Gemini models | Very generous free tier |

**Key feature:** Bring Your Own Key (BYOK). Users pick their provider, enter their own API key, load available models dynamically, select one, and chat. No keys are hardcoded.

---

## What the Agent Can Do

| Tool | Purpose | Example Query |
|------|---------|---------------|
| 🔍 **Web Search** | Search the internet for current info | "What is the latest news about AI?" |
| 🌤️ **Weather Lookup** | Get real-time weather for any city | "What is the weather in Lahore?" |
| 🧠 **Reasoning** | Combine tools to answer complex questions | "Find the capital of India and then find its weather" |

The agent uses the **ReAct pattern** (Reason + Act):
```
Thought → Action → Observation → Thought → ... → Final Answer
```

---

## How to Run Locally

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the App
```bash
streamlit run agent_app.py
```

### 3. Setup (in the sidebar)
1. **Select Provider:** Groq or Google AI Studio
2. **Enter API Key** for that provider
3. **Click "Load Models"** — models are fetched dynamically from the provider
4. **Select a Model** from the dropdown
5. **Enter SerpAPI Key** and **WeatherAPI Key**
6. **Ask away!**

---

## How to Deploy to Streamlit Cloud

### 1. Push to GitHub
```bash
git init
git add agent_app.py requirements.txt README.md
git commit -m "AI Agent with Groq + Google AI Studio"
git push origin main
```

### 2. Deploy
1. Go to **share.streamlit.io**
2. Connect your GitHub repo
3. Select `agent_app.py` as the main file
4. Click **Deploy**

### 3. Share
Send the deployed URL to anyone. They just need their own free API keys.

---

## API Key Setup (Free Tiers)

| Service | Free Tier | Sign Up Link |
|---------|-----------|--------------|
| Groq | $200 credits | console.groq.com |
| Google AI Studio | Very generous | aistudio.google.com |
| SerpAPI | 100 searches/month | serpapi.com |
| WeatherAPI | 1M calls/month | weatherapi.com |

---

## Architecture

```
User Query
    ↓
Provider Selection (Groq / Google AI Studio)
    ↓
Dynamic Model Fetch → Model Selection
    ↓
LangChain ReAct Agent
    ↓
Selected LLM (Reasoning Engine)
    ↓
Tools: [SerpAPI Search, WeatherAPI Lookup]
    ↓
Final Answer
```

---

## Files

| File | Purpose |
|------|---------|
| `agent_app.py` | Main Streamlit application |
| `requirements.txt` | Python dependencies |
| `README.md` | This file |

---

## Notes

- **No OpenAI credits needed.** Both providers have generous free tiers.
- **API keys are never stored.** They exist only in your browser session.
- **Dynamic model loading.** The app fetches live model lists from Groq/Google APIs.
- **Works on mobile.** Responsive UI for Android/iPhone browsers.
- **Provider-agnostic.** Switch between Groq and Google without changing code.

---

*"AI is not replacing humans — but humans who use AI are replacing those who don't."* — Shan Ali
