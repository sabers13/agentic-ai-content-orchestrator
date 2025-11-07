# src/quality_agent/readability.py
import re

def count_syllables(word: str) -> int:
    word = word.lower()
    vowels = "aeiouy"
    count = 0
    prev_vowel = False
    for ch in word:
        is_vowel = ch in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    if word.endswith("e"):
        count = max(1, count - 1)
    return max(count, 1)

def flesch_reading_ease(text: str) -> float:
    sentences = max(1, text.count(".") + text.count("!") + text.count("?"))
    words = re.findall(r"\w+", text)
    num_words = max(1, len(words))
    syllables = sum(count_syllables(w) for w in words)
    # Flesch Reading Ease
    return 206.835 - 1.015 * (num_words / sentences) - 84.6 * (syllables / num_words)

def readability_score(text: str) -> float:
    """Normalize to 0-100, higher is easier."""
    score = flesch_reading_ease(text)
    # clamp
    if score < 0:
        score = 0
    if score > 100:
        score = 100
    return score
