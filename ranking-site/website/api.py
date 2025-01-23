"""
URL configuration for ranking project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from django.http import JsonResponse, HttpRequest
from .models import Ranking

from typing import Callable

def error(message: str, status: int) -> JsonResponse:
    return JsonResponse({'error': message}, status = status)

def response_wrapper(
        get: Callable[[HttpRequest, ...], JsonResponse] = None,
        post: Callable[[HttpRequest, ...], JsonResponse] = None,
        put: Callable[[HttpRequest, ...], JsonResponse] = None,
        delete: Callable[[HttpRequest, ...], JsonResponse] = None
) -> Callable[[HttpRequest, ...], JsonResponse]:
    def wrapper(request: HttpRequest, *args, **kwargs) -> JsonResponse:
        match request.method:
            case 'GET':
                if get is None:
                    return error('GET not allowed', 405)
                return get(request, *args, **kwargs)
            case 'POST':
                if post is None:
                    return error('POST not allowed', 405)
                return post(request, *args, **kwargs)
            case 'PUT':
                if put is None:
                    return error('PUT not allowed', 405)
                return put(request, *args, **kwargs)
            case 'DELETE':
                if delete is None:
                    return error('DELETE not allowed', 405)
                return delete(request, *args, **kwargs)
            case _:
                return error('Method not allowed', 405)
    return wrapper

def getRankings(request: HttpRequest) -> JsonResponse:
    print(request)
    data = [
        {
            'name': ranking.name,
            'rid': ranking.rid,
            'character': ranking.character,
            'channel': ranking.channel,
            'date': ranking.date,
        }
        for ranking in Ranking.objects.all()
    ]
    return JsonResponse(data, safe = False)

def getRankingsbyChannel(request: HttpRequest, channel: int) -> JsonResponse:
    data = [
        {
            'name': ranking.name,
            'rid': ranking.rid,
            'character': ranking.character,
            'channel': ranking.channel,
            'date': ranking.date,
        }
        for ranking in Ranking.objects.filter(channel = channel)
    ]
    return JsonResponse(data, safe = False)

def getRanking(request: HttpRequest, rid: int) -> JsonResponse:
    ranking = Ranking.objects.get(rid = rid)
    data = {
        'name': ranking.name,
        'rid': ranking.rid,
        'character': ranking.character,
        'channel': ranking.channel,
        'date': ranking.date,
    }
    return JsonResponse(data, safe = False)

def getRankingsbySearch(request: HttpRequest) -> JsonResponse:
    channel = request.GET.get('channel')
    character = request.GET.get('character')
    data = [
        {
            'name': ranking.name,
            'rid': ranking.rid,
            'character': ranking.character,
            'channel': ranking.channel,
            'date': ranking.date,
        }
        for ranking in Ranking.objects.filter(channel = channel, character = character)
    ]
    return JsonResponse(data, safe = False)

urlpatterns = [
    path('', response_wrapper(
        get = getRankings,
    ), name = 'getRanking'),
    path('channel/<int:channel>/', response_wrapper(
        get = getRankingsbyChannel,
    ), name = 'getRankingsbyChannel'),
    path('rid/<int:rid>/', response_wrapper(
        get = getRanking,
    ), name = 'getRanking'),
    path('search/', response_wrapper(
        get = getRankingsbySearch,
    ), name = 'getRankingsbySearch'),
]