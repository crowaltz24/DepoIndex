import os
from topic_extraction import load_transcript, extract_topics, save_topics_to_json
from toc_generator import load_topics, generate_toc_markdown, generate_toc_docx

# just running THIS script should go through our entire process
def run_depoindex():
    # all relevant file paths
    transcript_file = "./inputs/Deposition for PersisYu_Link.pdf"
    extracted_topics_file = "./outputs/extracted_topics.json"
    markdown_toc_file = "./outputs/table_of_contents.md"
    docx_toc_file = "./outputs/table_of_contents.docx"
    checkpoint_file = "./outputs/checkpoint.json"

    # Step 1 - topic extraction
    print("\n\nStarting topic extraction...\n\n")
    transcript = load_transcript(transcript_file)
    extract_topics(transcript, extracted_topics_file, checkpoint_file)
    print(f"\n\nTopics saved to {extracted_topics_file}\n")

    # Step 2 - generating TOC
    print("\n\nGenerating Table of Contents...\n")
    topics = load_topics(extracted_topics_file)
    generate_toc_markdown(topics, markdown_toc_file)
    generate_toc_docx(topics, docx_toc_file)
    print(f"\n\nTOC saved to {markdown_toc_file} and {docx_toc_file}\n")

    # (todo) step 3 - validation with notebook
    
if __name__ == "__main__":
    run_depoindex()