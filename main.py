# python2.7

import sys
import json
import random
import argparse
import signal
import re

from twisted.words.protocols import irc
from twisted.internet import protocol
from twisted.internet.task import LoopingCall
from twisted.internet import reactor


"""
    requirements:
        - python 2.7
        - twisted
        - zope.interface

    - be able to make commands from the chat (like !command theCommand 'what to write').
        - only the mods of the channel can do it
        - useful for links etc
        - have them in a .json file

        - be able to join more than 1 channel (add in the config.json an array for multiple channels, or if just one channel a string)
        - be able to change the title !title "the title"
        - have the words to count per minute in the config.json in an array, and it automatically counts for all the ones there
        - the !help says all the commands (and is automatically, instead of having to update the string manually)

    Issues:

        - not quitting correctly
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

        try:
            with open( 'commands.json', 'r' ) as f:
                commands = f.read()

        except IOError:
            self.commands = {}

        else:
            try:
                self.commands = json.loads( commands )

            except ValueError:
                self.commands = {}


        self.builtin_commands = {
            '!help': self.printHelpText,
            '!byebye': self.stopBot
            }

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

        elif message in self.commands:
            self.sendMessage( self.factory.channel, self.commands[ message ] )


        for builtInCommand in self.builtin_commands:

            if builtInCommand in message:

                self.builtin_commands[ builtInCommand ]()



        match = re.search( r'!command !(\w+) (.+)', message )

        if match:
            self.addCommand( '!' + match.group( 1 ), match.group( 2 ) )



        self.count_occurrences += message.count( self.word_to_count )



    def getAverageOccurrences( self ):

        return float( self.total_count_occurrences ) / float( self.total_rounds )


    def printOccurrencesPerMinute( self ):

        self.total_count_occurrences += self.count_occurrences
        self.total_rounds += 1

        average = self.getAverageOccurrences()

        self.sendMessage( self.factory.channel, '{} Per Minute: {} // Average: {:.3f}'.format( self.word_to_count, self.count_occurrences, average ) )

        self.count_occurrences = 0



    def addCommand( self, command, response ):

        self.commands[ command ] = response




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



    def printHelpText( self ):

        self.sendMessage( self.factory.channel, '!help -- something' )



    def stopBot( self ):

        self.save()
        reactor.stop()

        sys.exit()



    def save( self ):
        """
            Call when exiting the program
        """

        with open( 'commands.json', 'w' ) as f:
            json.dump( self.commands, f )






class BotFactory( protocol.ClientFactory ):

    protocol = Bot

    def __init__( self, channel, username, password ):

        self.channel = channel
        self.username = username
        self.password = password


    def buildProtocol( self, addr ):
        """
            Override to get a reference to the protocol/bot object in the factory
        """

        proto = protocol.ClientFactory.buildProtocol( self, addr )

        self.bot = proto

        return proto


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


    botFactory = BotFactory( channel, username, password )


    def signal_handler( signal, frame ):
        """
            Close the program with ctrl + c

            Saves and stops twisted
        """

        try:
            botFactory.bot.save()

        except AttributeError:  # in case .bot attribute isn't set yet
            print 'test'
            pass

        reactor.stop()
        sys.exit()


        # catch sigint (ctrl + c), and save then
    signal.signal( signal.SIGINT, signal_handler )

    reactor.connectTCP( server, 6667, botFactory, timeout= 2 )
    reactor.run()
