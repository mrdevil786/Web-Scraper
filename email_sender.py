import time
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils import load_existing_emails
from utils import load_email_template
from utils import save_to_json

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
