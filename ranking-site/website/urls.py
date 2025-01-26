from django.urls import path

from . import views

app_name = 'website'

urlpatterns = [
    path("", views.index, name="index"),
    path("<int:rid>", views.ranking_detail, name="ranking_detail")
]