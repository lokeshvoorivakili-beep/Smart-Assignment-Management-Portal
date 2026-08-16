import os
import re
from difflib import SequenceMatcher
from utils.file_utils import extract_text_from_file

def preprocess_text(text: str) -> list[str]:
    """Cleans text into tokens for comparison (normalizes whitespace, removes symbols)."""
    text = text.lower()
    tokens = re.findall(r'\b\w+\b', text)
    return tokens

def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculates percentage similarity (0.0 to 100.0) between two text strings
    using sequence ratio and token overlap.
    """
    if not text1.strip() or not text2.strip():
        return 0.0

    tokens1 = preprocess_text(text1)
    tokens2 = preprocess_text(text2)

    if not tokens1 or not tokens2:
        return 0.0

    str1 = " ".join(tokens1)
    str2 = " ".join(tokens2)

    # Sequence Matcher ratio
    seq_ratio = SequenceMatcher(None, str1, str2).ratio()

    # Jaccard Token set overlap
    set1, set2 = set(tokens1), set(tokens2)
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    jaccard_ratio = len(intersection) / len(union) if union else 0.0

    # Weighted blend
    score = (seq_ratio * 0.6 + jaccard_ratio * 0.4) * 100.0
    return round(score, 2)

def compute_submission_similarity(new_file_path: str, existing_file_paths: list[str]) -> float:
    """
    Compares newly uploaded file against all existing submission files for the same assignment.
    Returns the maximum similarity percentage found.
    """
    new_text = extract_text_from_file(new_file_path)
    if not new_text.strip():
        return 0.0

    max_score = 0.0
    for file_path in existing_file_paths:
        if os.path.exists(file_path):
            existing_text = extract_text_from_file(file_path)
            score = calculate_text_similarity(new_text, existing_text)
            if score > max_score:
                max_score = score

    return max_score
