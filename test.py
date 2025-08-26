import fitz  # PyMuPDF

doc = fitz.open("DEMANDE DE STAGE.pdf")
page = doc[0]

# Search for the text you want to replace
search_text = "«PRENOM»"
replace_text = "Othmane"

areas = page.search_for(search_text)
for area in areas:
    # First, redact (cover with white rectangle)
    page.add_redact_annot(area, fill=(1, 1, 1))
    page.apply_redactions()
    
    # Then insert the new text at the same spot
    page.insert_text(area.bl, replace_text, fontsize=12, color=(0, 0, 0))

doc.save("output.pdf")
