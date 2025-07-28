import argparse
import os
import sys
from pathlib import Path
import time

def main():
    start_time = time.perf_counter()
    parser = argparse.ArgumentParser(description="CLI Wrapper for  DepoIndex")
    
    # Main args
    parser.add_argument(
        "--input", 
        type=str, 
        required=True,
        help="Input deposition file (PDF) in the inputs/ directory"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output TOC file name (with .docx or .md extension) in outputs/"
    )
    
    args = parser.parse_args()

    #  input valid?
    input_path = Path("inputs") / args.input
    if not input_path.exists():
        print(f"Error: Input file not found at {input_path}")
        sys.exit(1)

    # detecting output format, generate path based on extension
    output_path = Path("outputs") / args.output
    output_format = output_path.suffix.lower()
    
    if output_format not in [".docx", ".md"]:
        print("Error: Output file must end with .docx or .md")
        sys.exit(1)

    # create output dir if needed
    Path("outputs").mkdir(exist_ok=True)

    # file paths
    preprocessed_path = Path("outputs") / "preprocessed.json"
    chunks_path = Path("outputs") / "chunks.json"
    vector_store_path = Path("outputs") / "vector_store"
    topics_path = output_path.with_suffix(".json")

    # pipeline
    try:

        print("\n=== STEP 1: Preprocessing ===")
        os.system(f"python utils/preprocess_doc.py {input_path} {preprocessed_path}")
        

        print("\n=== STEP 2: Chunking ===")
        os.system(f"python utils/chunk_doc.py {preprocessed_path} {chunks_path}")
        

        print("\n=== STEP 3: Creating Vector Store ===")
        os.system(f"python utils/embed_doc.py {chunks_path} {vector_store_path}")
        

        print("\n=== STEP 4: Extracting Topics ===")
        os.system(f"python utils/extract_topics.py {vector_store_path} {topics_path}")
        

        print("\n=== STEP 5: Generating Table of Contents ===")
        os.system(f"python utils/generate_toc.py {topics_path} {output_path}")

        print(f"\nProcessing complete! TOC saved to {output_path}")
        
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        print(f"Total processing time: {elapsed_time:.2f} seconds")

    except Exception as e:
        print(f"\nError during processing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()