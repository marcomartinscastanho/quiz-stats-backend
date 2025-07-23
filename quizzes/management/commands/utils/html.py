import json
import re

import requests
from bs4 import BeautifulSoup


def fetch_page(url):
    """Fetches the HTML content of the given URL."""
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()  # Raise an error for bad status codes
    response.encoding = "utf-8"
    return response.text


class HtmlException(requests.exceptions.RequestException):
    pass


def parse_html(html):
    """Parses the HTML content using BeautifulSoup."""
    return BeautifulSoup(html, "html.parser", from_encoding="latin-1")


def extract_page_title(soup: BeautifulSoup):
    """Extracts and cleans the page title."""
    title_tag = soup.find("title")
    if not title_tag:
        return ""

    title = title_tag.get_text().strip()
    return title


def find_jf_game(soup: BeautifulSoup):
    whole_json = {}
    excluded_prefixes = {"mvp-global", "mvp-jornada", "temas", "classificação"}
    divs = [
        div
        for div in soup.find_all("div", class_="level3")
        if div.get("id") and not any(div["id"].startswith(prefix) for prefix in excluded_prefixes)
    ]
    for div in divs:
        script_tag = div.find("script", type="application/json")
        if not script_tag:
            continue
        try:
            whole_json = json.loads(script_tag.string)
        except json.JSONDecodeError:
            continue
        try:
            title: str = whole_json["x"]["layout"]["title"]["text"]
        except KeyError:
            continue
        if "José Figueiras" in title:
            return whole_json
    print("Did not find José Figueiras.")
    return whole_json


def extract_quiz_data(soup: BeautifulSoup) -> list[list[dict]]:
    whole_json = find_jf_game(soup)
    if not whole_json:
        print("No matching div with target title found.")
        return []
    try:
        quiz_data = whole_json["x"]["data"]
    except KeyError as e:
        print(f"Error parsing JSON: {e}")
        return []

    parsed_data = []
    for part in quiz_data:
        part_data = []
        if "text" not in part:
            continue
        for row in part["text"]:
            soup_text = BeautifulSoup(row, "html.parser")
            parts = re.split(r"<br\s*/>", str(soup_text))
            if len(parts) < 2:
                continue
            player_tag = parts[0].strip()
            player_soup = BeautifulSoup(player_tag, "html.parser")
            b_tag = player_soup.find("b")
            if b_tag:
                full_name_and_team = b_tag.get_text(strip=True)
                player_name = full_name_and_team.split(" - ")[0]
                team_name = full_name_and_team.split(" - ")[1]
            final_part = parts[-1].strip()
            final_soup = BeautifulSoup(final_part, "html.parser")
            points_tag = final_soup.find("b")

            if points_tag:
                points = points_tag.get_text(strip=True)
            theme_xt_xp = parts[1].strip()
            pattern = re.compile(r"^(.*?)\s*\(xT\s*=\s*([\d.]+),\s*xP\s*=\s*([\d.]+)\)")
            match = pattern.search(theme_xt_xp)
            if match:
                theme = match.group(1).strip()
                # Remove "Parte X " from theme if present
                theme = re.sub(r"^Parte\s\d\s", "", theme).strip()
                xt = float(match.group(2))
                xp = float(match.group(3))
            else:
                continue
            for br in soup_text.find_all("br"):
                br.replace_with(" ")
            # Extract question
            question_tag = soup_text.find("i")
            question = question_tag.get_text() if question_tag else ""
            # Extract answer
            answer_tag = soup_text.find("b", string="Resposta")
            answer = answer_tag.find_next("i").get_text() if answer_tag else ""
            part_data.append(
                {
                    "theme": theme,
                    "xT": xt,
                    "xP": xp,
                    "question": question,
                    "answer": answer,
                    "player": player_name,
                    "team": team_name,
                    "guessed": points == "2",
                }
            )
        parsed_data.append(part_data)
    return parsed_data


def sort_quiz_data(parsed_data: list[list[dict]]):
    """Sorts each part of quiz data alphabetically by theme, except themes starting with 'Mystery Box' come last."""
    for part in parsed_data:
        part.sort(key=lambda x: (x["theme"].startswith("Mystery Box"), x["theme"]))
    return parsed_data


def get_sorted_themes(data: list[dict]):
    return sorted(set(row["theme"] for row in data), key=lambda x: (x.startswith("Mystery Box"), x))
