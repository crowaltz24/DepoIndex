import re
import os
from typing import List
from llama_index.core.schema import TextNode
from llama_index.core import SimpleDirectoryReader

END_PHRASES = [
    "end of deposition",
    "deposition concluded",
    "this concludes today's",
    "word index"
]

QA_PREFIX = re.compile(r"^\s*([QA]|BY [A-Z'. ]+):?\s+")
LINE_NUM_RE = re.compile(r"^\s*(\d{1,4})\s+(.*)$")
TIMESTAMP_RE = re.compile(r"\b\d{2}:\d{2}\b")

def is_end_of_deposition(text: str) -> bool:
    tl = text.lower()
    return any(p in tl for p in END_PHRASES)

def clean_line(raw: str) -> str:
    
    raw = raw.rstrip()
    # timestamps
    raw = TIMESTAMP_RE.sub("", raw)
    # leading Q/A/BY labels
    raw = QA_PREFIX.sub("", raw)
    # internal whitespace
    raw = re.sub(r"\s+", " ", raw)
    return raw.strip()

def derive_page_number(line_no: int, lines_per_page: int = 25) -> int:
    if line_no < 1:
        return 1
    return (line_no - 1) // lines_per_page + 1

def process_pdf(input_path: str, *, max_chars: int = 2000, lines_per_page: int = 25) -> List[TextNode]:
    documents = SimpleDirectoryReader(
        input_files=[input_path],
        file_metadata=lambda x: {"filename": os.path.basename(x)}
    ).load_data()

    all_chunks: List[TextNode] = []
    global_prev_line_no = 0

    for doc in documents:
        if is_end_of_deposition(doc.text):
            break

        # (line_no, text) sequence
        parsed_lines = [] 
        for raw_line in doc.text.splitlines():
            if not raw_line.strip():
                continue  # skip blank spacer lines
            m = LINE_NUM_RE.match(raw_line)
            if m:
                candidate_no = int(m.group(1))
                content_part = m.group(2)
                # just use sequential if too far ahead
                if candidate_no <= global_prev_line_no or candidate_no - global_prev_line_no > 5:
                    candidate_no = global_prev_line_no + 1
                global_prev_line_no = candidate_no
                cleaned = clean_line(content_part)
            else:
                # sequential if no specific number
                global_prev_line_no += 1
                cleaned = clean_line(raw_line)
            if cleaned:
                parsed_lines.append((global_prev_line_no, cleaned))

        if not parsed_lines:
            continue

        # Chunking by char budget
        current: List[tuple[int, str]] = []
        current_chars = 0

        def flush():
            nonlocal current, current_chars
            if not current:
                return
            # global line numbers
            global_line_start = current[0][0]
            global_line_end = current[-1][0]
            lines_count = len(current)
            page_start = derive_page_number(global_line_start, lines_per_page)
            page_end = derive_page_number(global_line_end, lines_per_page)
            page_numbers = list(range(page_start, page_end + 1))
            chunk_text = "\n".join(t for _, t in current)
            # relative line indices
            page_line_start = ((global_line_start - 1) % lines_per_page) + 1
            if page_start == page_end:
                page_line_end = ((global_line_end - 1) % lines_per_page) + 1
            else:
                # span crosses pages
                page_line_end = None
            meta = {
                "filename": doc.metadata.get("filename"),
                
                "line_start": page_line_start,
                "line_end": page_line_end,
                
                "global_line_start": global_line_start,
                "global_line_end": global_line_end,
                "lines_count": lines_count,
                "page_start": page_start,
                "page_end": page_end,
                "page_numbers": page_numbers,
                "page_number": page_start,
            }
            all_chunks.append(TextNode(text=chunk_text, metadata=meta))
            current = []
            current_chars = 0

        for line_no, content in parsed_lines:
            # Soft boundary
            if current and current_chars + len(content) + 1 > max_chars:
                flush()
            current.append((line_no, content))
            current_chars += len(content) + 1
        flush()

    return all_chunks