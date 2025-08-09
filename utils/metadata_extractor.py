import os
import json
from llama_index.core.extractors import SummaryExtractor
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

DEPOSITION_PROMPT = """
Analyze this deposition excerpt and extract:
1. Primary subject (3-5 words)
2. Key factual statements (bullet points)
3. Page range being discussed

Format as:
SUBJECT: <subject>
STATEMENTS:
- <statement1>
- <statement2>
PAGE: <current page>

Excerpt:
{context_str}
"""

def parse_summary(summary_text):
    result = {"subject": "", "statements": []}
    
    try:
        if "SUBJECT:" in summary_text:
            result["subject"] = summary_text.split("SUBJECT:")[1].split("\n")[0].strip()
        
        if "STATEMENTS:" in summary_text:
            statements = []
            for line in summary_text.split("STATEMENTS:")[1].split("\n"):
                if line.startswith("- "):
                    statements.append(line[2:].strip())
            result["statements"] = statements
    except:
        # if parsing fails
        result["subject"] = "Deposition Testimony"
        result["statements"] = [summary_text[:200] + "..."]
    
    return result

async def extract_metadata(nodes):
    if not nodes:
        return []
    
    # LLM
    llm = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-3.5-turbo",
        temperature=0.3
    )
    Settings.llm = llm

    # extractor
    summary_extractor = SummaryExtractor(
        summaries=["self"],
        prompt_template=DEPOSITION_PROMPT,
        extract_template="{summary}",
        metadata_mode="all"
    )

    processed_nodes = []
    for node in nodes:
        try:
            processed = await summary_extractor.aprocess_nodes([node])
            if processed:
                summary = processed[0].metadata.get("section_summary", "")
                node.metadata["deposition_summary"] = parse_summary(summary)
                processed_nodes.append(node)
        except Exception as e:
            print(f"Node processing error: {e}")
            continue
    
    return processed_nodes