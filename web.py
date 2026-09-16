import streamlit as st
import requests
import json
import pandas as pd
import io
import xml.etree.ElementTree as ET
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from urllib.parse import quote

st.set_page_config(page_title="Atlas Research", layout="wide", initial_sidebar_state="expanded")

if 'results' not in st.session_state:
    st.session_state.results = None
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
if 'last_query' not in st.session_state:
    st.session_state.last_query = ""
if 'num_papers' not in st.session_state:
    st.session_state.num_papers = 20

professional_css = """<style>
* { margin: 0; padding: 0; }
body { background: #ffffff; color: #1d1d1d; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; line-height: 1.6; }
[data-testid="stAppViewContainer"] { background: #ffffff; }
[data-testid="stMainBlockContainer"] { background: #ffffff; padding: 0; }
[data-testid="stSidebar"] { background: #f5f5f7; border-right: 1px solid #e5e5e7; }
h1 { color: #1d1d1d; font-size: 3.5rem; font-weight: 600; letter-spacing: -0.02em; line-height: 1.1; margin: 40px 0 20px 0; }
h2 { color: #1d1d1d; font-size: 2rem; font-weight: 600; margin: 30px 0 15px 0; }
h3 { color: #1d1d1d; font-size: 1.3rem; font-weight: 600; margin: 20px 0 10px 0; }
input { font-size: 1rem; padding: 12px 16px; border: 1px solid #d2d2d7; border-radius: 8px; background: #ffffff; color: #1d1d1d; }
input:focus { border-color: #0071e3; outline: none; box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.1); }
button { font-size: 1rem; font-weight: 500; padding: 12px 24px; border: none; border-radius: 8px; background: #0071e3; color: white; cursor: pointer; transition: background 0.2s; }
button:hover { background: #0077ed; }
button:active { background: #005cc8; }
[data-testid="stMarkdownContainer"] p { color: #424245; margin: 8px 0; }
.result-card { background: #ffffff; border: 1px solid #e5e5e7; border-radius: 12px; padding: 24px; margin: 16px 0; transition: box-shadow 0.2s; }
.result-card:hover { box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08); }
.score-badge { display: inline-block; background: #f5f5f7; color: #1d1d1d; padding: 6px 12px; border-radius: 6px; font-weight: 500; border: 1px solid #e5e5e7; font-size: 0.9rem; }
a { color: #0071e3; text-decoration: none; }
a:hover { text-decoration: underline; }
[data-testid="stTabs"] { border-bottom: 1px solid #e5e5e7; }
div[data-testid="stVerticalBlock"] > div:first-child > div > div > button { margin-right: 12px; }
</style>"""

st.markdown(professional_css, unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## Atlas Research")
    st.markdown("Research Papers at Scale")
    st.markdown("---")
    st.markdown("ArXiv API | Credibility Scoring | Export Options")
    if st.session_state.search_history:
        st.markdown("### Recent")
        for i, h in enumerate(st.session_state.search_history[:5], 1):
            if st.button(f"{i}. {h['query']}", key=f"hist_{i}", use_container_width=True):
                st.session_state.last_query = h['query']
                st.session_state.results = h.get('results', None)

st.markdown("# Atlas Research")
st.markdown("Discover, analyze, and export academic research from ArXiv.")

col1, col2, col3 = st.columns([3, 1.2, 1])
with col1:
    query = st.text_input("What research interests you?", label_visibility="collapsed", placeholder="e.g., quantum computing, machine learning")
with col2:
    num_papers = st.slider("Papers", 5, 100, 20, 5, label_visibility="collapsed")
with col3:
    search_btn = st.button("Search", use_container_width=True)

def calculate_credibility(paper):
    score = 50
    reasons = []
    if paper.get('summary') and len(paper.get('summary', '')) > 100:
        score += 15
        reasons.append("Comprehensive abstract: +15")
    try:
        year_str = paper.get('published', '')[:4]
        year = int(year_str)
        years_old = 2025 - year
        if years_old <= 2:
            score += 20
            reasons.append(f"Recently published ({year}): +20")
        elif years_old <= 5:
            score += 15
            reasons.append(f"Recently published ({year}): +15")
        elif years_old <= 10:
            score += 10
            reasons.append(f"Published {year}: +10")
    except:
        pass
    if len(paper.get('authors', [])) > 3:
        score += 10
        reasons.append("Collaborative research: +10")
    return min(100, score), reasons

def format_citation(paper, style='APA'):
    authors = paper.get('authors', ['Unknown'])
    author_str = ', '.join(authors[:3])
    if len(authors) > 3:
        author_str += ", et al."
    title = paper.get('title', 'Unknown Title').strip()
    year = paper.get('published', 'n.d.')[:4]
    arxiv_id = paper.get('arxiv_id', 'Unknown')
    if style == 'APA':
        return f"{author_str} ({year}). {title}. arXiv preprint {arxiv_id}."
    elif style == 'MLA':
        return f"{author_str}. \"{title}.\" arXiv preprint {arxiv_id}, {year}."
    elif style == 'Chicago':
        return f"{author_str}. \"{title}.\" arXiv preprint {arxiv_id} ({year})."
    elif style == 'BibTeX':
        return f'@article{{{arxiv_id.replace("/", "_")},\n  title={{{title}}},\n  author={{{author_str}}},\n  year={{{year}}},\n  journal={{arXiv preprint {arxiv_id}}}\n}}'
    return author_str

def fetch_arxiv(query, num_papers):
    try:
        url = "http://export.arxiv.org/api/query"
        params = {'search_query': f'all:{query}', 'start': 0, 'max_results': min(num_papers, 100), 'sortBy': 'relevance', 'sortOrder': 'descending'}
        st.info(f"Searching ArXiv for research on {query}")
        response = requests.get(url, params=params, timeout=15)
        if response.status_code != 200:
            st.error(f"Unable to fetch results. Status: {response.status_code}")
            return []
        root = ET.fromstring(response.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
        papers = []
        entries = root.findall('atom:entry', ns)
        st.success(f"Found {len(entries)} papers on arXiv")
        for entry in entries[:num_papers]:
            try:
                title = entry.find('atom:title', ns).text.strip()
                authors = [author.find('atom:name', ns).text for author in entry.findall('atom:author', ns)]
                summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
                published = entry.find('atom:published', ns).text
                arxiv_id = entry.find('atom:id', ns).text.split('/abs/')[-1]
                paper_data = {'title': title, 'authors': authors, 'summary': summary, 'published': published, 'arxiv_id': arxiv_id, 'arxiv_url': f"https://arxiv.org/abs/{arxiv_id}"}
                credibility, reasons = calculate_credibility(paper_data)
                paper_data['credibility'] = credibility
                paper_data['credibility_reasons'] = reasons
                papers.append(paper_data)
            except:
                continue
        return sorted(papers, key=lambda x: x['credibility'], reverse=True)
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []

if search_btn and query:
    st.session_state.last_query = query
    if query not in [h['query'] for h in st.session_state.search_history]:
        st.session_state.search_history.insert(0, {'query': query, 'results': None})
    with st.spinner("Searching..."):
        results = fetch_arxiv(query, num_papers)
        if results:
            st.session_state.results = results
            for h in st.session_state.search_history:
                if h['query'] == query:
                    h['results'] = results
                    break
        else:
            st.warning("No results found. Try a different query.")
            st.session_state.results = None

if st.session_state.results:
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["Papers", "Analysis", "Export"])
    
    with tab1:
        st.markdown(f"### {len(st.session_state.results)} Papers Found")
        for i, paper in enumerate(st.session_state.results, 1):
            authors = ', '.join(paper.get('authors', ['Unknown'])[:3])
            if len(paper.get('authors', [])) > 3:
                authors += ", et al."
            abstract = paper.get('summary', 'No abstract')
            if abstract and len(abstract) > 250:
                abstract = abstract[:250] + "..."
            credibility = paper.get('credibility', 0)
            reasons = paper.get('credibility_reasons', [])
            
            st.markdown(f"""<div class='result-card'>
<h3>{i}. {paper['title']}</h3>
<p><span class='score-badge'>Credibility Score: {credibility}/100</span></p>
<p><strong>Authors:</strong> {authors}</p>
<p><strong>Published:</strong> {paper.get('published', 'Unknown')[:10]}</p>
<p><strong>Abstract:</strong> {abstract}</p>
<a href="{paper.get('arxiv_url', '#')}" target="_blank" style="display: inline-block; margin-top: 12px;">Read on arXiv</a>
</div>""", unsafe_allow_html=True)
            
            if reasons:
                with st.expander("Why this credibility score"):
                    for reason in reasons:
                        st.write(f"• {reason}")
            
            with st.expander("Citation formats"):
                cols = st.columns(2)
                with cols[0]:
                    st.markdown("**APA**")
                    st.code(format_citation(paper, 'APA'), language="text")
                with cols[1]:
                    st.markdown("**MLA**")
                    st.code(format_citation(paper, 'MLA'), language="text")
                st.markdown("**Chicago**")
                st.code(format_citation(paper, 'Chicago'), language="text")
                st.markdown("**BibTeX**")
                st.code(format_citation(paper, 'BibTeX'), language="text")
    
    with tab2:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Papers", len(st.session_state.results))
        with col2:
            avg_cred = sum(p.get('credibility', 0) for p in st.session_state.results) / len(st.session_state.results)
            st.metric("Average Credibility", f"{avg_cred:.0f}/100")
        with col3:
            recent = sum(1 for p in st.session_state.results if int(p.get('published', '0000')[:4]) >= 2024)
            st.metric("From 2024+", recent)
    
    with tab3:
        st.markdown("### Download Results")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Download PDF", use_container_width=True):
                try:
                    pdf_buf = io.BytesIO()
                    doc = SimpleDocTemplate(pdf_buf, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
                    story = []
                    styles = getSampleStyleSheet()
                    
                    title_style = ParagraphStyle(
                        'CustomTitle',
                        parent=styles['Heading1'],
                        fontSize=24,
                        textColor=colors.HexColor('#1d1d1d'),
                        spaceAfter=30,
                        fontName='Helvetica-Bold'
                    )
                    
                    story.append(Paragraph(f"Research: {st.session_state.last_query}", title_style))
                    story.append(Spacer(1, 0.3*inch))
                    
                    for i, paper in enumerate(st.session_state.results, 1):
                        authors = ', '.join(paper.get('authors', ['Unknown'])[:5])
                        story.append(Paragraph(f"<b>{i}. {paper['title']}</b>", styles['Heading2']))
                        story.append(Paragraph(f"Credibility: {paper.get('credibility', 0)}/100", styles['Normal']))
                        story.append(Paragraph(f"Authors: {authors}", styles['Normal']))
                        story.append(Paragraph(f"Published: {paper.get('published', 'Unknown')[:10]}", styles['Normal']))
                        if paper.get('summary'):
                            abstract = paper['summary'][:300] + "..." if len(paper['summary']) > 300 else paper['summary']
                            story.append(Paragraph(f"<b>Abstract:</b> {abstract}", styles['Normal']))
                        for fmt in ['APA', 'MLA', 'Chicago']:
                            citation = format_citation(paper, fmt)
                            story.append(Paragraph(f"<b>{fmt}:</b> {citation}", styles['Normal']))
                        story.append(Spacer(1, 0.2*inch))
                    
                    story.append(Paragraph(f"Copyright 2025 Shashank Upadhyay", styles['Normal']))
                    doc.build(story)
                    pdf_buf.seek(0)
                    st.download_button("Download PDF", pdf_buf, "research.pdf", "application/pdf", use_container_width=True)
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        with col2:
            if st.button("Download JSON", use_container_width=True):
                data = [{'title': p.get('title', ''), 'authors': p.get('authors', []), 'published': p.get('published', ''), 'arxiv_id': p.get('arxiv_id', ''), 'credibility': p.get('credibility', 0), 'abstract': p.get('summary', ''), 'url': p.get('arxiv_url', '')} for p in st.session_state.results]
                st.download_button("Download JSON", json.dumps(data, indent=2), "research.json", "application/json", use_container_width=True)
        
        with col3:
            if st.button("Download CSV", use_container_width=True):
                data = [{'Title': p.get('title', ''), 'Authors': ', '.join(p.get('authors', [])[:3]), 'Published': p.get('published', '')[:10], 'ID': p.get('arxiv_id', ''), 'Credibility': p.get('credibility', 0)} for p in st.session_state.results]
                st.download_button("Download CSV", pd.DataFrame(data).to_csv(index=False), "research.csv", "text/csv", use_container_width=True)
