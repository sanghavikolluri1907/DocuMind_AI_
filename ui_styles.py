"""ui_styles.py - pill navigation, colourful hero and tonal buttons for DocuMind AI (Streamlit)."""
import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{
  --bg:#12131b; --side:#171923; --pill:#2b3245; --pill-hi:#38425f; --card:#1d2030; --line:#2c3148;
  --text:#eceef7; --dim:#a3a9c2; --blue:#a8c7fa; --ink:#0a1a3a;
  --grad:linear-gradient(120deg,#ff8a3d 0%,#e5456f 45%,#8a4dff 100%);
}
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:var(--bg);}
header[data-testid="stHeader"]{background:transparent;}

/* ---------- hero ---------- */
.dm-hero{position:relative;overflow:hidden;padding:2rem 2.2rem 1.8rem;margin-bottom:1.6rem;border-radius:28px;
  background:var(--grad);box-shadow:0 18px 50px rgba(138,77,255,.28);}
.dm-hero:before{content:"";position:absolute;inset:-40% -10% auto 55%;height:120%;border-radius:50%;
  background:radial-gradient(closest-side,rgba(255,255,255,.28),transparent);}
.dm-hero-title{position:relative;font-size:2.7rem;font-weight:800;color:#fff;letter-spacing:-.02em;line-height:1.1;}
.dm-hero-sub{position:relative;margin:.45rem 0 0;color:rgba(255,255,255,.92);font-size:1.05rem;}

/* ---------- sidebar navigation: coloured buttons ---------- */
section[data-testid="stSidebar"]{background:var(--side);border-right:1px solid var(--line);}
section[data-testid="stSidebar"] div[role="radiogroup"]{gap:10px;}
section[data-testid="stSidebar"] div[role="radiogroup"]>label{
  width:100%;padding:13px 18px;border-radius:14px;border:1px solid rgba(255,255,255,.08);cursor:pointer;
  background:linear-gradient(135deg,#2a56d6,#1c3fa8);box-shadow:0 3px 10px rgba(20,50,140,.35);
  transition:transform .15s ease,box-shadow .15s ease,filter .15s ease;}
section[data-testid="stSidebar"] div[role="radiogroup"]>label>div:first-child{display:none;}
section[data-testid="stSidebar"] div[role="radiogroup"]>label p{margin:0;font-size:.97rem;font-weight:600;color:#fff;}
section[data-testid="stSidebar"] div[role="radiogroup"]>label:hover{
  filter:brightness(1.18);transform:translateY(-1px);box-shadow:0 6px 16px rgba(47,107,255,.4);}
section[data-testid="stSidebar"] div[role="radiogroup"]>label:has(input:checked){
  background:linear-gradient(135deg,#3fa2ff,#7b5cff);border-color:rgba(255,255,255,.55);
  box-shadow:0 8px 22px rgba(95,120,255,.55);transform:none;}
section[data-testid="stSidebar"] div[role="radiogroup"]>label:has(input:checked) p{font-weight:800;}

/* ---------- buttons (pills) ---------- */
.stButton>button,.stDownloadButton>button,div[data-testid="stFormSubmitButton"]>button{
  padding:.65rem 1.5rem;border-radius:999px;border:none;background:var(--pill);color:var(--text);
  font-weight:600;font-size:.95rem;transition:all .15s ease;}
.stButton>button:hover,.stDownloadButton>button:hover{background:var(--pill-hi);color:#fff;transform:translateY(-1px);}
.stButton>button:focus-visible{outline:2px solid var(--blue);outline-offset:2px;}
.stButton>button[kind="primary"],button[data-testid="stBaseButton-primary"]{
  background:var(--grad);color:#fff;box-shadow:0 8px 22px rgba(229,69,111,.32);}
.stButton>button[kind="primary"]:hover,button[data-testid="stBaseButton-primary"]:hover{
  filter:brightness(1.1);box-shadow:0 10px 26px rgba(229,69,111,.45);}
section[data-testid="stSidebar"] .stButton>button{width:100%;background:var(--blue);color:var(--ink);font-weight:700;}
section[data-testid="stSidebar"] .stButton>button:hover{background:#c2d7fb;color:var(--ink);}

/* ---------- tabs as pills ---------- */
div[data-baseweb="tab-list"]{gap:8px;}
div[data-baseweb="tab-highlight"],div[data-baseweb="tab-border"]{display:none;}
button[data-baseweb="tab"]{padding:.5rem 1.3rem;border-radius:999px;background:var(--pill);color:var(--text);font-weight:500;}
button[data-baseweb="tab"]:hover{background:var(--pill-hi);}
button[data-baseweb="tab"][aria-selected="true"]{background:var(--blue);color:var(--ink);font-weight:700;}

/* ---------- cards, inputs ---------- */
div[data-testid="stMetric"]{padding:16px 20px;border-radius:20px;border:1px solid var(--line);
  background:linear-gradient(145deg,rgba(138,77,255,.20),rgba(255,138,61,.09));}
div[data-testid="stVerticalBlockBorderWrapper"]{border-radius:20px;}
div[data-testid="stExpander"]{border-radius:16px;background:var(--card);border:1px solid var(--line);}
.stTextArea textarea,.stTextInput input{background:var(--card);border:1px solid var(--line);border-radius:16px;}
.stTextArea textarea:focus,.stTextInput input:focus{border-color:#8a4dff;box-shadow:0 0 0 1px #8a4dff;}
section[data-testid="stFileUploaderDropzone"]{background:var(--card);border:1.5px dashed #4a5280;border-radius:20px;}
section[data-testid="stFileUploaderDropzone"]:hover{border-color:#e5456f;}
div[data-testid="stAlert"]{border-radius:16px;}
h2,h3{letter-spacing:-.01em;}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def render_hero() -> None:
    st.markdown('<div class="dm-hero"><div class="dm-hero-title">📄 DocuMind AI</div>'
                '<div class="dm-hero-sub">Intelligent Resume &amp; Job Description Analysis System</div></div>',
                unsafe_allow_html=True)
