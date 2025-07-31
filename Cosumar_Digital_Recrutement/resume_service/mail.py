import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Cosumar_Digital_Recrutement.settings')
django.setup()

from django.conf import settings
from imap_tools import MailBox
import socket
import time
from resume_service.models import Poste
from resume_service.models import Candidat
from resume_service.models import Candidature

EMAIL = settings.EMAIL
PASSWORD = settings.PASSWORD
IMAP_SERVER = settings.IMAP_SERVER

SAVE_FOLDER = 'downloaded_pdfs'
os.makedirs(SAVE_FOLDER, exist_ok=True)

# Set socket timeout to prevent hanging
socket.setdefaulttimeout(30)

def check_emails():
    """Check for new emails and process PDF attachments"""
    try:
        print(f"Checking emails at {time.strftime('%Y-%m-%d %H:%M:%S')}...")
        with MailBox(IMAP_SERVER).login(EMAIL, PASSWORD, 'INBOX') as mailbox:
            
            # Get all unseen messages
            messages = list(mailbox.fetch('(UNSEEN)'))
            
            if len(messages) > 0:
                print(f"Found {len(messages)} new unseen messages")
                
                pdf_count = 0
                for msg in messages:
                    print(f"Processing message from: {msg.from_} - Subject: '{msg.subject}'")
                    
                    # Fetch all job positions and candidates from database
                    postes = {p.titre: p for p in Poste.objects.all()}
                    candidats = {c.email: c for c in Candidat.objects.all()}
                    posteslower = {p.titre.lower(): p for p in postes.values()}
                    
                    print(f"Available job titles: {list(postes.keys())}")
                    print(f"Available candidates: {list(candidats.keys())}")

                    if not msg.attachments:
                        print(f"❌ No attachments found in message: '{msg.subject}'. Skipping...")
                        continue

                    if msg.subject.strip().lower() not in [titre.lower() for titre in postes]:
                        print(f"❌ Subject '{msg.subject.strip().lower()}' not found in job titles. Available titles: {list(postes.keys())}")
                        continue

                    # Check if candidate exists, if not create one
                    if msg.from_ not in candidats:
                        print(f"❌ Candidate '{msg.from_}' not found. Creating new candidate...")
                        candidat = Candidat() 
                        candidat.email = msg.headers.get('From')
                        candidat.nom = "Unknown"  # Will be updated later
                        candidat.prenom = "User"  # Will be updated later
                        candidat.save()
                        candidats[msg.from_] = candidat
                        print(f"✅ Added new candidate: {candidat.email}")
                
                    # Create candidature
                    candidature = Candidature()
                    candidature.poste = postes[msg.subject.strip()]
                    candidature.candidat = candidats[msg.from_]

                    # Process PDF attachments
                    pdf_saved = False
                    for att in msg.attachments:
                        if att.filename and att.filename.lower().endswith('.pdf'):
                            filepath = os.path.join(SAVE_FOLDER, att.filename)
                            with open(filepath, 'wb') as f:
                                f.write(att.payload)
                            
                            # Save PDF content to candidature
                            candidature.cv = att.payload
                            print(f"✅ Saved PDF: {filepath}")
                            pdf_count += 1
                            pdf_saved = True
                    
                    # Only save candidature if we found a PDF
                    if pdf_saved:
                        candidature.save()
                        print(f"✅ Created candidature for {candidats[msg.from_].email} -> {postes[msg.subject.strip()].titre}")
                    else:
                        print(f"❌ Error saving PDF")
                
                    # Mark message as seen
                    mailbox.flag(msg.uid, ['\\Seen'], True)
                    print(f"📧 Marked message as seen: '{msg.subject}'")
                
                print(f"✅ Processed {len(messages)} emails, downloaded {pdf_count} PDF files.")
            else:
                print("No new emails found.")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Will retry in next cycle...")

def main():
    """Main loop to continuously check for emails"""
    print("🚀 Starting email monitoring service...")
    print(f"📧 Monitoring: {EMAIL}")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            check_emails()
            print(f"⏰ Waiting 5 seconds before next check...\n")
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n🛑 Email monitoring stopped by user.")
    except Exception as e:
        print(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    main()
