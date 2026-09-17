import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
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
import re

# Page config
st.set_page_config(
    page_title="Atlas Research Engine",
    page_icon="🔍",
    layout="wide"
)

# Custom styling
st.markdown("""
    <style>
    .main {
        max-width: 1200px;
    }
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 18px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🔍 Atlas Research Engine")
st.markdown("Search Google Scholar and export your findings as PDF reports")

# Initialize session state
if 'articles' not in st.session_state:
    st.session_state.articles = []
if 'captcha_waiting' not in st.session_state:
    st.session_state.captcha_waiting = False
if 'captcha_done' not in st.session_state:
    st.session_state.captcha_done = False

def format_citation(article, style='APA'):
    """Format citation in different styles"""
    title = article.get('title', 'Untitled')
    authors = article.get('authors', 'Unknown')
    year = article.get('year', 'n.d.')
    publication = article.get('publication', 'Unknown')
    link = article.get('scholar_link', '')

    if style == 'APA':
        return f"{authors} ({year}). {title}. {publication}. Retrieved from {link}"
    elif style == 'MLA':
        return f"{authors}. \"{title}.\" {publication}, {year}. Web. {link}"
    elif style == 'Chicago':
        return f"{authors}. \"{title}.\" {publication} ({year}). Accessed from {link}"
    elif style == 'BibTeX':
        key = title[:20].replace(' ', '').lower()
        return f"@article{{{key},\n  title={{{title}}},\n  author={{{authors}}},\n  journal={{{publication}}},\n  year={{{year}}},\n  url={{{link}}}\n}}"
    return authors

def calculate_credibility(article):
    """Calculate credibility score 0-100"""
    score = 50
    if len(article.get('abstract', '')) > 200:
        score += 15
    publication = (article.get('publication', '') or '').lower()
    quality_sources = ['nature', 'science', 'ieee', 'acm', 'proceedings', 'journal', 'conference']
    if any(s in publication for s in quality_sources):
        score += 15
    year_text = article.get('year', '')
    try:
        year = int(year_text)
        years_old = 2025 - year
        if years_old <= 3:
            score += 15
        elif years_old <= 7:
            score += 10
        elif years_old <= 15:
            score += 5
    except:
        pass
    return min(100, score)

def scrape_google_scholar(query, num_results=10):
    """Scrape Google Scholar using Selenium"""
    articles = []
    page = 0

    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")

        driver = webdriver.Chrome(options=options)
        status_placeholder = st.empty()

        try:
            while len(articles) < num_results:
                start = page * 10
                driver.get(f"https://scholar.google.com/scholar?q={quote(query)}&start={start}")

                # Check if CAPTCHA appears
                st.session_state.captcha_done = False
                captcha_detected = False
                start_time = time.time()
                max_wait = 10  # Wait 10 seconds to see if CAPTCHA appears

                while (time.time() - start_time) < max_wait and not st.session_state.captcha_done:
                    try:
                        results = driver.find_elements(By.CSS_SELECTOR, "div.gs_ri")
                        if len(results) > 0:
                            break  # Results loaded, no CAPTCHA
                    except:
                        pass
                    time.sleep(1)

                # If CAPTCHA detected (no results after wait), show button and wait for user
                try:
                    results = driver.find_elements(By.CSS_SELECTOR, "div.gs_ri")
                    if len(results) == 0:
                        captcha_detected = True
                except:
                    captcha_detected = True

                if captcha_detected:
                    st.session_state.captcha_waiting = True
                    with status_placeholder.container():
                        st.warning("⚠️ Complete the CAPTCHA in the Chrome window, then click below")
                        if st.button("✅ CAPTCHA Done - Continue", key=f"captcha_btn_{page}_{int(time.time())}"):
                            st.session_state.captcha_done = True
                            time.sleep(2)
                            st.rerun()
                    return None  # Wait for next rerun

                # Extract results
                time.sleep(1)
                results = driver.find_elements(By.CSS_SELECTOR, "div.gs_ri")

                if not results:
                    status_placeholder.empty()
                    break

                for result in results:
                    if len(articles) >= num_results:
                        break

                    try:
                        title_elem = result.find_element(By.CSS_SELECTOR, "h3 a")
                        title = title_elem.text
                        scholar_link = title_elem.get_attribute("href")

                        pdf_link = None
                        try:
                            pdf_elem = result.find_element(By.CSS_SELECTOR, "a[href*='.pdf']")
                            pdf_link = pdf_elem.get_attribute("href")
                        except:
                            pass

                        try:
                            info_elem = result.find_element(By.CSS_SELECTOR, "div.gs_a")
                            info_text = info_elem.text
                            parts = [p.strip() for p in info_text.split(' - ')]
                            authors = parts[0] if len(parts) > 0 else "Unknown"
                            publication = parts[1] if len(parts) > 1 else "Unknown"
                            year = parts[2] if len(parts) > 2 else "Unknown"
                        except:
                            authors = "Unknown"
                            publication = "Unknown"
                            year = "Unknown"

                        try:
                            abstract_elem = result.find_element(By.CSS_SELECTOR, "div.gs_rs")
                            abstract = abstract_elem.text
                        except:
                            abstract = "No abstract available"

                        articles.append({
                            'title': title,
                            'authors': authors,
                            'publication': publication,
                            'year': year,
                            'abstract': abstract,
                            'scholar_link': scholar_link,
                            'pdf_link': pdf_link
                        })

                        time.sleep(0.3)

                    except Exception as e:
                        continue

                page += 1
                if page > 5:
                    break

        finally:
            driver.quit()

        status_placeholder.empty()
        st.session_state.captcha_waiting = False
        return articles[:num_results]

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return []

def create_pdf_report(articles, query, citation_format='APA'):
    """Create PDF report"""
    try:
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        story = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=22,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=15,
            alignment=1
        )

        heading_style = ParagraphStyle(
            'ArticleTitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=10
        )

        credibility_style = ParagraphStyle(
            'Credibility',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#059669'),
            spaceAfter=8,
            fontName='Helvetica-Bold'
        )

        story.append(Paragraph(f"📚 Research Report: {query}", title_style))
        story.append(Paragraph(f"Citation Format: {citation_format}", styles['Normal']))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(f"<b>Total Papers Found:</b> {len(articles)}", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))

        for idx, article in enumerate(articles, 1):
            credibility = calculate_credibility(article)

            story.append(Paragraph(f"<b>{idx}. {article['title']}</b>", heading_style))
            story.append(Paragraph(f"Credibility Score: {credibility}/100", credibility_style))
            story.append(Paragraph(f"<b>Authors:</b> {article['authors']}", styles['Normal']))
            story.append(Paragraph(f"<b>Publication:</b> {article['publication']}", styles['Normal']))
            story.append(Paragraph(f"<b>Year:</b> {article['year']}", styles['Normal']))

            if article['scholar_link']:
                story.append(Paragraph(f"<b>🔗 Link:</b> <a href='{article['scholar_link']}'>View Paper</a>", styles['Normal']))

            if article['pdf_link']:
                story.append(Paragraph(f"<b>📄 PDF:</b> <a href='{article['pdf_link']}'>Download PDF</a>", styles['Normal']))

            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(f"<b>Citation ({citation_format}):</b>", styles['Normal']))
            citation_text = format_citation(article, citation_format)
            story.append(Paragraph(citation_text, styles['Normal']))

            story.append(Paragraph(f"<b>Abstract:</b> {article['abstract'][:300]}...", styles['Normal']))
            story.append(Spacer(1, 0.15*inch))

        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("_" * 80, styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
        copyright_style = ParagraphStyle(
            'Copyright',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#666666'),
            alignment=1
        )
        story.append(Paragraph(f"© {datetime.now().year} Shashank Upadhyay. All rights reserved.", copyright_style))

        doc.build(story)
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()

    except Exception as e:
        st.error(f"PDF Error: {str(e)}")
        return None

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    num_results = st.slider("Number of results", 5, 20, 10)

    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    **Atlas Research Engine** searches Google Scholar with Selenium and exports findings as PDF reports.

    **How it works:**
    - Enter a search query
    - If CAPTCHA appears, complete it and click the button
    - View results in tabs
    - Export as PDF, JSON, or CSV
    """)

# Main search interface
col1, col2 = st.columns([3, 1])

with col1:
    query = st.text_input(
        "🔍 What would you like to research?",
        placeholder="e.g., machine learning, climate change, quantum computing...",
        label_visibility="collapsed"
    )

with col2:
    search_button = st.button("Search", use_container_width=True, type="primary")

# Search and display results
if search_button and query:
    with st.spinner(f"🔍 Searching Google Scholar for '{query}'..."):
        results = scrape_google_scholar(query, num_results)

    if results:
        st.session_state.articles = results
        st.success(f"✅ Found {len(results)} papers!")

if st.session_state.articles:
    results = st.session_state.articles

    # Display results in tabs
    tab1, tab2, tab3 = st.tabs(["📄 View Results", "📊 Summary", "⬇️ Export"])

    with tab1:
        st.markdown("### Search Results")
        for idx, paper in enumerate(results, 1):
            with st.expander(f"**{idx}. {paper['title'][:80]}...**", expanded=(idx==1)):
                st.markdown(f"**Authors:** {paper['authors']}")
                st.markdown(f"**Publication:** {paper['publication']}")
                st.markdown(f"**Year:** {paper['year']}")

                if paper['scholar_link']:
                    st.markdown(f"[🔗 View Paper]({paper['scholar_link']})")

                if paper['pdf_link']:
                    st.markdown(f"[📄 Download PDF]({paper['pdf_link']})")

                st.markdown(f"**Abstract:** {paper['abstract']}")

    with tab2:
        st.markdown("### Summary Statistics")

        years = [p['year'] for p in results if p['year'] != 'Unknown']

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Papers", len(results))
        with col2:
            st.metric("With Links", sum(1 for p in results if p['scholar_link']))
        with col3:
            if years:
                valid_years = [int(y) for y in years if y.isdigit()]
                if valid_years:
                    st.metric("Avg Year", f"{sum(valid_years) / len(valid_years):.0f}")

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

        st.markdown("### 📚 Citation Formats")
        st.info("Select a paper to view citations in different formats:")

        selected_paper_idx = st.selectbox(
            "Choose a paper:",
            range(len(results)),
            format_func=lambda x: f"{x+1}. {results[x]['title'][:60]}..."
        )

        if selected_paper_idx is not None:
            paper = results[selected_paper_idx]
            col1, col2 = st.columns(2)
            with col1:
                with st.expander("📖 APA Style"):
                    st.code(format_citation(paper, 'APA'), language="text")
                with st.expander("📖 MLA Style"):
                    st.code(format_citation(paper, 'MLA'), language="text")
            with col2:
                with st.expander("📖 Chicago Style"):
                    st.code(format_citation(paper, 'Chicago'), language="text")
                with st.expander("📖 BibTeX"):
                    st.code(format_citation(paper, 'BibTeX'), language="text")

    with tab3:
        st.markdown("### Export Options")

        st.subheader("📑 PDF Report")
        citation_format = st.radio(
            "Select citation format:",
            ["APA", "MLA", "Chicago", "BibTeX"],
            horizontal=True
        )

        pdf_data = create_pdf_report(results, query, citation_format)
        if pdf_data:
            st.download_button(
                label=f"📥 Download PDF ({citation_format} Citations)",
                data=pdf_data,
                file_name=f"research_{query.replace(' ', '_')}_{citation_format}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="pdf_download"
            )
            st.success(f"✅ PDF ready with credibility scores, links, and {citation_format} citations!")

        st.subheader("📋 JSON Data")
        json_data = json.dumps(results, indent=2)
        st.download_button(
            label="⬇️ Download JSON",
            data=json_data,
            file_name=f"research_{query.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            use_container_width=True
        )

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
    st.info("👉 Enter a search query and click **Search** to find papers on Google Scholar")
