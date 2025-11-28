# ✈️ LifePilot: AI Personal Life Operating System

### Track: Concierge Agents
**LifePilot** is a Multi-Agent AI System that acts as your real-time Personal Chief Operating Officer (COO). It takes a vague goal, researches it on YouTube, and builds a strict, interactive schedule that syncs with your Outlook/Google Calendar.

---

## 🏗️ Architecture
LifePilot utilizes a **Sequential Multi-Agent Architecture** powered by **Google Gemini 2.0 Flash**:

1.  **Agent 1 (Strategist):** Breaks down vague goals into specific search queries using logical reasoning.
2.  **Agent 2 (Researcher):** Uses a custom **YouTube Search Tool** to find real, verifiable video resources (not hallucinated links).
3.  **Agent 3 (Scheduler):** Synthesizes the strategy and resources into a structured JSON dataset, creating an interactive checklist.

---

## 🚀 Key Features
* **Real-Time Research:** Connects to live YouTube data.
* **Interactive UI:** Check off tasks as you complete them.
* **Calendar Integration:** Generates `.ics` files for one-click import to Google Calendar/Outlook.
* **Crash-Proof Parsing:** Uses robust regex to handle AI output errors gracefully.
* **Perplexity Mode:** Toggle between Standard Gemini agents and deep-research mode.

---

## 🤖 Technologies Used
* **Frontend:** Streamlit
* **AI Model:** Google Gemini 2.0 Flash
* **Tools:** `Youtube`, `ics` (Calendar)