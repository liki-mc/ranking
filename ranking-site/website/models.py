from django.db import models

# Create your models here.
class Ranking(models.Model):
    name = models.CharField(max_length = 200)
    rid = models.IntegerField(primary_key = True)
    character = models.CharField(max_length = 200)
    channel = models.IntegerField()
    date = models.DateTimeField("date published", auto_now_add = True)
    
    def __str__(self):
        return self.name

class Entry(models.Model):
    ranking = models.ForeignKey(Ranking, on_delete = models.CASCADE)
    number = models.IntegerField()
    user = models.IntegerField()
    date = models.DateTimeField("date published", auto_now_add = True)
    
    def __str__(self):
        return f"{self.user}, {self.number}"