import requests
import re
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from email_validator import validate_email, EmailNotValidError
import time

def is_media_url(url):
    media_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.mp4', '.avi', '.svg', '.webp', '.pdf', '.mp3', '.wav')
    return url.lower().endswith(media_extensions)

def scrape_emails(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Request failed for {url}: {e}")
        return []

    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text()
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)

    valid_emails = set()
    for email in emails:
        try:
            valid = validate_email(email)
            valid_emails.add(valid.email)
        except EmailNotValidError:
            continue

    return list(valid_emails)

def crawl_website(start_url, visited, emails):
    queue = [start_url]
    total_pages = 0

    while queue:
        url = queue.pop(0)
        if url in visited or is_media_url(url):
            continue
        visited.add(url)

        scraped_emails = scrape_emails(url)
        emails.update(scraped_emails)

        total_pages += 1
        print(f"Scanned page {total_pages}: {url}")

        time.sleep(1)

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            for link in soup.find_all('a', href=True):
                next_url = urljoin(url, link['href'])
                if urlparse(next_url).netloc == urlparse(start_url).netloc and next_url not in visited and not is_media_url(next_url):
                    queue.append(next_url)
        except requests.RequestException as e:
            logging.error(f"Failed to retrieve {url}: {e}")

    print(f"\nTotal unique emails found: {len(emails)}")
