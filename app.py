import streamlit as st
import google.generativeai as genai
import time
import pandas as pd
from datetime import datetime

# ==========================================
# 1. הגדרות תצורה
# ==========================================
st.set_page_config(
    page_title="Prompt Engineer Pro V12",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. תיקון עיצוב וצבעים (Colors & Layout Fix)
# ==========================================
st.markdown("""
    <style>
        /* --- תיקון פריסה (Layout) --- */
        .stApp { direction: ltr; background-color: #FAFAFA; }
        
        /* --- תיקון צבעים קריטי (Color Fix) --- */
        /* מכריח את כל הטקסטים להיות כהים כדי שיראו אותם על הרקע הלבן */
        .stApp, .element-container, .stMarkdown, h1, h2, h3, h4, h5, h6, p, div, span {
            color: #212121 !important; /* שחור כהה */
            direction: rtl; 
            text-align: right;
        }
        
        /* --- תיקון שדות קלט --- */
        .stTextInput input, .stTextArea textarea { 
            direction: rtl; 
            text-align: right; 
            background-color: #FFFFFF !important; /* רקע לבן */
            color: #000000 !important; /* טקסט שחור */
            border: 1px solid #E0E0E0;
        }
        
        /* --- תיקון תפריטים --- */
        .stSelectbox div[data-baseweb="select"] > div { 
            direction: rtl; 
            text-align: right;
            color: #000000 !important;
        }
        
        /* --- יישור סרגל צד --- */
        section[data-testid="stSidebar"] > div { 
            direction: rtl; 
            text-align: right; 
            background-color: #F0F2F6;
        }
        section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span {
            color: #212121 !important;
        }
        
        /* --- כפתור ראשי --- */
        .stButton button { 
            width: 100%; 
            border-radius: 12px; 
            height: 55px; 
            font-weight: bold; 
            font-size: 18px;
            background: linear-gradient(90deg, #6a11cb 0%, #2575fc 100%); 
            color: white !important; /* טקסט לבן בכפתור */
            border: none;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        /* הסתרת רכיבים מיותרים */
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. ניהול זיכרון
# ==========================================
if 'history' not in st.session_state:
    st.session_state.history = []

def add_to_history(original_request, refined_prompt, model_rec, used_model):
    timestamp = datetime.now().strftime("%H:%M")
    st.session_state.history.insert(0, {
        "time": timestamp,
        "original": original_request,
        "prompt": refined_prompt,
        "recommendation": model_rec,
        "engine": used_model
    })

# ==========================================
# 4. לוגיקה עסקית
# ==========================================
CONTEXT_LOGIC = {
    "שיווק וקופירייטינג": "Expert Copywriter. Focus: Psychology, Virality.",
    "כתיבת קוד ופיתוח": "Software Architect. Focus: Clean Code, Security.",
    "כתיבה יוצרת": "Storyteller. Focus: Narrative depth.",
    "אסטרטגיה עסקית": "Consultant. Focus: Growth, ROI.",
    "כללי/אחר": "Prompt Engineer. Focus: Clarity."
}

MODEL_LINKS = {
    "Claude": "https://claude.ai",
    "GPT": "https://chat.openai.com",
    "Gemini": "https://gemini.google.com"
}

def get_model_link_button(analysis_text):
    target_url = "https://chat.openai.com"
    label = "ChatGPT"
    if "Claude" in analysis_text:
        target_url = MODEL_LINKS["Claude"]
        label = "Claude AI"
    elif "Gemini" in analysis_text:
        target_url = MODEL_LINKS["Gemini"]
        label = "Gemini"
    return target_url, label

def get_api_key():
    try: return st.secrets["GEMINI_API_KEY"]
    except: return ""

def get_working_model():
    try:
        # בדיקה מהירה ללא קריאה כבדה לרשת
        return 'gemini-1.5-flash'
    except:
        return 'gemini-pro'

def clean_response(text):
    return text.replace("undefined", "").replace("null", "").strip()

def generate_smart_prompt(api_key, raw_input, context_key, tone):
    try:
        genai.configure(api_key=api_key.strip())
        model_name = get_working_model()
        model = genai.GenerativeModel(model_name)
        
        specific_logic = CONTEXT_LOGIC.get(context_key, CONTEXT_LOGIC["כללי/אחר"])

        full_query = f"""
        Act as a world-class Meta-Prompting System (CO-STAR framework).
        INPUT: Request="{raw_input}", Persona="{specific_logic}", Tone="{tone}".
        TASK:
        1. Write an expert prompt in Hebrew.
        2. Recommend best AI model (Claude/GPT/Gemini).
        OUTPUT FORMAT:
        ---DIVIDER---
        [Hebrew Prompt]
        ---DIVIDER---
        [Recommendation]
        """
        
        response = model.generate_content(full_query)
        return clean_response(response.text), model_name
    except Exception as e:
        if "429" in str(e): return "QUOTA_ERROR", ""
        return f"Error: {str(e)}", ""

# ==========================================
# 5. ממשק משתמש
# ==========================================
saved_key = get_api_key()

with st.sidebar:
    st.title("⚙️ הגדרות")
    if saved_key:
        st.success("מפתח מחובר ✅")
        api_key = saved_key
    else:
        api_key = st.text_input("מפתח API", type="password")
    
    selected_context = st.selectbox("תחום:", list(CONTEXT_LOGIC.keys()))
    selected_tone = st.select_slider("טון:", ["רשמי", "ישיר", "יצירתי", "שיווקי"], value="רשמי")
    
    st.markdown("---")
    if st.session_state.history:
        st.caption("היסטוריה אחרונה:")
        for item in st.session_state.history[:3]:
            st.text(f"🕒 {item['time']}")
            st.code(item['prompt'][:40] + "...", language="markdown")

st.title("Prompt Pro V12 🧠")
st.markdown("##### מחולל פרומפטים חכם")

user_input = st.text_area("מה המשימה שלך?", height=100, placeholder="למשל: פוסט לינקדאין על AI...")

if st.button("צור פרומפט מנצח 🚀"):
    if not api_key or not user_input:
        st.error("חסר מפתח או טקסט")
    else:
        # --- אינדיקציה ויזואלית לחשיבה ---
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("🔄 מתחבר למוח המלאכותי...")
        time.sleep(0.5) # השהייה קטנה לאפקט
        progress_bar.progress(30)
        
        status_text.text("⚡ מנתח את הבקשה ובונה אסטרטגיה...")
        
        # ביצוע הפעולה האמיתית
        result, used_model = generate_smart_prompt(api_key, user_input, selected_context, selected_tone)
        
        progress_bar.progress(80)
        status_text.text("📝 מנסח את הפרומפט הסופי...")
        time.sleep(0.3)
        
        progress_bar.progress(100)
        time.sleep(0.2)
        progress_bar.empty() # ניקוי הפס בסיום
        status_text.empty()
        # ----------------------------------

        if result == "QUOTA_ERROR":
            st.warning("⚠️ עומס רגעי על המודל. אנא נסה שוב בעוד דקה.")
        elif "Error" in result:
            st.error(f"שגיאה: {result}")
        else:
            parts = result.split("---DIVIDER---")
            prompt_content = parts[1] if len(parts) > 1 else result
            analysis_content = parts[2] if len(parts) > 2 else "אין המלצה."
            
            add_to_history(user_input, prompt_content, analysis_content, used_model)
            
            st.success(f"הפרומפט מוכן! (מודל: {used_model})")
            st.code(prompt_content.strip(), language="markdown")
            
            url, label = get_model_link_button(analysis_content)
            st.link_button(f"🚀 פתח ב-{label}", url, use_container_width=True)
