import re
import os
from llama_index.core import Document
from llama_index.core.node_parser import TokenTextSplitter
from llama_index.core import SimpleDirectoryReader

def clean_deposition_text(text):
    # line numbers and timestamps
    text = re.sub(r'^\d+\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\d{2}:\d{2}', '', text)
    
    # Q/A markers
    text = re.sub(r'^\s*[QA]\s+', '', text, flags=re.MULTILINE)
    
    # whitespace
    text = '\n\n'.join([' '.join(para.split()) for para in text.split('\n\n')])
    return text.strip()

def process_pdf(input_path):
    documents = SimpleDirectoryReader(
        input_files=[input_path],
        file_metadata=lambda x: {"filename": os.path.basename(x)}
    ).load_data()

    # cleaned document copies
    cleaned_docs = []
    for doc in documents:
        cleaned_text = clean_deposition_text(doc.text)
        cleaned_docs.append(Document(
            text=cleaned_text,
            metadata=doc.metadata,
            excluded_llm_metadata_keys=doc.excluded_llm_metadata_keys,
            excluded_embed_metadata_keys=doc.excluded_embed_metadata_keys,
            relationships=doc.relationships
        ))

    # chunker for deposition content
    parser = TokenTextSplitter(
        chunk_size=1500,
        chunk_overlap=300,
        separator="\n\n",  # split at paragraph breaks
        include_metadata=True
    )

    # Process cleaned documents
    nodes = []
    for doc in cleaned_docs:
        doc_nodes = parser.get_nodes_from_documents([doc])
        for node in doc_nodes:
            node.metadata.update({
                "page_number": int(node.metadata.get("page_label", 0)),
                "line_start": 1  # refine later
            })
        nodes.extend(doc_nodes)
    
    # filtering out very short nodes
    return [n for n in nodes if len(n.text.strip()) > 100]