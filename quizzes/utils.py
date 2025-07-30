import logging
import traceback

from rapidfuzz import fuzz, process

from openai_utils.client import ask_chatgpt
from openai_utils.loaders import get_prompt

logger = logging.getLogger(__name__)


def classify_topics_list(topics: list[str], categories: list[str]) -> list[dict]:
    prompt = get_prompt("categorize_topics", topics="\n".join(topics), categories="\n".join(categories))
    raw_result = ask_chatgpt(prompt, model="gpt-4.1-mini")
    results = []
    for line in raw_result.splitlines():
        if "->" not in line:
            logger.warning(f"NO ARROW | {line}")
            continue
        try:
            topic_part, category_part = line.split("->", 1)
            topic_raw = topic_part.replace("Item:", "").strip()
            categories_raw_str = category_part.replace("Categories:", "").strip()
            matched_topic, topic_score, _ = process.extractOne(topic_raw, topics, scorer=fuzz.token_sort_ratio)
            if topic_score < 70:
                logger.error(f"NO TOPIC MATCH | {line}")
                continue
            raw_categories = [c.strip() for c in categories_raw_str.split(",")]
            matched_categories = []
            for raw_category in raw_categories:
                match, score, _ = process.extractOne(raw_category, categories, scorer=fuzz.token_sort_ratio)
                if score >= 70:
                    matched_categories.append(match)
                else:
                    logger.error(f"NO CATEGORY MATCH | {line}")
            results.append({"topic": matched_topic, "category": matched_categories if matched_categories else []})
        except Exception:
            logger.exception(traceback.format_exc())
            continue
    return results
