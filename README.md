# Email Scraper and Sender

This project is a Python-based tool designed to scrape emails from a specified website and send emails to those addresses. It utilizes several libraries for web scraping, email validation, and SMTP functionality.

## Features

- **Email Scraping**: Crawls a specified website to extract valid email addresses.
- **Email Sending**: Sends HTML emails to a list of scraped addresses.
- **Batch Processing**: Allows sending emails in batches to avoid being flagged as spam.
- **Configuration Management**: Loads configurations from a JSON file for easy customization.
- **Logging**: Provides detailed logging of operations for troubleshooting.

## Requirements

- Python 3.x
- Libraries:
  - `requests`
  - `beautifulsoup4`
  - `email-validator`

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
