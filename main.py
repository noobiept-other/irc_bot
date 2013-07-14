# python2.7

import sys

from twisted.words.protocols import irc
from twisted.internet import protocol
from twisted.internet.task import LoopingCall
from twisted.internet import reactor


class Bot( irc.IRCClient ):

    def _get_nickname( self ):
        return self.factory.nickname

    nickname = property( _get_nickname )


    def signedOn( self ):

        self.join( self.factory.channel )

        print 'Signed on as {}'.format( self.nickname )



    def joined( self, channel ):

        print 'Joined {}'.format( channel )

        self.count_occurrences = 0
        self.word_to_count = 'something'

        LoopingCall( self.printOccurrencesPerMinute ).start( 10, now= False )


    def privmsg( self, user, channel, message ):
        """
            This is called when the bot receives a message
        """

        print message

        if not user:
            return

            # private message to the bot
        if channel == self.nickname:
            self.msg( self.factory.channel, 'hello there' )


        if self.nickname in message:
            self.msg( self.factory.channel, message )

        self.count_occurrences += message.count( self.word_to_count )




    def printOccurrencesPerMinute( self ):

        self.msg( self.factory.channel, '{} Per Minute: {}'.format( self.word_to_count, self.count_occurrences ) )

        self.count_occurrences = 0



class BotFactory( protocol.ClientFactory ):

    protocol = Bot

    def __init__( self, channel, nickname= 'bot' ):

        self.channel = channel
        self.nickname = nickname



    def clientConnectionLost( self, connector, reason ):

        print 'Lost Connection {}, reconnecting.'.format( reason )
        connector.connect()


    def clientConnectionFailed( self, connector, reason ):

        print 'Could not connect: {}'.format( reason )



if __name__ == '__main__':

    channel = sys.argv[1]
    reactor.connectTCP( 'irc.freenode.net', 6667, BotFactory('#' + channel), timeout= 5 )
    reactor.run()