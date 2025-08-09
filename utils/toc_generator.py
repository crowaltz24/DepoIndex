async def generate_toc(nodes):
    toc = []
    
    for node in nodes:
        if not node.metadata.get("deposition_summary"):
            continue
            
        summary = node.metadata["deposition_summary"]
        toc.append({
            "topic": summary["subject"],
            "page_start": node.metadata.get("page_number", 0),
            "line_start": node.metadata.get("line_start", 0),
            "key_points": summary["statements"][:3]  # Top 3 statements
        })
    
    # fallback if no nodes processed
    if not toc:
        toc = [{
            "topic": "Deposition Transcript",
            "page_start": 1,
            "line_start": 1,
            "key_points": ["Full deposition transcript"]
        }]
    
    return toc