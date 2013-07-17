# python2.7

import json
import random
import argparse

from twisted.words.protocols import irc
from twisted.internet import protocol
from twisted.internet.task import LoopingCall
from twisted.internet import reactor


"""
    - be able to make commands from the chat (like !command theCommand 'what to write').
        - only the mods of the channel can do it
        - useful for links etc
        - have them in a .json file
"""


class Bot( irc.IRCClient ):


    def _get_username( self ):
        return self.factory.username

    def _get_password( self ):
        return self.factory.password


    username = property( _get_username )
    nickname = username
    password = property( _get_password )


    def __init__( self ):

        self.last_random_number = 1     # used when sending a message


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

            # the command depends on what word we're counting
        firstLetter = self.word_to_count[ 0 ]

        if '!{}pm'.format( firstLetter ) in message:

            average = self.getAverageOccurrences()

            self.sendMessage( self.factory.channel, '{} per minute (average): {:.3f}'.format( self.word_to_count, average ) )

        elif '!help' in message:

            self.sendMessage( self.factory.channel, 'Commands: !{}pm'.format( firstLetter ) )


        self.count_occurrences += message.count( self.word_to_count )



    def getAverageOccurrences( self ):

        return float( self.total_count_occurrences ) / float( self.total_rounds )


    def printOccurrencesPerMinute( self ):

        self.total_count_occurrences += self.count_occurrences
        self.total_rounds += 1

        average = self.getAverageOccurrences()

        self.sendMessage( self.factory.channel, '{} Per Minute: {} // Average: {:.3f}'.format( self.word_to_count, self.count_occurrences, average ) )

        self.count_occurrences = 0



    def sendMessage( self, channel, message ):

        """
            Add a random string at the end, so that the message is always different than the one before (even if we're sending the same 'message' twice)
        """

        randomNumber = random.randint( 0, 9 )

        if randomNumber == self.last_random_number:
            randomNumber += 1

        if randomNumber > 9:
            randomNumber = 0

        randomString = '%' + str( randomNumber ) + '% - '

        self.msg( channel, randomString + message )





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

    parser = argparse.ArgumentParser( description= 'Chat Bot.' )

    parser.add_argument( 'configPath', help= 'Path to the configuration file.', nargs= '?', default= 'config.json' )

    args = parser.parse_args()

    with open( args.configPath, 'r' ) as f:
        content = f.read()

    contentJson = json.loads( content )

        # twisted doesn't like unicode
    username = str( contentJson[ 'username' ] )
    password = str( contentJson[ 'password' ] )
    server = str( contentJson[ 'server' ] )
    channel = str( contentJson[ 'channel' ] )


    reactor.connectTCP( server, 6667, BotFactory( channel, username, password ), timeout= 2 )
    reactor.run()