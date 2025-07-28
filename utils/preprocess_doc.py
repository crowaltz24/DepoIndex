import re
import os
from PyPDF2 import PdfReader
import json

def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    pages = []
    
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if not text:
            continue
            
        lines = text.split('\n')
        clean_lines = []
        line_counter = 1  # reset counter for each page
        
        for line in lines:
            clean_line = line.strip()
            if not clean_line or any(skip in clean_line for skip in ['Veritext', 'Page', '866 299-5127']):
                continue
                
            # timestamps go but line counting stays
            clean_line = re.sub(r'\d{2}:\d{2}$', '', clean_line).strip()
            if clean_line:  # only lines that arent empty
                clean_lines.append({
                    'text': clean_line,
                    'page': page_num,
                    'line_start': line_counter,
                    'line_end': line_counter
                })
                line_counter += 1
                
        pages.extend(clean_lines)
    return pages

def clean_transcript_text(entries):
    for entry in entries:
        text = entry['text']
        
        # common patterns
        text = re.sub(r'\[(WITNESS|ATTORNEY)\]', r'(\1)', text)
        text = re.sub(r'\.{3,}', '...', text)  # ellipses simplification
        
        # clean formaatting
        entry['text'] = ' '.join(text.split())  # extra spaces
    
    return [e for e in entries if len(e['text']) > 5]  # empty/short lines

def preprocess_document(file_path):
    if not file_path.lower().endswith('.pdf'):
        raise ValueError("Only PDF transcripts are supported")
    
    entries = extract_text_from_pdf(file_path)
    return clean_transcript_text(entries)

def save_preprocessed(data, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else './outputs/preprocessed.json'
    
    processed = preprocess_document(input_file)
    save_preprocessed(processed, output_file)
    print(f"Preprocessed {len(processed)} lines. Saved to {output_file}")