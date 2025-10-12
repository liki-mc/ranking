from django.db import models
from django.utils import timezone

from datetime import datetime
from annoying.fields import AutoOneToOneField

from typing import Coroutine

from .rankingsettings import TIMEFRAME

# Create your models here.
class TimeStamp(models.Model):
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    class Meta:
        abstract = True



class Settings(models.Model):
    ranking = AutoOneToOneField(
        "website.Ranking", 
        on_delete = models.CASCADE, 
        primary_key = True
    )
    reverse_sort = models.BooleanField(default = False)
    is_timestamp = models.BooleanField(default = False)
    mean = models.CharField(max_length = 10, choices = TIMEFRAME)
    median = models.CharField(max_length = 10, choices = TIMEFRAME)

class Ranking(TimeStamp):
    name = models.CharField(max_length = 200, blank = False)
    token = models.CharField(max_length = 20, null = True, blank = True)
    description = models.TextField(blank = True)
    active = models.BooleanField(default = True)

    def __str__(self):
        return self.name
    
    @property
    def from_time(self) -> datetime:
        return self.subranking_set.filter(
            models.Q(active_until__isnull = True) | models.Q(active_until__gt = datetime.now()), 
            active_from__lte = datetime.now()
        ).aggregate(models.Min('active_from'))['active_from__min'] or datetime.min

    @property
    def afrom_time(self) -> Coroutine[datetime, None, None]:
        async def coro() -> Coroutine[datetime, None, None]:
            return (await self.subranking_set.filter(
                models.Q(active_until__isnull = True) | models.Q(active_until__gt = datetime.now()), 
                active_from__lte = datetime.now()
            ).aaggregate(models.Min('active_from')))['active_from__min'] or datetime.min
        return coro()

    @property
    def subranking_name(self) -> str:
        try:
            return self.subranking_set.filter(
                models.Q(active_until__isnull = True) | models.Q(active_until__gt = datetime.now()), 
                active_from__lte = datetime.now()
            ).earliest('active_from').name or ""
        except Subranking.DoesNotExist:
            return ""
    
    @property
    def asubranking_name(self) -> Coroutine[str, None, None]:
        async def coro() -> Coroutine[str, None, None]:
            try:
                return (await self.subranking_set.filter(
                    models.Q(active_until__isnull = True) | models.Q(active_until__gt = datetime.now()), 
                    active_from__lte = datetime.now()
                ).aearliest('active_from')).name or ""
            except Subranking.DoesNotExist:
                return ""
        return coro()

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
    message_id = models.BigIntegerField(blank = False)

    def __str__(self):
        return (self.ranking.name + " - " + str(self.number))
    
    class Meta:
        unique_together = ('ranking', 'message_id')

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

class Subranking(TimeStamp):
    ranking = models.ForeignKey(Ranking, on_delete = models.CASCADE)
    name = models.CharField(max_length = 200, blank = False)
    description = models.TextField(blank = True)
    active_from = models.DateTimeField(default = timezone.now)
    active_until = models.DateTimeField(null = True, blank = True)

    def __str__(self):
        return self.name
    
    class Meta:
        pass