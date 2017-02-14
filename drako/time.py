import collections
import datetime
import re


class delta(object):
    """a delta object to replace datetime.timedelta
    it parses string and does not reducs months to days blindly
    """
    __slots__ = (
        "years",
        "months",
        "weeks",
        "days",
        "hours",
        "minutes",
        "seconds",
    )
    PERIOD_RE = re.compile(r'(\d*)\s*(Y|M|W|D|h|m|s)')
    UNIT_MAP = {
        "Y": "years",
        "M": "months",
        "W": "weeks",
        "D": "days",
        "h": "hours",
        "m": "minutes",
        "s": "seconds",
    }

    def __init__(self, string=None, **kwargs):
        for k in self.__slots__:
            setattr(self, k, 0)
        if string:
            kwargs.update({
                self.UNIT_MAP[unit]: int(count or 1)
                for count, unit in self.PERIOD_RE.findall(string)
            })
        for unit, count in kwargs.items():
            setattr(self, unit, count)

    def __repr__(self):
        return '<delta : {}>'.format(
            ' '.join('{} {}'.format(v, k) for k, v in self._asdict().items())
            )

    def __bool__(self):
        return any(getattr(self, s) for s in self.__slots__)

    def _asdict(self):
        return {
            s: getattr(self, s)
            for s in self.__slots__
            if getattr(self, s)
        }

    def __mul__(self, rhs):
        return Period(**{
            s: getattr(self, s) * rhs
            for s in self.__slots__
        })


def range(arrow, delta, start, end):
    """use our Period for proper range on Arrow objects
    because Arrow does not respect months boundaries
    """
    i = 1
    while True:
        res = arrow.shift(**((delta * i)._asdict()))
        i += 1
        if res >= end:
            break
        yield res
