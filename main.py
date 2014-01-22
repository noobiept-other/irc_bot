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

        - be able to change the title !title "the title"
        - the !help says all the commands (and is automatically, instead of having to update the string manually)
        - block links in chat (and be able to exclude some)
        -use pyside, and show there the chat, and also be able to write messages with the bots account through there

        - check all the words and give a top5 words (say message, started x time ago, top 5 words, to call press !command)

        - tell the uptime (time it is working)

        - count per minute:
            - since the program start (what is now)
            - highest since start
            - last minute?..
        
    Issues:

        - not quitting correctly

        ## use mode() -- http://twistedmatrix.com/documents/current/api/twisted.words.protocols.irc.IRCClient.html#mode

        - PySide doesnt seem to play well with twisted (the event loops...)
            need to have a different program with pyside, and communicate with sockets or something (interprocess communication)
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
        self.minutes_passed = 0
        self.commands = {}
        self.builtin_commands = {
            '!help'    : self.printHelpText,
            '!topic'   : self.setTopic,
            '!command' : self.addCommand
            }
        self.words_to_count = {}



    def init( self ):
        """
            This is not in __init__() because when that runs the properties of factory aren't accessible yet (self.factory.config for example)
        """


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


        for countWord in self.factory.config[ 'count_per_minute' ]:
            self.words_to_count[ countWord[ 'word' ] ] = {
                    'command': countWord[ 'command' ],
                    'count_occurrences': 0,     # in each minute
                    'total_count_occurrences': 0
                }



    def signedOn( self ):

        self.init()

        for channel in self.factory.channels:

            self.join( channel )

        print 'Signed on as {}'.format( self.nickname )



    def joined( self, channel ):

        print 'Joined {}'.format( channel )

        LoopingCall( self.updateWordsCount ).start( 60, now= False )


    def privmsg( self, user, channel, message ):
        """
            This is called when the bot receives a message
        """

        print message

        if not user:
            return


            # count of words per minute
        for word, stuff in self.words_to_count.items():

            command = stuff[ 'command' ]

            if command in message:

                average = self.getAverageOccurrences( stuff[ 'total_count_occurrences' ] )

                self.sendMessage( channel, '{} per minute (average): {:.3f}'.format( word, average ) )


                # count the occurrences #HERE need to identify a word?.. right now counts even if not a word (for example testtest)
            stuff[ 'count_occurrences' ] += message.count( word )


            # custom messages/commands
        if message in self.commands:
            self.sendMessage( channel, self.commands[ message ] )

            # builtin commands
        for builtInCommand in self.builtin_commands:

            if builtInCommand in message:

                self.builtin_commands[ builtInCommand ]( message )



    def updateWordsCount( self ):

        self.minutes_passed += 1

        for word, stuff in self.words_to_count.items():

            stuff[ 'total_count_occurrences' ] += stuff[ 'count_occurrences' ]
            stuff[ 'count_occurrences' ] = 0



    def getAverageOccurrences( self, total_count ):

        if self.minutes_passed == 0:
            return 0

        return float( total_count ) / float( self.minutes_passed )




    def sendMessage( self, channel, message ):

        """
            Add a random string at the end, so that the message is always different than the one before (even if we're sending the same 'message' twice)
        """

        randomNumber = random.randint( 0, 9 )

        if randomNumber == self.last_random_number:
            randomNumber += 1

        if randomNumber > 9:
            randomNumber = 0

        self.last_random_number = randomNumber

        randomString = '%' + str( randomNumber ) + '% - '

        finalMessage = randomString + message

        self.msg( channel, str( finalMessage ) )



    def save( self ):
        """
            Call when exiting the program
        """

        with open( 'commands.json', 'w' ) as commandsFile:
            json.dump( self.commands, commandsFile )



    ### --- builtin commands --- ###

    def printHelpText( self, message ):
        #HERE
        self.sendMessage( self.factory.channel, '!help -- something' )


    def setTopic( self, message ):

        match = re.search( r'!topic (.+)', message )

        if match:
            topic = match.group( 1 )

            self.topic( self.factory.channel, topic )

        else:

            self.sendMessage( self.factory.channel, 'Invalid syntax, write: !topic something like this' )


    def addCommand( self, message ):

        match = re.search( r'!command !(\w+) (.+)', message )

        if match:
            self.commands[ '!' + match.group( 1 ) ] = match.group( 2 )

        else:

            self.sendMessage( self.factory.channel, 'Invalid syntax, write: !command !theCommand what to say in response' )


    def stopBot( self, message ):

        self.save()
        reactor.stop()

        sys.exit()






class BotFactory( protocol.ClientFactory ):

    protocol = Bot

    def __init__( self, config ):

        self.config = config
        self.username = config[ 'username' ]
        self.password = config[ 'password' ]
        self.channels = config[ 'channels' ]


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




def fromUnicodeToStr( config ):

    """
        twisted doesn't like unicode, so gotta convert everything
    """

    config[ 'username' ] = str( config[ 'username' ] )
    config[ 'password' ] = str( config[ 'password' ] )
    config[ 'server' ] = str( config[ 'server' ] )

    for position, channel in enumerate( config[ 'channels' ] ):

        config[ 'channels' ][ position ] = str( channel )


    return config


if __name__ == '__main__':

    parser = argparse.ArgumentParser( description= 'Chat Bot.' )

    parser.add_argument( 'configPath', help= 'Path to the configuration file.', nargs= '?', default= 'config.json' )

    args = parser.parse_args()

    with open( args.configPath, 'r' ) as f:
        content = f.read()

    configJson = json.loads( content )


    configJson = fromUnicodeToStr( configJson )

    server = configJson[ 'server' ]

    botFactory = BotFactory( configJson )


    def signal_handler( theSignal, frame ):
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
