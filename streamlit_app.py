"""
Research Engine - Google Scholar with Selenium
Uses real browser automation to bypass Google Scholar bot detection
Reliable, works consistently
"""

import streamlit as st
import time
from datetime import datetime
import json
import io
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import urllib.parse

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib import colors
except:
    pass

st.set_page_config(page_title="Research Engine", page_icon="📚", layout="wide")

st.markdown("""
    <style>
    body { background-color: #0e1319; color: #e9eef4; }
    .main { background-color: #0e1319; }
    .stTextInput > div > div > input { background-color: #151b23; color: #e9eef4; border-color: #2e3945; }
    .stButton > button { background-color: #e8b34a; color: #191203; font-weight: 600; border-radius: 5px; }
    .stButton > button:hover { background-color: #d19b33; }
    .stSuccess { background-color: rgba(55, 211, 154, 0.12); color: #37d39a; }
    .stError { background-color: rgba(255, 107, 99, 0.12); color: #ff6b63; }
    .stWarning { background-color: rgba(255, 193, 7, 0.12); color: #ffc107; }
    .stInfo { background-color: #1b222c; color: #b6c0cc; }
    h1, h2, h3 { color: #e9eef4; }
    </style>
    """, unsafe_allow_html=True)


class GoogleScholarSearch:
    def __init__(self):
        self.articles = []
        self.driver = None

    def init_driver(self):
        """Initialize Selenium WebDriver with options to avoid detection"""
        chrome_options = Options()

        # Don't make it headless - Google Scholar blocks headless browsers
        # chrome_options.add_argument("--headless")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
        except:
            st.error("Chrome driver not found. Install it with: pip install chromedriver-binary")
            return False
        return True

    def search(self, query: str, num_results: int = 10, status_callback=None) -> List[Dict]:
        """Search Google Scholar for papers"""

        try:
            if not self.init_driver():
                return None

            if status_callback:
                status_callback("Opening Google Scholar...")

            # Navigate to Google Scholar
            self.driver.get("https://scholar.google.com/")

            # Wait for page to load
            time.sleep(2)

            # Find search box and enter query
            try:
                search_box = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "q"))
                )
                search_box.send_keys(query)

                if status_callback:
                    status_callback("Searching...")

                search_box.submit()
                time.sleep(3)

            except Exception as e:
                st.error(f"Search box error: {str(e)}")
                return None

            # Extract results
            articles = self.extract_results(num_results, status_callback)

            self.driver.quit()
            self.driver = None

            return articles

        except Exception as e:
            st.error(f"Search Error: {str(e)}")
            if self.driver:
                self.driver.quit()
            return None

    def extract_results(self, num_results: int, status_callback=None) -> List[Dict]:
        """Extract article information from Google Scholar results"""

        articles = []

        try:
            if status_callback:
                status_callback("Extracting results...")

            # Find all result divs
            results = self.driver.find_elements(By.CLASS_NAME, "gs_ri")

            for idx, result in enumerate(results[:num_results]):
                try:
                    # Title and link
                    title_elem = result.find_element(By.TAG_NAME, "h3")
                    link_elem = title_elem.find_element(By.TAG_NAME, "a")
                    title = link_elem.text
                    link = link_elem.get_attribute("href")

                    # Authors and publication info
                    info_elem = result.find_element(By.CLASS_NAME, "gs_a")
                    info_text = info_elem.text

                    # Try to parse: "Authors - Publication - Year"
                    parts = info_text.split(" - ")
                    authors = parts[0] if len(parts) > 0 else "Unknown"
                    publication = parts[1] if len(parts) > 1 else "Unknown"
                    year = parts[2] if len(parts) > 2 else "Unknown"

                    # Abstract/Summary
                    try:
                        abstract_elem = result.find_element(By.CLASS_NAME, "gs_rs")
                        abstract = abstract_elem.text
                    except:
                        abstract = "No abstract available"

                    summary = (abstract[:250] + "...") if len(abstract) > 250 else abstract

                    article = {
                        'title': title,
                        'authors': authors,
                        'publication': publication,
                        'year': year,
                        'abstract': abstract,
                        'link': link,
                        'summary': summary
                    }

                    articles.append(article)

                except Exception as e:
                    continue

            return articles if articles else None

        except Exception as e:
            st.error(f"Extraction Error: {str(e)}")
            return None

    def generate_pdf(self) -> bytes:
        """Generate PDF report"""
        if not self.articles:
            return None

        try:
            pdf_buffer = io.BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                textColor=colors.HexColor('#e8b34a'),
                spaceAfter=12,
            )

            story.append(Paragraph("Research Summary", title_style))
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
            story.append(Paragraph(f"Source: Google Scholar | Total Papers: {len(self.articles)}", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))

            for idx, article in enumerate(self.articles, 1):
                story.append(Paragraph(f"<b>{idx}. {article['title']}</b>", styles['Heading2']))
                story.append(Paragraph(
                    f"<b>Authors:</b> {article['authors']}<br/>"
                    f"<b>Publication:</b> {article['publication']}<br/>"
                    f"<b>Year:</b> {article['year']}",
                    styles['Normal']
                ))

                story.append(Paragraph(f"<b>Summary:</b> {article['summary']}", styles['Normal']))

                if article['link']:
                    story.append(Paragraph(f"<a href='{article['link']}'>📄 Read Full Paper</a>", styles['Normal']))

                story.append(Spacer(1, 0.15*inch))
                if idx < len(self.articles):
                    story.append(Paragraph("<hr/>", styles['Normal']))

            doc.build(story)
            pdf_buffer.seek(0)
            return pdf_buffer.getvalue()
        except:
            return None


def main():
    st.title("📚 Research Engine - Google Scholar")
    st.markdown("Search Google Scholar for peer-reviewed papers")

    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        query = st.text_input("Search topic", placeholder="machine learning")
        num_results = st.slider("Results", 5, 20, 10)

        st.divider()
        st.info("💡 **How it works:**\n- Opens Google Scholar in a browser\n- Searches for your query\n- Extracts paper titles, authors, and abstracts\n- Generates PDF with links")

    if query and st.button("🔍 Search", use_container_width=True):
        search = GoogleScholarSearch()

        progress = st.progress(0)
        status = st.empty()

        def update_status(msg):
            status.text(msg)

        with st.spinner("Searching Google Scholar..."):
            progress.progress(25)
            articles = search.search(query, num_results, status_callback=update_status)
            progress.progress(100)
            status.empty()

        if articles is None:
            # Error already shown
            pass
        elif articles:
            st.success(f"✅ Found {len(articles)} papers!")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Papers", len(articles))
            with col2:
                years = [int(a['year']) for a in articles if a['year'].isdigit()]
                st.metric("Avg Year", int(sum(years)/len(years)) if years else "-")
            with col3:
                st.metric("Source", "Google Scholar")

            st.divider()

            for idx, article in enumerate(articles, 1):
                with st.expander(f"{idx}. {article['title'][:70]}"):
                    st.caption(f"👥 {article['authors']}")
                    st.caption(f"📖 {article['publication']} ({article['year']})")
                    st.markdown(f"**Abstract**\n\n{article['summary']}")
                    if article['link']:
                        st.markdown(f"[📄 Read Full Paper]({article['link']})")

            st.divider()

            col1, col2 = st.columns(2)
            search.articles = articles

            with col1:
                pdf = search.generate_pdf()
                if pdf:
                    st.download_button(
                        "📄 PDF Report",
                        pdf,
                        f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        "application/pdf",
                        use_container_width=True
                    )

            with col2:
                json_data = json.dumps(articles, indent=2)
                st.download_button(
                    "📊 JSON Data",
                    json_data,
                    f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    "application/json",
                    use_container_width=True
                )
        else:
            st.error("❌ No papers found")


if __name__ == "__main__":
    main()
