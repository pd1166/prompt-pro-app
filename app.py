import streamlit as st
import google.generativeai as genai
import time
import pandas as pd # נדרש לייצוא ההיסטוריה
from datetime import datetime

# ==========================================
# 1. הגדרות תצורה (Configuration)
# ==========================================
st.set_page_config(
    page_title="Prompt Engineer Pro V8",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# עיצוב CSS מתקדם
st.markdown("""
    <style>
        .stApp { direction: rtl; text-align: right; background-color: #FAFAFA; }
        h1, h2, h3, h4, h5, h6, p, .stMarkdown, .stRadio, .stSelectbox, .stSlider, .stText { 
            text-align: right !important; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
        }
        .stTextInput input, .stTextArea textarea, .stSelectbox div { 
            text-align: right; 
            direction: rtl; 
            background-color: #FFFFFF;
        }
        section[data-testid="stSidebar"] { 
            direction: rtl; 
            text-align: right; 
            background-color: #F0F2F6; 
        }
        /* כפתור ראשי */
        .stButton button { 
            width: 100%; 
            background: linear-gradient(90deg, #6a11cb 0%, #2575fc 100%);
            color: white; 
            font-weight: bold; 
            border-radius: 12px; 
            height: 55px; 
            font-size: 18px; 
            border: none;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: all 0.3s;
        }
        .stButton button:hover { 
            transform: translateY(-2px);
            box-shadow: 0 6px 8px rgba(0,0,0,0.15);
        }
        /* היסטוריה בסרגל צד */
        .history-card {
            background-color: white;
            padding: 10px;
            border-radius: 8px;
            border-right: 4px solid #6a11cb;
            margin-bottom: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ניהול זיכרון (Session State)
# ==========================================
if 'history' not in st.session_state:
    st.session_state.history = []

def add_to_history(original_request, refined_prompt, model_rec, used_model):
    timestamp = datetime.now().strftime("%H:%M")
    st.session_state.history.insert(0, { # מוסיף להתחלה (הכי חדש למעלה)
        "time": timestamp,
        "original": original_request,
        "prompt": refined_prompt,
        "recommendation": model_rec,
        "engine": used_model
    })

# ==========================================
# 3. לוגיקה עסקית
# ==========================================

CONTEXT_LOGIC = {
    "שיווק וקופירייטינג": "Expert Copywriter & Brand Strategist. Focus: Psychology, Virality, Hooks, Emotional Triggers.",
    "כתיבת קוד ופיתוח": "Senior Software Architect. Focus: Clean Code, Security, Scalability, Edge Cases, Modern patterns.",
    "כתיבה יוצרת": "Best-Selling Author. Focus: Narrative depth, Character development, Show don't tell, Sensory details.",
    "אסטרטגיה עסקית": "MBB Consultant (McKinsey/Bain style). Focus: ROI, Market Analysis, Actionable KPIs, Growth Hacking.",
    "כללי/אחר": "Expert Prompt Engineer. Focus: Clarity, Precision, Structure, COT (Chain of Thought)."
}

# מיפוי מודלים לקישורים
MODEL_LINKS = {
    "Claude": "https://claude.ai",
    "GPT": "https://chat.openai.com",
    "Gemini": "https://gemini.google.com",
    "Midjourney": "https://discord.com/invite/midjourney" # למקרה שהפרומפט הוא לתמונות
}

def get_model_link_button(analysis_text):
    """מנתח את הטקסט ומחזיר כפתור קישור למודל המתאים"""
    target_url = "https://chat.openai.com" # ברירת מחדל
    label = "פתח את ChatGPT"
    
    if "Claude" in analysis_text:
        target_url = MODEL_LINKS["Claude"]
        label = "פתח את Claude AI"
    elif "Gemini" in analysis_text:
        target_url = MODEL_LINKS["Gemini"]
        label = "פתח את Google Gemini"
    
    return target_url, label

def get_api_key():
    try:
        return st.secrets["GEMINI_API_KEY"]
    except:
        return ""

def get_safe_model():
    try:
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for m in all_models:
            if 'flash' in m and 'exp' not in m: return m
        for m in all_models:
            if 'pro' in m and 'exp' not in m: return m
        return 'gemini-1.5-flash'
    except:
        return 'gemini-1.5-flash'

def clean_response(text):
    text = text.replace("undefined", "").replace("null", "")
    return text.strip()

def generate_smart_prompt(api_key, raw_input, context_key, tone):
    try:
        genai.configure(api_key=api_key.strip())
        model_name = get_safe_model()
        model = genai.GenerativeModel(model_name)
        specific_logic = CONTEXT_LOGIC.get(context_key, CONTEXT_LOGIC["כללי/אחר"])

        full_query = f"""
        Act as a world-class Meta-Prompting System using the CO-STAR framework.
        
        INPUT DATA:
        - User Request: "{raw_input}"
        - Domain Persona: {specific_logic}
        - Desired Tone: {tone}
        
        TASK:
        1. Rewrite the user request into a highly structured, expert-level prompt using 'CO-STAR' (Context, Objective, Style, Target, Answer, Role).
        2. The output MUST be in Hebrew.
        3. Add a section explaining which AI Model (Claude 3.5 Sonnet, GPT-4o, Gemini Advanced) is best for this task.
        
        OUTPUT FORMAT (Strictly follow this):
        ---DIVIDER---
        [The Hebrew Prompt Code Block]
        ---DIVIDER---
        [Analysis and Model Recommendation in Hebrew]
        """

        response = model.generate_content(full_query)
        return clean_response(response.text), model_name
        
    except Exception as e:
        if "429" in str(e): return "QUOTA_ERROR", ""
        return f"Error: {str(e)}", ""

# ==========================================
# 4. ממשק משתמש (UI)
# ==========================================

saved_key = get_api_key()

# --- סרגל צד: הגדרות + היסטוריה ---
with st.sidebar:
    st.title("⚙️ הגדרות")
    if saved_key:
        st.success("✅ מפתח API מחובר")
        api_key = saved_key
    else:
        api_key = st.text_input("מפתח API", type="password")
    
    st.subheader("🧠 מוח וסגנון")
    selected_context = st.selectbox("תחום:", list(CONTEXT_LOGIC.keys()))
    selected_tone = st.select_slider("טון:", options=["רשמי", "ישיר", "יצירתי", "שיווקי"], value="רשמי")
    
    st.markdown("---")
    
    # --- אזור ההיסטוריה ---
    st.subheader("📚 ספריית הפרומפטים שלי")
    
    # כפתור הורדה
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 הורד היסטוריה (CSV)",
            data=csv,
            file_name='my_prompts_history.csv',
            mime='text/csv',
        )
    
    # הצגת כרטיסיות היסטוריה
    for i, item in enumerate(st.session_state.history):
        with st.expander(f"{item['time']} - {item['original'][:20]}..."):
            st.caption("הפרומפט שנוצר:")
            st.code(item['prompt'], language="markdown")
            st.caption("המלצה:")
            st.info(item['recommendation'][:100] + "...")

# --- אזור ראשי ---
st.title("Prompt Engineer Pro V8 🧠")
st.markdown("### המערכת הלומדת: צור, שמור ונהל פרומפטים")

user_input = st.text_area("מה המשימה שלך?", height=100, placeholder="למשל: תכתוב לי תסריט לטיקטוק על בינה מלאכותית...")

if st.button("צור פרומפט מנצח 🚀"):
    if not api_key:
        st.error("⚠️ חסר מפתח API")
    elif not user_input:
        st.warning("⚠️ נא להזין בקשה")
    else:
        with st.spinner("🤖 המוח המלאכותי עובד..."):
            result, used_model = generate_smart_prompt(api_key, user_input, selected_context, selected_tone)
            
            if result == "QUOTA_ERROR":
                st.error("⏳ הגעת למכסת השימוש. המתן דקה.")
            elif "Error:" in result:
                st.error(result)
            else:
                parts = result.split("---DIVIDER---")
                prompt_content = parts[1] if len(parts) > 1 else result
                analysis_content = parts[2] if len(parts) > 2 else "אין ניתוח זמין."
                
                # שמירה להיסטוריה
                add_to_history(user_input, prompt_content, analysis_content, used_model)
                
                st.success("✅ בוצע בהצלחה!")
                
                # אזור התוצאה הראשית
                st.subheader("1. הפרומפט שלך (CO-STAR)")
                st.code(prompt_content.strip(), language="markdown")
                
                # אזור ההמלצה והקישור
                st.markdown("---")
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.subheader("2. ניתוח והמלצת מודל")
                    st.info(analysis_content.strip())
                
                with col2:
                    # יצירת כפתור קישור דינמי
                    target_url, label = get_model_link_button(analysis_content)
                    st.markdown("<br><br>", unsafe_allow_html=True) # ריווח
                    st.link_button(f"🚀 {label}", target_url, use_container_width=True)