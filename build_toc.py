import argparse
import os
from utils.topic_extraction import load_transcript, extract_topics
from utils.toc_generator import load_topics, generate_toc_markdown, generate_toc_docx

"""
Example usage:
python build_toc.py --file deposition.pdf --out toc.docx
"""

def main():
    parser = argparse.ArgumentParser(description="CLI Wrapper for DepoIndex")
    
    # args for I/O (relevant file paths)
    parser.add_argument(
        "--file", 
        type=str, 
        required=True, 
        help="Name of the deposition transcript file (located in the 'inputs' folder)."
    )
    parser.add_argument(
        "--out", 
        type=str, 
        required=True, 
        help="Name of the output file (saved in the 'outputs' folder)."
    )
    
    # parse args
    args = parser.parse_args()
    
    # paths relative to root directory, generated based on what file is specified in --out arg
    input_file = os.path.join("inputs", args.file)
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file '{input_file}' not found in the 'inputs' folder.")

    output_file = os.path.join("outputs", args.out)
    output_extension = os.path.splitext(output_file)[1].lower()
    if output_extension not in [".md", ".docx"]:
        raise ValueError("Invalid output format. Use '.md' for Markdown or '.docx' for DOCX.")

    # json path
    output_topics = os.path.splitext(output_file)[0] + ".json"
    checkpoint_file = os.path.join("outputs", "checkpoint.json")  # default checkpoint file

    # Step 1 - topic extraction
    print("\n\nStarting topic extraction...\n\n")
    transcript = load_transcript(input_file)
    extract_topics(transcript, output_topics, checkpoint_file=checkpoint_file)
    print(f"\n\nTopics saved to {output_topics}\n")
    
    # Step 2 - generating TOC
    print("\n\nGenerating Table of Contents...\n")
    topics = load_topics(output_topics)
    if output_extension == ".md":
        generate_toc_markdown(topics, output_file)
        print(f"\n\nTOC saved to {output_file}\n")
    elif output_extension == ".docx":
        generate_toc_docx(topics, output_file)
        print(f"\n\nTOC saved to {output_file}\n")

if __name__ == "__main__":
    main()

