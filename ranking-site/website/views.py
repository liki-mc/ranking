from django.shortcuts import render, get_object_or_404

# Create your views here.
from django.http import HttpResponse

from .models import Ranking
def index(request):
    args = {}
    args['rankings'] = Ranking.objects.all()
    return render(request, "website/index.html",args)


def ranking_detail(request, rid):
    args = {}
    args['ranking'] = get_object_or_404(Ranking, pk=rid)
    return render(request, "website/ranking_detail.html", args)