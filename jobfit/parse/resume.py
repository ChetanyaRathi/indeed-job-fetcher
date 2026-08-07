import json
from pathlib import Path
from pypdf import PdfReader
from jobfit.models import Profile
from jobfit.llm.client import chat_no_think

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

    # Extract structured data using LLM.
    # qwen3.5 is a thinking model; extraction is mechanical and needs no reasoning,
    # so thinking is disabled (see chat_no_think). We also do NOT force json_object
    # grammar, which makes this model emit empty content here.
    system_prompt = (
        "You are an expert technical recruiter. Your task is to extract information from a resume. "
        "Return ONLY a single compact JSON object (no whitespace/newlines between keys) with the following keys:\n"
        "- \"skills\": list of strings (extract all technical and professional skills)\n"
        "- \"experience_years\": float (your best estimate of total years of professional experience)\n"
        "- \"summary\": string (a 2-3 line concise summary of the candidate's profile)\n"
        "Do not include any prose, explanations, or markdown code fences. Return only compact JSON."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Resume Text:\n{raw_text}"}
    ]

    def clean_json(text: str) -> str:
        text = (text or "").strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return text[start:end+1]
        return text

    max_retries = 1
    response_json = ""
    for attempt in range(max_retries + 1):
        try:
            # Thinking disabled so the mechanical extraction returns complete JSON
            # instead of burning the token budget reasoning (which truncated it).
            resp = chat_no_think(messages, max_tokens=2000)
            message = resp.get("message", {})
            response_json = message.get("content") or ""

            # With thinking off this should be empty; log it (and done_reason) so
            # any regression to the reasoning-eats-budget failure is diagnosable.
            thinking = message.get("thinking") or ""
            print(f"[resume extraction] attempt={attempt+1} done_reason={resp.get('done_reason')}")
            print(f"[resume extraction] raw content:\n{response_json}")
            if thinking:
                print(f"[resume extraction] thinking field present ({len(thinking)} chars); content may be empty")

            cleaned = clean_json(response_json)
            data = json.loads(cleaned)
            
            return Profile(
                raw_text=raw_text,
                skills=data.get("skills", []),
                experience_years=float(data.get("experience_years", 0.0)),
                summary=data.get("summary", ""),
                embedding=None
            )
        except Exception as e:
            if attempt < max_retries:
                continue
            raise RuntimeError(
                f"Failed to extract structured data from resume after {max_retries + 1} attempts. "
                f"Last error: {e}. Raw response: {response_json!r}"
            ) from e
