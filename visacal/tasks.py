from django.http import JsonResponse

from .api import CalApi
from .models import CalUser


def refresh_all_users(request):
    for user in CalUser.objects.all():
        cal = CalApi(user)
        cal.refresh_cards()
        for card in user.calcard_set.filter(is_effective=True):
            cal.get_expenses(card)

    return JsonResponse({"message": "ok"})
