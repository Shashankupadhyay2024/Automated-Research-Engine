import streamlit as st
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import json
import pandas as pd
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from urllib.parse import quote

st.set_page_config(page_title="Atlas - Local", layout="wide", initial_sidebar_state="expanded")

if 'results' not in st.session_state:
    st.session_state.results = None
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
if 'last_query' not in st.session_state:
    st.session_state.last_query = ""

dark_css = """<style>
body { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #e2e8f0; }
[data-testid="stAppViewContainer"] { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); }
[data-testid="stMainBlockContainer"] { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%); }
h1 { background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-size: 3rem !important; font-weight: 800 !important; }
h2, h3 { color: #e2e8f0 !important; }
input[type="text"], input[type="number"] { background: rgba(15, 23, 42, 0.8) !important; border: 2px solid rgba(148, 163, 184, 0.3) !important; color: #ffffff !important; padding: 12px 16px !important; border-radius: 8px !important; }
button { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important; color: white !important; border: none !important; padding: 12px 24px !important; border-radius: 8px !important; font-weight: 600 !important; }
button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 16px rgba(59, 130, 246, 0.3) !important; }
p, span, label { color: #cbd5e1 !important; }
a { color: #60a5fa !important; }
.score-badge { display: inline-block; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 6px 12px; border-radius: 6px; font-weight: bold; margin-right: 8px; }
</style>"""

st.markdown(dark_css, unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🔍 Atlas Research")
    st.markdown("### LOCAL VERSION")
    st.markdown("---")
    st.markdown("✅ Google Scholar\n✅ PDF exports\n✅ CSV & JSON")
    if st.session_state.search_history:
        st.markdown("### 📜 Recent Searches")
        for i, h in enumerate(st.session_state.search_history[:5], 1):
            if st.button(f"{i}. {h['query']}", key=f"hist_{i}", use_container_width=True):
                st.session_state.last_query = h['query']
                st.session_state.results = h.get('results', None)

st.markdown("# 🔍 Atlas Research")
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    query = st.text_input("Search:", label_visibility="collapsed", placeholder="e.g., machine learning, quantum computing")
with col2:
    num_papers = st.slider("Results", 5, 100, 20, 5, label_visibility="collapsed")
with col3:
    search_btn = st.button("🔍 Search", use_container_width=True)

def calculate_credibility(item):
    score = 50
    reasons = []
    
    citation_text = item.get('citations', '')
    try:
        if 'Cited by' in citation_text:
            citations = int(citation_text.split('Cited by')[1].strip().split()[0])
            bonus = min(30, citations // 5)
            score += bonus
            reasons.append(f"Citations ({citations}): +{bonus}")
    except:
        pass
    
    year_text = item.get('year', '')
    try:
        year = int(year_text)
        years_old = 2025 - year
        if years_old <= 3:
            bonus = 15
            score += bonus
            reasons.append(f"Recent paper ({years_old}y old): +{bonus}")
        elif years_old <= 7:
            bonus = 10
            score += bonus
            reasons.append(f"Recent paper ({years_old}y old): +{bonus}")
        elif years_old <= 15:
            bonus = 5
            score += bonus
            reasons.append(f"Established paper ({years_old}y old): +{bonus}")
    except:
        pass
    
    if item.get('abstract') and len(item.get('abstract', '')) > 100:
        score += 10
        reasons.append("Quality abstract: +10")
    
    publication = (item.get('publication', '') or '').lower()
    quality_sources = ['nature', 'science', 'ieee', 'acm', 'proceedings', 'journal', 'conference']
    if any(s in publication for s in quality_sources):
        score += 10
        reasons.append("Quality venue: +10")
    
    item['credibility_reasons'] = reasons
    return min(100, score)

def format_citation(item, style='APA'):
    authors = item.get('authors', 'Unknown')
    title = item.get('title', 'Unknown Title')
    year = item.get('year', 'n.d.')
    publication = item.get('publication', 'Unknown Venue')
    if style == 'APA':
        return f"{authors} ({year}). {title}. {publication}."
    elif style == 'MLA':
        return f"{authors}. \"{title}.\" {publication}, {year}."
    elif style == 'Chicago':
        return f"{authors}. \"{title}.\" {publication} ({year})."
    elif style == 'BibTeX':
        return f'@article{{scholar_{hash(title) % 10000},\n  title={{{title}}},\n  author={{{authors}}},\n  year={{{year}}},\n  journal={{{publication}}}\n}}'
    return authors

def scrape_google_scholar(query, num_papers):
    results = []
    driver = None
    try:
        st.info(f"📍 Searching Google Scholar for: {query}")
        driver = uc.Chrome(version_main=None)
        url = f"https://scholar.google.com/scholar?q={quote(query)}&num={num_papers}"
        driver.get(url)
        time.sleep(5)
        
        items = driver.find_elements(By.CSS_SELECTOR, "div.gs_ri")
        st.success(f"✅ Found {len(items)} results on page")

        for item in items[:num_papers]:
            try:
                title_el = item.find_element(By.CSS_SELECTOR, "h3 a")
                title = title_el.text
                link = title_el.get_attribute("href")
                info_el = item.find_element(By.CSS_SELECTOR, "div.gs_a")
                info_parts = info_el.text.split(' - ')
                authors = info_parts[0] if len(info_parts) > 0 else "Unknown"
                publication = info_parts[1] if len(info_parts) > 1 else "Unknown"
                year = info_parts[2] if len(info_parts) > 2 else "Unknown"
                abstract = "No abstract"
                try:
                    abstract_el = item.find_element(By.CSS_SELECTOR, "div.gs_rs")
                    abstract = abstract_el.text
                except:
                    pass
                citations = ""
                try:
                    citations_el = item.find_element(By.CSS_SELECTOR, "div.gs_fl")
                    citations = citations_el.text
                except:
                    pass
                paper_data = {
                    'title': title,
                    'authors': authors,
                    'publication': publication,
                    'year': year,
                    'abstract': abstract,
                    'link': link,
                    'citations': citations
                }
                paper_data['credibility'] = calculate_credibility(paper_data)
                results.append(paper_data)
            except:
                continue

        driver.quit()
        results = sorted(results, key=lambda x: x['credibility'], reverse=True)
        return results

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        if driver:
            driver.quit()
        return []

if search_btn and query:
    st.session_state.last_query = query
    if query not in [h['query'] for h in st.session_state.search_history]:
        st.session_state.search_history.insert(0, {'query': query, 'results': None})

    with st.spinner("Searching Google Scholar..."):
        results = scrape_google_scholar(query, num_papers)
        if results:
            st.session_state.results = results
            for h in st.session_state.search_history:
                if h['query'] == query:
                    h['results'] = results
                    break
        else:
            st.warning("⚠️ No papers found or search failed.")
            st.session_state.results = None

if st.session_state.results:
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📄 Papers", "📊 Summary", "⬇️ Export"])

    with tab1:
        for i, paper in enumerate(st.session_state.results, 1):
            abstract = paper.get('abstract', 'No abstract available')
            if abstract and len(abstract) > 300:
                abstract = abstract[:300] + "..."

            credibility = paper.get('credibility', 0)
            link = paper.get('link', '')

            st.markdown("---")
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"**{i}. {paper['title']}**")
                st.markdown(f"**Authors:** {paper['authors']}")
                st.markdown(f"**Year:** {paper['year']} | **Pub:** {paper['publication']}")
                st.markdown(f"**Abstract:** {abstract}")
                if link:
                    st.markdown(f"[🔗 View on Scholar]({link})")
            
            with col2:
                st.markdown(f"<div class='score-badge' style='text-align: center; padding: 10px;'>{credibility}/100</div>", unsafe_allow_html=True)
            
            with st.expander("📊 Score Breakdown"):
                st.markdown("**Base Score:** 50")
                for reason in paper.get('credibility_reasons', []):
                    st.markdown(f"• {reason}")
                st.markdown(f"**Total:** {credibility}/100")

    with tab2:
        col1, col2, col3 = st.columns(3)
        col1.metric("Papers Found", len(st.session_state.results))
        col2.metric("Avg Credibility", f"{sum(p.get('credibility', 0) for p in st.session_state.results) / len(st.session_state.results):.0f}/100")
        citations_count = sum(1 for p in st.session_state.results if 'Cited by' in p.get('citations', ''))
        col3.metric("Cited Papers", citations_count)

    with tab3:
        if st.button("📥 Download PDF", use_container_width=True):
            try:
                pdf_buf = io.BytesIO()
                doc = SimpleDocTemplate(pdf_buf, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
                story = []
                styles = getSampleStyleSheet()

                story.append(Paragraph(f"Research: {st.session_state.last_query}", styles['Heading1']))
                story.append(Spacer(1, 0.3*inch))

                for i, paper in enumerate(st.session_state.results, 1):
                    story.append(Paragraph(f"<b>{i}. {paper['title']}</b>", styles['Heading2']))
                    story.append(Paragraph(f"Credibility Score: {paper.get('credibility', 0)}/100", styles['Normal']))
                    story.append(Paragraph(f"Authors: {paper['authors']}", styles['Normal']))
                    story.append(Paragraph(f"Year: {paper['year']} | Publication: {paper['publication']}", styles['Normal']))
                    if paper.get('abstract') != 'No abstract':
                        abstract_text = paper['abstract'][:300] + "..." if len(paper['abstract']) > 300 else paper['abstract']
                        story.append(Paragraph(f"<b>Abstract:</b> {abstract_text}", styles['Normal']))
                    if paper.get('link'):
                        story.append(Paragraph(f"<a href='{paper.get('link')}'><u>🔗 View on Scholar</u></a>", styles['Normal']))
                    story.append(Spacer(1, 0.2*inch))

                story.append(Spacer(1, 0.3*inch))
                story.append(Paragraph(f"© Shashank Upadhyay", styles['Normal']))

                doc.build(story)
                pdf_buf.seek(0)
                st.download_button(label="⬇️ Download PDF", data=pdf_buf, file_name="research.pdf", mime="application/pdf", use_container_width=True)
                st.success("✅ PDF ready!")
            except Exception as e:
                st.error(f"❌ PDF Error: {str(e)}")

        st.divider()

        if st.button("📥 Download JSON", use_container_width=True):
            json_str = json.dumps(st.session_state.results, indent=2)
            st.download_button(label="⬇️ Download JSON", data=json_str, file_name="research.json", mime="application/json", use_container_width=True)

        st.divider()

        if st.button("📥 Download CSV", use_container_width=True):
            csv_data = []
            for paper in st.session_state.results:
                csv_data.append({
                    'Title': paper.get('title', ''),
                    'Authors': paper.get('authors', ''),
                    'Year': paper.get('year', ''),
                    'Publication': paper.get('publication', ''),
                    'Credibility': paper.get('credibility', 0),
                    'URL': paper.get('link', '')
                })
            csv_str = pd.DataFrame(csv_data).to_csv(index=False)
            st.download_button(label="⬇️ Download CSV", data=csv_str, file_name="research.csv", mime="text/csv", use_container_width=True)

        st.divider()
        st.markdown("### 📋 Citation Formats")
        citation_style = st.radio("Format:", ["APA", "MLA", "Chicago", "BibTeX"], horizontal=True, key="citation_format", label_visibility="collapsed")

        for i, paper in enumerate(st.session_state.results[:3], 1):
            citation = format_citation(paper, citation_style)
            st.code(citation, language="text")
