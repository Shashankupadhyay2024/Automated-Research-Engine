"""
Research Engine - Fixed Socket Timeout
Stable, production-ready version
"""

import streamlit as st
import urllib.request
import urllib.error
import urllib.parse
import socket
import time
from datetime import datetime
import json
import io
from typing import List, Dict
import xml.etree.ElementTree as ET

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
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


class ArxivSearch:
    def __init__(self):
        self.articles = []
        self.last_request_time = 0

    def respect_rate_limit(self, delay_seconds: int = 5):
        """Respect arXiv rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < delay_seconds:
            wait_time = delay_seconds - elapsed
            time.sleep(wait_time)
        self.last_request_time = time.time()

    def parse_xml(self, xml_string: str) -> List[Dict]:
        """Parse arXiv Atom XML response"""
        articles = []
        try:
            root = ET.fromstring(xml_string)
            ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}

            for entry in root.findall('atom:entry', ns):
                try:
                    title_elem = entry.find('atom:title', ns)
                    title = title_elem.text if title_elem is not None else "No title"
                    title = title.replace('\n', ' ').strip()

                    authors = []
                    for author in entry.findall('atom:author', ns):
                        name_elem = author.find('atom:name', ns)
                        if name_elem is not None:
                            authors.append(name_elem.text)
                    author_str = ", ".join(authors[:5]) if authors else "Unknown"

                    published_elem = entry.find('atom:published', ns)
                    published = published_elem.text if published_elem is not None else ""
                    year = published[:4] if published else "Unknown"

                    summary_elem = entry.find('atom:summary', ns)
                    abstract = summary_elem.text if summary_elem is not None else "No abstract"
                    abstract = abstract.replace('\n', ' ').strip()

                    id_elem = entry.find('atom:id', ns)
                    arxiv_id = id_elem.text if id_elem is not None else ""
                    arxiv_id = arxiv_id.split('/abs/')[-1] if '/abs/' in arxiv_id else arxiv_id

                    category_elem = entry.find('arxiv:primary_category', ns)
                    category = category_elem.get('term', 'Unknown') if category_elem is not None else 'Unknown'

                    pdf_link = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

                    article = {
                        'title': title,
                        'authors': author_str,
                        'publication': f"arXiv ({category})",
                        'year': year,
                        'abstract': abstract,
                        'link': pdf_link,
                        'summary': (abstract[:250] + "...") if len(abstract) > 250 else abstract,
                        'arxiv_id': arxiv_id
                    }

                    articles.append(article)

                except Exception as e:
                    continue

            return articles

        except Exception as e:
            return []

    def search(self, query: str, num_results: int = 10, status_callback=None) -> List[Dict]:
        """Search arXiv with proper timeout handling"""

        try:
            self.respect_rate_limit(delay_seconds=5)

            search_string = f"all:{query}"

            params = {
                'search_query': search_string,
                'start': 0,
                'max_results': min(num_results, 50),
                'sortBy': 'relevance',
                'sortOrder': 'descending'
            }

            base_url = "https://export.arxiv.org/api/query"
            query_string = urllib.parse.urlencode(params)
            full_url = f"{base_url}?{query_string}"

            if status_callback:
                status_callback("Connecting to arXiv...")

            req = urllib.request.Request(
                full_url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
                    'Accept-Encoding': 'gzip, deflate'
                }
            )

            # Make request with 120 second timeout
            with urllib.request.urlopen(req, timeout=120) as response:
                if status_callback:
                    status_callback("Reading response...")
                xml_data = response.read().decode('utf-8')

            if status_callback:
                status_callback("Parsing results...")

            articles = self.parse_xml(xml_data)
            return articles

        except urllib.error.HTTPError as e:
            if e.code == 429:
                st.error("🚫 Rate Limited - Wait 60-120 seconds")
                return None
            elif e.code == 503:
                st.warning("⚠️ arXiv is temporarily overloaded")
                st.info("arXiv gets overloaded sometimes. Try again in 5-10 minutes.")
                return None
            elif e.code == 500:
                st.warning("⚠️ arXiv server error (500)")
                st.info("Try again in a moment")
                return None
            else:
                st.error(f"HTTP Error {e.code}")
                return None

        except socket.timeout:
            st.warning("⚠️ Connection Timeout")
            st.info("arXiv is slow or offline. Try again in 5-10 minutes.")
            return None

        except urllib.error.URLError as e:
            st.error(f"Connection Error: {e.reason}")
            st.info("Check your internet connection or try again later")
            return None

        except TimeoutError:
            st.warning("⚠️ Request Timeout")
            st.info("arXiv is very slow. Try again in a few moments.")
            return None

        except Exception as e:
            st.error(f"Error: {str(e)}")
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
            story.append(Paragraph(f"Source: arXiv | Total Papers: {len(self.articles)}", styles['Normal']))
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
    st.title("📚 Research Engine")
    st.markdown("Search arXiv for peer-reviewed papers")

    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        query = st.text_input("Search topic", placeholder="machine learning")
        num_results = st.slider("Results", 5, 50, 10)

        st.divider()
        st.info("💡 **Tip:** Start with simple searches like 'neural networks' or 'machine learning'")

    if query and st.button("🔍 Search", use_container_width=True):
        search = ArxivSearch()

        progress = st.progress(0)
        status = st.empty()

        def update_status(msg):
            status.text(msg)

        with st.spinner("Searching arXiv..."):
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
                st.metric("Source", "arXiv")

            st.divider()

            for idx, article in enumerate(articles, 1):
                with st.expander(f"{idx}. {article['title'][:70]}"):
                    st.caption(f"👥 {article['authors']}")
                    st.caption(f"📖 {article['publication']} ({article['year']})")
                    st.markdown(f"**Abstract**\n\n{article['summary']}")
                    if article['link']:
                        st.markdown(f"[📄 PDF]({article['link']})")

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
