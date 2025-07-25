# DepoIndex

DepoIndex is an automated, AI-powered workflow that reads deposition transcripts, detects every distinct subject discussed, and produces a Table of Contents (TOC). For each topic, the system lists the starting page number and line number, then outputs the results as a chronologically ordered Topic Index.

DepoIndex enables clerks to generate an accurate, paginated topic index from a deposition in minutes - eliminating manual scanning and ensuring that judges can jump directly to any point of interest.

Developed to apply for docu3C's Summer Internship Program 2025.

### To-Do
- ~~Topic Extraction~~
- ~~Table of Contents Generation~~
- ~~Validation Notebook~~
- CLI wrapper


## Requirements

- Python 3.12
- OLlama with the following models pulled:
  - Gemma3 (4B) for topic extraction.
  - DeepSeek-R1 (8B) for reasoning based validation.
  
## Setup
1. Clone repo
   ```bash
   git clone https://crowaltz24/DepoIndex
   cd DepoIndex
   ```

2. Ensure your directory structure is as follows:
   
   ```
   DepoIndex
   |_ /inputs
   |_ /outputs
   |_ /scripts
   |_ /validation
   ```

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

### Manual Usage

Run the scripts one by one:
- `topic_extraction.py` extracts topics into `extracted_topics.json`.
- `topc_generator.py` uses the extracted topics to generate a table of contents, saving it in Markdown and docx formats.

## Validation
`validation.ipynb` is... a validation notebook. It takes a random sample of topics from y our extracted topics, and runs them past a reasoning LLM to compare with an excerpt of the text they were generated from to judge accuracy. 

**NOTE:** You can change the `number_of_topics` to validate on as many topics as you want.

## License
MIT License.