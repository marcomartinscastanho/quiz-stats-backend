from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from answers.models import UserAnswer


class UserCategoryStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, *args, **kwargs):
        user = self.request.user
        # Get UserAnswer queryset for the user, select related question and categories for efficiency
        user_answers = (
            UserAnswer.objects.filter(user=user).select_related("question").prefetch_related("question__categories")
        )
        # Prepare a dict to hold category stats
        category_stats = {}
        # Iterate through user answers, categorize and count correct/total
        for ua in user_answers:
            for category in ua.question.categories.all():
                stats = category_stats.setdefault(category.name, {"correct": 0, "total": 0})
                stats["total"] += 1
                if ua.is_correct:
                    stats["correct"] += 1
        # Format response sorted by xC value descending
        response = sorted(
            [
                {
                    "category_name": name,
                    "xC": round((data["correct"] / data["total"]) * 2, 1),
                    "answered": data["total"],
                }
                for name, data in category_stats.items()
            ],
            key=lambda x: x["xC"],
            reverse=True,
        )
        return Response(response)
