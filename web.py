import streamlit as st
import requests
import xml.etree.ElementTree as ET
import json
import pandas as pd
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from urllib.parse import quote

st.set_page_config(page_title="Atlas - Web", layout="wide", initial_sidebar_state="expanded")

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
    st.markdown("### WEB VERSION")
    st.markdown("---")
    st.markdown("✅ ArXiv API\n✅ PDF exports\n✅ CSV & JSON")
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
    quality_sources = ['nature', 'science', 'ieee', 'acm', 'proceedings', 'journal', 'conference', 'arxiv']
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
        return f'@article{{arxiv_{hash(title) % 10000},\n  title={{{title}}},\n  author={{{authors}}},\n  year={{{year}}},\n  journal={{{publication}}}\n}}'
    return authors

def scrape_arxiv(query, num_papers):
    results = []
    try:
        url = "http://export.arxiv.org/api/query"
        params = {
            'search_query': f'all:{query}',
            'start': 0,
            'max_results': num_papers,
            'sortBy': 'relevance',
            'sortOrder': 'descending'
        }
        
        st.info(f"📍 Searching ArXiv for: {query}")
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            
            for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                paper = {}
                paper['title'] = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
                
                authors_list = []
                for author in entry.findall('{http://www.w3.org/2005/Atom}author'):
                    name = author.find('{http://www.w3.org/2005/Atom}name').text
                    authors_list.append(name)
                
                paper['authors'] = ', '.join(authors_list[:3]) if authors_list else 'Unknown'
                if len(authors_list) > 3:
                    paper['authors'] += ', et al.'
                
                paper['abstract'] = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip()
                paper['id'] = entry.find('{http://www.w3.org/2005/Atom}id').text
                paper['link'] = paper['id'].replace('http://arxiv.org/abs/', 'https://arxiv.org/abs/')
                paper['published'] = entry.find('{http://www.w3.org/2005/Atom}published').text
                paper['year'] = paper['published'][:4]
                paper['publication'] = 'ArXiv'
                paper['citations'] = ''
                
                paper['credibility'] = calculate_credibility(paper)
                results.append(paper)
            
            results = sorted(results, key=lambda x: x['credibility'], reverse=True)
            st.success(f"✅ Found {len(results)} results")
            return results
        else:
            st.error(f"❌ API Error: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return []

if search_btn and query:
    st.session_state.last_query = query
    if query not in [h['query'] for h in st.session_state.search_history]:
        st.session_state.search_history.insert(0, {'query': query, 'results': None})

    with st.spinner("Searching ArXiv..."):
        results = scrape_arxiv(query, num_papers)
        if results:
            st.session_state.results = results
            for h in st.session_state.search_history:
                if h['query'] == query:
                    h['results'] = results
                    break
        else:
            st.warning("⚠️ No papers found.")
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
                    st.markdown(f"[🔗 View on ArXiv]({link})")
            
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
        col3.metric("Papers Analyzed", len(st.session_state.results))

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
                        story.append(Paragraph(f"<a href='{paper.get('link')}'><u>🔗 View Paper</u></a>", styles['Normal']))
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
