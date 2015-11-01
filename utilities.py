import datetime


class TimePassed:

    def __init__(self):
        self.initial_time = datetime.datetime.now()


    def getTimePassed(self):
        current = datetime.datetime.now()

        difference = current - self.initial_time

        totalSeconds = difference.total_seconds()

        return get_time_string( totalSeconds )


def get_time_string( totalSeconds ):
    """
        Converts seconds to days/hours/minutes/seconds

    :param totalSeconds: int
    :return: str
    """
    try:
        totalSeconds = int( totalSeconds )

    except ValueError:
        return totalSeconds


        # we work in seconds
    minute = 60
    hour = 60 * minute
    day = 24 * hour

    minuteCount = 0
    hourCount = 0
    dayCount = 0

        # count the days
    while totalSeconds >= day:
        dayCount += 1
        totalSeconds -= day

        # count the hours
    while totalSeconds >= hour:
        hourCount += 1
        totalSeconds -= hour

        # count the minutes
    while totalSeconds >= minute:
        minuteCount += 1
        totalSeconds -= minute

    secondCount = int( round( totalSeconds, 0 ) )

    def addUnit( dateStr, value, unit ):

        if value != 0:
            if value > 1:
                unit += 's'

                # first unit we add, don't need to add a space between the previous date string
            if dateStr == '':
                return '{} {}'.format( value, unit )

            else:
                return '{} {} {}'.format( dateStr, value, unit )

        else:
            return dateStr


    time = addUnit( '', dayCount, 'day' )
    time = addUnit( time, hourCount, 'hour' )
    time = addUnit( time, minuteCount, 'minute' )
    time = addUnit( time, secondCount, 'second' )

    return time