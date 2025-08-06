import json
import os
import re
from collections import defaultdict
import spacy

# spacy init
nlp = spacy.load("en_core_web_sm", disable=["parser", "ner", "tagger"])

def word_tokenize(text):
    return [token.text for token in nlp(text)]

def calculate_chunk_size(text, target_words=150):
    words = word_tokenize(text)
    return len(words) > target_words

def create_chunk_object(entries):
    start = entries[0]
    end = entries[-1]
    
    return {
        'text': ' '.join(e['text'] for e in entries),
        'page_start': start['page'],
        'line_start': start['line_start'],  # first line of chunk
        'page_end': end['page'],
        'line_end': end['line_end'],  # last line of chunk
        'chunk_id': f"{start['page']}-{start['line_start']}"
    }

def semantic_chunking(entries, max_words=300):  # increased chunk size
    chunks = []
    current_chunk = []
    current_word_count = 0
    
    # batch optimization
    tokenized_entries = [
        {'word_count': len(word_tokenize(entry['text'])), **entry}
        for entry in entries
    ]
    
    for entry in tokenized_entries:
        text = entry['text']
        word_count = entry['word_count']
        
        # Q/A breaks
        if re.search(r'^(Q:|A:|BY\s|MR\.|MS\.)', text, re.IGNORECASE) and current_chunk:
            chunks.append(create_chunk_object(current_chunk))
            current_chunk = []
            current_word_count = 0
            
        # finalize if exceeds size
        if current_word_count + word_count > max_words and current_chunk:
            chunks.append(create_chunk_object(current_chunk))
            current_chunk = []
            current_word_count = 0
            
        current_chunk.append(entry)
        current_word_count += word_count
    
    # add last chunk
    if current_chunk:
        chunks.append(create_chunk_object(current_chunk))
    
    return merge_small_chunks(chunks)

def merge_small_chunks(chunks, min_words=50):
    merged = []
    for chunk in chunks:
        words = word_tokenize(chunk['text'])
        if merged and len(words) < min_words:
            last = merged[-1]
            last['text'] += ' ' + chunk['text']
            last['page_end'] = chunk['page_end']
            last['line_end'] = chunk['line_end']
        else:
            merged.append(chunk)
    return merged

def save_chunks(chunks, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(chunks, f, indent=2)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else '../outputs/chunks.json'
    
    with open(input_file, 'r') as f:
        preprocessed = json.load(f)
    
    chunks = semantic_chunking(preprocessed)
    save_chunks(chunks, output_file)
    print(f"Created {len(chunks)} chunks. Saved to {output_file}")