import re

from quizzes.management.commands.utils.html import (
    extract_page_title,
    extract_quiz_data,
    fetch_page,
    get_sorted_themes,
    parse_html,
    sort_quiz_data,
)
from quizzes.management.commands.utils.ppt import create_ppt


def extract_season_week(url):
    match = re.search(r"QNpt(\d+)[_-]([^.?#]+)", url)
    if not match:
        raise ValueError(f"Could not extract season and week from: {url}")
    season = int(match.group(1))
    raw_week = match.group(2)
    # If week starts with 'I's (e.g., "II3"), strip them off
    week = re.sub(r"^I+", "", raw_week)
    # If week starts with a letter and is not numeric, replace leading non-digit with 'G'
    if re.match(r"^\D\d", week):
        week = "G" + week[1:]
    return season, week


def get_quiz_data(url: str):
    html_content = fetch_page(url)
    soup = parse_html(html_content)
    page_title = extract_page_title(soup)
    quiz_data = extract_quiz_data(soup)
    sorted_data = sort_quiz_data(quiz_data)
    season, week = extract_season_week(url)
    quiz = {"season": season, "week": week}
    parts = []
    for i, part_data in enumerate(sorted_data, 1):
        ppt_filename = f"{page_title} - Parte {i}"
        themes = [theme for theme in get_sorted_themes(part_data) if not theme.startswith("Mystery Box")]
        ppt = create_ppt(part_data, ppt_filename)
        parts.append({"sequence": i, "themes": themes, "questions": part_data, "ppt": ppt})
    quiz["parts"] = parts
    return quiz
