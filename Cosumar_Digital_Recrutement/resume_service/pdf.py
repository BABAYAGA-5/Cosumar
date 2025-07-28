from pdf2image import convert_from_path
import easyocr
import os
import torch
from langdetect import detect
import json
import re
from datetime import datetime
from googletrans import Translator
from resume_service.models import Domaine, Poste, Candidature

def extract_structured_data(text_lines, detected_language, domaine, poste):
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
    if text_lines:
        first_line = text_lines[0]
        name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        potential_names = re.findall(name_pattern, first_line)
        if potential_names:
            extracted_data["structured_data"]["potential_names"] = potential_names
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

    keywords = []
    try:
        domaine = Domaine.objects.filter(poste=Poste).first()
        if domaine and domaine.keywords:
            keywords = [kw.strip().lower() for kw in domaine.keywords.split(',')]
    except Exception as e:
        print(f"Error fetching keywords from Domaine: {e}")

    poste_keywords = []

    try:
        poste = Poste.objects.filter(domaine=domaine).first()
        if poste and poste.keywords:
            poste_keywords = [kw.strip().lower() for kw in poste.keywords.split(',')]
    except Exception as e:
        print(f"Error fetching keywords from Poste: {e}")

    if keywords and poste_keywords:
        
        found_keywords = []
        ratio = 0
        for kw in keywords:
            if kw in full_text:
                found_keywords.append(kw)
                if kw in poste_keywords:
                    ratio += 1
        if found_keywords:
            extracted_data["structured_data"] = found_keywords
        
        ratio = ratio / len(poste_keywords) if poste_keywords else 0
        extracted_data["structured_data"]["keyword_match_ratio"] = ratio
    langues = ["français", "anglais", "espagnol", "allemand", "italien", "portugais", "néerlandais", "russe", "chinois", "japonais", "coréen"]
    found_languages = []
    for langue in langues:
        if langue in full_text:
            found_languages.append(langue)
    if found_languages:
        extracted_data["structured_data"]["langues"] = found_languages
    

    
    return extracted_data

all_extracted_data = []

print("Starting OCR process...")

pdf_path = r"C:/Users/othma/Downloads/CV_FR-9.pdf"

poppler_path = r"C:/Program Files/poppler-24.08.0/Library/bin"

print("Converting PDF to images...")
print(f"Using Poppler path: {poppler_path}")
print("This may take a while depending on the PDF size...")

images = convert_from_path(pdf_path, dpi=300, poppler_path=poppler_path)

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
        structured_data = extract_structured_data(result, "fr")
        structured_data["page_number"] = i + 1
        structured_data["image_path"] = img_path
        structured_data["original_language"] = detected_lang
        all_extracted_data.append(structured_data)
        print(f"📊 Structured data extracted from page {i+1}")
        if structured_data["structured_data"]:
            for key, value in structured_data["structured_data"].items():
                print(f"  {key}: {value}")
    print("-" * 40)

output_json = "extracted_data.json"
with open(output_json, 'w', encoding='utf-8') as f:
    json.dump(all_extracted_data, f, indent=2, ensure_ascii=False)

print(f"\n🎉 Processing complete!")
print(f"📄 Extracted data saved to: {output_json}")
print(f"📊 Total pages processed: {len(all_extracted_data)}")
