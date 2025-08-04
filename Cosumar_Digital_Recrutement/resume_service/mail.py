from io import BytesIO
import os
import sys
import django
from django.conf import settings

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Cosumar_Digital_Recrutement.settings')
django.setup()

from PyPDF2 import PdfReader
import docx
from imap_tools import MailBox, AND
from datetime import datetime
import spacy

# Import Django models
from resume_service.models import Candidat, Poste, Candidature
import time
from django.core.mail import send_mail
from docx import Document
from fpdf import FPDF
from resume_service.pdf_process import cv_process


# Chargement du modèle NLP français
nlp = spacy.load("fr_core_news_md")

# Email configuration
EMAIL_HOST = settings.IMAP_SERVER
EMAIL_USER = settings.EMAIL
EMAIL_PASS = settings.PASSWORD

def poste_existe(titre_poste, seuil_similarite=0.8):
    titre_input = nlp(titre_poste.lower())
    if Poste.objects.filter(titre=titre_input).exists():
        return titre_poste
    postes = Poste.objects.all()
    meilleur_score = 0
    meilleur_poste = None

    for poste in postes:
        titre_bdd_doc = nlp(poste.titre.lower())
        score = titre_input.similarity(titre_bdd_doc)
        if score > meilleur_score:
            meilleur_score = score
            meilleur_poste = poste

    if meilleur_score >= seuil_similarite:
        return meilleur_poste
    else:
        return None

def candidat_existe(email):
    try:
        return Candidat.objects.get(email=email)
    except Candidat.DoesNotExist:
        return None

def insert_candidat(email):
    candidat = Candidat(email=email)
    candidat.save()
    return candidat.id

def has_active_candidature(candidat_id):
    return Candidature.objects.filter(candidat_id=candidat_id, statut='en_attente').exists()

def insert_candidature(candidat_id, poste_id, cv_bytes):
    candidature = Candidature(
        candidat_id=candidat_id,
        poste_id=poste_id,
        cv=cv_bytes
    )
    candidature.save()
    return candidature

def main():
    try:
        with MailBox(EMAIL_HOST).login(EMAIL_USER, EMAIL_PASS, 'INBOX') as mailbox:
            messages = mailbox.fetch(AND(seen=False), reverse=True)

            for msg in messages:
                subject = msg.subject.strip()
                email = msg.from_

                poste = poste_existe(subject)
                if not poste:
                    print(f"[-] Poste non reconnu : {subject}")
                    continue

                print(f"[✔] Poste reconnu : {subject}")

                if not msg.attachments:
                    print(f"[!] Email sans pièce jointe pour le poste '{subject}'")
                    continue

                att = msg.attachments[0]
                filename = att.filename.lower()
                ext = os.path.splitext(filename)[1]
                if ext not in [".pdf", ".docx"]:
                    print(f"[!] Fichier non pris en charge : {filename}")
                    continue

                if ext == ".docx":
                    # Convertir le fichier DOCX en PDF

                    # Charger le document DOCX depuis les bytes
                    docx_bytes = BytesIO(att.payload)
                    document = Document(docx_bytes)

                    # Créer un PDF temporaire
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_auto_page_break(auto=True, margin=15)
                    pdf.set_font("Arial", size=12)

                    for para in document.paragraphs:
                        text = para.text.strip()
                        if text:
                            pdf.multi_cell(0, 10, text)

                    # Sauvegarder le PDF dans un buffer mémoire
                    pdf_buffer = BytesIO()
                    pdf.output(pdf_buffer)
                    pdf_bytes = pdf_buffer.getvalue()
                    att.payload = pdf_bytes

                candidat = candidat_existe(email)
                print(f"Vérification de l'existence du candidat : {email} - ID {candidat.id if candidat else 'N/A'}")
                if not candidat:
                    candidat_id = insert_candidat(email)
                    candidat = Candidat.objects.get(id=candidat_id)
                else:
                    candidat_id = candidat.id
                if has_active_candidature(candidat_id):
                    print(f"[!] Candidat {email} a déjà une candidature active pour le poste {subject}.")
                    continue
                candidature = insert_candidature(candidat_id, poste.id, att.payload)

                print(f"[✔] Candidature enregistrée : ID {candidature.id} pour le poste {subject} et le candidat {candidat.id} ({email})")

                if candidature:
                    return True, email, subject, att.payload, candidature.id
                else:
                    return False, email, subject, None, None
        return False, None, None, None, None
    except Exception as e:
        print("Erreur :", e)
        return False, None, None, None, None

def main_loop():
    while True:
        print(f"Vérification des nouveaux emails time {time.time()}...")
        success, email, subject, pdf_bytes, candidature_id = main()

        if candidature_id is None or pdf_bytes is None:
            continue
        cv_process_result = cv_process(candidature_id, pdf_bytes)

        if success and cv_process_result:
            send_mail(
                subject="Candidature reçue",
                message=f"Votre candidature pour le poste {subject} a bien été reçue. Merci de postuler.\n"+
                        f"ID de la candidature : {candidature_id}\n"+
                        f"ID du candidat : {Candidature.objects.get(id=candidature_id).candidat_id}\n"+
                        f"\n\nNous vous contacterons bientôt pour la suite du processus de recrutement."+
                        f"\n\nCordialement,\nL'équipe de recrutement",
                from_email=EMAIL_USER,
                recipient_list=[email],
                fail_silently=False,
            )
        time.sleep(5)  # Wait 5 seconds before checking again

if __name__ == "__main__":
    main_loop()