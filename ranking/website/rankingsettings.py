from __future__ import annotations

from typing import Callable, TYPE_CHECKING
from datetime import timedelta, datetime
import re

class TimeStampParsing:
    @staticmethod
    def year_func(number: int) -> timedelta:
        return timedelta(days = number * 365)
    
    @staticmethod
    def week_func(number: int) -> timedelta:
        return timedelta(weeks = number)
    
    @staticmethod
    def day_func(number: int) -> timedelta:
        return timedelta(days = number)
    
    @staticmethod
    def hour_func(number: int) -> timedelta:
        return timedelta(hours = number)
    
    @staticmethod
    def minute_func(number: int) -> timedelta:
        return timedelta(minutes = number)
    
    @staticmethod
    def second_func(number: int) -> timedelta:
        return timedelta(seconds = number)
    
    values: list[tuple[list[str], Callable[[int], timedelta]]] = [
        (["Y", "J"], year_func),
        (["W"], week_func),
        (["D"], day_func),
        (["u", "h"], hour_func),
        (["m"], minute_func),
        (["s"], second_func),
    ]

    regex = r"([+-]) ?" + "".join([rf"((?:\d+[{''.join(letters)}])?)" for (letters, _) in values]) + r"((?:\d+)?)"

    @classmethod
    def parse_match(cls, value: re.Match) -> timedelta:
        last_i = -1
        s = timedelta()
        groups = value.groups()
        sign = 1 if groups[0] == "+" else -1
        for i, (v, (letters, func)) in enumerate(zip(groups[1:-1], cls.values)):
            if v and v[-1] in letters:
                last_i = i
                s += func(int(v[:-1]))
        
        if groups[-1]:
            if last_i == -1:
                raise ValueError("Invalid timestamp format")
            
            s += cls.values[last_i + 1  ][1](int(groups[-1]))
        
        return s * sign
    
    @classmethod
    def parse(cls, value: str) -> list[timedelta]:
        values = []
        for match in re.finditer(cls.regex, value):
            try:
                values.append(cls.parse_match(match))
            except ValueError:
                pass
        
        return values

if __name__ == "__main__":
    def test_timestamp_parsing():
        print(TimeStampParsing.regex)
        TESTS = [
            "1Y2W3D4h5m6s",
            "1J2W3D4h5m6s",
            "1Y2W3D4u5m6s",
            "1Y2W3D4h5m6 ",
            "4u5m6s",
            "5m6s",
            "6s",
            "4u23",
            "23m",
            "23m12",
            "12",
        ]
        SIGNS = [
            "-",
            "-",
            "+",
            "+",
            "+",
            "+",
            "-",
            "+",
            "+",
            "+",
            "-",
        ]
        VALUES = [
            timedelta(days = 365 + 2*7 + 3, hours = 4, minutes = 5, seconds = 6),
            timedelta(days = 365 + 2*7 + 3, hours = 4, minutes = 5, seconds = 6),
            timedelta(days = 365 + 2*7 + 3, hours = 4, minutes = 5, seconds = 6),
            timedelta(days = 365 + 2*7 + 3, hours = 4, minutes = 5, seconds = 6),
            timedelta(hours = 4, minutes = 5, seconds = 6),
            timedelta(minutes = 5, seconds = 6),
            timedelta(seconds = 6),
            timedelta(hours = 4, minutes = 23),
            timedelta(minutes = 23),
            timedelta(minutes = 23, seconds = 12),
            ValueError("Invalid timestamp format"),
        ]
        for test in TESTS:
            match = re.match(TimeStampParsing.regex, test)
            if match:
                print(f"{test} -> Matched: {match.groups()}")
            else:
                print(f"{test} -> No match")
        
        message_string = "".join(f"{sign} {test} " for sign, test in zip(SIGNS, TESTS))
        for match, test, sign, value in zip(re.finditer(TimeStampParsing.regex, message_string), TESTS, SIGNS, VALUES):
            print(f"Testing '{test}' in '{message_string}'")
            if isinstance(value, Exception):
                try:
                    result = TimeStampParsing.parse_match(match)
                    print(f"Expected exception {value}, but got result {result}")
                except Exception as e:
                    assert isinstance(e, type(value)) and str(e) == str(value), f"Expected exception {value}, but got {e}"
                    print(f"Correctly raised exception: {e}")
            else:
                result = TimeStampParsing.parse_match(match)
                expected = value if sign == "+" else -value
                assert result == expected, f"Expected {expected}, but got {result}"
                print(f"Parsed '{test}' as {result}, expected {expected}")
        
        print(f"Parsing string '{message_string}'")
        for result, sign, value in zip(TimeStampParsing.parse(message_string), SIGNS, [VALUES[i] for i in range(len(VALUES)) if not isinstance(VALUES[i], Exception)]):
            expected = value if sign == "+" else -value
            assert result == expected, f"Expected {expected}, but got {result}"
            print(f"○ {result}, expected {expected}")

    
    test_timestamp_parsing()

else:
    # django raises stupid errors if this is not in a module and settings aren't loaded or sum
    from django.db import models
    from asgiref.sync import sync_to_async
    if TYPE_CHECKING:
        from website.models import Entry, Ranking, Settings
        from typing import Coroutine
        import logging

    class TIMEFRAME(models.TextChoices):
        ALL = "all"
        YEAR = "year"
        MONTH = "month"
        WEEK = "week"
        DAY = "day"
        ENTRY = "entry"
        
        __empty__ = "none"
    
    class TimeFrameDisplay:
        funcs: dict[TIMEFRAME, callable[[datetime], datetime]] = {
            TIMEFRAME.ALL: lambda x: x,
            TIMEFRAME.YEAR: models.functions.TruncYear,
            TIMEFRAME.MONTH: models.functions.TruncMonth,
            TIMEFRAME.WEEK: models.functions.TruncWeek,
            TIMEFRAME.DAY: models.functions.TruncDay,
            TIMEFRAME.ENTRY: lambda x: x,
        }

        @classmethod
        async def parse_mean(cls, objects: models.BaseManager[Entry], settings: Settings, ranking: Ranking, users: list[int], logger: logging.Logger) -> Coroutine[dict[int, float]]:
            logger.info("Parsing timeframe mean")
            # return_value = objects.filter(
            #     ranking_id = ranking.id,
            #     user__in = users,
            #     created_at__gte = ranking.from_time
            # ).annotate(
            #     timeframe_mean = cls.funcs[settings.mean](models.F("created_at"))
            # ).values(
            #     "timeframe_mean", "user"
            # ).annotate(
            #     timeframe_value = models.Sum("score")
            # ).values(
            #     "user"
            # ).annotate(
            #     mean = models.Avg("timeframe_value")
            # ).order_by(
            #     "-mean"
            # )
            from_time: datetime = await ranking.afrom_time
            a = objects.filter(
                ranking_id = ranking.id,
                user__in = users,
                created_at__gte = from_time
            )
            logger.info(f"Filtered entries: {a.query}")
            b = a.annotate(
                timeframe_mean = cls.funcs[settings.mean](models.F("created_at"))
            )
            logger.info(f"Annotated timeframe_mean: {b.query}")
            c = b.values(
                "timeframe_mean", "user"
            )
            logger.info(f"Intermediate values: {await sync_to_async(list)(c)}")
            logger.info(f"Values selected: {c.query}")
            d = c.annotate(
                timeframe_value = models.Sum("number")
            )
            logger.info(f"Annotated timeframe_values: {await sync_to_async(list)(d)}")
            logger.info(f"Annotated timeframe_value: {d.query}")
            # e = d.values(
            #     "user"
            # )
            # logger.info(f"Values selected: {e.query}")
            # values = await sync_to_async(list)(e)
            # logger.info(f"Intermediate values: {values}")
            # return_value = e.annotate(
            #     mean = models.Avg("timeframe_value")
            # ).order_by(
            #     "-mean"
            # )
            # logger.info(f"Final query: {return_value.query}")
            entries = await sync_to_async(list)(d)

            def user_values(user):
                score = 0
                last_updated = datetime.min.replace(tzinfo = from_time.tzinfo)
                for entry in entries:
                    if entry["user"] == user:
                        if entry["timeframe_mean"] > last_updated:
                            last_updated = entry["timeframe_mean"]
                        
                        score += entry["timeframe_value"]
                
                return {
                    "score": score,
                    "last_updated": last_updated,
                }
            return {
                user : user_values(user) for user in users
            }
    