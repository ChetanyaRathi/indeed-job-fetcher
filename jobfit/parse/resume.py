import json
from pathlib import Path
from pypdf import PdfReader
from jobfit.models import Profile
from jobfit.llm.client import chat

def parse_resume(file_path: str | Path) -> Profile:
    """
    Reads a resume from a file (PDF or TXT), extracts its raw text,
    and uses the local LLM to extract structured profile data.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Resume not found at {file_path}")

    raw_text = ""
    if file_path.suffix.lower() == ".pdf":
        reader = PdfReader(file_path)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                raw_text += text + "\n"
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

    if not raw_text.strip():
        raise ValueError("Resume file appears to be empty or could not be parsed.")

    # Extract structured data using LLM
    system_prompt = (
        "You are an expert technical recruiter. Your task is to extract information from a resume. "
        "Return ONLY a valid JSON object with the following keys:\n"
        "- \"skills\": list of strings (extract all technical and professional skills)\n"
        "- \"experience_years\": float (your best estimate of total years of professional experience)\n"
        "- \"summary\": string (a 2-3 line concise summary of the candidate's profile)\n"
        "Do not include any prose or markdown blocks. Return only JSON."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Resume Text:\n{raw_text}"}
    ]

    try:
        response_json = chat(messages, response_format={"type": "json_object"})
        data = json.loads(response_json)
        
        return Profile(
            raw_text=raw_text,
            skills=data.get("skills", []),
            experience_years=float(data.get("experience_years", 0.0)),
            summary=data.get("summary", ""),
            embedding=None
        )
    except Exception as e:
        raise RuntimeError(f"Failed to extract structured data from resume: {e}") from e
