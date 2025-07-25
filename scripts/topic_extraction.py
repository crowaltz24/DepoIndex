import json
import os
# from dotenv import load_dotenv

from ollama import chat, ChatResponse
from difflib import SequenceMatcher # for comparing topic similarity

from PyPDF2 import PdfReader
from tqdm import tqdm  # for progress bar


# initially I was using the openrouter API but now i switched to local models via ollama so I'm just gonna comment this out
# load_dotenv()

# pdf loader
def load_transcript(file_path):
    reader = PdfReader(file_path)
    return [page.extract_text() for page in reader.pages] # returning a list of pages

def normalize_topic(topic):
    return topic.lower().strip()


"""
So I'm chunking the pdf by page, and then extracting topics from each page.
This can cause some problems if the same topic is being discussed across multiple pages
so whenever we find a topic, we check if it already exists in the list of topics.
We normalize topic names and run a sequence matcher to check for similarity
and we merge similar topics by updating their page_end and line_end.
Thus we can eliminate topic redundancy.
"""

# !!! SIMILARITY THRESHOLD !!!
similarity_threshold = 0.8

def are_topics_similar(topic1, topic2, threshold=similarity_threshold):
    return SequenceMatcher(None, topic1, topic2).ratio() >= threshold

def parse_topic_line(line):
    try:
        # splitting lines by common punctuation (weird implementation but what to do)
        parts = line.split(", ")
        topic = parts[0].split(": ")[1].strip('"')
        page = parts[1].split(": ")[1]
        line_start = parts[2].split(": ")[1]
        return topic, page, line_start
    except (IndexError, ValueError): # if somehow theres nothing we'll just return None 3 times lol not sure what else to do for now
        return None, None, None

def save_page_topics_to_json(page_number, page_topics, output_file):
    # we save each page to json as soon as its done so that we dont lose progress if the extraction fails midway
    if os.path.exists(output_file):
        with open(output_file, "r") as f:
            all_topics = json.load(f)
    else:
        all_topics = {}

    all_topics[f"Page {page_number}"] = page_topics

    with open(output_file, "w") as f:
        json.dump(all_topics, f, indent=4)

def is_end_of_deposition(page_content, model_response):
    # We check if the deposition has ended so that this script doesnt try to extract topics from anything other than the actual transcript text
    end_phrases = [
        "End of Deposition",
        "This concludes the deposition",
        "This concludes today's",
        # "off the record"
    ]
    for phrase in end_phrases:
        if phrase.lower() in page_content.lower() or phrase.lower() in model_response.lower():  # comparing model response too
            return True
    return False




# CHECKPOINT SYSTEM
# I decided to implement a checkpoint system so that the script wouldnt have to start from scratch if it fails midway
# just to give my poor GPU some relief

def save_checkpoint(page_number, checkpoint_file):
    # checkpointing last processed page
    with open(checkpoint_file, "w") as f:
        json.dump({"last_processed_page": page_number}, f, indent=4)

def load_checkpoint(checkpoint_file):
    # loading the last processed page from checkpoint
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, "r") as f:
            data = json.load(f)
            return data.get("last_processed_page", 0)
    return 0

def reset_checkpoint(checkpoint_file):
    # checkpoint reset function
    with open(checkpoint_file, "w") as f:
        json.dump({"last_processed_page": 0}, f, indent=4)





# EXTRACTION STARTS HERE


def extract_topics(transcript, output_file, checkpoint_file):
    # now we process each page one by one and extract topics from it
    pages = transcript  # the transcript is now a list of pages
    total_pages = len(pages)
    print(f"Total pages detected: {total_pages}")  # Debugging

    # load the last processed page from the checkpoint (this helps in case our extraction process got interrupted midway)
    last_processed_page = load_checkpoint(checkpoint_file)
    print(f"Resuming from Page {last_processed_page + 1}...")  # Debugging

    # progress bar)
    progress_bar = tqdm(
        total=total_pages,
        desc="\n\nProcessing Deposition",
        unit="page",
        dynamic_ncols=True
    )
    # whats better than waiting? waiting watching numbers go up :D

    # we have to manually update the progress bar for skipped pages (or in case of checkpoint load)
    if last_processed_page > 0:
        progress_bar.update(last_processed_page)

    for page_number, page_content in enumerate(pages, start=1):
        if page_number <= last_processed_page:
            # already processed pages get skipped
            continue

        # Using tqdm.write to avoid interfering with the progress bar 
        tqdm.write(f"\n\nProcessing Page {page_number}...")  
        tqdm.write(f"\nPage Content (first 500 chars): \n{page_content[:500]}")  # Debugging


        # LLM PROMPT
        prompt = f"""
        Extract ONLY a series of topics from the following deposition text. For each topic, provide the topic name, starting page, and line number in plain text format. 
        If a specific person is relevant to the topic (i.e the current witness, expert, questioning attorney etc), ALWAYS INCLUDE THEIR NAME in the topic.
        If the topic is a question, include the content of the question as well as who asked or answered it in the topic name, if provided
        Do NOT generate generic topic names such as "Witness Testimony", "Expert Analysis", "Questioning", "Discussion", "Conclusion", etc.
        Do NOT generate topics for irrelevant details like someone being corrected for their manner of speaking, clarifications, or adjustments. Only informative topics, necessary to the testimony and flow of transcript should be extracted.
        Do NOT include ANY description, analysis, commentary, or additional information. Do NOT use any formatting, only plain text. Do NOT include ANYTHING except the output. Ensure the output is structured exactly as follows:
        
        Topic: "<topic_name>", Page: <page_number>, Line: <line_number>
        
        Example Output:
        Topic: "Introduction", Page: 1, Line: 1
        Topic: "Contract Details", Page: 2, Line: 5

        Deposition Text (Page {page_number}):
        {page_content}

        Topics:
        """

        # USING GEMMA3 (4B) LLM
        try:
            response: ChatResponse = chat(
                model="gemma3",
                messages=[{"role": "user", "content": prompt}],
            )
            extracted = response.message.content.strip()
            tqdm.write(f"\n\nRaw Response for Page {page_number}:\n{extracted}\n\n")  # Debugging
        except Exception as e:
            tqdm.write(f"Error processing page {page_number}: {e}")
            progress_bar.update(1)  # update progress bar even if the page is skipped
            continue

        if not extracted:
            tqdm.write(f"No valid response for Page {page_number}. Skipping.")
            progress_bar.update(1)  # update progress bar even if the page is skipped
            continue

        # now we check if the response or actual text indicates the end of the deposition so we're not wasting resources on anything other than the actual transcript text
        if is_end_of_deposition(page_content, extracted):
            tqdm.write(f"End of Deposition detected on Page {page_number}. Stopping further processing.")
            # and save "End of Deposition" as a topic for this page
            save_page_topics_to_json(page_number, [
                {
                    "topic": "End of Deposition",
                    "page_start": page_number,
                    "line_start": 1,
                    "page_end": page_number,
                    "line_end": len(page_content.split("\n")),  # last line of the page
                }
            ], output_file)
            save_checkpoint(page_number, checkpoint_file)  # update the checkpoint asap
            progress_bar.n = total_pages  # fill the progress bar cause we're done
            progress_bar.refresh()
            break




        
        page_topics = []
        lines = extracted.split("\n")

        for line in lines:
            topic, page, line_start = parse_topic_line(line)
            if not topic or not page or not line_start:
                continue
            
            # SIMILARITY CHECKING TO REDUCE REDUNDANT TOPICS

            normalized_topic = normalize_topic(topic)
            existing_topic = next(
                (t for t in page_topics[-2:] if are_topics_similar(normalized_topic, normalize_topic(t["topic"]))), # -2 because i only want to check the past 2 pages
                None
            )

            if existing_topic:
                # updating existic topics page and line to incorporate the redundant topic
                existing_topic["page_end"] = max(existing_topic["page_end"], page_number)
                existing_topic["line_end"] = max(existing_topic["line_end"], int(line_start))
                tqdm.write(f"Existing topic detected, updating: {existing_topic}")
            else:
                # IF no similar topic exists, then we add a new topic.
                page_topics.append({
                    "topic": topic,
                    "page_start": int(page),
                    "line_start": int(line_start),
                    "page_end": page_number,
                    "line_end": int(line_start),
                })

        # update topics, checkpoint, progress bar for the current page asap
        save_page_topics_to_json(page_number, page_topics, output_file)
        save_checkpoint(page_number, checkpoint_file)
        progress_bar.update(1)

    progress_bar.close()  # close the progress bar when processing is complete

    # reset the checkpoint after successful completion
    # thus if we run script on a completed transcript again, it will start from the beginning
    reset_checkpoint(checkpoint_file)
    tqdm.write("\n\nProcessing complete. Checkpoint reset.")

def save_topics_to_json(topics, output_file):
    with open(output_file, "w") as f:
        json.dump(topics, f, indent=4)

if __name__ == "__main__":
    transcript_file = "./inputs/Deposition for PersisYu_Link.pdf"   # here goes our transcript file
    output_file = "./outputs/extracted_topics.json"                 # here go our extracted topics
    checkpoint_file = "./outputs/checkpoint.json"                   # here goes our checkpoints

    # load transcript as a list of pages
    transcript = load_transcript(transcript_file)
    extract_topics(transcript, output_file, checkpoint_file)
    
    print(f"Topics saved to {output_file}")