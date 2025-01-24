from django.db.models import Sum
from django.shortcuts import render, get_object_or_404

# Create your views here.
from django.http import HttpResponse

from .models import Ranking, Entry
def index(request):
    args = {}
    args['rankings'] = Ranking.objects.all()
    return render(request, "website/index.html",args)


def ranking_detail(request, rid):
    args = {}
    args['ranking_details'] = get_object_or_404(Ranking, pk=rid)
    args['user_ranking'] = Entry.objects.filter(ranking=rid).values('user').annotate(total_sum=Sum('number')).order_by('-total_sum')
    return render(request, "website/ranking_detail.html", args)