import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import json
from urllib.parse import quote
import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
import io

# Page config
st.set_page_config(
    page_title="Atlas Research Engine",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Atlas Research Engine")
st.markdown("Search Google Scholar and export your findings as PDF reports")

# Headers for requests (to mimic browser)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def search_google_scholar(query, num_results=10):
    """Search Google Scholar using web scraping (no Selenium needed)"""
    results = []
    try:
        url = f"https://scholar.google.com/scholar?q={quote(query)}&hl=en&num={num_results}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        result_divs = soup.find_all('div', class_='gs_ri')

        for result in result_divs[:num_results]:
            try:
                title_elem = result.find('h3', class_='gs_ct')
                if not title_elem:
                    continue
                link_elem = title_elem.find('a')
                title = link_elem.text if link_elem else "No title"
                link = link_elem['href'] if link_elem else ""

                info_elem = result.find('div', class_='gs_a')
                if info_elem:
                    info_text = info_elem.text
                    parts = info_text.split(' - ')
                    authors = parts[0] if len(parts) > 0 else "Unknown"
                    publication = parts[1] if len(parts) > 1 else "Unknown"
                    year = parts[2] if len(parts) > 2 else "Unknown"
                else:
                    authors = "Unknown"
                    publication = "Unknown"
                    year = "Unknown"

                abstract_elem = result.find('div', class_='gs_rs')
                abstract = abstract_elem.text if abstract_elem else "No abstract available"

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
                st.warning(f"Error parsing result: {str(e)}")
                continue

        return results
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Search failed: {str(e)}")
        st.info("💡 Tip: Google Scholar might block automated requests. Try again in a moment or use a simpler query.")
        return []

def create_pdf_report(results, query):
    """Create a PDF report from search results"""
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

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=12,
        spaceBefore=12
    )

    story.append(Paragraph(f"📚 Research Report: {query}", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(f"<b>Total Results Found:</b> {len(results)}", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))

    for idx, paper in enumerate(results, 1):
        story.append(Paragraph(f"<b>{idx}. {paper['title']}</b>", heading_style))
        story.append(Paragraph(f"<b>Authors:</b> {paper['authors']}", styles['Normal']))
        story.append(Paragraph(f"<b>Publication:</b> {paper['publication']}", styles['Normal']))
        story.append(Paragraph(f"<b>Year:</b> {paper['year']}", styles['Normal']))

        if paper['link']:
            story.append(Paragraph(f"<b>Link:</b> <a href='{paper['link']}'>View Paper</a>", styles['Normal']))

        story.append(Paragraph(f"<b>Abstract:</b> {paper['abstract'][:300]}...", styles['Normal']))
        story.append(Spacer(1, 0.15*inch))

    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    num_results = st.slider("Number of results", 5, 20, 10)

    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    **Atlas Research Engine** searches Google Scholar and exports findings as PDF reports.

    **Note:** Web scraping has limitations. If searches fail, try simpler queries.
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
        results = search_google_scholar(query, num_results)

    if results:
        st.success(f"✅ Found {len(results)} results!")

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

            years = [p['year'] for p in results if p['year'] != 'Unknown']

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Papers", len(results))
            with col2:
                st.metric("With Links", sum(1 for p in results if p['link']))
            with col3:
                if years:
                    st.metric("Avg Year", f"{sum(int(y) for y in years if y.isdigit()) / len([y for y in years if y.isdigit()]):.0f}")

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
        st.warning("❌ No results found. Try a different search term.")

else:
    st.info("👉 Enter a search query and click 'Search' to begin!")

st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Built with ❤️ using Streamlit | Powered by Google Scholar</p>
</div>
""", unsafe_allow_html=True)
