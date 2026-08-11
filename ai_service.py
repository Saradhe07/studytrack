import json
import math
import os
import re
import urllib.request
from typing import List, Dict, Any

try:
    from dotenv import load_dotenv
    # Load .env file from project root or backend directory
    load_dotenv()
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass

# Initial seed list of study notes for semantic search (in-memory list)
SAMPLE_NOTES: List[Dict[str, Any]] = [
    {
        "id": 1,
        "text": "Binary search requires a sorted array and repeatedly halves the search range using a midpoint comparison.",
    },
    {
        "id": 2,
        "text": "Insertion sort builds a sorted list one element at a time by shifting larger elements to the right.",
    },
    {
        "id": 3,
        "text": "FastAPI uses Pydantic models to validate request bodies and automatically generates Swagger documentation.",
    },
    {
        "id": 4,
        "text": "SQL joins combine rows from two tables using a matching column, such as inner join, left join, and full join.",
    },
    {
        "id": 5,
        "text": "Prompt engineering structures a task, context, constraints, and desired output format to guide an LLM's response.",
    },
]

# Fixed 12-word vocabulary for mock_embed in exact specified order
VOCABULARY: List[str] = [
    "sort",
    "search",
    "binary",
    "insertion",
    "sql",
    "join",
    "fastapi",
    "pydantic",
    "prompt",
    "llm",
    "database",
    "validate",
]


def get_ai_mode() -> str:
    """Returns active AI mode ('mock' or 'real'). Defaults to 'mock'."""
    return os.getenv("AI_MODE", "mock").lower()


def get_api_key() -> str:
    """Retrieves API key from environment variables if present."""
    return os.getenv("GEMINI_API_KEY") or os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY") or ""


def summarize_notes_mock(raw_text: str) -> Dict[str, Any]:
    """Deterministic offline mock note summarizer."""
    if not raw_text or not raw_text.strip():
        return {
            "topic": "untitled",
            "key_points": [],
            "difficulty": "easy",
        }

    stripped = raw_text.strip()

    # Topic derivation: first sentence of the first non-empty line
    lines = [line.strip() for line in stripped.splitlines() if line.strip()]
    if lines:
        first_line = lines[0]
        sentences_in_line = [s.strip() for s in re.split(r"[.!?]+", first_line) if s.strip()]
        topic = sentences_in_line[0] if sentences_in_line else first_line
    else:
        topic = "untitled"

    # Key points: split into sentences on [.!?]+, take up to 3 non-empty sentences
    raw_sentences = re.split(r"[.!?]+", stripped)
    key_points = [s.strip() for s in raw_sentences if s.strip()][:3]

    # Difficulty derivation based on total word count
    words = stripped.split()
    word_count = len(words)

    if word_count < 40:
        difficulty = "easy"
    elif word_count <= 100:
        difficulty = "medium"
    else:
        difficulty = "hard"

    return {
        "topic": topic,
        "key_points": key_points,
        "difficulty": difficulty,
    }


def summarize_notes_real(raw_text: str, api_key: str) -> Dict[str, Any]:
    """Calls Gemini LLM API to summarize notes into structured JSON."""
    if not raw_text or not raw_text.strip():
        return {"topic": "untitled", "key_points": [], "difficulty": "easy"}

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    prompt_content = f"""Task: Summarize raw study notes into a fixed structured JSON object.
Constraints: Output ONLY valid raw JSON with no markdown code blocks.
Format:
{{
  "topic": "<string topic>",
  "key_points": ["<string point 1>", "<string point 2>", "<string point 3>"],
  "difficulty": "<easy|medium|hard>"
}}

Input Text:
{raw_text}"""

    payload = {
        "contents": [{"parts": [{"text": prompt_content}]}],
        "generationConfig": {"response_mime_type": "application/json"},
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            content_str = res_data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(content_str)
            return {
                "topic": parsed.get("topic", "untitled"),
                "key_points": parsed.get("key_points", []),
                "difficulty": parsed.get("difficulty", "easy").lower(),
            }
    except Exception as e:
        # Fallback to mock mode on any network error or invalid key
        print(f"[AI_SERVICE] Real mode call failed ({e}), falling back to mock mode.")
        return summarize_notes_mock(raw_text)


def summarize_notes(raw_text: str) -> Dict[str, Any]:
    """Main summary dispatcher."""
    mode = get_ai_mode()
    key = get_api_key()

    if mode == "real" and key:
        return summarize_notes_real(raw_text, key)

    return summarize_notes_mock(raw_text)


def mock_embed(text: str) -> List[float]:
    """Deterministically embeds any input text into a 12-dimensional vector

    matching the exact VOCABULARY frequency count.
    """
    if not text:
        return [0.0] * len(VOCABULARY)

    # Lowercase and split on non-alphanumeric characters
    tokens = [t for t in re.split(r"[^a-z0-9]+", text.lower()) if t]

    # Count exact whole-token matches for each vocabulary word
    token_counts = {}
    for token in tokens:
        token_counts[token] = token_counts.get(token, 0) + 1

    vector = [float(token_counts.get(word, 0)) for word in VOCABULARY]
    return vector


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Computes cosine similarity between two 12-dimensional numeric vectors.

    Zero-vector edge case: If either vector has an L2 norm of 0.0, returns 0.0 directly.
    """
    norm_a = math.sqrt(sum(x * x for x in vec_a))
    norm_b = math.sqrt(sum(x * x for x in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    similarity = dot_product / (norm_a * norm_b)

    if abs(similarity - 1.0) < 1e-6:
        return 1.0

    return similarity


def find_matched_vocab_words(query: str, note_text: str) -> List[str]:
    """Extracts overlapping 12-vocab tokens present in both query and note text."""
    query_tokens = set([t for t in re.split(r"[^a-z0-9]+", query.lower()) if t])
    note_tokens = set([t for t in re.split(r"[^a-z0-9]+", note_text.lower()) if t])
    vocab_set = set(VOCABULARY)

    matched = list((query_tokens & note_tokens) & vocab_set)
    return sorted(matched)


def search_notes(query: str) -> List[Dict[str, Any]]:
    """Embeds query and computes cosine similarity against all notes."""
    query_vec = mock_embed(query)
    results = []

    for note in SAMPLE_NOTES:
        note_vec = mock_embed(note["text"])
        score = cosine_similarity(query_vec, note_vec)
        matched_words = find_matched_vocab_words(query, note["text"]) if score > 0 else []

        results.append(
            {
                "id": note["id"],
                "text": note["text"],
                "score": round(score, 4),
                "matched_words": matched_words,
            }
        )

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def add_custom_note(text: str) -> Dict[str, Any]:
    """Appends a new study note to the in-memory notes list for semantic search."""
    new_id = max([n["id"] for n in SAMPLE_NOTES], default=0) + 1
    new_note = {"id": new_id, "text": text.strip()}
    SAMPLE_NOTES.append(new_note)
    return new_note


def get_all_notes() -> List[Dict[str, Any]]:
    """Returns all currently indexed study notes."""
    return SAMPLE_NOTES
