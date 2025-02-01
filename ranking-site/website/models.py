from django.db import models

# Create your models here.
class Ranking(models.Model):
    name = models.CharField(max_length = 200, blank = False)
    rid = models.AutoField(primary_key = True)
    token = models.CharField(max_length = 200, null = True, blank = True)
    channel = models.IntegerField()
    date = models.DateTimeField("date published", auto_now_add = True)
    active = models.BooleanField(default = True)
    reverse_sorting = models.BooleanField(default = False)
    
    def __str__(self):
        return self.name

class Caffeine_content(models.Model):
    name = models.CharField(max_length = 200, blank = False, primary_key = True)
    caffeine = models.FloatField(default = 0)
    
    def __str__(self):
        return self.name

class User(models.Model):
    uid = models.IntegerField(primary_key = True)
    name = models.CharField(max_length = 200, blank = False)

    def __str__(self):
        return self.name

class Entry(models.Model):
    ranking = models.ForeignKey(Ranking, on_delete = models.CASCADE)
    number = models.FloatField(default = 1)
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    date = models.DateTimeField("date published", auto_now_add = True)
    message_id = models.IntegerField()
    
    def __str__(self):
        return f"{self.user}, {self.number}"
