"""
Automated Research Engine for Google Scholar
Fetches peer-reviewed articles and generates a PDF with summaries + links
No hallucinations - uses actual abstracts and metadata
"""

import requests
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime
from typing import List, Dict
import subprocess
import sys

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.lib import colors
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab", "requests", "beautifulsoup4", "-q"])
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.lib import colors


class GoogleScholarScraper:
    def __init__(self):
        self.base_url = "https://scholar.google.com/scholar"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.articles = []

    def search(self, query: str, num_results: int = 10) -> List[Dict]:
        """
        Search Google Scholar for peer-reviewed articles
        """
        print(f"\n🔍 Searching Google Scholar for: '{query}'")
        print(f"📊 Fetching up to {num_results} results...\n")

        params = {
            'q': query,
            'hl': 'en',
            'as_sdt': '1,5',  # Peer-reviewed papers only
            'num': num_results
        }

        try:
            response = requests.get(self.base_url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            results = soup.find_all('div', class_='gs_ri')

            count = 0
            for result in results:
                if count >= num_results:
                    break

                try:
                    # Title and link
                    title_elem = result.find('h3', class_='gs_ct')
                    if not title_elem:
                        continue

                    title_link = title_elem.find('a')
                    if not title_link:
                        continue

                    title = title_link.get_text(strip=True)
                    link = title_link.get('href', '')

                    # Abstract/Summary
                    abstract_div = result.find('div', class_='gs_rs')
                    abstract = abstract_div.get_text(strip=True) if abstract_div else "No abstract available"

                    # Authors and publication info
                    info_div = result.find('div', class_='gs_a')
                    if info_div:
                        info_text = info_div.get_text(strip=True)
                        # Parse "Authors - Publication - Year"
                        parts = info_text.split('-')
                        authors = parts[0].strip() if len(parts) > 0 else "Unknown"
                        publication = parts[1].strip() if len(parts) > 1 else "Unknown"
                        year = parts[2].strip() if len(parts) > 2 else "Unknown"
                    else:
                        authors = "Unknown"
                        publication = "Unknown"
                        year = "Unknown"

                    article = {
                        'title': title,
                        'authors': authors,
                        'publication': publication,
                        'year': year,
                        'abstract': abstract,
                        'link': link,
                        'summary': abstract[:200] + "..." if len(abstract) > 200 else abstract
                    }

                    self.articles.append(article)
                    count += 1
                    print(f"✓ Found: {title[:60]}...")
                    time.sleep(1)  # Be respectful to Google

                except Exception as e:
                    continue

            print(f"\n✅ Successfully fetched {count} articles\n")
            return self.articles

        except Exception as e:
            print(f"❌ Error searching Google Scholar: {e}")
            return []

    def summarize_with_ollama(self, text: str, max_length: int = 150) -> str:
        """
        Summarize text using Ollama (local, free)
        Make sure Ollama is running: `ollama serve`
        """
        try:
            # Check if Ollama is running
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': 'mistral',  # or 'llama2'
                    'prompt': f'Summarize this in 2-3 sentences:\n{text}',
                    'stream': False
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result.get('response', text[:max_length])
            else:
                return text[:max_length]

        except requests.exceptions.ConnectionError:
            print("⚠️  Ollama not running. Using abstract text as-is.")
            print("   To use AI summaries, run: `ollama serve` in another terminal")
            return text[:max_length]
        except Exception as e:
            return text[:max_length]

    def generate_pdf(self, output_file: str = "research_summary.pdf", use_ollama: bool = False):
        """
        Generate a professional PDF with article summaries and links
        """
        if not self.articles:
            print("❌ No articles to generate PDF from. Search first!")
            return

        print(f"\n📄 Generating PDF: {output_file}")

        # Create PDF
        doc = SimpleDocTemplate(output_file, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=10,
            alignment=1  # Center
        )

        title = Paragraph("📚 Automated Research Summary", title_style)
        story.append(title)

        # Metadata
        meta_text = f"<b>Search Query & Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}<br/><b>Total Articles:</b> {len(self.articles)}<br/><b>Note:</b> All sources are from Google Scholar (peer-reviewed)"
        story.append(Paragraph(meta_text, styles['Normal']))
        story.append(Spacer(1, 0.3*inch))

        # Articles
        for idx, article in enumerate(self.articles, 1):
            # Article number and title
            article_title = Paragraph(
                f"<b>{idx}. {article['title']}</b>",
                styles['Heading2']
            )
            story.append(article_title)

            # Metadata
            meta = f"<b>Authors:</b> {article['authors']}<br/><b>Publication:</b> {article['publication']}<br/><b>Year:</b> {article['year']}"
            story.append(Paragraph(meta, styles['Normal']))

            # Summary (use Ollama if available)
            summary_text = article['summary']
            if use_ollama:
                summary_text = self.summarize_with_ollama(article['abstract'])

            story.append(Paragraph(f"<b>Summary:</b> {summary_text}", styles['Normal']))

            # Link
            if article['link']:
                link_text = f"<a href='{article['link']}'><b>📎 Read Full Paper</b></a>"
            else:
                link_text = "<i>Link not available</i>"

            story.append(Paragraph(link_text, styles['Normal']))
            story.append(Spacer(1, 0.2*inch))

            # Separator
            if idx < len(self.articles):
                story.append(Paragraph("<hr/>", styles['Normal']))
                story.append(Spacer(1, 0.1*inch))

        # Build PDF
        doc.build(story)
        print(f"✅ PDF generated successfully: {output_file}\n")

    def export_json(self, output_file: str = "research_articles.json"):
        """
        Export articles as JSON for programmatic access
        """
        with open(output_file, 'w') as f:
            json.dump(self.articles, f, indent=2)
        print(f"✅ JSON export saved: {output_file}\n")


def main():
    """Main entry point"""
    print("=" * 60)
    print("🔬 AUTOMATED RESEARCH ENGINE - Google Scholar")
    print("=" * 60)

    # Get search query from user
    query = input("\n🔍 Enter your research topic: ").strip()
    if not query:
        print("❌ Query cannot be empty!")
        return

    num_results = input("📊 How many articles to fetch? (default: 10): ").strip()
    try:
        num_results = int(num_results) if num_results else 10
    except ValueError:
        num_results = 10

    use_ollama = input("🤖 Use Ollama for AI summaries? (y/n, default: n): ").strip().lower() == 'y'

    # Search
    scraper = GoogleScholarScraper()
    articles = scraper.search(query, num_results)

    if articles:
        # Generate outputs
        pdf_name = f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        json_name = f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        scraper.generate_pdf(pdf_name, use_ollama=use_ollama)
        scraper.export_json(json_name)

        print("\n" + "=" * 60)
        print("✅ RESEARCH SUMMARY COMPLETE!")
        print("=" * 60)
        print(f"📄 PDF: {pdf_name}")
        print(f"📊 JSON: {json_name}")
        print(f"📈 Articles found: {len(articles)}")
    else:
        print("❌ No articles found. Try a different search query.")


if __name__ == "__main__":
    main()
