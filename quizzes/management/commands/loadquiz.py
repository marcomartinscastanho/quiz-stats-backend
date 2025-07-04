import json

from django.core.management.base import BaseCommand, CommandError

from quizzes.models import Question, Quiz, QuizPart, Topic


class Command(BaseCommand):
    help = "Import quiz data from a JSON file"

    def add_arguments(self, parser):
        parser.add_argument("json_file", type=str, help="Path to the JSON file")

    def handle(self, *args, **options):
        json_file = options["json_file"]
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f"File {json_file} not found.")
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON: {e}")

        # Create or get Quiz
        quiz, created = Quiz.objects.get_or_create(season=data["season"], week=data["week"])
        if created:
            self.stdout.write(f"Created quiz for Season {quiz.season} Week {quiz.week}")
        else:
            self.stdout.write(f"Using existing quiz for Season {quiz.season} Week {quiz.week}")

        # Loop through parts
        for part_data in data.get("parts", []):
            part, created = QuizPart.objects.get_or_create(quiz=quiz, sequence=part_data["sequence"])
            if created:
                self.stdout.write(f"  Created part {part.sequence}")
            else:
                self.stdout.write(f"  Using existing part {part.sequence}")

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
                self.stdout.write(f"    Added question: {question.statement[:30]}...")
        self.stdout.write(self.style.SUCCESS("Quiz import complete!"))
