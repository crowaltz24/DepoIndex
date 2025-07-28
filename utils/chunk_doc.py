import json
import os
import nltk
from nltk.tokenize import word_tokenize

nltk.download('punkt', quiet=True)

def calculate_chunk_size(text, target_words=150):
    words = word_tokenize(text)
    return len(words) > target_words

def semantic_chunking(entries, max_words=150):
    chunks = []
    current_chunk = []
    current_word_count = 0
    
    for entry in entries:
        words = word_tokenize(entry['text'])
        word_count = len(words)
        
        # if exceeds, we can finalize chunk
        if current_word_count + word_count > max_words and current_chunk:
            chunks.append(create_chunk_object(current_chunk))
            current_chunk = []
            current_word_count = 0
            
        current_chunk.append(entry)
        current_word_count += word_count
        
    # add last chunk
    if current_chunk:
        chunks.append(create_chunk_object(current_chunk))
    
    return chunks

def create_chunk_object(entries):
    """Combine entries while tracking exact line numbers"""
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