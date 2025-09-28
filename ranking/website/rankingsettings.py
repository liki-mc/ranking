from typing import Callable
from datetime import timedelta
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

    class TIMEFRAME(models.TextChoices):
        ALL = "all"
        YEAR = "year"
        MONTH = "month"
        WEEK = "week"
        DAY = "day"
        ENTRY = "entry"
        
        __empty__ = "none"
    