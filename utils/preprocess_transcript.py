import os
from PyPDF2 import PdfReader
from llama_index.core import StorageContext, VectorStoreIndex, Document
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

def load_transcript(file_path):
    if file_path.endswith(".pdf"):
        reader = PdfReader(file_path)
        return {i+1: page.extract_text() for i, page in enumerate(reader.pages)}
    elif file_path.endswith(".txt"):
        with open(file_path, "r") as f:
            return {i+1: chunk for i, chunk in enumerate(f.read().split("\n\n"))}
    else:
        raise ValueError("Unsupported file format")

def preprocess_transcript(input_file, output_dir):
    print(f"Loading {input_file}...")
    pages = load_transcript(input_file)
    
    # using my custom metadata for now very minimalistic
    documents = [Document(
        text=text,
        metadata={"page": page_num}
    ) for page_num, text in pages.items()]
    
    print("Building index...")
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=StorageContext.from_defaults(),
        embed_model=HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
    )
    
    print(f"Saving to {output_dir}...")
    index.storage_context.persist(persist_dir=output_dir)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="Input PDF or text file")
    parser.add_argument("--out", required=True, help="Output directory")
    args = parser.parse_args()
    
    os.makedirs(args.out, exist_ok=True)
    preprocess_transcript(args.file, args.out)