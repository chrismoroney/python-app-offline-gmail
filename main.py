import imaplib
import email
from email.header import decode_header
import sqlite3
import os

# Gmail IMAP settings
IMAP_SERVER = 'imap.gmail.com'
IMAP_PORT = 993

# Database settings
DATABASE_NAME = 'emails.db'

def connect_to_gmail(username, password):
    """Connects to Gmail IMAP server and logs in."""
    try:
        imap = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        imap.login(username, password)
        return imap
    except Exception as e:
        print(f"Error connecting to Gmail: {e}")
        return None

def create_database():
    """Creates the database table for storing emails."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            subject TEXT,
            body TEXT,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()

def store_email(sender, subject, body, date):
    """Stores an email in the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO emails (sender, subject, body, date) VALUES (?, ?, ?, ?)", 
                   (sender, subject, body, date))
    conn.commit()
    conn.close()

def fetch_and_store_emails(imap):
    """Fetches emails from Gmail and stores them in the database."""
    imap.select('INBOX')
    status, messages = imap.search(None, 'ALL') 

    if status == 'OK':
        for num in messages[0].split():
            status, data = imap.fetch(num, '(RFC822)')
            if status == 'OK':
                email_message = email.message_from_bytes(data[0][1])

                sender = email_message['From']
                subject = decode_header(email_message['Subject'])[0][0] 
                if isinstance(subject, bytes):
                    subject = subject.decode()
                date = email_message['Date']

                # Get email body
                body = ""
                if email_message.is_multipart():
                    for part in email_message.walk():
                        content_type = part.get_content_type()
                        if content_type == 'text/plain' and 'attachment' not in part.get('Content-Disposition', ''):
                            body += part.get_payload(decode=True).decode()
                else:
                    body = email_message.get_payload(decode=True).decode()

                store_email(sender, subject, body, date)
    imap.close()
    imap.logout()

def view_emails_offline():
    """Displays the stored emails from the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM emails")
    emails = cursor.fetchall()
    conn.close()

    if emails:
        for email in emails:
            print("-" * 40)
            print(f"From: {email[1]}")
            print(f"Subject: {email[2]}")
            print(f"Date: {email[4]}")
            print("\n", email[3], "\n")
    else:
        print("No emails found in the database.")

if __name__ == '__main__':
    if not os.path.isfile(DATABASE_NAME):
        create_database()
    
    username = input("Enter your Gmail address: ")
    password = input("Enter your Gmail password: ")

    imap = connect_to_gmail(username, password)
    if imap:
        fetch_and_store_emails(imap)
        print("Emails fetched and stored successfully!")
        
    view_emails_offline()
