import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import json
import pandas as pd
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import colors
import io
from urllib.parse import quote
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
    .stTabs [data-baseweb="tab-list"] button { font-size: 16px; font-weight: 500; }
    .header-text {
        font-size: 2.5rem; font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }
    .subtitle-text { font-size: 1.2rem; color: #666; margin-bottom: 2rem; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-text">🔍 Atlas Research Engine</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle-text">Discover & Export Academic Research from Google Scholar</div>', unsafe_allow_html=True)

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = None
if 'query' not in st.session_state:
    st.session_state.query = None

DB_PATH = "/tmp/atlas_research_history.db"

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS pdf_history
                     (id INTEGER PRIMARY KEY, query TEXT, num_results INTEGER, 
                      created_date TIMESTAMP, file_name TEXT)''')
        conn.commit()
        conn.close()
    except:
        pass

def save_to_history(query, num_results, file_name):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT INTO pdf_history (query, num_results, created_date, file_name) VALUES (?, ?, ?, ?)',
                  (query, num_results, datetime.now(), file_name))
        conn.commit()
        conn.close()
    except:
        pass

def get_pdf_history():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT query, num_results, created_date, file_name FROM pdf_history ORDER BY created_date DESC LIMIT 50')
        rows = c.fetchall()
        conn.close()
        return rows
    except:
        return []

def cleanup_old_pdfs():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        cutoff_date = datetime.now() - timedelta(days=30)
        c.execute('DELETE FROM pdf_history WHERE created_date < ?', (cutoff_date,))
        conn.commit()
        conn.close()
    except:
        pass

init_db()
cleanup_old_pdfs()

def search_google_scholar(query, num_results=10):
    results = []
    try:
        options = webdriver.ChromeOptions()
        options.binary_location = "/usr/bin/chromium"
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-web-resources")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-hang-monitor")
        options.add_argument("--disable-sync")
        options.add_argument("--mute-audio")
        options.add_argument("--no-first-run")
        options.add_argument("--start-maximized")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0")
        options.add_argument("--blink-settings=imagesEnabled=false")

        driver = webdriver.Chrome(options=options)

        try:
            st.info(f"🔍 Searching Google Scholar for '{query}'...")
            driver.get(f"https://scholar.google.com/scholar?q={quote(query)}&num={num_results}")
            time.sleep(3)

            for result in driver.find_elements(By.CSS_SELECTOR, "div.gs_ri")[:num_results]:
                try:
                    title_elem = result.find_element(By.CSS_SELECTOR, "h3 a")
                    title = title_elem.text
                    link = title_elem.get_attribute("href")

                    info_elem = result.find_element(By.CSS_SELECTOR, "div.gs_a")
                    parts = [p.strip() for p in info_elem.text.split(' - ')]

                    authors = parts[0] if len(parts) > 0 else "Unknown"
                    publication = parts[1] if len(parts) > 1 else "Unknown"
                    year = parts[2] if len(parts) > 2 else "Unknown"

                    try:
                        abstract = result.find_element(By.CSS_SELECTOR, "div.gs_rs").text
                    except:
                        abstract = "No abstract"

                    results.append({'title': title, 'authors': authors, 'publication': publication, 'year': year, 'abstract': abstract, 'link': link})
                    time.sleep(0.5)
                except:
                    continue

        finally:
            driver.quit()

        return results
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []

def make_pdf(results, query):
    """Create PDF and return bytes"""
    try:
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#1f77b4'), spaceAfter=30, alignment=1)

        story.append(Paragraph(f"📚 Google Scholar Report: {query}", title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(f"<b>Papers Found:</b> {len(results)}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))

        for idx, paper in enumerate(results, 1):
            story.append(Paragraph(f"<b>{idx}. {paper['title']}</b>", styles['Heading2']))
            story.append(Paragraph(f"<b>Authors:</b> {paper['authors']}", styles['Normal']))
            story.append(Paragraph(f"<b>Publication:</b> {paper['publication']}", styles['Normal']))
            story.append(Paragraph(f"<b>Year:</b> {paper['year']}", styles['Normal']))
            if paper['link']:
                story.append(Paragraph(f"<b>Link:</b> <a href='{paper['link']}'>View Paper</a>", styles['Normal']))
            abstract = paper['abstract'][:300] + "..." if len(paper['abstract']) > 300 else paper['abstract']
            story.append(Paragraph(f"<b>Abstract:</b> {abstract}", styles['Normal']))
            story.append(Spacer(1, 0.15*inch))

        doc.build(story)
        buf.seek(0)
        return buf.getvalue()
    except Exception as e:
        st.error(f"PDF Error: {str(e)}")
        return None

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    num_results = st.slider("Number of results", 5, 20, 10)
    st.divider()
    st.markdown("### 📚 How It Works")
    st.info("1. Enter topic\n2. Search Google Scholar\n3. Extract papers\n4. Export as PDF/JSON/CSV")

st.markdown("---")
st.subheader("🔎 Search Research Papers")

col1, col2 = st.columns([4, 1])
with col1:
    query = st.text_input("What would you like to research?", placeholder="e.g., machine learning...", label_visibility="collapsed")
with col2:
    search_btn = st.button("🔍 Search", use_container_width=True, type="primary")

if search_btn and query:
    with st.spinner(f"🔍 Searching..."):
        st.session_state.results = search_google_scholar(query, num_results)
        st.session_state.query = query

if st.session_state.results:
    results = st.session_state.results
    query = st.session_state.query
    
    st.success(f"✅ Found **{len(results)} papers!**")

    tab1, tab2, tab3, tab4 = st.tabs(["📖 Papers", "📊 Analytics", "⬇️ Downloads", "📜 History"])

    with tab1:
        st.markdown("### Search Results")
        for idx, paper in enumerate(results, 1):
            with st.expander(f"**{idx}. {paper['title'][:80]}...**", expanded=(idx==1)):
                st.markdown(f"**Authors:** {paper['authors']}\n**Publication:** {paper['publication']}\n**Year:** {paper['year']}")
                if paper['link']:
                    st.markdown(f"[🔗 View Paper]({paper['link']})")
                st.markdown(f"**Abstract:** {paper['abstract']}")

    with tab2:
        st.markdown("### Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total", len(results))
        with col2:
            st.metric("With Links", sum(1 for p in results if p['link']))
        with col3:
            st.metric("With Abstract", sum(1 for p in results if 'No abstract' not in p['abstract']))

        df = pd.DataFrame([{'Title': p['title'][:50], 'Year': p['year'], 'Authors': p['authors'][:40]} for p in results])
        st.dataframe(df, use_container_width=True)

    with tab3:
        st.markdown("### Export Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("📑 PDF")
            pdf_data = make_pdf(results, query)
            if pdf_data:
                fname = f"research_{query.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
                st.download_button(
                    label="⬇️ Download PDF",
                    data=pdf_data,
                    file_name=fname,
                    mime="application/pdf",
                    use_container_width=True
                )
                save_to_history(query, len(results), fname)
                st.caption("✅ Ready")

        with col2:
            st.subheader("📋 JSON")
            json_data = json.dumps(results, indent=2)
            st.download_button(
                label="⬇️ Download JSON",
                data=json_data,
                file_name=f"research_{query.replace(' ', '_')}.json",
                mime="application/json",
                use_container_width=True
            )

        with col3:
            st.subheader("📊 CSV")
            csv_data = pd.DataFrame(results).to_csv(index=False)
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_data,
                file_name=f"research_{query.replace(' ', '_')}.csv",
                mime="text/csv",
                use_container_width=True
            )

    with tab4:
        st.markdown("### 📜 History (30 days)")
        history = get_pdf_history()
        if history:
            for q, nr, created, fname in history:
                st.write(f"**{q}** • {nr} papers • {created[:10]}")
        else:
            st.info("No PDFs yet")

else:
    st.info("👉 Enter a query and click Search!")

st.markdown("---")
st.markdown("<div style='text-align: center'><p>Built with Streamlit + Selenium | Auto-delete after 30 days</p></div>", unsafe_allow_html=True)
