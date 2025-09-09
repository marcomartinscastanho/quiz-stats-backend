import logging
import traceback
from difflib import get_close_matches

from rapidfuzz import fuzz, process

from openai_utils.client import ask_chatgpt
from openai_utils.loaders import get_prompt
from quizzes.models import Category, Question
from quizzes.serializers import CategorySerializer

logger = logging.getLogger(__name__)


def classify_topics_list(topics: list[str]) -> list[dict]:
    categories = list(Category.objects.all())
    category_names = [category.name for category in categories]
    prompt = get_prompt("categorize_topics", topics="\n".join(topics), categories="\n".join(category_names))
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
                _, score, index = process.extractOne(raw_category, category_names, scorer=fuzz.token_sort_ratio)
                if score >= 70:
                    category = categories[index]
                    matched_categories.append(category)
                else:
                    logger.error(f"NO CATEGORY MATCH | {line}")
            serialized_categories = CategorySerializer(matched_categories, many=True).data
            results.append(
                {"topic": matched_topic, "categories": serialized_categories if serialized_categories else []}
            )
        except Exception:
            logger.exception(traceback.format_exc())
            continue
    return results


def format_categories_inline():
    categories = Category.objects.all().order_by("name")
    return "\n".join(cat.name for cat in categories)


def categorize_question(question: Question) -> None:
    """
    Categorize a Question instance using ChatGPT.
    - Returns None.
    - If the question has existing categories, they are replaced only if new valid categories are found.
    """
    categories_prompt = format_categories_inline()
    prompt = get_prompt(
        "categorize_question", question=question.statement, answer=question.answer, categories=categories_prompt
    )
    response = ask_chatgpt(prompt, model="gpt-4.1-mini")
    if not response or response.strip().lower() == "none":
        return  # do nothing, keep existing categories

    valid_categories_qs = Category.objects.all()
    valid_category_names = [cat.name for cat in valid_categories_qs]
    valid_category_names_lower = [name.lower() for name in valid_category_names]

    matched_categories = set()
    suggested_categories_raw = [c.strip() for c in response.split(",") if c.strip()]
    for suggested_raw in suggested_categories_raw:
        suggested_lower = suggested_raw.lower()
        matches = get_close_matches(suggested_lower, valid_category_names_lower, n=1, cutoff=0.8)
        if matches:
            matched_index = valid_category_names_lower.index(matches[0])
            matched_categories.add(valid_category_names[matched_index])

    # Only replace categories if we got new matches
    if matched_categories:
        question.categories.set(valid_categories_qs.filter(name__in=matched_categories))
