from difflib import SequenceMatcher, get_close_matches
from io import BytesIO

from answers.models import UserAnswer
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from quizzes.models import Question, Quiz, QuizPart, Topic


def is_similar(a: str, b: str, threshold: float = 0.8) -> bool:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() >= threshold


User = get_user_model()


def get_user(player_name: str):
    users = list(User.objects.all())
    full_name_map = {f"{u.first_name} {u.last_name}".strip(): u for u in users}
    full_names = list(full_name_map.keys())
    match = get_close_matches(player_name, full_names, n=1, cutoff=0.7)
    if match:
        matched_name = match[0]
        user = full_name_map[matched_name]
        return user


def create_quiz(quiz_data: dict):
    # Create or get Quiz
    quiz, created = Quiz.objects.get_or_create(season=quiz_data["season"], week=quiz_data["week"])
    print(f"{'Created' if created else 'Using existing'} quiz for Season {quiz.season} Week {quiz.week}")

    # Loop through parts
    for part_data in quiz_data.get("parts", []):
        part, created = QuizPart.objects.get_or_create(quiz=quiz, sequence=part_data["sequence"])
        print(f"{'  Created' if created else '  Using existing'} part {part.sequence}")

        if created:
            ppt = part_data.get("ppt")
            if ppt:
                buffer = BytesIO()
                ppt.save(buffer)
                buffer.seek(0)
                filename = f"quiz_s{quiz.season}_w{quiz.week}_part{part.sequence}.pptx"
                part.ppt_file.save(filename, ContentFile(buffer.read()))
                part.save()
                print(f"    Attached ppt: {filename}")

        for question_data in part_data.get("questions", []):
            # Create Topic
            topic, _ = Topic.objects.get_or_create(title=question_data["theme"], quiz_part=part)

            # Create Question
            question = Question.objects.create(
                topic=topic,
                statement=question_data["question"],
                answer=question_data["answer"],
                is_box=topic.title.startswith("Mystery Box"),
            )
            team_name = question_data["team"]
            if not is_similar(team_name, "José Figueiras"):
                continue
            player_name = question_data["player"]
            if player_name == "Equipa":  # TODO: support for team-answered questions
                continue
            user = get_user(player_name)
            if user:
                is_correct = bool(question_data["guessed"])
                UserAnswer.objects.create(user=user, question=question, is_correct=is_correct)
            print(f"    Added question: {question.statement[:30]}...")
