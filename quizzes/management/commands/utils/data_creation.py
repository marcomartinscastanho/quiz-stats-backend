from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile

from answers.models import UserAnswer
from quizzes.models import Question, Quiz, QuizPart, Topic

User = get_user_model()


def name_to_username(name: str):
    parts = name.strip().lower().split()
    if len(parts) < 2:
        raise ValueError("Name must contain at least two parts")

    initials = "".join(word[0] for word in parts[:-1])  # all but last
    last_name = parts[-1]
    return f"{initials}{last_name}"


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
            # FIXME: only create the question if it doesn't exist yet

            player_name = question_data["player"]
            if player_name == "Equipa":  # TODO: support for team-answered questions
                continue
            username = name_to_username(player_name)
            is_correct = bool(question_data["guessed"])
            print("username", username)
            try:
                user = User.objects.get(username=username)
                # Create UserAnswer
                UserAnswer.objects.create(user=user, question=question, is_correct=is_correct)
            except User.DoesNotExist:
                pass

            print(f"    Added question: {question.statement[:30]}...")
