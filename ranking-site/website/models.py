from django.db import models

# Create your models here.
class TimeStamp(models.Model):
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    class Meta:
        abstract = True

class Ranking(TimeStamp):
    name = models.CharField(max_length = 200, blank = False)
    token = models.CharField(max_length = 20, null = True, blank = True)
    description = models.TextField(blank = True)
    active = models.BooleanField(default = True)
    reverse_sort = models.BooleanField(default = False)

    def __str__(self):
        return self.name

class RankingChannel(TimeStamp):
    ranking = models.ForeignKey(Ranking, on_delete = models.CASCADE)
    channel_id = models.BigIntegerField(blank = False)
    guild_id = models.BigIntegerField(blank = False)

    def __str__(self):
        return (self.ranking.name + " - " + self.channel_id)
    
    class Meta:
        unique_together = ('ranking', 'channel_id')


class Entry(TimeStamp):
    ranking = models.ForeignKey(Ranking, on_delete = models.CASCADE)
    number = models.FloatField(default = 1)
    user = models.BigIntegerField(blank = False)
    message_id = models.BigIntegerField(blank = False, unique = True)

class User(TimeStamp):
    name = models.CharField(max_length = 200, blank = False)
    user = models.BigIntegerField(blank = False)
    ranking = models.ForeignKey(Ranking, on_delete = models.CASCADE)
    guild_id = models.BigIntegerField(blank = False)

    def __str__(self):
        return self.name
    
    class Meta:
        unique_together = ('user', 'ranking', 'guild_id')

class Mapping(TimeStamp):
    ranking = models.ForeignKey(Ranking, on_delete = models.CASCADE)
    string = models.CharField(max_length = 200, blank = False)
    value = models.FloatField(default = 1)

    def __str__(self):
        return self.string
    
    class Meta:
        unique_together = ('ranking', 'string')