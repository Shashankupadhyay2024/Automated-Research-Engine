import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time, json, pandas as pd, io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import colors
from urllib.parse import quote

st.set_page_config(page_title="Atlas - Local", layout="wide")

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
    st.markdown("**LOCAL VERSION**\n✅ Real Chrome\n✅ PDF Exports\n✅ History")
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
            options = webdriver.ChromeOptions()
            options.add_argument("--disable-dev-shm-usage")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            url = f"https://scholar.google.com/scholar?q={quote(query)}&num=10"
            st.info(f"📍 Searching for: {query}")
            driver.get(url)
            time.sleep(4)

            items = driver.find_elements(By.CSS_SELECTOR, "div.gs_ri")
            st.success(f"✅ Found {len(items)} results")

            for item in items[:10]:
                try:
                    title = item.find_element(By.CSS_SELECTOR, "h3 a").text
                    link = item.find_element(By.CSS_SELECTOR, "h3 a").get_attribute("href")
                    info = item.find_element(By.CSS_SELECTOR, "div.gs_a").text
                    parts = info.split(' - ')
                    authors = parts[0] if len(parts) > 0 else "Unknown"
                    year = parts[2] if len(parts) > 2 else "Unknown"
                    try:
                        abstract = item.find_element(By.CSS_SELECTOR, "div.gs_rs").text
                    except:
                        abstract = "No abstract"
                    results.append({'title': title, 'authors': authors, 'year': year, 'abstract': abstract, 'link': link})
                except:
                    pass
            driver.quit()
            st.session_state.results = results
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
