import easyocr
from PIL import Image
import numpy as np
import torch
import json
import re
from datetime import datetime

def scan_cin(image_path):
    print("🆔 Starting CIN OCR...")
    print("✅ Using GPU" if torch.cuda.is_available() else "⚠️ Using CPU")

    img = Image.open(image_path).convert("RGB")
    img_np = np.array(img)

    reader = easyocr.Reader(['fr'], gpu=torch.cuda.is_available())

    result = reader.readtext(img_np, detail=0, paragraph=False)

    clean_lines = [line.strip() for line in result if line.strip()]
    return clean_lines

def extract_birth_date(lines):
    birth_date = None
    for i,line in enumerate(lines):
        if "né le" in line.lower() or "née le" in line.lower():
            after = lines[i+1].strip().lower()
            
            match = re.search(r'(\d{2}\.\d{2}\.\d{4})', after)
            if match:
                birth_date = match.group(1)
            else:
                words = after.split()
                if words:
                    birth_date = words[0]
                else:
                    print("⚠️ Found 'né le' but no text after it")
            break
    if birth_date is None:
        dates = []
        for l in lines:
            found = re.findall(r'\d{2}\.\d{2}\.\d{4}', l)
            dates.extend(found)
        if dates:
            try:
                birth_date = min(dates, key=lambda d: datetime.strptime(d, "%d.%m.%Y"))
            except Exception as e:
                print(f"⚠️ Error parsing dates: {e}")
                birth_date = dates[0]
    return birth_date

def extract_name(lines):
    for i,line in enumerate(lines):
        if "né le" in line.lower() or "née le" in line.lower():
            try:
                last_name = lines[i-1].strip().lower()
                first_name = lines[i-3].strip().lower()
                return first_name.title(), last_name.title()
            except IndexError:
                print("⚠️ Error extracting name: not enough lines before 'né le'")
                continue
    return None, None

def extract_cin(lines):
    pattern = r"^[A-Z]{1,2}\d{5,6}$"
    for line in lines:
        match = re.search(pattern, line.strip())
        if match:
            return match.group(0)
    return None

def extract_cin_data(lines):
    cin_data = {}
    birth_date = extract_birth_date(lines)
    first_name, last_name = extract_name(lines)
    cin = extract_cin(lines)
    if birth_date:
        cin_data["birth_date"] = birth_date
    if first_name:
        cin_data["first_name"] = first_name
    if last_name:
        cin_data["last_name"] = last_name
    if cin:
        cin_data["cin"] = cin
    return cin_data

if __name__ == "__main__":
    lines = scan_cin(r"C:/Users/othma/Downloads/2.jpg")
    print("📄 Extracted lines from CIN:", lines)
    cin_data = extract_cin_data(lines)
    print("🆔 Extracted CIN data:", cin_data)
