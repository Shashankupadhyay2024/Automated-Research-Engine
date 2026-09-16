import streamlit as st
from bs4 import BeautifulSoup
import requests
from urllib.parse import quote
import time
import json
import pandas as pd
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import colors

# Page config
st.set_page_config(
    page_title="Atlas Research",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = None
if 'history' not in st.session_state:
    st.session_state.history = []
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'

# Theme CSS
if st.session_state.theme == 'dark':
    theme_css = """
    <style>
        body {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #e2e8f0;
        }

        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        }

        [data-testid="stMainBlockContainer"] {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
        }

        h1 {
            background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 3rem !important;
            font-weight: 800 !important;
        }

        h2, h3 {
            color: #e2e8f0 !important;
        }

        input[type="text"] {
            background: rgba(15, 23, 42, 0.8) !important;
            border: 2px solid rgba(148, 163, 184, 0.3) !important;
            color: #ffffff !important;
            padding: 12px 16px !important;
            border-radius: 8px !important;
        }

        input[type="text"]:focus {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2) !important;
        }

        button {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
            color: white !important;
            border: none !important;
            padding: 12px 24px !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
        }

        button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 16px rgba(59, 130, 246, 0.3) !important;
        }

        .result-card {
            background: rgba(30, 41, 59, 0.5);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 12px;
            padding: 20px;
            margin: 15px 0;
            border-left: 4px solid #3b82f6;
            backdrop-filter: blur(10px);
        }

        [data-testid="metric-container"] {
            background: rgba(30, 41, 59, 0.5);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 12px;
            backdrop-filter: blur(10px);
        }

        p, span, label {
            color: #cbd5e1 !important;
        }

        a {
            color: #60a5fa !important;
        }
    </style>
    """
else:  # Light theme
    theme_css = """
    <style>
        body {
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            color: #0f172a;
        }

        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        }

        [data-testid="stMainBlockContainer"] {
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        }

        h1 {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #3b82f6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 3rem !important;
            font-weight: 800 !important;
        }

        h2, h3 {
            color: #0f172a !important;
        }

        input[type="text"] {
            background: white !important;
            border: 2px solid #e2e8f0 !important;
            color: #0f172a !important;
            padding: 12px 16px !important;
            border-radius: 8px !important;
        }

        input[type="text"]:focus {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
        }

        button {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
            color: white !important;
            border: none !important;
            padding: 12px 24px !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
        }

        button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 16px rgba(59, 130, 246, 0.3) !important;
        }

        .result-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin: 15px 0;
            border-left: 4px solid #3b82f6;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        [data-testid="metric-container"] {
            background: white;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
        }

        p, span, label {
            color: #0f172a !important;
        }

        a {
            color: #3b82f6 !important;
        }
    </style>
    """

st.markdown(theme_css, unsafe_allow_html=True)

# ============================================================================
# SIDEBAR - Navigation & Settings
# ============================================================================
with st.sidebar:
    st.markdown("## 🔍 Atlas Research")
    st.markdown("---")

    # Navigation sections
    st.markdown("### 📌 Navigation")
    nav_page = st.radio(
        "Choose section:",
        ["🏠 Home", "📊 Results", "⬇️ Export", "⚙️ Settings"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Theme toggle
    st.markdown("### 🎨 Theme")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("☀️ Light", use_container_width=True, key="light_btn"):
            st.session_state.theme = 'light'
            st.rerun()
    with col2:
        if st.button("🌙 Dark", use_container_width=True, key="dark_btn"):
            st.session_state.theme = 'dark'
            st.rerun()

    st.markdown("---")

    # About section
    st.markdown("### ℹ️ About")
    st.markdown("""
    **Atlas Research** is a professional research tool that searches Google Scholar and exports beautiful reports.

    **Features:**
    - 🔍 Real-time Scholar search
    - 📄 PDF exports with links
    - 📊 JSON & CSV exports
    - 🕐 Search history
    - 🎨 Light/Dark themes
    """)

    st.markdown("---")

    # Search history
    if st.session_state.history:
        st.markdown("### 🕐 Recent Searches")
        for i, h in enumerate(st.session_state.history[:5], 1):
            st.caption(f"{i}. {h['q']}")
            st.caption(f"   {h['d'].strftime('%b %d, %H:%M')}")

    st.markdown("---")
    st.markdown("<p style='text-align: center; font-size: 0.8rem; opacity: 0.7;'>Atlas Research v1.0</p>", unsafe_allow_html=True)

# ============================================================================
# MAIN CONTENT
# ============================================================================

# Title
st.markdown("# 🔍 Atlas Research")
st.markdown("Search and export academic research from Google Scholar")

st.markdown("---")

# Search section
col1, col2 = st.columns([4, 1], gap="small")
with col1:
    query = st.text_input(
        "What would you like to research?",
        placeholder="e.g., machine learning, quantum computing, climate change...",
        label_visibility="collapsed"
    )
with col2:
    search_btn = st.button("🔍 Search", use_container_width=True)

# Search logic
if search_btn and query:
    if query not in [h['q'] for h in st.session_state.history]:
        st.session_state.history.insert(0, {'q': query, 'd': datetime.now()})

    with st.spinner("🔍 Searching Google Scholar..."):
        results = []
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            url = f"https://scholar.google.com/scholar?q={quote(query)}&num=10"
            st.info(f"📍 Searching: {url}")

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            items = soup.find_all('div', {'class': 'gs_ri'})

            st.info(f"✅ Found {len(items)} results")

            for item in items[:10]:
                try:
                    # Title and link
                    title_el = item.find('h3')
                    if not title_el:
                        continue

                    link_el = title_el.find('a')
                    title = link_el.text if link_el else "Unknown"
                    link = link_el.get('href', '') if link_el else ''

                    # Info
                    info_el = item.find('div', {'class': 'gs_a'})
                    if info_el:
                        parts = info_el.text.split(' - ')
                        authors = parts[0] if len(parts) > 0 else "Unknown"
                        publication = parts[1] if len(parts) > 1 else "Unknown"
                        year = parts[2] if len(parts) > 2 else "Unknown"
                    else:
                        authors = publication = year = "Unknown"

                    # Abstract
                    abstract_el = item.find('div', {'class': 'gs_rs'})
                    abstract = abstract_el.text if abstract_el else "No abstract available"

                    results.append({
                        'title': title,
                        'authors': authors,
                        'pub': publication,
                        'year': year,
                        'abstract': abstract,
                        'link': link
                    })
                    time.sleep(0.1)
                except Exception as e:
                    st.warning(f"Error parsing item: {e}")

            st.session_state.results = results

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.info("💡 Make sure you have internet connection and Google Scholar is accessible")

# Display results
if st.session_state.results:
    st.markdown("---")
    st.success(f"✅ Found {len(st.session_state.results)} papers!")

    tab1, tab2, tab3 = st.tabs(["📄 Papers", "📊 Summary", "⬇️ Export"])

    with tab1:
        st.markdown("### Research Papers")
        for i, r in enumerate(st.session_state.results, 1):
            st.markdown(f"""
                <div class='result-card'>
                    <h3>{i}. {r['title']}</h3>
                    <p><b>Authors:</b> {r['authors']}</p>
                    <p><b>Publication:</b> {r['pub']}</p>
                    <p><b>Year:</b> {r['year']}</p>
                    <p><b>Abstract:</b> {r['abstract'][:200]}...</p>
                    <a href='{r['link']}' target='_blank'>🔗 View on Google Scholar</a>
                </div>
            """, unsafe_allow_html=True)

    with tab2:
        st.markdown("### Summary Statistics")
        col1, col2, col3 = st.columns(3)
        col1.metric("📚 Total Papers", len(st.session_state.results))
        col2.metric("🔗 With Links", sum(1 for x in st.session_state.results if x['link']))
        col3.metric("📝 With Abstract", sum(1 for x in st.session_state.results if 'No abstract' not in x['abstract']))

        st.markdown("### Data Table")
        df = pd.DataFrame([{
            'Title': r['title'][:70],
            'Authors': r['authors'][:50],
            'Year': r['year'],
            'Publication': r['pub'][:30]
        } for r in st.session_state.results])
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab3:
        st.markdown("### Export Your Research")
        st.markdown("Choose how you want to export your results:")

        # PDF Export
        st.markdown("#### 📄 PDF Report")
        st.markdown("Beautiful formatted PDF with all papers and Scholar links")

        if st.button("📥 Download PDF", key="pdf_download", use_container_width=True):
            try:
                st.info("⏳ Generating PDF... please wait")

                # Create PDF
                pdf_buf = io.BytesIO()
                doc = SimpleDocTemplate(
                    pdf_buf,
                    pagesize=letter,
                    topMargin=0.5*inch,
                    bottomMargin=0.5*inch,
                    leftMargin=0.75*inch,
                    rightMargin=0.75*inch
                )

                story = []
                styles = getSampleStyleSheet()

                # Custom styles
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=20,
                    textColor=colors.HexColor('#0f172a'),
                    spaceAfter=12,
                    spaceBefore=6,
                )

                heading_style = ParagraphStyle(
                    'CustomHeading',
                    parent=styles['Heading2'],
                    fontSize=11,
                    textColor=colors.HexColor('#1e293b'),
                    spaceAfter=6,
                    spaceBefore=8,
                    bold=True,
                )

                normal_style = ParagraphStyle(
                    'CustomNormal',
                    parent=styles['Normal'],
                    fontSize=9,
                    leading=12,
                )

                # Add title and metadata
                story.append(Paragraph(f"📚 Research Report: {query}", title_style))
                story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", normal_style))
                story.append(Spacer(1, 0.15*inch))
                story.append(Paragraph(f"Total Papers Found: {len(st.session_state.results)}", normal_style))
                story.append(Spacer(1, 0.25*inch))

                # Add each result
                for i, r in enumerate(st.session_state.results, 1):
                    story.append(Paragraph(f"<b>{i}. {r['title']}</b>", heading_style))
                    story.append(Paragraph(f"<b>Authors:</b> {r['authors']}", normal_style))
                    story.append(Paragraph(f"<b>Publication:</b> {r['pub']}", normal_style))
                    story.append(Paragraph(f"<b>Year:</b> {r['year']}", normal_style))

                    if r['abstract'] and 'No abstract' not in r['abstract']:
                        abstract_text = r['abstract'][:300] + "..." if len(r['abstract']) > 300 else r['abstract']
                        story.append(Paragraph(f"<b>Abstract:</b> {abstract_text}", normal_style))

                    if r['link']:
                        story.append(Paragraph(f'<a href="{r["link"]}" color="blue">🔗 View on Google Scholar</a>', normal_style))

                    story.append(Spacer(1, 0.2*inch))

                # Build PDF
                doc.build(story)
                pdf_buf.seek(0)

                # Provide download button
                st.download_button(
                    label="⬇️ Click here to download PDF",
                    data=pdf_buf,
                    file_name=f"research_{query.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                st.success("✅ PDF ready! Click button above to download")

            except ImportError as e:
                st.error(f"❌ Missing dependency: {e}")
                st.warning("Please install reportlab: pip install reportlab")
            except Exception as e:
                st.error(f"❌ Error generating PDF: {str(e)}")
                st.info("📋 Detailed error info above ☝️")

        st.markdown("---")

        # JSON Export
        st.markdown("#### 📋 JSON Export")
        st.markdown("Raw data format for APIs and data processing")
        json_str = json.dumps(st.session_state.results, indent=2)
        st.download_button(
            label="⬇️ Download JSON",
            data=json_str,
            file_name=f"research_{query.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )

        st.markdown("---")

        # CSV Export
        st.markdown("#### 📊 CSV Export")
        st.markdown("Open in Excel, Google Sheets, or any spreadsheet app")
        csv_str = pd.DataFrame(st.session_state.results).to_csv(index=False)
        st.download_button(
            label="⬇️ Download CSV",
            data=csv_str,
            file_name=f"research_{query.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

# Footer
st.markdown("---")
if st.session_state.theme == 'dark':
    st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 0.85rem;'>🔍 Atlas Research | Google Scholar Only | All links exclusive to Google Scholar</p>", unsafe_allow_html=True)
else:
    st.markdown("<p style='text-align: center; color: #64748b; font-size: 0.85rem;'>🔍 Atlas Research | Google Scholar Only | All links exclusive to Google Scholar</p>", unsafe_allow_html=True)
