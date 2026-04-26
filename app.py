import streamlit as st
import google.generativeai as genai
import os
import time
import hashlib
import io
import contextlib
from dotenv import load_dotenv

# ================= LOAD ENV =================
load_dotenv()
api_key = os.getenv("GEMINI_KEY")

if not api_key:
    st.error("❌ GEMINI_KEY missing. Check your .env file!")
    st.stop()

# ================= GEMINI SETUP =================
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash")

# ================= PAGE CONFIG =================
st.set_page_config(page_title="CodeReview Pro", layout="wide")

# ================= UI STYLE =================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

.stApp {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    font-family: 'Inter', sans-serif;
    color: white;
}

/* Title */
h1 {
    font-size: 3rem !important;
    font-weight: 800;
    text-align: center;
    background: linear-gradient(90deg, #00dbde, #fc00ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* TEXTAREA FIX */
textarea {
    background: rgba(0,0,0,0.7) !important;
    color: white !important;
    border-radius: 15px !important;
}

/* LABELS */
label {
    color: white !important;
    font-weight: 600;
}

/* TABS FIX */
.stTabs [data-baseweb="tab"] {
    color: #ffffff !important;
    font-weight: 600;
}

.stTabs [aria-selected="true"] {
    color: #00dbde !important;
    border-bottom: 3px solid #00dbde !important;
}

/* BUTTONS */
.stButton>button {
    border-radius: 12px;
    padding: 12px 25px;
    font-weight: 600;
    background: linear-gradient(90deg, #00dbde, #fc00ff);
    border: none;
}

/* OUTPUT */
.output-card {
    background: rgba(255,255,255,0.05);
    padding: 20px;
    border-radius: 20px;
    margin-top: 20px;
    border-left: 4px solid #00dbde;
}
.stRadio > div {
    color: white !important;
    font-weight: 600;
}

.stRadio label {
    color: white !important;
}

.stRadio div[role="radiogroup"] > label {
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================
st.markdown("""
<div style='text-align:center; margin-bottom:20px;'>
    <h1>🚀 CodeReview Pro</h1>
    <p style='color:#ccc;'>AI-powered code auditor • Explain • Fix • Optimize</p>
</div>
""", unsafe_allow_html=True)

# ================= SESSION =================
if "fixed_code" not in st.session_state:
    st.session_state.fixed_code = ""

# ================= AI =================
@st.cache_data(show_spinner=False, ttl=3600)
def get_ai_reply(prompt, code_hash):
    try:
        time.sleep(0.5)
        response = model.generate_content(prompt)

        if hasattr(response, "text") and response.text:
            return response.text

        if hasattr(response, "candidates"):
            return response.candidates[0].content.parts[0].text

        return "⚠️ Empty response."

    except Exception as e:
        if "429" in str(e):
            return "RATE_LIMIT"
        return f"Error: {str(e)}"

# ================= ACTION =================
def process_action(task, prompt_ext, code, lang):
    if not code.strip():
        st.warning("⚠️ Paste code first!")
        return

    code_hash = hashlib.md5(code.encode()).hexdigest()
    prompt = f"{prompt_ext} for this {lang} code:\n\n{code}"

    with st.spinner("Processing..."):
        res = get_ai_reply(prompt, code_hash)

        if res == "RATE_LIMIT":
            st.error("❌ Too many requests.")
        else:
            st.markdown(f'<div class="output-card"><b>{task}:</b><br><br>{res}</div>', unsafe_allow_html=True)

# ================= RUN =================
def run_python_code(code):
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            exec(code, {})
        return output.getvalue()
    except Exception as e:
        return str(e)

def simulate_code(code, lang):
    prompt = f"Simulate output of this {lang} code. Only return output:\n\n{code}"
    return get_ai_reply(prompt, hashlib.md5(code.encode()).hexdigest())

# ================= UI =================
col1, col2 = st.columns([1, 4])

with col1:
    lang = st.selectbox("💻 Language", ["Python", "JavaScript", "C++", "Java", "Go", "Rust"])

with col2:
    code = st.text_area("📄 Paste your code", height=300)

# ================= TABS =================
tab1, tab2, tab3, tab4 = st.tabs(["🐞 Bug Report", "🧠 Explain", "🛠 Fix", "▶️ Run"])

# BUG
with tab1:
    if st.button("Find Bugs"):
        process_action("Bug Report", "Find bugs and issues", code, lang)

# EXPLAIN
with tab2:
    if st.button("Explain Code"):
        process_action("Explanation", "Explain clearly", code, lang)

# FIX
with tab3:
    if st.button("Fix Code"):
        if code.strip():
            prompt = f"Fix and optimize this {lang} code. Only return code:\n\n{code}"
            res = get_ai_reply(prompt, hashlib.md5(code.encode()).hexdigest())

            if res != "RATE_LIMIT":
                st.session_state.fixed_code = res
                st.code(res, language=lang.lower())

# RUN
with tab4:
    option = st.selectbox("Select Code Version", ["Original Code", "Fixed Code"])

    if st.button("Run Code"):
        selected = code if option == "Original Code" else st.session_state.fixed_code

        if not selected.strip():
            st.warning("No code to run")
        else:
            with st.spinner("Running..."):
                if lang == "Python":
                    result = run_python_code(selected)
                else:
                    result = simulate_code(selected, lang)

                st.code(result)

# ================= FOOTER =================
st.markdown("""
<hr>
<p style='text-align:center; color:gray;'>
Built with ❤️ using Gemini • 2026
</p>
""", unsafe_allow_html=True)
