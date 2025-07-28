from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import chromadb

def load_index(persist_dir):
    # chroma init
    chroma_client = chromadb.PersistentClient(path=persist_dir)
    chroma_collection = chroma_client.get_collection("deposition_index")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    
    # storage context
    storage_context = StorageContext.from_defaults(
        vector_store=vector_store
    )
    
    return VectorStoreIndex.from_vector_store(
        vector_store,
        embed_model=HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5"),
        storage_context=storage_context
    )

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        sys.exit(1)
        
    persist_dir = sys.argv[1] if len(sys.argv) > 1 else './outputs/vector_store'
    query = sys.argv[2] if len(sys.argv) > 2 else "introduction of the witness"
    
    print(f"Loading ChromaDB index from {persist_dir}...")
    index = load_index(persist_dir)
    
    print(f"\nTesting query: '{query}'")
    retriever = index.as_retriever(similarity_top_k=3)
    results = retriever.retrieve(query)
    
    print("\nTop Results:")
    for i, node in enumerate(results, 1):
        print(f"\nResult {i}:")
        print(f"Text: {node.text[:200]}...")
        print(f"Metadata: {node.metadata}")
        print(f"Score: {node.score:.4f}")