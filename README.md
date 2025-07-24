# DepoIndex

DepoIndex is an automated, AI-powered workflow that reads deposition transcripts, detects every distinct subject discussed, and produces a Table of Contents (TOC). For each topic, the system lists the starting page number and line number, then outputs the results as a chronologically ordered Topic Index.

DepoIndex enables clerks to generate an accurate, paginated topic index from a deposition in minutes - eliminating manual scanning and ensuring that judges can jump directly to any point of interest.

Made for docu3C's Summer Internship Program 2025.

### To-Do
- Validation Notebook
- Topic accuracy optimization
- Improve docx pagination...?
- CLI/API wrapper

## Models

- Gemma3 (4B) for topic extraction.
<!-- - DeepSeek-R1 (8B) for validation and reasoning. -->
  
## Setup
1. Clone repo
   ```bash
   git clone https://crowaltz24/DepoIndex
   cd DepoIndex
   ```

2. Ensure your directory structure is as follows:
   
   DepoIndex
   - /inputs
   - /outputs
   - /scripts
   
3. Create venv
   ```bash
   python -m venv venv
   venv/scripts/activate
   ```

4. Install requirements
   ```bash
   pip install -r requirements.txt
   ```

## How to Use
1. Place your Deposition Transcript in `/inputs`.
   
2. Move to `/scripts`
   ```bash
   cd scripts
   ```

3. Run DepoIndex
   ```bash
   python depoindex.py
   ```

   - This creats and saves `extracted_topics.json` into `/outputs`. It also forms a `checkpoint.json` to keep track of progress.
   - You will see a progress bar in the terminal to indicate topic extraction progress.
   - Then, it creates and saves `table_of_contents.md` and `table_of_contents.docx` to `/outputs`.

   **NOTE:** If you have a different input file, modify the `transcript_file` variable in this script to point to it: `./inputs/YOUR_DEPOSITION_FILE.pdf`.

### Alternatively

Run the scripts one by one:
- `topic_extraction.py` extracts topics into `extracted_topics.json`.
- `topc_generator.py` uses the extracted topics to generate a table of contents, saving it in Markdown and docx formats.