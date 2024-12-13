import logging
import shutil
import os
from config import load_config, save_to_json
from scraper import crawl_website
from email_sender import send_emails_in_batches
from utils import load_existing_emails

def copy_config_example():
    if not os.path.exists('config.json') and os.path.exists('config.example.json'):
        try:
            shutil.copy('config.example.json', 'config.json')
            logging.info('config.example.json copied to config.json')
        except Exception as e:
            logging.error(f"Error copying config.example.json to config.json: {e}")

def merge_emails(new_emails, filename='emails.json'):
    existing_emails = load_existing_emails(filename)
    combined_emails = list(set(existing_emails + new_emails))
    save_to_json(combined_emails, filename)

def main():
    copy_config_example()
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
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()
