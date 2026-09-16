import streamlit as st
import requests
import json
import pandas as pd
import io
import xml.etree.ElementTree as ET
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
if 'num_papers' not in st.session_state:
    st.session_state.num_papers = 20

dark_css = """<style>
body { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #e2e8f0; }
[data-testid="stAppViewContainer"] { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); }
[data-testid="stMainBlockContainer"] { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%); }
h1 { background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-size: 3rem !important; font-weight: 800 !important; }
h2, h3 { color: #e2e8f0 !important; }
button { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important; color: white !important; border: none !important; padding: 12px 24px !important; border-radius: 8px !important; font-weight: 600 !important; }
.result-card { background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 12px; padding: 20px; margin: 15px 0; border-left: 4px solid #3b82f6; }
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
    num_papers = st.slider("Papers:", min_value=5, max_value=100, value=20, step=5)
with col3:
    search_btn = st.button("🔍 Search", use_container_width=True)

def calculate_credibility(paper):
    score = 50
    reasons = []
    if paper.get('summary') and len(paper.get('summary', '')) > 100:
        score += 15
        reasons.append("Good abstract: +15")
    try:
        year_str = paper.get('published', '')[:4]
        year = int(year_str)
        years_old = 2025 - year
        if years_old <= 2:
            score += 20
            reasons.append(f"Recent paper ({year}): +20")
        elif years_old <= 5:
            score += 15
            reasons.append(f"Recent paper ({year}): +15")
        elif years_old <= 10:
            score += 10
            reasons.append(f"Recent paper ({year}): +10")
    except:
        pass
    if len(paper.get('authors', [])) > 3:
        score += 10
        reasons.append("Multiple authors: +10")
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
        st.info(f"📍 Searching ArXiv for: {query}")
        response = requests.get(url, params=params, timeout=15)
        if response.status_code != 200:
            st.error(f"❌ Error: HTTP {response.status_code}")
            return []
        root = ET.fromstring(response.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
        papers = []
        entries = root.findall('atom:entry', ns)
        st.success(f"✅ Found {len(entries)} results on arXiv")
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
        st.error(f"❌ Error: {str(e)}")
        return []

if search_btn and query:
    st.session_state.last_query = query
    if query not in [h['query'] for h in st.session_state.search_history]:
        st.session_state.search_history.insert(0, {'query': query, 'results': None})
    with st.spinner("Searching ArXiv..."):
        results = fetch_arxiv(query, num_papers)
        if results:
            st.session_state.results = results
            for h in st.session_state.search_history:
                if h['query'] == query:
                    h['results'] = results
                    break
        else:
            st.warning("⚠️ No papers found. Try a different search term.")
            st.session_state.results = None

if st.session_state.results:
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📄 Papers", "📊 Summary", "⬇️ Export"])
    with tab1:
        for i, paper in enumerate(st.session_state.results, 1):
            authors = ', '.join(paper.get('authors', ['Unknown'])[:3])
            if len(paper.get('authors', [])) > 3:
                authors += ", et al."
            abstract = paper.get('summary', 'No abstract')
            if abstract and len(abstract) > 300:
                abstract = abstract[:300] + "..."
            credibility = paper.get('credibility', 0)
            reasons = paper.get('credibility_reasons', [])
            st.markdown(f"""<div class='result-card'>
<h3>{i}. {paper['title']}</h3>
<p><span class='score-badge'>Credibility: {credibility}/100</span></p>
<p><b>Authors:</b> {authors}</p>
<p><b>Published:</b> {paper.get('published', 'Unknown')[:10]} | <b>ArXiv ID:</b> {paper.get('arxiv_id', 'N/A')}</p>
<p><b>Abstract:</b> {abstract}</p>
<a href='{paper.get('arxiv_url', '#')}' target='_blank'>🔗 View on arXiv</a>
</div>""", unsafe_allow_html=True)
            if reasons:
                with st.expander("📊 Score Breakdown"):
                    for reason in reasons:
                        st.write(f"• {reason}")
            with st.expander("📚 Citations"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.subheader("APA")
                    st.code(format_citation(paper, 'APA'), language="text")
                with col2:
                    st.subheader("MLA")
                    st.code(format_citation(paper, 'MLA'), language="text")
                with col3:
                    st.subheader("Chicago")
                    st.code(format_citation(paper, 'Chicago'), language="text")
                st.subheader("BibTeX")
                st.code(format_citation(paper, 'BibTeX'), language="text")
    with tab2:
        col1, col2, col3 = st.columns(3)
        col1.metric("Papers Found", len(st.session_state.results))
        col2.metric("Avg Credibility", f"{sum(p.get('credibility', 0) for p in st.session_state.results) / len(st.session_state.results):.0f}/100")
        recent_count = sum(1 for p in st.session_state.results if int(p.get('published', '0000')[:4]) >= 2024)
        col3.metric("Recent Papers (2024+)", recent_count)
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
                    authors = ', '.join(paper.get('authors', ['Unknown'])[:5])
                    story.append(Paragraph(f"<b>{i}. {paper['title']}</b>", styles['Heading2']))
                    story.append(Paragraph(f"Credibility: {paper.get('credibility', 0)}/100", styles['Normal']))
                    story.append(Paragraph(f"Authors: {authors}", styles['Normal']))
                    story.append(Paragraph(f"Published: {paper.get('published', 'Unknown')[:10]}", styles['Normal']))
                    if paper.get('summary'):
                        abstract_text = paper['summary'][:300] + "..." if len(paper['summary']) > 300 else paper['summary']
                        story.append(Paragraph(f"<b>Abstract:</b> {abstract_text}", styles['Normal']))
                    if paper.get('arxiv_url'):
                        story.append(Paragraph(f"<a href='{paper.get('arxiv_url')}'><u>View on arXiv</u></a>", styles['Normal']))
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
            json_data = [{'title': p.get('title', ''), 'authors': p.get('authors', []), 'published': p.get('published', ''), 'arxiv_id': p.get('arxiv_id', ''), 'credibility': p.get('credibility', 0), 'abstract': p.get('summary', ''), 'url': p.get('arxiv_url', '')} for p in st.session_state.results]
            st.download_button(label="⬇️ Download JSON", data=json.dumps(json_data, indent=2), file_name="research.json", mime="application/json", use_container_width=True)
        st.divider()
        if st.button("📥 Download CSV", use_container_width=True):
            csv_data = [{'Title': p.get('title', ''), 'Authors': ', '.join(p.get('authors', [])[:3]), 'Published': p.get('published', '')[:10], 'ArXiv ID': p.get('arxiv_id', ''), 'Credibility': p.get('credibility', 0), 'URL': p.get('arxiv_url', '')} for p in st.session_state.results]
            st.download_button(label="⬇️ Download CSV", data=pd.DataFrame(csv_data).to_csv(index=False), file_name="research.csv", mime="text/csv", use_container_width=True)
        st.divider()
        st.markdown("### 📋 Citation Formats")
        citation_style = st.selectbox("Format:", ["APA", "MLA", "Chicago", "BibTeX"], key="citation_format", label_visibility="collapsed")
        for i, paper in enumerate(st.session_state.results[:3], 1):
            st.code(format_citation(paper, citation_style), language="text")
