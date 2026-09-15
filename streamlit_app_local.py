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

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 16px;
        font-weight: 500;
    }
    .header-text {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }
    .subtitle-text {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'pdf_history' not in st.session_state:
    st.session_state.pdf_history = []
if 'pdf_buffer' not in st.session_state:
    st.session_state.pdf_buffer = None
if 'pdf_filename' not in st.session_state:
    st.session_state.pdf_filename = None

# Database setup
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

def save_pdf_to_history(query, num_results, file_name):
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

def delete_old_pdfs():
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
delete_old_pdfs()

# Header
st.markdown('<div class="header-text">🔍 Atlas Research Engine</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle-text">Discover & Export Academic Research from Google Scholar</div>', unsafe_allow_html=True)

def search_google_scholar_selenium(query, num_results=10):
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
        options.add_argument("--disable-breakpad")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-hang-monitor")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-sync")
        options.add_argument("--mute-audio")
        options.add_argument("--no-first-run")
        options.add_argument("--start-maximized")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36")
        options.add_argument("--blink-settings=imagesEnabled=false")

        driver = webdriver.Chrome(options=options)

        try:
            st.info(f"🔍 Opening Google Scholar and searching for '{query}'...")
            scholar_url = f"https://scholar.google.com/scholar?q={quote(query)}&num={num_results}"
            driver.get(scholar_url)
            time.sleep(3)
            st.info("📄 Extracting paper information...")

            result_containers = driver.find_elements(By.CSS_SELECTOR, "div.gs_ri")

            if not result_containers:
                st.warning("No results found on Google Scholar")
                return []

            for result in result_containers[:num_results]:
                try:
                    title_elem = result.find_element(By.CSS_SELECTOR, "h3 a")
                    title = title_elem.text
                    link = title_elem.get_attribute("href")

                    info_elem = result.find_element(By.CSS_SELECTOR, "div.gs_a")
                    info_text = info_elem.text
                    parts = [p.strip() for p in info_text.split(' - ')]

                    authors = parts[0] if len(parts) > 0 else "Unknown"
                    publication = parts[1] if len(parts) > 1 else "Unknown"
                    year = parts[2] if len(parts) > 2 else "Unknown"

                    try:
                        abstract_elem = result.find_element(By.CSS_SELECTOR, "div.gs_rs")
                        abstract = abstract_elem.text
                    except:
                        abstract = "No abstract available"

                    results.append({
                        'title': title,
                        'authors': authors,
                        'publication': publication,
                        'year': year,
                        'abstract': abstract,
                        'link': link
                    })
                    time.sleep(0.5)

                except Exception as e:
                    continue

        finally:
            driver.quit()

        return results

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return []

def create_pdf_report(results, query):
    try:
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=30,
            alignment=1
        )

        story.append(Paragraph(f"📚 Google Scholar Research Report: {query}", title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(f"<b>Total Papers Found:</b> {len(results)}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))

        for idx, paper in enumerate(results, 1):
            story.append(Paragraph(f"<b>{idx}. {paper['title']}</b>", styles['Heading2']))
            story.append(Paragraph(f"<b>Authors:</b> {paper['authors']}", styles['Normal']))
            story.append(Paragraph(f"<b>Publication:</b> {paper['publication']}", styles['Normal']))
            story.append(Paragraph(f"<b>Year:</b> {paper['year']}", styles['Normal']))

            if paper['link']:
                story.append(Paragraph(f"<b>Link:</b> <a href='{paper['link']}'>View Paper</a>", styles['Normal']))

            abstract_text = paper['abstract'][:300] + "..." if len(paper['abstract']) > 300 else paper['abstract']
            story.append(Paragraph(f"<b>Abstract:</b> {abstract_text}", styles['Normal']))
            story.append(Spacer(1, 0.15*inch))

        doc.build(story)
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
    except Exception as e:
        st.error(f"PDF Error: {str(e)}")
        return None

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    num_results = st.slider("Number of results", 5, 20, 10, help="How many papers to retrieve")
    st.divider()
    st.markdown("### 📚 How It Works")
    st.info("1. Enter a research topic\n2. Browser searches Google Scholar\n3. Extract papers automatically\n4. Download as PDF, JSON, or CSV")
    st.divider()
    st.markdown("### 💡 Tips")
    st.caption("• Use specific keywords\n• Try recent topics\n• See your history below")

# Main interface
st.markdown("---")
st.subheader("🔎 Search Research Papers")

col1, col2 = st.columns([4, 1])

with col1:
    query = st.text_input("What would you like to research?", placeholder="e.g., machine learning, quantum computing...", label_visibility="collapsed")

with col2:
    search_button = st.button("🔍 Search", use_container_width=True, type="primary")

# Search
if search_button and query:
    with st.spinner(f"🔍 Searching for '{query}'..."):
        results = search_google_scholar_selenium(query, num_results)

    if results:
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
            st.markdown("### Summary Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Papers", len(results))
            with col2:
                st.metric("With Links", sum(1 for p in results if p['link']))
            with col3:
                st.metric("With Abstract", sum(1 for p in results if 'No abstract' not in p['abstract']))

            st.markdown("### All Results")
            df = pd.DataFrame([
                {
                    'Title': p['title'][:50] + '...' if len(p['title']) > 50 else p['title'],
                    'Authors': p['authors'][:40] + '...' if len(p['authors']) > 40 else p['authors'],
                    'Year': p['year'],
                    'Publication': p['publication'][:30] + '...' if len(p['publication']) > 30 else p['publication']
                }
                for p in results
            ])
            st.dataframe(df, use_container_width=True)

        with tab3:
            st.markdown("### Export Options")

            # PDF Section
            st.subheader("📑 PDF Report")
            if st.button("📥 Generate PDF", use_container_width=True, key="gen_pdf"):
                pdf_data = create_pdf_report(results, query)
                if pdf_data:
                    st.session_state.pdf_buffer = pdf_data
                    st.session_state.pdf_filename = f"research_{query.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    save_pdf_to_history(query, len(results), st.session_state.pdf_filename)
                    st.success("✅ PDF ready to download!")
                else:
                    st.error("Failed to create PDF")

            # Show download button if PDF is ready
            if st.session_state.pdf_buffer:
                st.download_button(
                    label="⬇️ Download PDF",
                    data=st.session_state.pdf_buffer,
                    file_name=st.session_state.pdf_filename,
                    mime="application/pdf",
                    use_container_width=True,
                    key="download_pdf"
                )

            st.divider()

            # JSON Export
            st.subheader("📋 JSON Data")
            json_data = json.dumps(results, indent=2)
            st.download_button(
                label="⬇️ Download JSON",
                data=json_data,
                file_name=f"research_{query.replace(' ', '_')}.json",
                mime="application/json",
                use_container_width=True
            )

            st.divider()

            # CSV Export
            st.subheader("📊 CSV Spreadsheet")
            df_export = pd.DataFrame(results)
            csv_data = df_export.to_csv(index=False)
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_data,
                file_name=f"research_{query.replace(' ', '_')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        with tab4:
            st.markdown("### 📜 PDF History (Last 30 days)")
            history = get_pdf_history()
            if history:
                for q, nr, created, fname in history:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{q}** • {nr} papers")
                        st.caption(f"📅 {created[:10]}")
                    with col2:
                        st.caption("✓ Saved")
            else:
                st.info("No PDFs yet. Generate one above!")

    else:
        st.warning("❌ No results found.")

else:
    st.info("👉 Enter a query and click Search!")

st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Built with ❤️ using Streamlit + Selenium</p>
    <p><small>PDFs auto-delete after 30 days</small></p>
</div>
""", unsafe_allow_html=True)
