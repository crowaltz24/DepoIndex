# DepoIndex

DepoIndex is an automated, AI-powered workflow that reads deposition transcripts, detects every distinct subject discussed, and produces a Table of Contents (TOC). For each topic, the system lists the starting page number and line number, then outputs the results as a chronologically ordered Topic Index.

DepoIndex enables clerks to generate an accurate, paginated topic index from a deposition in minutes - eliminating manual scanning and ensuring that judges can jump directly to any point of interest.

Developed to apply for docu3C's Summer Internship Program 2025.

### What it does:
- Reads the transcript
- Cleans each line (removes timestamps, Q/A labels)
- Tracks both global and page‑relative line numbers
- Chunks the text by character budget
- Summarizes chunks with an LLM (subject + key statements)
- Emits a TOC with (page, line_start) anchors
- Exports JSON, Markdown, or DOCX

## Requirements
- Python 3.12+
- `pip install -r requirements.txt`
- OpenAI key: set `OPENAI_API_KEY` (for SummaryExtractor)

## Get Started
```powershell
git clone https://github.com/crowaltz24/DepoIndex.git
cd DepoIndex
git checkout rich-metadata-implementation
```

Ensure your directory structure is as follows:
```
DepoIndex
|_ /inputs
|_ /outputs
|_ /utils
|_ /validation
```

Then,
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Copy your deposition file into `inputs` folder.

```powershell
python build_toc.py --file deposition.pdf --output outputs/toc.json
```

Other output formats:
```powershell
python build_toc.py --file deposition.pdf --output outputs/toc.md
python build_toc.py --file deposition.pdf --output outputs/toc.docx
```

Flags:
- `--file`  input PDF (name or path; if name only, looked up in inputs/)
- `--output` path ending with .json / .md / .docx (default outputs/toc.json)

## License
MIT
