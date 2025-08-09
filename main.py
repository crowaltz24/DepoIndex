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
    print("Starting processing pipeline...")
    start_time = time.time()
    
    print("Processing PDF...")
    pdf_start = time.time()
    nodes = process_pdf(input_path)
    print(f"PDF processed in {time.time() - pdf_start:.2f}s ({len(nodes)} chunks)")
    
    print("Extracting metadata...")
    meta_start = time.time()
    nodes = await extract_metadata(nodes)
    print(f"Metadata extracted in {time.time() - meta_start:.2f}s ({len(nodes)} processed)")
    
    print("Generating table of contents...")
    toc_start = time.time()
    toc = await generate_toc(nodes)
    print(f"TOC generated in {time.time() - toc_start:.2f}s ({len(toc)} entries)")
    
    print("Saving results...")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(toc, f, indent=2)
    
    print(f"\nPipeline completed in {time.time() - start_time:.2f} seconds")
    print(f"Output saved to: {output_path}")

if __name__ == "__main__":
    input_pdf = os.path.join("inputs", "deposition.pdf")
    output_json = os.path.join("outputs", "toc.json")
    
    # Clear terminal and run
    os.system('cls' if os.name == 'nt' else 'clear')
    asyncio.run(run_pipeline(input_pdf, output_json))