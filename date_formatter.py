import datetime
from dateutil.relativedelta import relativedelta
import six

import matplotlib.dates as dates

"""
Short module containing a matplotlib date formatter.
"""

def format_microseconds(dt, pos=None, locator=None):
  """String formatting at microseconds resolution.
  Override first tick to display abbreviated date.
  Round microseconds to the nearest thousands to account for
  datetime 64-bit floating point precision issues, assuming
  that current axis is zoomed out sufficiently far (i.e.
  showing more than 1000 microseconds time range).
  """
  microseconds_epsilon = 15
  should_round_microseconds = False
  if locator is not None:
    dmin, dmax = locator.viewlim_to_dt()
    if dmin > dmax:
      dmax, dmin = dmin, dmax
    delta = relativedelta(dmax, dmin)
    if any([delta.years, delta.months, delta.days,
            delta.hours, delta.minutes, delta.seconds]):
      # Date range is at least in seconds
      num_micros = 1e6
    else:
      num_micros = delta.microseconds
    if num_micros > 1000:
      should_round_microseconds = True
  dt = dates.num2date(dt)
  if should_round_microseconds:
    # TODO: maybe snap to a smaller multiple of microseconds
    # than a thousand? With epsilon of 15, maybe even 100 would be okay.
    mus = dt.microsecond % 1000
    if mus < microseconds_epsilon:
      dt -= datetime.timedelta(microseconds=mus)
    elif mus > 1000 - microseconds_epsilon:
      dt += datetime.timedelta(microseconds=(1000 - mus))
  return dt.strftime('%H:%M:%S.%f')

class AutoMicrosecondFormatter(dates.AutoDateFormatter):
  """
  Refer to AutoDateFormatter documentation:
  https://github.com/matplotlib/matplotlib/blob/master/lib/mdates.py
  We adjust the default microsecond tick formatting by rounding.
  """

  def __init__(self, locator=None, tz=None, defaultfmt='%Y-%m-%d'):
    self._auto_locator = dates.AutoDateLocator() if locator is None else locator
    super(AutoMicrosecondFormatter, self).__init__(self._auto_locator, tz, defaultfmt)

    self.scaled = {365.0: '%Y',
                   30.0: '%b %Y',
                   1.0: '%b %d %Y',
                   1. / 24.: '%H:%M:%S',
                   1. / (24. * 60 * 60 * 1000): format_microseconds}

  def __call__(self, x, pos=None):
    """This callback does the same exact thing as the underlying
    matplotlib.dates.AutoDateFormatter class implementation, except
    it also passes the locator to the formatter which is called if
    the formatter is a function. The locator contains information
    such as the current viewing window limit range.
    """
    locator_unit_scale = float(self._locator._get_unit())
    fmt = self.defaultfmt

    # Pick the first scale which is greater than the locator unit.
    for possible_scale in sorted(self.scaled):
        if possible_scale >= locator_unit_scale:
            fmt = self.scaled[possible_scale]
            break

    if isinstance(fmt, six.string_types):
        self._formatter = dates.DateFormatter(fmt, self._tz)
        result = self._formatter(x, pos)
    elif six.callable(fmt):
        result = fmt(x, pos, locator=self._locator)
    else:
        raise TypeError('Unexpected type passed to {!r}.'.formatter(self))

    return result
