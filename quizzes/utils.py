import logging
import traceback

from rapidfuzz import fuzz, process

from openai_utils.client import ask_chatgpt
from openai_utils.loaders import get_prompt
from quizzes.models import Category
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
