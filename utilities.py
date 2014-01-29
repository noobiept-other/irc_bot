# python 2.7

import datetime

class TimePassed:

    def __init__(self):

        self.initial_time = datetime.datetime.now()

    def getTimePassed(self):

        current = datetime.datetime.now()

        difference = current - self.initial_time

        totalSeconds = difference.total_seconds()
        #HERE have a better string


        return str( difference )




def fromUnicodeToStr( config ):

    """
        twisted doesn't like unicode, so gotta convert everything

        Config is a dictionary where the values is either a string or a list of strings

        #HERE can also be a list of dicts
    """

    for key, value in config.items():

            # we check against basestring to work on str and unicode
        if isinstance( value, basestring ):

            config[ key ] = str( value )

            # its a list otherwise
        else:
            for index, element in enumerate( value ):
                if isinstance( element, basestring ):
                    value[ index ] = str( element )


    return config
