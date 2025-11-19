import streamlit as st
import google.generativeai as genai
import time
import pandas as pd
from datetime import datetime

# ==========================================
# 1. הגדרות תצורה
# ==========================================
st.set_page_config(
    page_title="Prompt Engineer Pro V10",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. תיקון CSS "כירורגי" (Surgical Fix)
# ==========================================
st.markdown("""
    <style>
        /* משאירים את המעטפת הראשית רגילה כדי לא לשבור את העימוד */
        .stApp {
            direction: ltr; 
            background-color: #FAFAFA;
        }
        
        /* הופכים רק את הטקסטים הפנימיים */
        .element-container, .stMarkdown, h1, h2, h3, h4, h5, h6, p {
            direction: rtl;
            text-align: right;
        }
        
        /* תיקון ספציפי לשדות קלט */
        .stTextInput input, .stTextArea textarea {
            direction: rtl;
            text-align: right;
        }
        
        /* יישור תפריטים נפתחים */
        .stSelectbox div[data-baseweb="select"] > div {
            direction: rtl;
            text-align: right;
        }
        
        /* יישור סרגל צד */
        section[data-testid="stSidebar"] > div {
            direction: rtl;
            text-align: right;
        }
        
        /* כפתור ראשי */
        .stButton button { 
            width: 100%;
            border-radius: 10px;
            height: 50px;
            font-weight: bold;
            background: linear-gradient(90deg, #4B4BFF 0%, #0068C9 100%);
            color: white;
            border: none;
        }

        /* הסתרת רכיבים מיותרים */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;} /* מסתיר את הפס הצבעוני למעלה שנתקע */
        
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

def get_safe_model():
    try: return 'gemini-1.5-flash'
    except: return 'gemini-pro'

def clean_response(text):
    return text.replace("undefined", "").replace("null", "").strip()

def generate_smart_prompt(api_key, raw_input, context_key, tone):
    try:
        genai.configure(api_key=api_key.strip())
        model_name = get_safe_model()
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

# סרגל צד
with st.sidebar:
    st.title("⚙️ הגדרות")
    if saved_key:
        st.success("המפתח מחובר")
        api_key = saved_key
    else:
        api_key = st.text_input("מפתח API", type="password")
    
    selected_context = st.selectbox("תחום:", list(CONTEXT_LOGIC.keys()))
    selected_tone = st.select_slider("טון:", ["רשמי", "ישיר", "יצירתי", "שיווקי"], value="רשמי")
    
    st.markdown("---")
    # היסטוריה מקוצרת
    if st.session_state.history:
        st.caption("היסטוריה:")
        for item in st.session_state.history[:3]:
            st.text(f"🕒 {item['time']}")
            st.code(item['prompt'][:50] + "...", language="markdown")

# מסך ראשי
st.title("Prompt Pro V10 🎯")
st.markdown("##### מחולל פרומפטים מקצועי (גרסה יציבה)")

user_input = st.text_area("מה המשימה שלך?", height=100, placeholder="למשל: פוסט לינקדאין על AI...")

if st.button("צור פרומפט 🚀"):
    if not api_key or not user_input:
        st.error("חסר מפתח או טקסט")
    else:
        with st.spinner("מעבד..."):
            result, used_model = generate_smart_prompt(api_key, user_input, selected_context, selected_tone)
            
            if result == "QUOTA_ERROR":
                st.warning("עומס רגעי, נסה שוב.")
            elif "Error" in result:
                st.error(result)
            else:
                parts = result.split("---DIVIDER---")
                prompt_content = parts[1] if len(parts) > 1 else result
                analysis_content = parts[2] if len(parts) > 2 else "אין המלצה."
                
                add_to_history(user_input, prompt_content, analysis_content, used_model)
                
                st.success("מוכן!")
                st.code(prompt_content.strip(), language="markdown")
                
                url, label = get_model_link_button(analysis_content)
                st.link_button(f"פתח ב-{label}", url, use_container_width=True)
