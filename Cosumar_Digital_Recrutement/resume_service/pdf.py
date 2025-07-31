import django
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Cosumar_Digital_Recrutement.settings')
django.setup()
try:
    from pdf2image import convert_from_path
    import easyocr
    import torch
    from langdetect import detect
    import json
    import re
    from datetime import datetime
    from googletrans import Translator
    from resume_service.models import Domaine, Poste, Candidature, Candidat
except ImportError as e:
    print(f"Error importing modules: {e}")
    raise

print("starting ocr process")

def extract_structured_data(pdf_id, text_lines, detected_language, titre_poste):
    full_text = " ".join(text_lines).lower()
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

    for line in text_lines[:7]:
        line = line.strip()
        
        # Case 1: LASTNAME (ALLCAPS) FIRSTNAME (Capitalized)
        match = re.match(r'^([A-Z]{2,}) ([A-Z][a-z]+)$', line)
        if match:
            prenom_nom = (match.group(2), match.group(1).capitalize())  # prenom, nom

        # Case 2: FIRSTNAME (Capitalized) LASTNAME (ALLCAPS)
        match = re.match(r'^([A-Z][a-z]+) ([A-Z]{2,})$', line)
        if match:
            prenom_nom = (match.group(1), match.group(2).capitalize())

        # Case 3: Both Capitalized (e.g., Othmane Zrioual)
        match = re.match(r'^([A-Z][a-z]+) ([A-Z][a-z]+)$', line)
        if match:
            prenom_nom = (match.group(1), match.group(2))

        # Optional Case 4: Both UPPERCASE (e.g., JOHN DOE)
        match = re.match(r'^([A-Z]{2,}) ([A-Z]{2,})$', line)
        if match:
            prenom_nom = (match.group(1).capitalize(), match.group(2).capitalize())

        if "potential_names" not in extracted_data["structured_data"]:
            extracted_data["structured_data"]["potential_names"] = []
        extracted_data["structured_data"]["potential_names"].append(" ".join(prenom_nom))

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

    domaine_keywords = []
    try:
        poste = Poste.objects.filter(titre=titre_poste).first()
        nom_domaine = poste.domaine.nom if poste else None
        domaine = Domaine.objects.filter(nom=nom_domaine).first() if nom_domaine else None
        if domaine and domaine.keywords:
            domaine_keywords = [kw.strip().lower() for kw in domaine.keywords]
    except Exception as e:
        print(f"Error fetching keywords from Domaine: {e}")

    print("Domaine name:", nom_domaine)
    print("domaine_keywords:", domaine_keywords)

    poste_keywords = []

    try:
        if poste and poste.keywords:
            poste_keywords = [kw.strip().lower() for kw in poste.keywords]
    except Exception as e:
        print(f"Error fetching keywords from Poste: {e}")

    print("poste_keywords:", poste_keywords)

    if domaine_keywords and poste_keywords:
        
        found_keywords = []
        ratio = 0
        for kw in domaine_keywords:
            if kw in full_text:
                found_keywords.append(kw)
                if kw in poste_keywords:
                    ratio += 1
        if found_keywords:
            extracted_data["structured_data"]["found_keywords"] = found_keywords

        ratio = ratio / len(poste_keywords) if poste_keywords else 0
        extracted_data["structured_data"]["keyword_match_ratio"] = ratio
        print(f"Keyword match ratio: {ratio:.2f}")
    print(f"Found keywords: {found_keywords}")
    langues = ["arabe", "français", "anglais", "espagnol", "allemand", "italien", "portugais", "néerlandais", "russe", "chinois", "japonais", "coréen"]
    found_languages = []
    for langue in langues:
        if langue in full_text:
            found_languages.append(langue)
    if found_languages:
        extracted_data["structured_data"]["langues"] = found_languages

    Candidature.objects.filter(id=pdf_id).update(extracted_data=json.dumps(extracted_data, ensure_ascii=False, indent=2))

    return extracted_data

def ocr_process(pdf_id):
    all_extracted_data = []

    print("Starting OCR process...")

    pdf = Candidature.objects.get(id=pdf_id).cv
    
    if not pdf:
        print("❌ No PDF found for the given candidature ID.")
        return

    print("PDF found, proceeding with OCR...")

    poppler_path = r"C:/Program Files/poppler-24.08.0/Library/bin"

    print("Converting PDF to images...")
    print(f"Using Poppler path: {poppler_path}")
    print("This may take a while depending on the PDF size...")

    images = convert_from_path(pdf, poppler_path=poppler_path)

    if not torch.cuda.is_available():
        print("⚠️ CUDA GPU not detected. EasyOCR will run on CPU.")
        use_gpu = False
    else:
        print("✅ CUDA GPU detected. EasyOCR will use GPU.")
        use_gpu = True
    reader = easyocr.Reader(['en','fr'], gpu=use_gpu)

    output_dir = "ocr_pages"
    os.makedirs(output_dir, exist_ok=True)

    for i, img in enumerate(images):
        img_path = os.path.join(output_dir, f"page_{i + 1}.png")
        img.save(img_path, "PNG")
        print(f"🔍 OCR on: {img_path}")
        result = reader.readtext(img_path, detail=0)
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
        if result:
            structured_data = extract_structured_data(result, "fr", titre_poste="Data Scientist")
            structured_data["page_number"] = i + 1
            structured_data["image_path"] = img_path
            structured_data["original_language"] = detected_lang
            all_extracted_data.append(structured_data)
            print(f"📊 Structured data extracted from page {i+1}")
            if structured_data["structured_data"]:
                for key, value in structured_data["structured_data"].items():
                    print(f"  {key}: {value}")
        print("-" * 40)

    print(f"\n🎉 Processing complete!")
    print(f"📄 Extracted data saved to Candidature with ID: {pdf_id}")
    print(f"📊 Total pages processed: {len(all_extracted_data)}")
    return all_extracted_data, detected_lang

"""
all_extracted_data, detected_lang = ocr_process(1)
extracted_data = extract_structured_data(1, all_extracted_data, detected_language=detected_lang, titre_poste="Data Scientist")
print("Final extracted data:")
print(json.dumps(extracted_data, ensure_ascii=False, indent=2))
"""
print("OCR process completed successfully.")
