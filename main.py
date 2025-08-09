import asyncio
import json
import time
import os
from pathlib import Path
from dotenv import load_dotenv
from utils.pdf_processor import process_pdf
from utils.metadata_extractor import extract_metadata
from utils.toc_generator import generate_toc

load_dotenv()

async def run_pipeline(input_path, output_path):
    print("Starting deposition processing...")
    start_time = time.time()
    
    print("Processing PDF (with end detection)...")
    nodes = process_pdf(input_path)
    print(f"Processed {len(nodes)} content chunks before deposition end")
    
    print("Extracting metadata in batches...")
    nodes = await extract_metadata(nodes, batch_size=5)
    print(f"Extracted metadata from {len(nodes)} relevant chunks")
    
    toc = await generate_toc(nodes)

    with open(output_path, 'w') as f:
        json.dump(toc, f, indent=2)
    
    print(f"\nCompleted in {time.time() - start_time:.2f}s")
    print(f"Final TOC entries: {len(toc)}")

if __name__ == "__main__":
    input_pdf = os.path.join("inputs", "deposition.pdf")
    output_json = os.path.join("outputs", "toc.json")
    
    # Clear terminal and run
    os.system('cls' if os.name == 'nt' else 'clear')
    asyncio.run(run_pipeline(input_pdf, output_json))