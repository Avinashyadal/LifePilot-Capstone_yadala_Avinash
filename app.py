import streamlit as st
import json
import re
import time
from datetime import datetime, timedelta

# --- SAFETY IMPORTS (CRASH PROOF) ---
try:
    import google.generativeai as genai
    from youtube_search import YoutubeSearch
    from ics import Calendar, Event
    import pytz  # Required for Indian Time
except ImportError as e:
    st.error(f"⚠️ MISSING LIBRARY ERROR: {e}")
    st.info("👉 Please add 'pytz' to requirements.txt and run: pip install -r requirements.txt")
    st.stop()

# --- CONFIGURATION ---
st.set_page_config(page_title="LifePilot Hub", page_icon="✈️", layout="wide")

# --- CLASSIC UI CSS (Professional Look) ---
st.markdown("""
<style>
    .main {background-color: #f5f5f5;}
    
    .agent-box {
        padding: 20px; 
        border-radius: 10px; 
        background-color: #ffffff; 
        color: #000000 !important; 
        border-left: 5px solid #2196F3; 
        margin-bottom: 20px; 
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    
    /* BEAUTIFUL TABLE STYLE */
    .styled-table {
        border-collapse: collapse; margin: 25px 0; font-size: 16px; 
        font-family: sans-serif; min-width: 100%; box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
        border-radius: 5px; overflow: hidden;
    }
    .styled-table thead tr {
        background-color: #4CAF50; color: #ffffff; text-align: left;
    }
    .styled-table th, .styled-table td {
        padding: 12px 15px; border-bottom: 1px solid #dddddd;
    }
    .styled-table tbody tr { background-color: #ffffff; color: #333; }
    .styled-table tbody tr:nth-of-type(even) { background-color: #f3f3f3; }
    
    .stButton>button {
        width: 100%; border-radius: 5px; background-color: #4CAF50; 
        color: white; font-weight: bold; height: 50px; border: none;
    }
    .stButton>button:hover { background-color: #45a049; }
    
    a {text-decoration: none; color: #d93025; font-weight: bold;}
    
    .video-card {
        background: white; padding: 10px; border-radius: 5px; 
        box-shadow: 0 1px 3px rgba(0,0,0,0.2); text-align: center;
    }
    
    .ai-link {
        display: block; padding: 10px; margin: 5px 0; background-color: #e0e0e0;
        text-align: center; border-radius: 5px; color: #333 !important; font-weight: bold; text-decoration: none;
    }
    .ai-link:hover {background-color: #d0d0d0;}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR (INDIAN TIME DEFAULT) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712009.png", width=100)
    st.title("LifePilot Pro")
    api_key = st.text_input("Enter Gemini API Key", type="password")
    
    st.divider()
    st.subheader("🌎 Location")
    
    # 1. TIMEZONE SELECTOR (India First)
    timezones = ['Asia/Kolkata', 'UTC', 'US/Pacific', 'US/Eastern', 'Europe/London']
    selected_tz = st.selectbox("Timezone:", timezones, index=0)
    
    # 2. CALCULATE TIME
    tz_obj = pytz.timezone(selected_tz)
    now = datetime.now(tz_obj)
    
    st.metric("📅 Date", now.strftime("%Y-%m-%d"))
    st.metric("🕒 Local Time", now.strftime("%I:%M %p"))
    
    st.divider()
    st.subheader("🧠 Intelligence")
    ai_mode = st.radio("Mode:", ["Standard Agent (Gemini)", "Perplexity Research Mode"])
    
    st.divider()
    st.subheader("🚀 Shortcuts")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<a href="https://chat.openai.com" target="_blank" class="ai-link">ChatGPT</a>', unsafe_allow_html=True)
    with c2:
        st.markdown('<a href="https://gemini.google.com" target="_blank" class="ai-link">Gemini</a>', unsafe_allow_html=True)

# --- ROBUST FUNCTIONS (CRASH PROOF) ---

def robust_json_extractor(text):
    """
    Finds JSON data even if the AI talks too much.
    """
    if not text: return []
    # Try regex first
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass
    # Try standard clean
    try:
        clean = text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except:
        return []

def safe_youtube_search(query):
    if not query: return None
    if isinstance(query, list): query = " ".join([str(x) for x in query])
    if not isinstance(query, str): query = str(query)

    fallback = {
        "title": f"Search: {query}", 
        "link": f"https://www.youtube.com/results?search_query={query}", 
        "thumbnail": "https://via.placeholder.com/300x200?text=YouTube"
    }
    try:
        results = YoutubeSearch(query, max_results=1).to_dict()
        if results and len(results) > 0:
            v = results[0]
            if 'id' in v and 'title' in v:
                return {
                    "title": v['title'], 
                    "link": f"https://www.youtube.com/watch?v={v['id']}", 
                    "thumbnail": v.get('thumbnails', [''])[0]
                }
    except:
        return fallback
    return fallback

def generate_clean_html_table(schedule_data):
    """
    Builds the HTML manually to prevent 'Raw Code' errors.
    """
    html = """<table class="styled-table">
    <thead><tr>
        <th>Time</th>
        <th>Activity</th>
        <th>Resource</th>
    </tr></thead>
    <tbody>"""
    
    plain_text = ""
    for item in schedule_data:
        t = item.get("time", "N/A")
        a = item.get("activity", "Task")
        e = item.get("emoji", "📝")
        r = item.get("resource_link", "#")
        
        html += f"""<tr><td>{t}</td><td>{e} {a}</td><td><a href="{r}" target="_blank">Open Resource</a></td></tr>"""
        plain_text += f"{t}: {a}\n"

    html += "</tbody></table>"
    return html, plain_text

def create_ics_file(text_plan, start_time_obj):
    try:
        c = Calendar()
        e = Event()
        e.name = "LifePilot Plan"
        # Use the Corrected Indian Time
        e.begin = start_time_obj
        e.duration = timedelta(hours=4)
        e.description = text_plan
        c.events.add(e)
        return c.serialize()
    except:
        return ""

def run_gemini(inputs, model):
    try:
        return model.generate_content(inputs).text
    except Exception as e:
        return None

# --- MAIN APP ---

st.title("✈️ LifePilot: AI Personal Operating System")
# Dynamic Header with Indian Time
st.markdown(f"### 📅 {now.strftime('%A, %B %d')} | {now.strftime('%I:%M %p')}")

user_goal = st.text_area("What is your goal?", placeholder="e.g. Master React JS and cook Lasagna", height=100)

if st.button("🚀 Run LifePilot Agents"):
    if not api_key:
        st.error("❌ Please enter your API Key in the sidebar.")
        st.stop()
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('models/gemini-2.0-flash')
    except Exception as e:
        st.error(f"Connection Error: {e}")
        st.stop()

    progress_bar = st.progress(0)
    
    # 1. TOPIC IMAGE
    with st.spinner("🎨 Finding topic image..."):
        img_data = safe_youtube_search(user_goal if user_goal else "Productivity")
        if img_data:
            st.image(img_data['thumbnail'], width=200)

    # 2. BREAKDOWN AGENT
    st.markdown("**🤖 Agent 1 (Breakdown): Analyzing...**")
    
    context_instruction = ""
    if ai_mode == "Perplexity Research Mode":
        context_instruction = "Act like Perplexity AI. Be extremely precise, factual, and research-oriented."
    
    inputs = [f"{context_instruction} Break down '{user_goal}' into 3 short YouTube search queries. Return JSON list."]
    response = run_gemini(inputs, model)
    
    queries = [user_goal]
    if response:
        try:
            clean = response.replace("```json", "").replace("```", "").strip()
            queries = json.loads(clean)
        except:
            queries = [user_goal]
            
    # Flatten List Check
    safe_queries = []
    if isinstance(queries, list):
        for q in queries:
            if isinstance(q, list):
                safe_queries.extend([str(i) for i in q])
            else:
                safe_queries.append(str(q))
    else:
        safe_queries = [str(queries)]

    st.markdown(f"<div class='agent-box'><b>✅ Strategy Identified:</b><br>{', '.join(safe_queries)}</div>", unsafe_allow_html=True)
    progress_bar.progress(30)

    # 3. RESOURCE AGENT
    st.markdown("**🤖 Agent 2 (Resources): Fetching Content...**")
    found_videos = []
    
    if safe_queries:
        cols = st.columns(len(safe_queries))
        for i, q in enumerate(safe_queries):
            if i < len(cols):
                with cols[i]:
                    v = safe_youtube_search(q)
                    if v:
                        st.markdown(f"""
                        <div class='video-card'>
                            <img src='{v['thumbnail']}' width='100%' style='border-radius:5px;'>
                            <p style='font-size:12px; margin-top:5px;'><b>{v['title'][:30]}..</b></p>
                            <a href='{v['link']}' target='_blank'>Watch Video</a>
                        </div>
                        """, unsafe_allow_html=True)
                        found_videos.append(v)
    progress_bar.progress(60)

    # 4. SCHEDULER AGENT (Uses Indian Time)
    st.markdown("**🤖 Agent 3 (Scheduler): Creating Interactive Plan...**")
    with st.spinner("Finalizing..."):
        # Pass Indian Time to AI
        now_str = now.strftime("%I:%M %p")
        res_txt = "\n".join([f"{r['title']} ({r['link']})" for r in found_videos])
        
        prompt = [f"""
        Current Time: {now_str}.
        Goal: {user_goal}
        Resources: {res_txt}
        
        Action: Create a Daily Schedule starting at {now_str}.
        STRICT FORMAT: Return a JSON List of Objects.
        
        Example:
        [
            {{"time": "{now_str} - ...", "activity": "Task 1", "emoji": "🚀", "resource_link": "http://..."}}
        ]
        """]
        
        response_json = run_gemini(prompt, model)
        schedule_data = robust_json_extractor(response_json)
        
        progress_bar.progress(100)

    # --- FINAL DISPLAY ---
    st.divider()
    
    if schedule_data:
        # Visual Table
        st.subheader("📅 Your Optimized Plan")
        html_table, text_plan = generate_clean_html_table(schedule_data)
        st.markdown(html_table, unsafe_allow_html=True)
        
        # Interactive Checklist
        st.divider()
        st.subheader("✅ Live Checklist")
        for idx, item in enumerate(schedule_data):
            c1, c2 = st.columns([0.8, 0.2])
            with c1:
                st.checkbox(f"{item.get('time','')} : {item.get('activity','')}", key=f"c_{idx}")
            with c2:
                if item.get('resource_link') != "#":
                    st.markdown(f"[Link ↗]({item.get('resource_link')})")
        
        # Calendar Export
        st.divider()
        ics_data = create_ics_file(text_plan, now)
        if ics_data:
            c1, c2 = st.columns([1, 4])
            with c1:
                st.download_button("📅 Download Calendar", ics_data, file_name="LifePilot.ics", mime="text/calendar")
            with c2:
                st.success("Ready for Outlook/Google Calendar")

    st.success("System Execution Complete.")