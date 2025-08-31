#!/usr/bin/env python3
import zipfile
import re
import os

def analyze_template():
    template_path = 'resume_service/media/DEMANDE DE STAGE.docx'
    
    if not os.path.exists(template_path):
        print("❌ Template not found")
        return
        
    print("🔍 Analyzing DOCX template...")
    
    with zipfile.ZipFile(template_path, 'r') as zip_file:
        # Extract document.xml
        document_xml = zip_file.read('word/document.xml').decode('utf-8')
        
        # Find all placeholders
        placeholders = re.findall(r'«[^»]+»', document_xml)
        
        print(f"\n📋 Found {len(set(placeholders))} unique placeholders:")
        for i, placeholder in enumerate(sorted(set(placeholders)), 1):
            print(f"{i:2d}. {placeholder}")
            # Show hex representation to check for encoding issues
            print(f"    Hex: {placeholder.encode('utf-8').hex()}")
            
        # Special focus on PERIODE placeholders
        periode_placeholders = [p for p in placeholders if 'PERIODE' in p]
        print(f"\n🎯 PERIODE placeholders specifically:")
        for p in periode_placeholders:
            print(f"  {p} -> Hex: {p.encode('utf-8').hex()}")
            
        # Test our replacement strings
        test_replacements = [
            '«PERIODE_DU»',
            '«PERIODE_AU»', 
            '«PERIODE_ACCORDEE_DU»',
            '«PERIODE_ACCORDEE_AU»'
        ]
        
        print(f"\n🧪 Testing our replacement strings:")
        for test_str in test_replacements:
            found_in_template = test_str in document_xml
            count = document_xml.count(test_str)
            print(f"  {test_str} -> Found: {found_in_template}, Count: {count}")
            print(f"    Our hex: {test_str.encode('utf-8').hex()}")

if __name__ == "__main__":
    analyze_template()
