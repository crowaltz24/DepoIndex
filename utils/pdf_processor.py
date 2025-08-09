import re
import os
from llama_index.core import Document
from llama_index.core.node_parser import TokenTextSplitter
from llama_index.core import SimpleDirectoryReader

def is_end_of_deposition(text):
    end_phrases = [
        "end of deposition",
        "deposition concluded",
        "This concludes today's"
        "word index"
    ]
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in end_phrases)

def clean_deposition_text(text):

    text = re.sub(r'^\d+\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\d{2}:\d{2}', '', text)
    text = re.sub(r'^\s*[QA]\s+', '', text, flags=re.MULTILINE)
    return '\n\n'.join([' '.join(para.split()) for para in text.split('\n\n')]).strip()

def process_pdf(input_path):
    """Process PDF with early termination"""
    documents = SimpleDirectoryReader(
        input_files=[input_path],
        file_metadata=lambda x: {"filename": os.path.basename(x)}
    ).load_data()

    parser = TokenTextSplitter(
        chunk_size=2000,
        chunk_overlap=400,
        separator="\n\n",
        include_metadata=True
    )

    nodes = []
    for doc in documents:
        # stop processing if we hit end markers
        if is_end_of_deposition(doc.text):
            break
            
        cleaned_text = clean_deposition_text(doc.text)
        if not cleaned_text or len(cleaned_text) < 100:
            continue
            
        doc_nodes = parser.get_nodes_from_documents([Document(
            text=cleaned_text,
            metadata=doc.metadata
        )])
        
        for node in doc_nodes:
            node.metadata.update({
                "page_number": int(node.metadata.get("page_label", 0)),
                "line_start": 1
            })
        nodes.extend(doc_nodes)
    
    return nodes