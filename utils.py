import json
import os
import logging

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
