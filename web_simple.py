import streamlit as st
import requests
from bs4 import BeautifulSoup
import json, pandas as pd, io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from urllib.parse import quote

st.set_page_config(page_title="Atlas - Web", layout="wide")

if 'results' not in st.session_state:
    st.session_state.results = None
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'
if 'last_query' not in st.session_state:
    st.session_state.last_query = ""

dark_css = "<style>body{background:#0f172a;color:#e2e8f0}[data-testid='stAppViewContainer']{background:#0f172a}[data-testid='stSidebar']{background:#1e293b}h1{color:#3b82f6;font-size:3rem}input{background:rgba(15,23,42,0.8)!important;border:2px solid #3b82f6!important;color:#fff!important}button{background:linear-gradient(135deg,#3b82f6,#2563eb)!important;color:white!important}.result-card{background:rgba(30,41,59,0.5);border-left:4px solid #3b82f6;border-radius:12px;padding:20px;margin:15px 0}</style>"
light_css = "<style>body{background:#f8fafc;color:#0f172a}[data-testid='stAppViewContainer']{background:#f8fafc}[data-testid='stSidebar']{background:#fff}h1{color:#0f172a;font-size:3rem}input{background:white!important;border:2px solid #e2e8f0!important;color:#0f172a!important}button{background:linear-gradient(135deg,#3b82f6,#2563eb)!important;color:white!important}.result-card{background:white;border-left:4px solid #3b82f6;border-radius:12px;padding:20px;margin:15px 0;box-shadow:0 1px 3px rgba(0,0,0,0.1)}</style>"

st.markdown(dark_css if st.session_state.theme == 'dark' else light_css, unsafe_allow_html=True)

with st.sidebar:
    st.title("🔍 Atlas")
    if st.button("☀️ Light Mode", use_container_width=True):
        st.session_state.theme = 'light'
        st.rerun()
    if st.button("🌙 Dark Mode", use_container_width=True):
        st.session_state.theme = 'dark'
        st.rerun()
    st.markdown("---")
    st.markdown("**WEB VERSION**\n✅ Web Scraping\n✅ PDF Exports\n✅ History")
    if st.session_state.search_history:
        st.markdown("### Recent Searches")
        for q in st.session_state.search_history[:5]:
            st.caption(f"• {q}")

st.title("🔍 Atlas Research")
query = st.text_input("Search Google Scholar:", placeholder="e.g., machine learning")
search_btn = st.button("🔍 Search", use_container_width=True)

if search_btn and query:
    st.session_state.last_query = query
    if query not in st.session_state.search_history:
        st.session_state.search_history.insert(0, query)

    with st.spinner("Searching Scholar..."):
        results = []
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            url = f"https://scholar.google.com/scholar?q={quote(query)}&num=10"
            st.info(f"📍 Searching for: {query}")
            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                items = soup.find_all('div', class_='gs_ri')
                st.success(f"✅ Found {len(items)} results")

                for item in items[:10]:
                    try:
                        title_el = item.find('h3')
                        if not title_el or not title_el.find('a'):
                            continue
                        title = title_el.get_text(strip=True)
                        link = title_el.find('a').get('href', '')

                        info_el = item.find('div', class_='gs_a')
                        info = info_el.get_text(strip=True) if info_el else ""
                        parts = info.split(' - ')
                        authors = parts[0] if len(parts) > 0 else "Unknown"
                        year = parts[2] if len(parts) > 2 else "Unknown"

                        abstract_el = item.find('div', class_='gs_rs')
                        abstract = abstract_el.get_text(strip=True) if abstract_el else "No abstract"

                        results.append({'title': title, 'authors': authors, 'year': year, 'abstract': abstract, 'link': link})
                    except:
                        pass

                st.session_state.results = results if results else None
            else:
                st.error("❌ Failed to fetch")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

if st.session_state.results:
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📄 Papers", "📊 Stats", "⬇️ Export"])

    with tab1:
        for i, r in enumerate(st.session_state.results, 1):
            st.markdown(f"<div class='result-card'><h3>{i}. {r['title']}</h3><p><b>Authors:</b> {r['authors']}</p><p><b>Year:</b> {r['year']}</p><p>{r['abstract'][:150]}...</p><a href='{r['link']}' target='_blank'>View →</a></div>", unsafe_allow_html=True)

    with tab2:
        st.metric("Total Papers", len(st.session_state.results))
        st.metric("With Links", sum(1 for x in st.session_state.results if x['link']))

    with tab3:
        if st.button("📥 Download PDF", use_container_width=True):
            try:
                pdf_buf = io.BytesIO()
                doc = SimpleDocTemplate(pdf_buf, pagesize=letter)
                story = [Paragraph(f"Research: {st.session_state.last_query}", getSampleStyleSheet()['Heading1'])]
                for i, r in enumerate(st.session_state.results, 1):
                    story.append(Paragraph(f"<b>{i}. {r['title']}</b>", getSampleStyleSheet()['Heading2']))
                    story.append(Paragraph(f"Year: {r['year']}", getSampleStyleSheet()['Normal']))
                doc.build(story)
                pdf_buf.seek(0)
                st.download_button("⬇️ Download PDF", pdf_buf, "research.pdf", "application/pdf", use_container_width=True)
                st.success("✅ Ready!")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

        st.json(st.session_state.results)
