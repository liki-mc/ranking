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
from django.urls import include, path
from django.http import JsonResponse, HttpRequest
from .models import Ranking, Entry
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError

from django.views.decorators.csrf import csrf_exempt

from typing import Callable, Any

def error(message: str, status: int) -> JsonResponse:
    return JsonResponse({'error': message}, status = status)

def response_wrapper(
        get: Callable[[HttpRequest, Any], JsonResponse] = None,
        post: Callable[[HttpRequest, Any], JsonResponse] = None,
        put: Callable[[HttpRequest, Any], JsonResponse] = None,
        delete: Callable[[HttpRequest, Any], JsonResponse] = None
) -> Callable[[HttpRequest, Any], JsonResponse]:
    # post = csrf_exempt(post) if post is not None else None
    # put = csrf_exempt(put) if put is not None else None
    # delete = csrf_exempt(delete) if delete is not None else None

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

serialize_ranking: Callable[[Ranking], dict[str, Any]] = lambda ranking : {"name": ranking.name, "rid": ranking.rid, "character": ranking.character, "channel": ranking.channel, "date": ranking.date}
serialize_rankings: Callable[[list[Ranking]], list[dict[str, Any]]] = lambda rankings : [{"name": ranking.name, "rid": ranking.rid, "character": ranking.character, "channel": ranking.channel, "date": ranking.date} for ranking in rankings]

serialize_entry: Callable[[Entry], dict[str, Any]] = lambda entry: {"ranking": serialize_ranking(entry.ranking), "number": entry.number, "user": entry.user, "date": entry.date, "id": entry.id, "message_id": entry.message_id}
serialize_entries: Callable[[list[Entry]], list[dict[str, Any]]] = lambda entries: [{"number": entry.number, "user": entry.user, "date": entry.date, "id": entry.id, "message_id": entry.message_id} for entry in entries]

def get_rankings(request: HttpRequest) -> JsonResponse:
    print(request)
    data = serialize_rankings(Ranking.objects.all())

    if not data:
        return error('Ranking not found', 404)
    
    return JsonResponse(data, safe = False)

def get_rankings_by_channel(request: HttpRequest, channel: int) -> JsonResponse:
    data = serialize_rankings(Ranking.objects.filter(channel = channel))

    if not data:
        return error('Ranking not found', 404)
    
    return JsonResponse(data, safe = False)

def get_ranking(request: HttpRequest, rid: int) -> JsonResponse:
    data = serialize_ranking(Ranking.objects.get(rid = rid))

    if not data:
        return error('Ranking not found', 404)
    
    return JsonResponse(data, safe = False)

def get_rankings_by_search(request: HttpRequest) -> JsonResponse:
    channel = request.GET.get('channel')
    character = request.GET.get('character')
    data = serialize_rankings(Ranking.objects.filter(channel = channel, character = character))

    if not data:
        return error('Ranking not found', 404)

    return JsonResponse(data, safe = False)

def create_ranking(request: HttpRequest) -> JsonResponse:
    if request.content_type == 'application/json':
        try:
            body = json.loads(request.body)
            
            # check if ranking already exists and is active
            possible_ranking = Ranking.objects.filter(character = body['character'], channel = body['channel'], active = True)
            if possible_ranking.exists():
                return error('Ranking already exists and is active', 409)
            
            ranking = Ranking.objects.create(
                name = body['name'],
                character = body['character'],
                channel = body['channel']
            )
            data = serialize_ranking(ranking)
            return JsonResponse(data, safe = False, status = 201)
        
        except json.JSONDecodeError:
            return error('Invalid JSON', 400)
        
        except IntegrityError as e:
            return error("Internal server error", 500)
        
        except ValidationError as e:
            return error(e.message_dict, 400)
        
        except KeyError as e:
            return error(f"Missing field {e}", 400)
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
            
            # check if a ranking already exists for this channel and token and is active
            possible_ranking = Ranking.objects.filter(character = ranking.character, channel = ranking.channel, active = True)
            if possible_ranking.exists():
                if possible_ranking.first().rid != ranking.rid:
                    return error('Ranking already exists and is active', 409)
                
            ranking.active = body.get('active', ranking.active)
            ranking.save()
            data = serialize_ranking(ranking)
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

def deactivate_ranking(request: HttpRequest, rid: int) -> JsonResponse:
    try:
        ranking = Ranking.objects.get(rid = rid)
        ranking.active = False
        ranking.save()
        return JsonResponse({}, status = 204)
    
    except Ranking.DoesNotExist:
        return error('Ranking not found', 404)

def get_entries(request: HttpRequest, rid: int) -> JsonResponse:
    try:
        ranking = Ranking.objects.get(rid = rid)

    except Ranking.DoesNotExist:
        return error('Ranking not found', 404)
    
    data = serialize_entries(Entry.objects.filter(ranking = ranking))
    
    return JsonResponse(data, safe = False)

def get_entries_by_user(request: HttpRequest, rid: int, user: int) -> JsonResponse:
    try:
        ranking = Ranking.objects.get(rid = rid)
    
    except Ranking.DoesNotExist:
        return error('Ranking not found', 404)
    
    data = serialize_entries(Entry.objects.filter(ranking = ranking, user = user))

    return JsonResponse(data, safe = False)

def get_entry(request: HttpRequest, rid: int, eid: int) -> JsonResponse:
    try:
        entry = serialize_entry(Entry.objects.get(ranking__rid = rid, id = eid))

    except Entry.DoesNotExist:
        return error('Entry not found', 404)
    
    return JsonResponse(entry, safe = False)

def create_entry(request: HttpRequest, rid: int) -> JsonResponse:
    if request.content_type == 'application/json':
        try:
            body = json.loads(request.body)
            ranking = Ranking.objects.get(rid = rid)

            if not ranking.active:
                return error('Ranking is not active', 403)
            
            entry = Entry.objects.create(
                ranking = ranking,
                number = body['number'],
                user = body['user'],
                message_id = body['message_id']
            )
            data = serialize_entry(entry)
            return JsonResponse(data, safe = False, status = 201)
        
        except json.JSONDecodeError:
            return error('Invalid JSON', 400)
        
        except IntegrityError as e:
            print(e)
            return error("Internal server error", 500)
        
        except ValidationError as e:
            return error(e.message_dict, 400)
        
        except KeyError as e:
            return error(f"Missing field {e}", 400)
    else:
        return error("Content-Type must be application/json", 400)

def update_entry(request: HttpRequest, rid: int, eid: int) -> JsonResponse:
    if request.content_type == 'application/json':
        try:
            body = json.loads(request.body)
            entry = Entry.objects.get(ranking__rid = rid, id = eid)
            if not entry.ranking.active:
                return error('Ranking is not active', 403)
            
            entry.number = body.get('number', entry.number)
            entry.user = body.get('user', entry.user)
            entry.save()
            data = serialize_entry(entry)
            return JsonResponse(data, safe = False)
        
        except json.JSONDecodeError:
            return error('Invalid JSON', 400)
        
        except Entry.DoesNotExist:
            return error('Entry not found', 404)
        
        except IntegrityError as e:
            return error("Internal server error", 500)
        
        except ValidationError as e:
            return error(e.message_dict, 400)
    else:
        return error("Content-Type must be application/json", 400)
    
def delete_entry(request: HttpRequest, rid: int, eid: int) -> JsonResponse:
    try:
        entry = Entry.objects.get(ranking__rid = rid, id = eid)
        if not entry.ranking.active:
            return error('Ranking is not active', 403)
        
        entry.delete()
        return JsonResponse({}, status = 204)
    except Entry.DoesNotExist:
        return error('Entry not found', 404)


entry_urls = [
    path('', response_wrapper(
        get = get_entries,
        post = create_entry,
    ), name = 'Entries'),
    path('user/<int:user>/', response_wrapper(
        get = get_entries_by_user,
    ), name = 'Entries by User'),
    path('eid/<int:eid>/', response_wrapper(
        get = get_entry,
        put = update_entry,
        delete = delete_entry,
    ), name = 'Entry by rid'),
]

urlpatterns = [
    path('', response_wrapper(
        get = get_rankings,
        post = create_ranking,
    ), name = 'Rankings'),
    path('channel/<int:channel>/', response_wrapper(
        get = get_rankings_by_channel,
    ), name = 'Ranking by Channel'),
    path('<int:rid>/', response_wrapper(
        get = get_ranking,
        put = update_ranking,
        delete = delete_ranking,
    ), name = 'Ranking by RID'),
    path('<int:rid>/deactivate/', response_wrapper(
        post = deactivate_ranking,
    ), name = 'Deactivate Ranking'),
    path('search/', response_wrapper(
        get = get_rankings_by_search,
    ), name = 'Ranking by Search'),
    path('<int:rid>/entries/', include(entry_urls)),
]