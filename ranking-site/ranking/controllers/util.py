from django.http import HttpResponse, HttpRequest, JsonResponse
from django.shortcuts import render

Response = HttpResponse | JsonResponse

def respond(
    request: HttpRequest,
    get: function[HttpRequest, tuple[dict, int, str]] = None,
    post: function[HttpRequest, tuple[dict, int, str]] = None,
    put: function[HttpRequest, tuple[dict, int, str]] = None,
    delete: function[HttpRequest, tuple[dict, int, str]] = None,
) -> Response:
    """
    Respond to a request with the appropriate method.
    """
    token = request.session.get("token")

    response: tuple[dict, int, str] = ({"error": "Internal server error"}, 500, "error.html")
    match request.method:
        case "GET":
            if get is not None:
                response = get(request)
            else:
                response = ({"error": "GET method not allowed"}, 405, "error.html")
            
        case "POST":
            if post is not None:
                response = post(request)
            else:
                response = ({"error": "POST method not allowed"}, 405, "error.html")

        case "PUT":
            if put is not None:
                response = put(request)
            else:
                response = ({"error": "PUT method not allowed"}, 405, "error.html")
        
        case "DELETE":
            if delete is not None:
                response = delete(request)
            else:
                response = ({"error": "DELETE method not allowed"}, 405, "error.html")
        
        case _:
            response = ({"error": "Method not allowed"}, 405, "error.html")
        
    context, status, template_name = response
    if request.accepts("text/html"):
        return render(
            request, 
            template_name, 
            context,
            content_type = "text/html; charset=utf-8",
            status = status,
        )
    
    if request.accepts("application/json"):
        return JsonResponse(
            context,
            status = status,
            content_type = "application/json; charset=utf-8",
        )

    return HttpResponse(
        content = "Unsupported media type",
        content_type = "text/plain; charset=utf-8",
        status = 415,
    )
