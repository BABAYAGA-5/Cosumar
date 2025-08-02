import sys
import os
import django
from django.conf import settings
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Cosumar_Digital_Recrutement.settings')
django.setup()

from resume_service.models import Candidat, Candidature, Poste

from pdf2image import convert_from_bytes, convert_from_path
import easyocr
import os
import torch
from langdetect import detect
import json
import re
from datetime import datetime
from googletrans import Translator
import spacy

def extract_structured_data(text_lines, detected_language, candidature_id):
    full_text = " ".join(text_lines).lower()

    candidature = Candidature.objects.filter(id=candidature_id).first()
    candidat = Candidat.objects.filter(id=candidature.candidat_id).first()
    poste = Poste.objects.filter(id=candidature.poste_id).first()
    domaine = poste.domaine if poste else None
    
    
    if not (domaine and poste and candidature):
        return {"error": f"Candidature {candidature.id}, Poste {poste.id} or Domaine {domaine.id} not found for the given ID."}

    extracted_data = {
        "extraction_date": datetime.now().isoformat(),
        "detected_language": detected_language,
        "raw_text": text_lines,
        "structured_data": {}
    }
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, full_text, re.IGNORECASE)
    if emails:
        extracted_data["structured_data"]["emails"] = emails
    phone_patterns = [
        r'\+?[\d\s\-\(\)]{10,15}',
        r'\b\d{2,4}[\s\-]?\d{2,4}[\s\-]?\d{2,4}[\s\-]?\d{2,4}\b'
    ]
    phones = []
    for pattern in phone_patterns:
        phones.extend(re.findall(pattern, full_text))
    phones = [phone.strip() for phone in phones if len(re.sub(r'[^\d]', '', phone)) >= 8]
    if phones:
        extracted_data["structured_data"]["phones"] = list(set(phones))
    
    candidat.telephone = phones[0] if phones else ""
    candidat.save()

    potential_names = []

    for line in text_lines[:7]:
        line = line.strip()
        
        # Case 1: LASTNAME (ALLCAPS) FIRSTNAME (Capitalized)
        match = re.match(r'^([A-Z]{2,}) ([A-Z][a-z]+)$', line)
        if match:
            prenom_nom = (match.group(2), match.group(1).capitalize())  # Prenom, Nom
            potential_names.append(" ".join(prenom_nom))
            continue

        # Case 2: FIRSTNAME (Capitalized) LASTNAME (ALLCAPS)
        match = re.match(r'^([A-Z][a-z]+) ([A-Z]{2,})$', line)
        if match:
            prenom_nom = (match.group(1), match.group(2).capitalize())
            potential_names.append(" ".join(prenom_nom))
            continue

        # Case 3: Both Capitalized (e.g., Othmane Zrioual)
        match = re.match(r'^([A-Z][a-z]+) ([A-Z][a-z]+)$', line)
        if match:
            potential_names.append(f"{match.group(1)} {match.group(2)}")
            continue

        # Case 4: Both UPPERCASE (e.g., JOHN DOE)
        match = re.match(r'^([A-Z]{2,}) ([A-Z]{2,})$', line)
        if match:
            prenom_nom = (match.group(1).capitalize(), match.group(2).capitalize())
            potential_names.append(" ".join(prenom_nom))

    # Deduplicate
    seen = set()
    unique_names = []
    for name in potential_names:
        if name not in seen:
            unique_names.append(name)
            seen.add(name)

    # Optional: use spaCy to validate with NER
    nlp = spacy.load("xx_ent_wiki_sm")
    doc = nlp(" ".join(unique_names))
    final_name = ""
    for ent in doc.ents:
        if ent.label_ == "PER":
            final_name = ent.text.strip()
            break
        else:
            final_name = unique_names[0] if unique_names else ""

    print("✅ Extracted name:", final_name)

    extracted_data["structured_data"]["potential_name"] = final_name

    list_final_name = final_name.split()
    
    first_name = list_final_name[0] if list_final_name else ""

    last_name = " ".join(list_final_name[1:]) if list_final_name else ""

    candidat.prenom = first_name
    candidat.nom = last_name
    candidat.save()

    date_patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
        r'\b\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{2,4}\b'
    ]
    dates = []
    for pattern in date_patterns:
        dates.extend(re.findall(pattern, full_text, re.IGNORECASE))
    if dates:
        extracted_data["structured_data"]["dates"] = dates
    
    ratio = 0
    poste_keywords = poste.keywords
    domaine_keywords = domaine.keywords

    extracted_data["structured_data"]["keywords"] = []
    for keyword in domaine_keywords:
        if keyword.lower() in full_text:
            extracted_data["structured_data"]["keywords"].append(keyword)
            if keyword.lower() in poste_keywords:
                ratio += 1
    ratio = ratio / len(poste_keywords)

    extracted_data["structured_data"]["matching_ratio"] = ratio

    Candidature.objects.filter(id=candidature_id).update(extracted_data=extracted_data)

    return extracted_data

def ocr_process(pdf_bytes):
    all_extracted_data = []

    print("Starting OCR process...")

    poppler_path = r"C:/Program Files/poppler-24.08.0/Library/bin"

    print("Converting PDF to images...")
    print(f"Using Poppler path: {poppler_path}")
    print("This may take a while depending on the PDF size...")

    images = convert_from_bytes(pdf_bytes, dpi=300, poppler_path=poppler_path)
    if not torch.cuda.is_available():
        print("⚠️ CUDA GPU not detected. EasyOCR will run on CPU.")
        use_gpu = False
    else:
        print("✅ CUDA GPU detected. EasyOCR will use GPU.")
        use_gpu = True
    reader = easyocr.Reader(['en','fr'], gpu=use_gpu)

    for i, img in enumerate(images):
        img_np = np.array(img)
        result = reader.readtext(img_np, detail=0)
        text_content = " ".join(result) if result else ""
        detected_lang = "unknown"
        if text_content:
            try:
                detected_lang = detect(text_content)
                print("Detected language:", detected_lang)
            except:
                print("Could not detect language")
        else:
            print("No text detected")
        print(f"✅ Extracted Text from Page {i+1}:")
        print("\n".join(result))
        if detected_lang != "fr":
            print("Detected language isn't French, translating to French...")
            translator = Translator()
            translated_result = []
            for line in result:
                try:
                    translated = translator.translate(line, src=detected_lang, dest='fr')
                    translated_result.append(translated.text)
                except Exception as e:
                    print(f"Translation failed for line: {line}")
                    translated_result.append(line)
            print("🔄 Translated text to French:")
            print("\n".join(translated_result))
            result = translated_result
        else:
            print("Text is already in French, no translation needed.")
        lines = [l.strip() for l in result if isinstance(l, str) and l.strip()]
        all_extracted_data.extend(lines)

    print(f"\n🎉 Processing complete!")
    print(f"📊 Total pages processed: {len(all_extracted_data)}")
    return all_extracted_data, detected_lang


def cv_process(candidature_id, pdf_bytes,):
    pdf_bytes = Candidature.objects.get(id=candidature_id).cv
    all_extracted_data, detected_lang = ocr_process(pdf_bytes)
    all_extracted_structured_data = extract_structured_data(all_extracted_data, detected_lang, candidature_id)
    if "error" in all_extracted_structured_data:
        print(all_extracted_structured_data["error"])
        return False
    else:
        print("✅ Extraction réussie !")
        return True
