from __future__ import annotations

from . import models
from django.db import models as djmodels
from asgiref.sync import sync_to_async

from datetime import datetime, timezone

from typing import Coroutine, TYPE_CHECKING, Callable
from .rankingsettings import TIMEFRAME

if TYPE_CHECKING:
    import logging

######
# Utility functions
######
def _user_values(user: int, entries: list[dict], from_time: datetime, func: Callable[[list[int]], float] = sum, logger: logging.Logger = None) -> dict:
    scores = []
    last_updated = datetime.min.replace(tzinfo = from_time.tzinfo or timezone.utc)
    logger.info(f"Value for last updated tzinfo: {last_updated.tzinfo}, from_time tzinfo: {from_time.tzinfo}")
    for entry in entries:
        if entry["user"] == user:
            logger and logger.debug(f"Entry for user {user}: {entry}")
            logger and logger.debug(f"Comparing {entry['last_updated']} to {last_updated} with tzinfo {entry['last_updated'].tzinfo} and {last_updated.tzinfo}")
            if entry["last_updated"] > last_updated:
                last_updated = entry["last_updated"]
            
            scores.append(entry["score"])
    
    return {
        "scores": scores,
        "score": func(scores),
        "last_updated": last_updated,
    }

def get_values_per_timeframe(ranking_id: models.Ranking, users: list[int], from_time: int, func: Callable | None):
    filtered_query = models.Entry.objects.filter(
        ranking_id = ranking_id,
        user__in = users,
        created_at__gte = from_time
    )
    if func:
        return filtered_query.annotate(
            last_updated = func(djmodels.F("created_at"))
        ).values(
            "last_updated", "user"
        ).annotate(
            score = djmodels.Sum("number")
        )
    else:
        return filtered_query.values(
            "user",
            "created_at"
        ).annotate(
            score = djmodels.Sum("number"),
            last_updated = djmodels.Max("created_at")
        )

funcs: dict[TIMEFRAME, callable[[datetime], datetime]] = {
    TIMEFRAME.YEAR: djmodels.functions.TruncYear,
    TIMEFRAME.MONTH: djmodels.functions.TruncMonth,
    TIMEFRAME.WEEK: djmodels.functions.TruncWeek,
    TIMEFRAME.DAY: djmodels.functions.TruncDay,
}

#######
# Parsing functions
#######
async def parse_sum(ranking: models.Ranking, users: list[int], logger: logging.Logger) -> Coroutine[dict[int, float]]:
    from_time = await ranking.afrom_time
    queryset = get_values_per_timeframe(ranking.id, users, from_time, None)
    values = await sync_to_async(list)(queryset)
    logger.info(f"Entries fetched: {values}")
    return {
        user: _user_values(user, values, from_time, sum, logger) for user in users
    }

async def parse_mean(ranking: models.Ranking, users: list[int], mean_timeframe: TIMEFRAME, logger: logging.Logger) -> Coroutine[dict[int, float]]:
    logger.info("Parsing timeframe mean")
    from_time: datetime = await ranking.afrom_time
    queryset = get_values_per_timeframe(ranking.id, users, from_time, funcs.get(mean_timeframe))
    values = await sync_to_async(list)(queryset)
    logger.info(f"Entries fetched: {values}")
    return {
        user: _user_values(user, values, from_time, lambda s: sum(s) / (len(s) or 1), logger) for user in users
    }