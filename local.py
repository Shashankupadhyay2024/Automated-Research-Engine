import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import pandas as pd
import io
from datetime import datetime
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
if 'num_papers' not in st.session_state:
    st.session_state.num_papers = 10

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
.result-card { background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 12px; padding: 20px; margin: 15px 0; border-left: 4px solid #3b82f6; }
p, span, label { color: #cbd5e1 !important; }
a { color: #60a5fa !important; }
.score-badge { display: inline-block; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 6px 12px; border-radius: 6px; font-weight: bold; margin-right: 8px; }
</style>"""

st.markdown(dark_css, unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🔍 Atlas Research")
    st.markdown("### LOCAL VERSION")
    st.markdown("---")
    st.markdown("✅ Real Chrome Browser\n✅ PDF exports\n✅ CSV & JSON")
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
    num_papers = st.slider("Papers:", min_value=5, max_value=100, value=10, step=5)
with col3:
    search_btn = st.button("🔍 Search", use_container_width=True)

def calculate_credibility(item):
    """Calculate credibility score 0-100 with breakdown"""
    score = 50
    reasons = []

    # Citation count from snippet
    citation_text = item.get('citations', '')
    try:
        if 'Cited by' in citation_text:
            citations = int(citation_text.split('Cited by')[1].strip().split()[0])
            bonus = min(30, citations // 5)
            score += bonus
            reasons.append(f"Citations ({citations}): +{bonus}")
    except:
        pass

    # Recency bonus
    try:
        year_str = item.get('year', '')
        if year_str:
            year = int(year_str)
            years_old = 2025 - year
            if years_old <= 2:
                score += 15
                reasons.append(f"Recent paper ({year}): +15")
            elif years_old <= 5:
                score += 10
                reasons.append(f"Recent paper ({year}): +10")
    except:
        pass

    # Abstract quality
    abstract = item.get('abstract', '')
    if abstract and len(abstract) > 100:
        score += 10
        reasons.append("Good abstract: +10")

    return min(100, score), reasons

def format_citation(item, style='APA'):
    """Generate citation in specified format"""
    authors = item.get('authors', 'Unknown')
    title = item.get('title', 'Unknown Title')
    year = item.get('year', 'n.d.')
    url = item.get('url', '')

    if style == 'APA':
        return f"{authors} ({year}). {title}. Retrieved from {url}"
    elif style == 'MLA':
        return f"{authors}. \"{title}.\" {year}. Web. {url}"
    elif style == 'Chicago':
        return f"{authors}. \"{title}.\" Accessed {year}. {url}"
    elif style == 'BibTeX':
        return f'@misc{{{year}_{title[:10].replace(" ", "_")},\n  author={{{authors}}},\n  title={{{title}}},\n  year={{{year}}},\n  url={{{url}}}\n}}'
    return authors

def fetch_google_scholar(query, num_papers):
    """Fetch papers from Google Scholar"""
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=options)
        st.session_state.driver = driver
        
        url = f"https://scholar.google.com/scholar?q={quote(query)}"
        st.info(f"📍 Opening Google Scholar for: {query}")
        driver.get(url)
        
        st.warning("⏳ Waiting for page to load (if CAPTCHA appears, complete it then click the button below)...")
        time.sleep(5)
        
        # Check for CAPTCHA
        try:
            driver.find_element(By.ID, "recaptcha")
            st.session_state.awaiting_captcha = True
            st.session_state.pending_search = {'query': query, 'num_papers': num_papers}
            st.warning("🤖 CAPTCHA detected! Please complete the CAPTCHA in the Chrome window, then click the button below.")
            if st.button("✅ CAPTCHA Done - Extract Papers"):
                st.session_state.awaiting_captcha = False
                results = extract_papers_from_driver(driver, num_papers)
                driver.quit()
                return results
            return []
        except:
            pass
        
        results = extract_papers_from_driver(driver, num_papers)
        driver.quit()
        return results
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return []

def extract_papers_from_driver(driver, num_papers):
    """Extract papers from Google Scholar using Selenium"""
    try:
        papers = []
        
        # Wait for results to load
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "gs_ri")))
        
        results = driver.find_elements(By.CLASS_NAME, "gs_ri")
        
        for result in results[:num_papers]:
            try:
                title_elem = result.find_element(By.TAG_NAME, "h3")
                title = title_elem.text
                
                link = result.find_element(By.TAG_NAME, "a").get_attribute("href")
                
                info = result.find_element(By.CLASS_NAME, "gs_a").text
                parts = info.split(" - ")
                authors = parts[0] if parts else "Unknown"
                
                abstract = result.find_element(By.CLASS_NAME, "gs_rs").text if result.find_elements(By.CLASS_NAME, "gs_rs") else "No abstract available"
                
                citations = ""
                meta = result.find_element(By.CLASS_NAME, "gs_fl")
                if meta:
                    citations = meta.text
                
                year = ""
                try:
                    year_text = info.split(" - ")[-1] if " - " in info else ""
                    year = year_text.strip().split()[0] if year_text else "Unknown"
                except:
                    year = "Unknown"
                
                paper_data = {
                    'title': title,
                    'authors': authors,
                    'abstract': abstract,
                    'citations': citations,
                    'year': year,
                    'url': link
                }
                
                credibility, reasons = calculate_credibility(paper_data)
                paper_data['credibility'] = credibility
                paper_data['credibility_reasons'] = reasons
                papers.append(paper_data)
                
            except Exception as e:
                continue
        
        papers = sorted(papers, key=lambda x: x.get('credibility', 0), reverse=True)
        st.success(f"✅ Found {len(papers)} papers")
        return papers
        
    except Exception as e:
        st.error(f"❌ Error extracting papers: {str(e)}")
        return []

if search_btn and query:
    st.session_state.last_query = query
    
    if query not in [h['query'] for h in st.session_state.search_history]:
        st.session_state.search_history.insert(0, {'query': query, 'results': None})
    
    with st.spinner("Searching Google Scholar..."):
        results = fetch_google_scholar(query, num_papers)
        
        if results:
            st.session_state.results = results
            for h in st.session_state.search_history:
                if h['query'] == query:
                    h['results'] = results
                    break
        else:
            st.warning("⚠️ No papers found or CAPTCHA pending.")

if st.session_state.results:
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📄 Papers", "📊 Summary", "⬇️ Export"])
    
    with tab1:
        for i, paper in enumerate(st.session_state.results, 1):
            abstract = paper.get('abstract', 'No abstract')
            if abstract and len(abstract) > 300:
                abstract = abstract[:300] + "..."
            
            credibility = paper.get('credibility', 0)
            reasons = paper.get('credibility_reasons', [])
            
            st.markdown(f"""<div class='result-card'>
<h3>{i}. {paper['title']}</h3>
<p><span class='score-badge'>Credibility: {credibility}/100</span></p>
<p><b>Authors:</b> {paper.get('authors', 'Unknown')}</p>
<p><b>Year:</b> {paper.get('year', 'Unknown')}</p>
<p><b>Abstract:</b> {abstract}</p>
<p><b>Citations:</b> {paper.get('citations', 'N/A')}</p>
{"<a href='" + paper.get('url', '#') + "' target='_blank'>🔗 View Paper</a>" if paper.get('url') else ""}
</div>""", unsafe_allow_html=True)
            
            if reasons:
                with st.expander("📊 Score Breakdown"):
                    for reason in reasons:
                        st.write(f"• {reason}")
    
    with tab2:
        col1, col2, col3 = st.columns(3)
        col1.metric("Papers Found", len(st.session_state.results))
        avg_cred = sum(p.get('credibility', 0) for p in st.session_state.results) / len(st.session_state.results) if st.session_state.results else 0
        col2.metric("Avg Credibility", f"{avg_cred:.0f}/100")
        col3.metric("Total Results", len(st.session_state.results))
    
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
                    story.append(Paragraph(f"Credibility: {paper.get('credibility', 0)}/100", styles['Normal']))
                    story.append(Paragraph(f"Authors: {paper.get('authors', 'Unknown')}", styles['Normal']))
                    story.append(Paragraph(f"Year: {paper.get('year', 'Unknown')}", styles['Normal']))
                    if paper.get('abstract'):
                        abstract_text = paper['abstract'][:300] + "..." if len(paper['abstract']) > 300 else paper['abstract']
                        story.append(Paragraph(f"<b>Abstract:</b> {abstract_text}", styles['Normal']))
                    if paper.get('url'):
                        story.append(Paragraph(f"<a href='{paper.get('url')}'><u>View Paper</u></a>", styles['Normal']))
                    
                    # Add citations
                    for fmt in ['APA', 'MLA', 'Chicago']:
                        citation = format_citation(paper, fmt)
                        story.append(Paragraph(f"<b>{fmt}:</b> {citation}", styles['Normal']))
                    
                    story.append(Spacer(1, 0.2*inch))
                
                story.append(Paragraph(f"© 2025 Shashank Upadhyay", styles['Normal']))
                doc.build(story)
                pdf_buf.seek(0)
                st.download_button(label="⬇️ Download PDF", data=pdf_buf, file_name="research.pdf", mime="application/pdf", use_container_width=True)
                st.success("✅ PDF ready!")
            except Exception as e:
                st.error(f"❌ PDF Error: {str(e)}")
        
        st.divider()
        
        if st.button("📥 Download JSON", use_container_width=True):
            json_data = []
            for paper in st.session_state.results:
                json_data.append({
                    'title': paper.get('title', ''),
                    'authors': paper.get('authors', ''),
                    'year': paper.get('year', ''),
                    'credibility': paper.get('credibility', 0),
                    'abstract': paper.get('abstract', ''),
                    'url': paper.get('url', '')
                })
            json_str = json.dumps(json_data, indent=2)
            st.download_button(label="⬇️ Download JSON", data=json_str, file_name="research.json", mime="application/json", use_container_width=True)
        
        st.divider()
        
        if st.button("📥 Download CSV", use_container_width=True):
            csv_data = []
            for paper in st.session_state.results:
                csv_data.append({
                    'Title': paper.get('title', ''),
                    'Authors': paper.get('authors', ''),
                    'Year': paper.get('year', ''),
                    'Credibility': paper.get('credibility', 0),
                    'URL': paper.get('url', '')
                })
            csv_str = pd.DataFrame(csv_data).to_csv(index=False)
            st.download_button(label="⬇️ Download CSV", data=csv_str, file_name="research.csv", mime="text/csv", use_container_width=True)
        
        st.divider()
        st.markdown("### 📋 Citation Formats")
        citation_style = st.selectbox("Format:", ["APA", "MLA", "Chicago", "BibTeX"], key="citation_format", label_visibility="collapsed")
        
        for i, paper in enumerate(st.session_state.results[:3], 1):
            citation = format_citation(paper, citation_style)
            st.code(citation, language="text")
