from io import BytesIO
import easyocr
from PIL import Image
import numpy as np
import torch
import json
import re
from datetime import datetime

def scan_cin(img):
    print("🆔 Starting CIN OCR...")
    print("✅ Using GPU" if torch.cuda.is_available() else "⚠️ Using CPU")

    img = img.convert("RGB")
    img_np = np.array(img)

    reader = easyocr.Reader(['fr'], gpu=torch.cuda.is_available())

    result = reader.readtext(img_np, detail=0, paragraph=False)

    # Force everything to string
    clean_lines = [str(line).strip() for line in result if str(line).strip()]
    print(f"Extracted {len(clean_lines)} lines from CIN image.")
    return clean_lines


def extract_birth_date(lines):
    birth_date = None
    for i, line in enumerate(lines):
        line_str = str(line)  # force to string
        if "né le" in line_str.lower() or "née le" in line_str.lower():
            after = str(lines[i+1]).strip().lower()
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
            found = re.findall(r'\d{2}\.\d{2}\.\d{4}', str(l))
            dates.extend(found)
        if dates:
            try:
                birth_date = min(dates, key=lambda d: datetime.strptime(d, "%d.%m.%Y"))
            except Exception as e:
                print(f"⚠️ Error parsing dates: {e}")
                birth_date = dates[0]
    
    # Convert to yyyy-mm-dd format
    if birth_date:
        try:
            # Parse the date and format as yyyy-mm-dd
            birth_date_obj = datetime.strptime(birth_date, "%d.%m.%Y")
            return birth_date_obj.strftime("%Y-%m-%d")
        except Exception as e:
            print(f"⚠️ Error converting birth date to yyyy-mm-dd format: {e}")
            return None
    return None


def extract_name(lines):
    for i, line in enumerate(lines):
        line_str = str(line)  # force to string
        if "né le" in line_str.lower() or "née le" in line_str.lower():
            try:
                last_name = str(lines[i-1]).strip().lower()
                first_name = str(lines[i-3]).strip().lower()
                return first_name.title(), last_name.title()
            except IndexError:
                print("⚠️ Error extracting name: not enough lines before 'né le'")
                continue
    return None, None


def extract_cin(lines):
    pattern = r"^[A-Z]{1,2}\d{5,6}$"
    for line in lines:
        match = re.search(pattern, str(line).strip())
        if match:
            return match.group(0)
    return None


def extract_cin_data(image_bytes):
    # Convert bytes to PIL Image
    try:
        img = Image.open(BytesIO(image_bytes))
    except Exception as e:
        print(f"Error opening image from bytes: {e}")
        return {}
    
    lines = scan_cin(img)
    cin_data = {}
    birth_date = extract_birth_date(lines)
    first_name, last_name = extract_name(lines)
    cin = extract_cin(lines)
    if birth_date:
        cin_data["date_naissance"] = birth_date
    if first_name:
        cin_data["prenom"] = first_name
    if last_name:
        cin_data["nom"] = last_name
    if cin:
        cin_data["cin"] = cin
    return cin_data
