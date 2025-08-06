import json
import os
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from llama_index.core import Settings, VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
import chromadb
from tqdm import tqdm 

# have to usee local embeddings
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

def detect_deposition_end(nodes):
    end_phrases = [
        r"deposition\s+concluded",
        r"end\s+of\s+deposition",
        r"this\s+concludes\s+today's",
        # r"whereupon.*deposition"
    ]
    
    # ignore start of document for ending check
    start_check = len(nodes) // 10
    
    for i in range(start_check, len(nodes)):
        text = nodes[i].text.lower()
        if any(re.search(phrase, text) for phrase in end_phrases):
            # ignore discussion about ending
            if "off the record" not in text and "resume" not in text:
                return i
    return len(nodes)

def validate_line_numbers(node):
    max_lines_per_chunk = 20
    line_diff = node.metadata['line_end'] - node.metadata['line_start']
    
    if line_diff > max_lines_per_chunk:
        node.metadata['line_end'] = node.metadata['line_start'] + max_lines_per_chunk
    return node

# def is_substantive(node):
#     text = node.text.lower()
#     return (
#         len(text.split()) > 15 and  # Minimum word count
#         not re.search(r'(exhibit|resume|off the record|break|recess)', text) and
#         re.search(r'(testimony|examination|discussion|question|answer)', text) is not None
#     )

def process_node(node, llm):
    try:
        node = validate_line_numbers(node)
        prompt = f"""Output ONLY a detailed label for this deposition segment including names if relevant (6-8 words max):
        {node.text[:300]}
        
        Avoid vague topics such as "Witness details regarding allegations" or "Legal deposition Transcript of testimony."

        Example formats:
        John Doe testimony about email correspondence
        Unusual Experience with XYZ
        Cross-examination regarding financial records - Jane Smith
        Discussion of meeting on June 15th
        
        Label: """
        
        topic = llm.complete(prompt).text.strip('"').strip()
        return {
            "topic": topic,
            "page_start": node.metadata['page_start'],
            "line_start": node.metadata['line_start'],
            "line_end": node.metadata['line_end'],
            "page_end": node.metadata['page_end'],
            "text_preview": node.text[:200] + "...",
            "score": float(node.score)
        }
    except Exception as e:
        print(f"\nError processing segment (Page {node.metadata.get('page_start', '?')}: {str(e)}")
        return None

def extract_topics(index_path, output_path, num_topics=50):
    # init component
    print("Loading vector store...")
    chroma_client = chromadb.PersistentClient(path=index_path)
    
    try:
        chroma_collection = chroma_client.get_collection("deposition_index")
    except Exception as e:
        print(f"Error: Collection not found. Run embed_doc.py first\n{str(e)}")
        return

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(vector_store, embed_model=Settings.embed_model)
    llm = Ollama(model="gemma3:1b", request_timeout=60)

    # chronological order
    print("Retrieving content in page order...")
    retriever = index.as_retriever(
        similarity_top_k=500,
        vector_store_query_mode="mmr",  # mmr = max marginal relevance, gives more diverse results apparently
    )
    
    # nodes sorted by page/line by default
    all_nodes = retriever.retrieve("substantive testimony")
    
    end_index = detect_deposition_end(all_nodes)
    substantive_nodes = all_nodes[:end_index]
    
    # metadata prefilter
    # filtered_nodes = [n for n in substantive_nodes if is_substantive(n)]
    filtered_nodes = [n for n in substantive_nodes]
    print(f"\nFiltered to {len(filtered_nodes)} substantive segments (from {len(substantive_nodes)})")

    # relevance and page order
    sorted_nodes = sorted(
        filtered_nodes,
        key=lambda x: (-x.score, x.metadata['page_start'], x.metadata['line_start'])
    )[:num_topics]  # Early limit to target count

    # parallel processing
    toc = defaultdict(list)
    print(f"Processing {len(sorted_nodes)} segments with parallel LLM...")
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for node in sorted_nodes:
            futures.append(executor.submit(process_node, node, llm))
        
        for future in tqdm(futures, desc="Processing segments"):
            result = future.result()
            if result:
                toc[f"Page {result['page_start']}"].append(result)

    # saving results
    print("\nFinalizing table of contents...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(dict(sorted(toc.items(), 
                          key=lambda x: int(x[0].split()[1]))), 
                  f, indent=2)
    
    print(f"\nProcessed {sum(len(v) for v in toc.values())} segments across {len(toc)} pages")
    print(f"Output saved to: {os.path.abspath(output_path)}")

if __name__ == '__main__':
    import sys
    extract_topics(
        sys.argv[1] if len(sys.argv) > 1 else './outputs/vector_store',
        sys.argv[2] if len(sys.argv) > 2 else './outputs/extracted_topics.json',
        int(sys.argv[3]) if len(sys.argv) > 3 else 50
    )