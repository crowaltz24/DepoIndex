from llama_index.core import VectorStoreIndex, StorageContext, Document
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import chromadb
import json
import os

def create_vector_index(chunks, persist_dir):
    # chromadb client init
    chroma_client = chromadb.PersistentClient(path=persist_dir)
    
    # delete collecting if exist and creating new

    try:
        chroma_collection = chroma_client.delete_collection("deposition_index")
    except:
        pass
    
    chroma_collection = chroma_client.create_collection("deposition_index")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    
    # conversion to document objects
    documents = []
    for chunk in chunks:
        documents.append(Document(
            text=chunk['text'],
            metadata={
                'page_start': chunk['page_start'],
                'line_start': chunk['line_start'],
                'page_end': chunk['page_end'],
                'line_end': chunk['line_end'],
                'chunk_id': chunk['chunk_id']
            }
        ))
    
    # creating index
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=StorageContext.from_defaults(vector_store=vector_store),
        embed_model=embed_model
    )
    return index

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        sys.exit(1)
        
    chunk_file = sys.argv[1]
    persist_dir = sys.argv[2] if len(sys.argv) > 2 else './outputs/vector_store'
    
    with open(chunk_file, 'r') as f:
        chunks = json.load(f)
    
    index = create_vector_index(chunks, persist_dir)
    print(f"Index created at {persist_dir}")