import easyocr
import re
from pdf2image import convert_from_bytes
import numpy as np
import io

def extract_emails(text):
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    return re.findall(email_pattern, text)

def extract_phones(text):
    phone_patterns = [
        r'(\+212|0)[-\s]*([67])[-\s]*(\d{2})[-\s]*(\d{2})[-\s]*(\d{2})[-\s]*(\d{2})',
        r'(\+212|0)([67]\d{8})',
        r'(\d{2})[-\s]*(\d{2})[-\s]*(\d{2})[-\s]*(\d{2})[-\s]*(\d{2})',
        r'\+212[-\s]*\d[-\s]*\d{2}[-\s]*\d{3}[-\s]*\d{3}',
        r'0[67][-\s]*\d{2}[-\s]*\d{2}[-\s]*\d{2}[-\s]*\d{2}'
    ]
    
    phones = []
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if isinstance(match, tuple) and len(match) > 1:
                if len(match) == 6:
                    phone = f"{match[0]}{match[1]}{match[2]}{match[3]}{match[4]}{match[5]}"
                elif len(match) == 2:
                    phone = f"{match[0]}{match[1]}"
                elif len(match) == 5:
                    phone = '0' + ''.join(match)
                else:
                    phone = ''.join(match)
            else:
                phone = str(match).replace('-', '').replace(' ', '')
                
            if phone and len(phone) >= 9:
                phones.append(phone)
    
    direct_patterns = [
        r'\+212[-\s]*[67][-\s]*\d{2}[-\s]*\d{3}[-\s]*\d{3}',
        r'\+212[-\s]*[67][-\s]*\d{2}[-\s]*\d{2}[-\s]*\d{2}[-\s]*\d{2}',
        r'0[67][-\s]*\d{2}[-\s]*\d{2}[-\s]*\d{2}[-\s]*\d{2}'
    ]
    
    for pattern in direct_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            clean_phone = match.replace('-', '').replace(' ', '')
            if clean_phone and len(clean_phone) >= 9:
                phones.append(clean_phone)
    
    return list(set(phones))

def extract_cv_data(pdf_bytes, lang='fr'):
    try:
        poppler_path = r"C:/Program Files/poppler-24.08.0/Library/bin"
        
        if isinstance(pdf_bytes, bytes):
            images = convert_from_bytes(pdf_bytes, dpi=300, poppler_path=poppler_path)
        else:
            from pdf2image import convert_from_path
            images = convert_from_path(pdf_bytes, dpi=300, poppler_path=poppler_path)
        
        reader = easyocr.Reader([lang])
        
        email = None
        phone = None
        all_text = ""
        
        for i, image in enumerate(images):
            img_array = np.array(image)
            
            result = reader.readtext(img_array, detail=0, paragraph=False)
            
            page_text = " ".join(result)
            all_text += page_text + " "
            
            if email is None:
                page_emails = extract_emails(page_text)
                if page_emails:
                    email = page_emails[0]
            
            if phone is None:
                page_phones = extract_phones(page_text)
                if page_phones:
                    phone = page_phones[0]
            
            if email and phone:
                break
        
        if email is None:
            all_emails = extract_emails(all_text)
            if all_emails:
                email = all_emails[0]
        
        if phone is None:
            all_phones = extract_phones(all_text)
            if all_phones:
                phone = all_phones[0]
        
        return {
            'email': email,
            'phone': phone,
        }
        
    except Exception as e:
        return {
            'email': None,
            'phone': None,
        }

if __name__ == "__main__":
    pdf_path = "C:/Users/othma/Downloads/CV_FR-9.pdf"
    
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    
    data = extract_cv_data(pdf_bytes)
    print(f"🎉 Extraction complete:")
    print(data)