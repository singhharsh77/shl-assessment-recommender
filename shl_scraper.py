import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin
import re

class SHLCatalogScraper:
    def __init__(self):
        self.base_url = "https://www.shl.com/solutions/products/product-catalog/"
        self.assessments = []
        
    def scrape_catalog(self):
        """Scrape the main catalog page to get all individual test solutions"""
        print("Fetching main catalog page...")
        response = requests.get(self.base_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all assessment links (excluding pre-packaged solutions)
        assessment_links = []
        
        # Look for product tiles or links
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/product-catalog/view/' in href:
                full_url = urljoin(self.base_url, href)
                if full_url not in assessment_links:
                    assessment_links.append(full_url)
        
        print(f"Found {len(assessment_links)} assessment links")
        
        # Scrape each assessment page
        for idx, url in enumerate(assessment_links[:50]):  # Limit to 50 for testing
            print(f"Scraping {idx+1}/{len(assessment_links)}: {url}")
            self.scrape_assessment_page(url)
            time.sleep(0.5)  # Be polite to the server
        
        return self.assessments
    
    def scrape_assessment_page(self, url):
        """Scrape individual assessment page for details"""
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract assessment name
            name = soup.find('h1')
            name = name.text.strip() if name else url.split('/')[-2]
            
            # Extract description
            description = ""
            desc_div = soup.find('div', class_='description') or soup.find('div', class_='content')
            if desc_div:
                description = desc_div.get_text(strip=True)[:500]
            
            # Extract test type (look for categories like "Knowledge & Skills", "Personality")
            test_type = self.extract_test_type(soup, description)
            
            # Extract duration (look for time mentions)
            duration = self.extract_duration(soup, description)
            
            # Extract skills/competencies
            skills = self.extract_skills(soup, description, name)
            
            assessment = {
                'name': name,
                'url': url,
                'description': description,
                'test_type': test_type,
                'duration_minutes': duration,
                'skills': skills,
                'full_text': f"{name} {description}"
            }
            
            self.assessments.append(assessment)
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
    
    def extract_test_type(self, soup, description):
        """Extract test type (K=Knowledge, P=Personality, C=Cognitive)"""
        text = (soup.get_text() + description).lower()
        
        if any(word in text for word in ['personality', 'behavior', 'opq', 'motivation']):
            return 'P'
        elif any(word in text for word in ['cognitive', 'reasoning', 'verify', 'numerical', 'verbal']):
            return 'C'
        elif any(word in text for word in ['knowledge', 'skill', 'technical', 'programming', 'software']):
            return 'K'
        return 'K'  # Default
    
    def extract_duration(self, soup, description):
        """Extract assessment duration in minutes"""
        text = soup.get_text() + description
        
        # Look for patterns like "30 minutes", "1 hour", "45 mins"
        duration_patterns = [
            r'(\d+)\s*minutes?',
            r'(\d+)\s*mins?',
            r'(\d+)\s*hours?'
        ]
        
        for pattern in duration_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                duration = int(match.group(1))
                if 'hour' in pattern:
                    duration *= 60
                return duration
        
        return 45  # Default duration
    
    def extract_skills(self, soup, description, name):
        """Extract skills tested by this assessment"""
        text = (name + " " + description).lower()
        
        # Common skills to look for
        skill_keywords = {
            'java': ['java'],
            'python': ['python'],
            'sql': ['sql', 'database'],
            'javascript': ['javascript', 'js'],
            'excel': ['excel'],
            'leadership': ['leadership', 'management'],
            'communication': ['communication', 'interpersonal'],
            'sales': ['sales', 'selling'],
            'analytical': ['analytical', 'analysis'],
            'problem_solving': ['problem solving', 'reasoning'],
            'english': ['english', 'verbal'],
            'numerical': ['numerical', 'mathematics'],
            'collaboration': ['collaboration', 'teamwork']
        }
        
        found_skills = []
        for skill, keywords in skill_keywords.items():
            if any(kw in text for kw in keywords):
                found_skills.append(skill)
        
        return found_skills
    
    def save_to_file(self, filename='shl_assessments.json'):
        """Save scraped data to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.assessments, f, indent=2)
        print(f"Saved {len(self.assessments)} assessments to {filename}")

# Usage
if __name__ == "__main__":
    scraper = SHLCatalogScraper()
    assessments = scraper.scrape_catalog()
    scraper.save_to_file()
    print(f"Total assessments scraped: {len(assessments)}")