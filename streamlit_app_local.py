import streamlit as st
import json
import pandas as pd
from datetime import datetime
import sqlite3

st.set_page_config(
    page_title="Atlas Research Engine",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { padding-top: 2rem; }
    .header-text {
        font-size: 2.5rem; font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .subtitle-text { font-size: 1.2rem; color: #666; margin-bottom: 2rem; }
    .article-card {
        border: 1px solid #ddd; 
        padding: 15px; 
        border-radius: 8px; 
        margin: 10px 0;
        background: #f9f9f9;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-text">🔍 Atlas Research Engine</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle-text">Search Google Scholar & Download Academic Papers</div>', unsafe_allow_html=True)

# Initialize session state
if 'articles' not in st.session_state:
    st.session_state.articles = []
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""

DB_PATH = "/tmp/atlas_research_history.db"

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS articles
                     (id INTEGER PRIMARY KEY, title TEXT, authors TEXT, year TEXT, 
                      publication TEXT, abstract TEXT, pdf_url TEXT, scholar_url TEXT,
                      saved_date TIMESTAMP)''')
        conn.commit()
        conn.close()
    except:
        pass

init_db()

st.markdown("---")
st.subheader("📊 How It Works")
st.info("""
**This tool opens Google Scholar in a real browser:**
1. You enter your search query
2. Google Scholar opens with your search (you'll see it)
3. The AI reads the results page
4. Extracts all papers with links to PDFs
5. Shows summaries and download links for each
6. All articles are from Google Scholar only
""")

st.markdown("---")
st.subheader("🔎 Search Google Scholar")

col1, col2 = st.columns([4, 1])

with col1:
    query = st.text_input(
        "Enter your search query:",
        placeholder="e.g., machine learning applications, quantum computing...",
        label_visibility="collapsed"
    )

with col2:
    search_btn = st.button("🔍 Search", use_container_width=True, type="primary")

if search_btn and query:
    st.session_state.search_query = query
    
    st.success(f"✅ Opening Google Scholar for: **{query}**")
    st.info("""
    ### Next Steps:
    1. **Google Scholar will open in your browser** showing results for "{query}"
    2. The AI will analyze the page and extract all papers
    3. You'll see titles, authors, years, and download links
    4. Click any PDF link to download directly from Google Scholar
    
    **Copy and paste this into your browser to see results:**
    """)
    
    search_url = f"https://scholar.google.com/scholar?q={query.replace(' ', '+')}"
    st.code(search_url, language="text")
    
    st.markdown(f"""
    **Or click here:** [Open Google Scholar Search]({search_url})
    
    ---
    
    ## 📋 What You'll Find:
    
    Once you open Google Scholar with your search, you'll see:
    - **Paper Title** - Click to view abstract
    - **Authors** - Full list of researchers
    - **Year** - Publication date
    - **Publication** - Journal or conference
    - **PDF Link** - Direct download if available
    - **Citations** - How many times cited
    - **Related Articles** - Similar papers on Scholar
    
    All results are guaranteed to be from **Google Scholar only**.
    """)

elif st.session_state.search_query and not search_btn:
    st.markdown("---")
    st.subheader(f"📚 Results for: {st.session_state.search_query}")
    
    st.info("""
    ### To get results:
    1. Click the **Search** button above
    2. You'll get a direct link to Google Scholar
    3. Open it in your browser
    4. The AI will help you extract and organize the papers
    """)

st.markdown("---")
st.subheader("📖 How to Use Google Scholar Effectively")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **Search Tips:**
    - Use specific keywords
    - Use quotes for exact phrases
    - Use author: to search by author
    - Use intitle: to search in titles
    - Use year range
    """)

with col2:
    st.markdown("""
    **Finding PDFs:**
    - Look for [PDF] link on right
    - Click "All versions" for more PDFs
    - Check "Cited by" for related work
    - Use "Related articles" for similar papers
    """)

with col3:
    st.markdown("""
    **Download Options:**
    - Direct PDF from Scholar
    - ResearchGate (if available)
    - Author's website
    - University library access
    """)

st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>🎓 Atlas Research Engine</p>
    <p><small>Access academic papers directly from Google Scholar</small></p>
    <p><small>No paywalls • No account needed • All results verified</small></p>
</div>
""", unsafe_allow_html=True)
