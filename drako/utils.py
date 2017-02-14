import collections
import re


class delta(object):
    """a delta object to replace datetime.timedelta
    it parses string and does not reducs months to days blindly

    >>> delta('3D')
    <delta [3 days]>

    >>> delta('D')
    <delta [1 day]>

    >>> delta(months=2)
    <delta [2 months]>

    >>> delta('1 month, 2 weeks')
    <delta [1 month 2 weeks]>

    >>> delta('')
    <delta []>

    >>> if not delta(): print("empty delta is False")
    empty delta is False

    >>> delta('3D') + delta('2W')
    <delta [2 weeks 3 days]>

    >>> delta('3 D') * 2
    <delta [6 days]>
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
    UNIT_MAP = collections.OrderedDict((
        # order is important: we want to match plural form before singular,
        # singular before abbreviations
        ("years", "years"),
        ("months", "months"),
        ("weeks", "weeks"),
        ("days", "days"),
        ("hours", "hours"),
        ("minutes", "minutes"),
        ("seconds", "seconds"),
        ("year", "years"),
        ("month", "months"),
        ("week", "weeks"),
        ("day", "days"),
        ("hour", "hours"),
        ("minute", "minutes"),
        ("second", "seconds"),
        ("Y", "years"),
        ("M", "months"),
        ("W", "weeks"),
        ("D", "days"),
        ("h", "hours"),
        ("m", "minutes"),
        ("s", "seconds"),
    ))
    PERIOD_RE = re.compile('(\\d*)\\s*({})'.format('|'.join(UNIT_MAP.keys())))

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

    def __str__(self):
        return ' '.join(
            '{} {}'.format(v, k[:-1] if v <= 1 else k)
            for k, v in self._asdict().items()
        )

    def __repr__(self):
        return '<delta [{}]>'.format(str(self))

    def _asdict(self):
        """similar to collections.namedtuple _asdict() method
        returns delta value ad a collections.OrderedDict
        """
        return collections.OrderedDict(
            (s, getattr(self, s))
            for s in self.__slots__
            if getattr(self, s)
        )

    def __bool__(self):
        return any(getattr(self, s) for s in self.__slots__)

    def __mul__(self, rhs):
        return self.__class__(**{
            s: getattr(self, s) * rhs
            for s in self.__slots__
        })

    def __add__(self, rhs):
        return self.__class__(**{
            s: getattr(self, s) + getattr(rhs, s)
            for s in self.__slots__
        })


def range(arrow, delta, start, end):
    """use our delta for proper range on Arrow objects
    because Arrow is not stable over months boundaries

    >>> import arrow
    >>> jan31 = arrow.get('2017-01-31')

    >>> jan31.range('month', jan31, arrow.get('2017-07-31'))
    ... # doctest: +NORMALIZE_WHITESPACE
    [<Arrow [2017-01-31T00:00:00+00:00]>,
     <Arrow [2017-02-28T00:00:00+00:00]>,
     <Arrow [2017-03-28T00:00:00+00:00]>,
     <Arrow [2017-04-28T00:00:00+00:00]>,
     <Arrow [2017-05-28T00:00:00+00:00]>,
     <Arrow [2017-06-28T00:00:00+00:00]>,
     <Arrow [2017-07-28T00:00:00+00:00]>]

    >>> list(range(jan31, delta('1 M'), jan31, arrow.get('2017-07-31')))
    ... # doctest: +NORMALIZE_WHITESPACE
    [<Arrow [2017-01-31T00:00:00+00:00]>,
     <Arrow [2017-02-28T00:00:00+00:00]>,
     <Arrow [2017-03-31T00:00:00+00:00]>,
     <Arrow [2017-04-30T00:00:00+00:00]>,
     <Arrow [2017-05-31T00:00:00+00:00]>,
     <Arrow [2017-06-30T00:00:00+00:00]>]

    >>> list(range(jan31, delta('2W 3D'), jan31, arrow.get('2017-03-01')))
    ... # doctest: +NORMALIZE_WHITESPACE
    [<Arrow [2017-01-31T00:00:00+00:00]>,
     <Arrow [2017-02-17T00:00:00+00:00]>]
    """
    i = 0
    while True:
        res = arrow.shift(**((delta * i)._asdict()))
        i += 1
        if res < start:
            continue
        if res >= end:
            break
        yield res
