from pdf2image import convert_from_path
import easyocr
import os
import torch
from langdetect import detect
import json
import re
from datetime import datetime
from googletrans import Translator

def extract_structured_data(text_lines, detected_language):
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
    programming_languages = [
        'Python', 'Java', 'JavaScript', 'HTML', 'CSS', 'SQL', 'PHP', 'C++', 'C#', 'Ruby', 'Go',
        'Kotlin', 'Swift', 'TypeScript', 'C', 'XML', 'NoSQL', 'MongoDB', 'MySQL', 'PostgreSQL'
    ]
    frameworks = [
        'React', 'Angular', 'Vue', 'Django', 'Flask', 'Spring', 'Spring Boot', 'Node.js', 'Node.js',
        'Laravel', 'Symfony', 'CodeIgniter', 'Express', 'FastAPI', 'Tornado', 'Bottle',
        'Bootstrap', 'Tailwind CSS', 'jQuery', 'Backbone.js', 'Ember.js', 'Svelte',
        'Jakarta EE', 'J2EE', 'ASP.NET', '.NET', 'Blazor', 'Xamarin',
        'TensorFlow', 'PyTorch', 'Keras', 'Scikit-learn', 'Pandas', 'NumPy', 'Matplotlib',
        'Unity', 'Unreal Engine', 'Godot', 'Vaadin', 'Hibernate', 'JPA'
    ]
    technologies = [
        'Docker', 'Kubernetes', 'Git', 'Jenkins', 'GitLab', 'GitHub', 'Bitbucket',
        'AWS', 'Azure', 'Google Cloud Platform', 'Firebase', 'Heroku', 'Vercel', 'Netlify',
        'Redis', 'Elasticsearch', 'Apache', 'Nginx', 'Tomcat', 'IIS',
        'Cassandra', 'CassandraDB', 'Oracle', 'SQLite', 'MariaDB',
        'Grafana', 'Prometheus', 'ELK Stack', 'Kibana', 'Logstash',
        'Maven', 'Gradle', 'NPM', 'Yarn', 'Pip', 'Composer'
    ]
    concepts = [
        'Machine Learning', 'Data Science', 'Artificial Intelligence', 'Deep Learning',
        'Project Management', 'Agile', 'Scrum', 'Leadership', 'Communication',
        'Bachelor', 'Master', 'PhD', 'Degree', 'University', 'College',
        'Experience', 'Years', 'Manager', 'Developer', 'Engineer', 'Analyst',
        'DevOps', 'Microservices', 'API', 'REST', 'GraphQL', 'MVC', 'MVVM'
    ]
    found_languages = []
    for lang in programming_languages:
        if lang.lower() in full_text:
            found_languages.append(lang)
    found_frameworks = []
    for framework in frameworks:
        if framework.lower() in full_text:
            found_frameworks.append(framework)
    found_technologies = []
    for tech in technologies:
        if tech.lower() in full_text:
            found_technologies.append(tech)
    found_concepts = []
    for concept in concepts:
        if concept.lower() in full_text:
            found_concepts.append(concept)
    if found_languages:
        extracted_data["structured_data"]["programming_languages"] = found_languages
    if found_frameworks:
        extracted_data["structured_data"]["frameworks"] = found_frameworks
    if found_technologies:
        extracted_data["structured_data"]["technologies"] = found_technologies
    if found_concepts:
        extracted_data["structured_data"]["concepts"] = found_concepts
    address_pattern = r'\b\d+\s+[A-Za-z\s,.-]+(?:street|st|avenue|ave|road|rd|boulevard|blvd|lane|ln)\b'
    addresses = re.findall(address_pattern, full_text, re.IGNORECASE)
    if addresses:
        extracted_data["structured_data"]["addresses"] = addresses
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
