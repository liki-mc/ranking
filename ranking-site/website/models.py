from django.db import models

# Create your models here.
class Ranking(models.Model):
    name = models.CharField(max_length = 200, blank = False)
    rid = models.AutoField(primary_key = True)
    character = models.CharField(max_length = 200, default = "+")
    channel = models.IntegerField()
    date = models.DateTimeField("date published", auto_now_add = True)
    active = models.BooleanField(default = True)
    
    def __str__(self):
        return self.name

class Entry(models.Model):
    ranking = models.ForeignKey(Ranking, on_delete = models.CASCADE)
    number = models.FloatField(default = 1)
    user = models.IntegerField(blank = False)
    date = models.DateTimeField("date published", auto_now_add = True)
    message_id = models.IntegerField()
    
    def __str__(self):
        return f"{self.user}, {self.number}"