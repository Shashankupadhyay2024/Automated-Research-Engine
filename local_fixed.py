import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time, json, pandas as pd, io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import colors
from urllib.parse import quote

st.set_page_config(page_title="Atlas - Local", layout="wide", initial_sidebar_state="expanded")

if 'results' not in st.session_state:
    st.session_state.results = None
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'
if 'last_query' not in st.session_state:
    st.session_state.last_query = ""

# Apply theme CSS - ONLY ONCE at startup
dark_css = """<style>
body { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #e2e8f0; }
[data-testid="stAppViewContainer"] { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); }
[data-testid="stMainBlockContainer"] { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%); }
h1 { background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-size: 3rem !important; font-weight: 800 !important; }
h2, h3 { color: #e2e8f0 !important; }
input[type="text"] { background: rgba(15, 23, 42, 0.8) !important; border: 2px solid rgba(148, 163, 184, 0.3) !important; color: #ffffff !important; padding: 12px 16px !important; border-radius: 8px !important; }
button { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important; color: white !important; border: none !important; padding: 12px 24px !important; border-radius: 8px !important; font-weight: 600 !important; }
button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 16px rgba(59, 130, 246, 0.3) !important; }
.result-card { background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 12px; padding: 20px; margin: 15px 0; border-left: 4px solid #3b82f6; }
p, span, label { color: #cbd5e1 !important; }
a { color: #60a5fa !important; }
</style>"""

light_css = """<style>
body { background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); color: #0f172a; }
[data-testid="stAppViewContainer"] { background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); }
[data-testid="stMainBlockContainer"] { background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%); }
h1 { background: linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #3b82f6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-size: 3rem !important; font-weight: 800 !important; }
h2, h3 { color: #0f172a !important; }
input[type="text"] { background: white !important; border: 2px solid #e2e8f0 !important; color: #0f172a !important; padding: 12px 16px !important; border-radius: 8px !important; }
button { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important; color: white !important; border: none !important; padding: 12px 24px !important; border-radius: 8px !important; font-weight: 600 !important; }
button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 16px rgba(59, 130, 246, 0.3) !important; }
.result-card { background: white; border-radius: 12px; padding: 20px; margin: 15px 0; border-left: 4px solid #3b82f6; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); }
p, span, label { color: #0f172a !important; }
a { color: #3b82f6 !important; }
</style>"""

st.markdown(dark_css if st.session_state.theme == 'dark' else light_css, unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🔍 Atlas Research")
    st.markdown("### LOCAL VERSION")
    st.markdown("---")
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
    st.markdown("✅ Real Chrome\n✅ PDF exports\n✅ CSV & JSON")
    if st.session_state.search_history:
        st.markdown("### 📜 Recent")
        for i, h in enumerate(st.session_state.search_history[:5], 1):
            st.caption(f"{i}. {h['query']}")

st.markdown("# 🔍 Atlas Research")
col1, col2 = st.columns([4, 1])
with col1:
    query = st.text_input("Search:", label_visibility="collapsed", placeholder="e.g., machine learning")
with col2:
    search_btn = st.button("🔍 Search", use_container_width=True)

if search_btn and query:
    st.session_state.last_query = query
    if query not in [h['query'] for h in st.session_state.search_history]:
        st.session_state.search_history.insert(0, {'query': query})

    with st.spinner("Searching Scholar..."):
        results = []
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

            url = f"https://scholar.google.com/scholar?q={quote(query)}&num=10"
            st.info(f"📍 Searching: {query}")
            driver.get(url)
            time.sleep(4)

            items = driver.find_elements(By.CSS_SELECTOR, "div.gs_ri")
            st.success(f"✅ Found {len(items)} results")

            for item in items[:10]:
                try:
                    title_el = item.find_element(By.CSS_SELECTOR, "h3 a")
                    title = title_el.text
                    link = title_el.get_attribute("href")
                    info_el = item.find_element(By.CSS_SELECTOR, "div.gs_a")
                    parts = info_el.text.split(' - ')
                    authors = parts[0] if len(parts) > 0 else "Unknown"
                    publication = parts[1] if len(parts) > 1 else "Unknown"
                    year = parts[2] if len(parts) > 2 else "Unknown"
                    try:
                        abstract_el = item.find_element(By.CSS_SELECTOR, "div.gs_rs")
                        abstract = abstract_el.text
                    except:
                        abstract = "No abstract"
                    results.append({'title': title, 'authors': authors, 'pub': publication, 'year': year, 'abstract': abstract, 'link': link})
                except:
                    pass
            driver.quit()
            st.session_state.results = results
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

if st.session_state.results:
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📄 Papers", "📊 Summary", "⬇️ Export"])

    with tab1:
        for i, r in enumerate(st.session_state.results, 1):
            st.markdown(f"""<div class='result-card'><h3>{i}. {r['title']}</h3><p><b>Authors:</b> {r['authors']}</p><p><b>Pub:</b> {r['pub']}</p><p><b>Year:</b> {r['year']}</p><p><b>Abstract:</b> {r['abstract'][:200]}...</p><a href='{r['link']}' target='_blank'>🔗 View</a></div>""", unsafe_allow_html=True)

    with tab2:
        col1, col2, col3 = st.columns(3)
        col1.metric("Papers", len(st.session_state.results))
        col2.metric("Links", sum(1 for x in st.session_state.results if x['link']))
        col3.metric("Abstracts", sum(1 for x in st.session_state.results if 'No abstract' not in x['abstract']))

    with tab3:
        if st.button("📥 Download PDF", use_container_width=True):
            try:
                pdf_buf = io.BytesIO()
                doc = SimpleDocTemplate(pdf_buf, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
                story = []
                styles = getSampleStyleSheet()
                story.append(Paragraph(f"Research: {st.session_state.last_query}", styles['Heading1']))
                for i, r in enumerate(st.session_state.results, 1):
                    story.append(Paragraph(f"<b>{i}. {r['title']}</b>", styles['Heading2']))
                    story.append(Paragraph(f"Authors: {r['authors']}", styles['Normal']))
                    story.append(Paragraph(f"Year: {r['year']}", styles['Normal']))
                    if 'No abstract' not in r['abstract']:
                        story.append(Paragraph(f"Abstract: {r['abstract'][:200]}...", styles['Normal']))
                doc.build(story)
                pdf_buf.seek(0)
                st.download_button(label="⬇️ Download PDF", data=pdf_buf, file_name=f"research.pdf", mime="application/pdf", use_container_width=True)
                st.success("✅ PDF ready!")
            except Exception as e:
                st.error(f"❌ PDF Error: {str(e)}")

        st.divider()
        json_str = json.dumps(st.session_state.results, indent=2)
        st.download_button(label="⬇️ Download JSON", data=json_str, file_name=f"research.json", mime="application/json", use_container_width=True)

        st.divider()
        csv_str = pd.DataFrame(st.session_state.results).to_csv(index=False)
        st.download_button(label="⬇️ Download CSV", data=csv_str, file_name=f"research.csv", mime="text/csv", use_container_width=True)
