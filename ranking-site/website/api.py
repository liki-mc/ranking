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
import json
from django.urls import path
from django.http import JsonResponse, HttpRequest
from .models import Ranking
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError

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

def get_rankings(request: HttpRequest) -> JsonResponse:
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

def get_rankings_by_channel(request: HttpRequest, channel: int) -> JsonResponse:
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

def get_ranking(request: HttpRequest, rid: int) -> JsonResponse:
    ranking = Ranking.objects.get(rid = rid)
    data = {
        'name': ranking.name,
        'rid': ranking.rid,
        'character': ranking.character,
        'channel': ranking.channel,
        'date': ranking.date,
    }
    return JsonResponse(data, safe = False)

def get_rankings_by_search(request: HttpRequest) -> JsonResponse:
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

def create_ranking(request: HttpRequest) -> JsonResponse:
    if request.content_type == 'application/json':
        try:
            body = json.loads(request.body)
            ranking = Ranking.objects.create(
                name = body['name'],
                character = body['character'],
                channel = body['channel']
            )
            data = {
                'name': ranking.name,
                'rid': ranking.rid,
                'character': ranking.character,
                'channel': ranking.channel,
                'date': ranking.date,
            }
            return JsonResponse(data, safe = False, status = 201)
        except json.JSONDecodeError:
            return error('Invalid JSON', 400)
        except IntegrityError as e:
            return error("Internal server error", 500)
        except ValidationError as e:
            return error(e.message_dict, 400)
    else:
        return error("Content-Type must be application/json", 400)

def update_ranking(request: HttpRequest, rid: int) -> JsonResponse:
    if request.content_type == 'application/json':
        try:
            body = json.loads(request.body)
            ranking = Ranking.objects.get(rid = rid)
            ranking.name = body.get('name', ranking.name)
            ranking.character = body.get('character', ranking.character)
            ranking.channel = body.get('channel', ranking.channel)
            ranking.save()
            data = {
                'name': ranking.name,
                'rid': ranking.rid,
                'character': ranking.character,
                'channel': ranking.channel,
                'date': ranking.date,
            }
            return JsonResponse(data, safe = False)
        except json.JSONDecodeError:
            return error('Invalid JSON', 400)
        except Ranking.DoesNotExist:
            return error('Ranking not found', 404)
        except IntegrityError as e:
            return error("Internal server error", 500)
        except ValidationError as e:
            return error(e.message_dict, 400)
    else:
        return error("Content-Type must be application/json", 400)

def delete_ranking(request: HttpRequest, rid: int) -> JsonResponse:
    try:
        ranking = Ranking.objects.get(rid = rid)
        ranking.delete()
        return JsonResponse({}, status = 204)
    except Ranking.DoesNotExist:
        return error('Ranking not found', 404)

urlpatterns = [
    path('', response_wrapper(
        get = get_rankings,
        post = create_ranking,
    ), name = 'Rankings'),
    path('channel/<int:channel>/', response_wrapper(
        get = get_rankings_by_channel,
    ), name = 'Ranking by Channel'),
    path('rid/<int:rid>/', response_wrapper(
        get = get_ranking,
        put = update_ranking,
        delete = delete_ranking,
    ), name = 'Ranking by RID'),
    path('search/', response_wrapper(
        get = get_rankings_by_search,
    ), name = 'Ranking by Search'),
]