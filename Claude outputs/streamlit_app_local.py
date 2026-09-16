import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
import io
from urllib.parse import quote

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

# Header with gradient
st.markdown('<div class="header-text">🔍 Atlas Research Engine</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle-text">Discover & Export Academic Research from Google Scholar</div>', unsafe_allow_html=True)

def search_google_scholar_selenium(query, num_results=10):
    """Open browser, search Google Scholar, extract results"""
    results = []

    try:
        # Create Chrome driver with proper container configuration
        options = webdriver.ChromeOptions()

        # Essential for containers
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--start-maximized")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # Disable images/CSS to speed up
        options.add_argument("--blink-settings=imagesEnabled=false")

        driver = webdriver.Chrome(options=options)

        try:
            st.info(f"🔍 Opening Google Scholar and searching for '{query}'...")

            # Navigate to Google Scholar
            scholar_url = f"https://scholar.google.com/scholar?q={quote(query)}&num={num_results}"
            driver.get(scholar_url)

            # Wait for results to load
            time.sleep(3)

            st.info("📄 Extracting paper information...")

            # Get all result containers
            result_containers = driver.find_elements(By.CSS_SELECTOR, "div.gs_ri")

            if not result_containers:
                st.warning("No results found on Google Scholar")
                return []

            for result in result_containers[:num_results]:
                try:
                    # Title and link
                    title_elem = result.find_element(By.CSS_SELECTOR, "h3 a")
                    title = title_elem.text
                    link = title_elem.get_attribute("href")

                    # Authors, publication, year
                    info_elem = result.find_element(By.CSS_SELECTOR, "div.gs_a")
                    info_text = info_elem.text
                    parts = [p.strip() for p in info_text.split(' - ')]

                    authors = parts[0] if len(parts) > 0 else "Unknown"
                    publication = parts[1] if len(parts) > 1 else "Unknown"
                    year = parts[2] if len(parts) > 2 else "Unknown"

                    # Abstract
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
                    st.warning(f"Error extracting paper: {str(e)[:50]}")
                    continue

        finally:
            driver.quit()

        return results

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.info("Make sure ChromeDriver is installed: `pip install webdriver-manager`")
        return []

def create_pdf_report(results, query):
    """Create PDF report"""
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
    return pdf_buffer

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    num_results = st.slider("Number of results", 5, 20, 10)

    st.markdown("---")
    st.markdown("### ✅ How it works:")
    st.markdown("""
    1. Enter your search query
    2. Click Search
    3. Browser opens Google Scholar
    4. Results are extracted automatically
    5. Download PDF/JSON/CSV
    """)

# Main search
col1, col2 = st.columns([3, 1])

with col1:
    query = st.text_input(
        "🔍 What do you want to research?",
        placeholder="e.g., machine learning, quantum computing...",
        label_visibility="collapsed"
    )

with col2:
    search_button = st.button("Search", use_container_width=True, type="primary")

# Search and results
if search_button and query:
    with st.spinner(f"🔍 Searching Google Scholar for '{query}'..."):
        results = search_google_scholar_selenium(query, num_results)

    if results:
        st.success(f"✅ Found {len(results)} papers!")

        # Display in tabs
        tab1, tab2, tab3 = st.tabs(["📄 View Results", "📊 Summary", "⬇️ Export"])

        with tab1:
            st.markdown("### Search Results")
            for idx, paper in enumerate(results, 1):
                with st.expander(f"**{idx}. {paper['title'][:80]}...**", expanded=(idx==1)):
                    st.markdown(f"**Authors:** {paper['authors']}")
                    st.markdown(f"**Publication:** {paper['publication']}")
                    st.markdown(f"**Year:** {paper['year']}")

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

            # Results table
            st.markdown("### All Results Table")
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

            # PDF Export
            st.subheader("📑 PDF Report")
            if st.button("Generate PDF Report", use_container_width=True):
                with st.spinner("Generating PDF..."):
                    pdf_buffer = create_pdf_report(results, query)
                    st.download_button(
                        label="⬇️ Download PDF Report",
                        data=pdf_buffer,
                        file_name=f"research_{query.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

            # JSON Export
            st.subheader("📋 JSON Data")
            json_data = json.dumps(results, indent=2)
            st.download_button(
                label="⬇️ Download JSON",
                data=json_data,
                file_name=f"research_{query.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )

            # CSV Export
            st.subheader("📊 CSV Spreadsheet")
            df_export = pd.DataFrame(results)
            csv_data = df_export.to_csv(index=False)
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_data,
                file_name=f"research_{query.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

    else:
        st.warning("❌ No results found. Check your query and try again.")

else:
    st.info("👉 Enter a search query and click 'Search' to begin!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Built with ❤️ using Streamlit + Selenium | Powered by Google Scholar</p>
    <p><small>Runs locally on your computer - Google Scholar won't block it!</small></p>
</div>
""", unsafe_allow_html=True)
