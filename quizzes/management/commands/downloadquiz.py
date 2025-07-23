import traceback

from django.core.management.base import BaseCommand, CommandError

from quizzes.management.commands.utils.data_creation import create_quiz
from quizzes.management.commands.utils.html import HtmlException
from quizzes.management.commands.utils.parser import get_quiz_data


class Command(BaseCommand):
    help = "Import quiz data from a JSON file"

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, help="Path to a text file containing one URL per line")
        parser.add_argument("--url", action="append", help="One or more URLs to process (can be repeated)")

    def handle(self, *args, **options):
        urls = []
        if options["file"]:
            file_path = options["file"]
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    urls = [line.strip() for line in f if line.strip()]
                    self.stdout.write(f"Loaded {len(urls)} URLs from file.")
            except FileNotFoundError:
                raise CommandError(f"File not found: {file_path}")

        elif options["url"]:
            urls = options["url"]
            self.stdout.write(f"Processing {len(urls)} URL(s) provided via --url.")

        else:
            raise CommandError("You must provide either --file or --url.")

        for url in urls:
            try:
                self.stdout.write(f"Processing: {url}")
                quiz_data = get_quiz_data(url)
                create_quiz(quiz_data)
            except HtmlException as e:
                self.stderr.write(f"Error fetching page {url}: {e}")
            except Exception as e:
                self.stderr.write(traceback.format_exc())
                self.stderr.write(f"Error processing {url}: {e}")
        self.stdout.write(self.style.SUCCESS("Quiz import complete!"))
