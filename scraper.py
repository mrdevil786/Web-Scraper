import subprocess
import sys
import json
import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urljoin, urlparse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import os
import concurrent.futures
import importlib
from email_validator import validate_email, EmailNotValidError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def install(package):
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', package])
    except Exception as e:
        logging.error(f"Failed to install package {package}: {e}")

def check_and_install_modules(required_modules):
    for module in required_modules:
        try:
            importlib.import_module(module)
        except ImportError:
            logging.info(f"{module} not found. Installing...")
            install(module)

required_modules = ['requests', 'bs4', 'email_validator']
check_and_install_modules(required_modules)

def load_config(filename='config.json'):
    if not os.path.exists(filename):
        logging.error(f"Configuration file {filename} not found.")
        return {}
    try:
        with open(filename, 'r') as jsonfile:
            return json.load(jsonfile)
    except json.JSONDecodeError as e:
        logging.error(f"Error reading JSON from {filename}: {e}")
        return {}

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

def load_existing_emails(filename='emails.json'):
    if not os.path.exists(filename):
        logging.warning(f"{filename} not found. Returning empty email list.")
        return []
    try:
        with open(filename, 'r') as jsonfile:
            return json.load(jsonfile)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error reading {filename}: {e}")
        return []

def save_to_json(emails, filename='emails.json'):
    try:
        with open(filename, 'w') as jsonfile:
            json.dump(emails, jsonfile)
        logging.info(f"Successfully saved {len(emails)} emails to {filename}.")
    except IOError as e:
        logging.error(f"Error writing to {filename}: {e}")

def is_media_url(url):
    media_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.mp4', '.avi', '.svg', '.webp', '.pdf', '.mp3', '.wav')
    return url.lower().endswith(media_extensions)

def crawl_website(start_url, visited, emails):
    queue = [start_url]
    total_pages = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        while queue:
            url = queue.pop(0)
            if url in visited or is_media_url(url):
                continue
            visited.add(url)

            future = executor.submit(scrape_emails, url)
            scraped_emails = future.result()
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

def load_email_template(template_file='email_template.html'):
    if not os.path.exists(template_file):
        logging.error(f"Email template file {template_file} not found.")
        return ""
    try:
        with open(template_file, 'r') as file:
            return file.read()
    except IOError as e:
        logging.error(f"Error reading {template_file}: {e}")
        return ""

def send_email(recipient_email, config):
    sender_email = config['email']['sender']
    sender_password = config['email']['password']
    smtp_server = config['smtp']['server']
    smtp_port = config['smtp']['port']
    subject = config.get('email_subject', 'Default Subject')

    html_template = load_email_template()
    if not html_template:
        logging.error("Cannot send email: HTML template is empty.")
        return False

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html_template, 'html'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            logging.info(f'Email sent to {recipient_email}')
            return True
    except smtplib.SMTPException as e:
        logging.error(f'Failed to send email to {recipient_email}: {e}')
        return False

def send_emails_in_batches(recipient_emails, config, batch_size=10):
    existing_emails = load_existing_emails()

    successfully_sent = []
    failed_emails = []

    for i in range(0, len(recipient_emails), batch_size):
        batch = recipient_emails[i:i+batch_size]
        for recipient_email in batch:
            if send_email(recipient_email, config):
                successfully_sent.append(recipient_email)
            else:
                failed_emails.append(recipient_email)

        time.sleep(2)

    remaining_emails = [email for email in existing_emails if email not in successfully_sent]

    save_to_json(remaining_emails)
    
    if failed_emails:
        logging.warning(f"The following emails failed to send: {failed_emails}")

def merge_emails(new_emails, filename='emails.json'):
    existing_emails = load_existing_emails(filename)
    combined_emails = list(set(existing_emails + new_emails))
    save_to_json(combined_emails, filename)

def main():
    config = load_config()
    if not config:
        logging.error("Exiting program due to configuration loading failure.")
        return

    while True:
        print("\nChoose an action:")
        print("\n1. Scrape emails")
        print("2. Send emails")
        print("3. Exit")
        choice = input("\nEnter your choice (1-3): ")

        if choice == '1':
            start_url = input("\nEnter the base URL (e.g., 'example.com'): ")
            if not start_url.startswith('https://'):
                start_url = 'https://' + start_url
            visited = set()
            all_emails = set()

            crawl_website(start_url, visited, all_emails)

            merge_emails(list(all_emails))

        elif choice == '2':
            all_emails = load_existing_emails()
            if not all_emails:
                print("No emails to send.")
                continue

            print("\nFound the following emails:\n")
            for i, email in enumerate(all_emails, start=1):
                print(f"{i}. {email}")

            send_choice = input("\nEnter email number or (A) to send to all: ").strip().upper()

            if send_choice == 'A':
                recipient_emails = all_emails
            else:
                try:
                    selected_index = int(send_choice) - 1
                    if 0 <= selected_index < len(all_emails):
                        recipient_emails = [all_emails[selected_index]]
                    else:
                        print("Invalid selection.")
                        continue
                except ValueError:
                    print("Please enter a valid number or 'A'.")
                    continue

            send_emails_in_batches(recipient_emails, config)

        elif choice == '3':
            logging.info("Exiting the program.")
            break

        else:
            print("Invalid choice. Please choose again.")

if __name__ == "__main__":
    main()
