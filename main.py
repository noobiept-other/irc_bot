# python2.7

import sys
import json

from twisted.words.protocols import irc
from twisted.internet import protocol
from twisted.internet.task import LoopingCall
from twisted.internet import reactor



class Bot( irc.IRCClient ):


    def _get_username( self ):
        return self.factory.username

    def _get_password( self ):
        return self.factory.password


    username = property( _get_username )
    nickname = username
    password = property( _get_password )


    def signedOn( self ):

        self.join( self.factory.channel )

        print 'Signed on as {}'.format( self.nickname )



    def joined( self, channel ):

        print 'Joined {}'.format( channel )

        self.count_occurrences = 0
        self.word_to_count = 'something'
        self.total_rounds = 0
        self.total_count_occurrences = 0

        LoopingCall( self.printOccurrencesPerMinute ).start( 10, now= False )


    def privmsg( self, user, channel, message ):
        """
            This is called when the bot receives a message
        """

        print message

        if not user:
            return

            # private message to the bot
        #if channel == self.nickname:
        #    self.msg( self.factory.channel, 'hello there' )


        if self.nickname in message:
            self.msg( self.factory.channel, message )


        self.count_occurrences += message.count( self.word_to_count )




    def printOccurrencesPerMinute( self ):

        self.total_count_occurrences += self.count_occurrences
        self.total_rounds += 1

        average = float( self.total_count_occurrences ) / float( self.total_rounds )


        self.msg( self.factory.channel, '{} Per Minute: {} // Average: {}'.format( self.word_to_count, self.count_occurrences, average ) )

        self.count_occurrences = 0






class BotFactory( protocol.ClientFactory ):

    protocol = Bot

    def __init__( self, channel, username, password ):

        self.channel = channel
        self.username = username
        self.password = password


    def clientConnectionLost( self, connector, reason ):

        print 'Lost Connection {}, reconnecting.'.format( reason )
        print reason.printTraceback()

        connector.connect()


    def clientConnectionFailed( self, connector, reason ):

        print 'Could not connect: {}'.format( reason )



if __name__ == '__main__':

    with open( 'config.json', 'r' ) as f:
        content = f.read()

    contentJson = json.loads( content )

        # twisted doesn't like unicode
    username = str( contentJson[ 'username' ] )
    password = str( contentJson[ 'password' ] )
    server = str( contentJson[ 'server' ] )
    channel = str( contentJson[ 'channel' ] )



    reactor.connectTCP( server, 6667, BotFactory( channel, username, password ), timeout= 2 )
    reactor.run()