# python 2.7

from __future__ import print_function
import sys
import json
import random
import argparse
import signal
import re
from collections import Counter

from twisted.words.protocols import irc
from twisted.internet import protocol
from twisted.internet.task import LoopingCall
from twisted.internet import reactor

import utilities


class Bot( irc.IRCClient ):

    def _get_username( self ):
        return self.factory.username

    def _get_password( self ):
        return self.factory.password


    username = property( _get_username )
    nickname = username
    password = property( _get_password )


    def __init__( self ):

        self.channels = {}
        self.builtin_commands = {       # receives as arguments: channel, message
            '!help'    : self.printHelpText,
            '!topic'   : self.setTopic,
            '!command' : self.addCommand,
            '!time'    : self.timePassed,
            '!top5'    : self.getTopFive
            }


    def init( self ):
        """
            This is not in __init__() because when that runs the properties of factory aren't accessible yet (self.factory.config for example)
        """
        try:
            with open( 'commands.json', 'r' ) as commandsFile:
                commands = commandsFile.read()

        except IOError:
            commands = {}

        else:
            try:
                commands = json.loads( commands )

            except ValueError:
                commands = {}


        for channel in self.factory.channels:

            try:
                channelCommands = commands[ channel ]

            except KeyError:
                channelCommands = {}

            wordsToCount = {}

            for countWord in self.factory.config[ 'count_per_minute' ]:
                wordsToCount[ countWord[ 'word' ] ] = {
                        'command': countWord[ 'command' ],
                        'count_occurrences': 0,     # in each minute
                        'total_count_occurrences': 0,
                        'highest': 0                # highest word per minute
                    }

            self.channels[ channel ] = {
                    'last_random_number': 1,    # used when sending a message
                    'minutes_passed': 0,
                    'commands': channelCommands,
                    'words_to_count': wordsToCount,
                    'time_passed': utilities.TimePassed(),
                    'counter': Counter()
                }


    def signedOn( self ):

        self.init()

        for channel in self.factory.channels:

            self.join( channel )

        print( 'Signed on as {}'.format( self.nickname ) )


    def joined( self, channel ):

        print( 'Joined {}'.format( channel ) )

        LoopingCall( lambda: self.updateWordsCount( channel ) ).start( 60, now= False )


    def privmsg( self, user, channel, message ):
        """
            This is called when the bot receives a message
        """
        if not user:
            return

        channelConfig = self.channels[ channel ]

            # count of words per minute
        for word, stuff in channelConfig[ 'words_to_count' ].items():

                # count the occurrences #HERE it counts even when there's symbols next to the word, for example !word $word
            allOccurrences = re.findall( r'\b{}\b'.format( word ), message )
            stuff[ 'count_occurrences' ] += len( allOccurrences )


            # count the occurrence of all words, to get a top5
        splitWords = message.split()

        channelConfig[ 'counter' ].update( splitWords )

        self.commands( channel, message )


    def commands( self, channel, message ):
        """
            Executes whatever commands were found in the message
        """
        channelConfig = self.channels[ channel ]

                    # count of words per minute
        for word, stuff in channelConfig[ 'words_to_count' ].items():

            command = stuff[ 'command' ]

            if command in message:

                average = self.getAverageOccurrences( channel, stuff[ 'total_count_occurrences' ] )
                highest = stuff[ 'highest' ]
                last = stuff[ 'count_occurrences' ]

                self.sendMessage( channel, '{word} per minute -- last minute: {last:.3f} / average: {average:.3f} / highest: {highest:.3f}'.format( word=word, average=average, highest=highest, last=last ) )


            # custom messages/commands
        if message in channelConfig[ 'commands' ]:
            self.sendMessage( channel, channelConfig[ 'commands' ][ message ] )

            # builtin commands
        for builtInCommand in self.builtin_commands:

            if builtInCommand in message:

                self.builtin_commands[ builtInCommand ]( channel, message )


    def updateWordsCount( self, channel ):

        channelData = self.channels[ channel ]

        channelData[ 'minutes_passed' ] += 1

        for word, stuff in channelData[ 'words_to_count' ].items():

            count = stuff[ 'count_occurrences' ]

            if count > stuff[ 'highest' ]:
                stuff[ 'highest' ] = count

            stuff[ 'total_count_occurrences' ] += count
            stuff[ 'count_occurrences' ] = 0


    def getAverageOccurrences( self, channel, total_count ):

        minutesPassed = self.channels[ channel ][ 'minutes_passed' ]
        if minutesPassed == 0:
            return 0

        return float( total_count ) / float( minutesPassed )


    def sendMessage( self, channel, message ):
        """
            Add a random string at the end, so that the message is always different than the one before (even if we're sending the same 'message' twice)
        """
        channelData = self.channels[ channel ]
        randomNumber = random.randint( 0, 9 )

        if randomNumber == channelData[ 'last_random_number' ]:
            randomNumber += 1

        if randomNumber > 9:
            randomNumber = 0

        channelData[ 'last_random_number' ] = randomNumber

        randomString = '%' + str( randomNumber ) + '% - '

        finalMessage = randomString + message

        self.msg( channel, str( finalMessage ) )


    def save( self ):
        """
            Call when exiting the program
        """
        commands = {}

        for channel, stuff in self.channels.items():

            commands[ channel ] = stuff[ 'commands' ]

        with open( 'commands.json', 'w' ) as commandsFile:
            json.dump( commands, commandsFile )


    ### --- builtin commands --- ###


    def printHelpText( self, channel, message ):

        channelData = self.channels[ channel ]
        helpMessage = 'Commands: '

            # add the builtin commands
        for command in self.builtin_commands:
            helpMessage += command + ', '

            # the custom commands
        for command in channelData[ 'commands' ]:
            helpMessage += command + ', '

            # and the words to count commands
        for word, stuff in channelData[ 'words_to_count' ].items():
            command = stuff[ 'command' ]
            helpMessage += command + ', '

            # remove the last comma and space
        helpMessage = helpMessage[ :-2 ]

        self.sendMessage( channel, helpMessage )


    def setTopic( self, channel, message ):

        match = re.search( r'!topic (.+)', message )

        if match:
            topic = match.group( 1 )

            self.topic( channel, topic )

        else:

            self.sendMessage( channel, 'Invalid syntax, write: !topic something like this' )


    def timePassed( self, channel, message ):

        timeMessage = 'Uptime: {}'.format( self.channels[ channel ][ 'time_passed' ].getTimePassed() )

        self.sendMessage( channel, timeMessage )


    def getTopFive( self, channel, message ):

        top5 = self.channels[ channel ][ 'counter' ].most_common( 5 )

        response = 'Top 5: '

        for element in top5:
            word = element[ 0 ]
            times = element[ 1 ]
            plural = 's'

            if times == 1:
                plural = ''

            response += '{} {} time{}, '.format( word, times, plural )


            # remove the last comma and space ', '
        response = response[ :-2 ]
        self.sendMessage( channel, response )


    def addCommand( self, channel, message ):

        match = re.search( r'!command !(\w+) (.+)', message )

        if match:
            self.channels[ channel ][ 'commands' ][ '!' + match.group( 1 ) ] = match.group( 2 )

        else:

            self.sendMessage( channel, 'Invalid syntax, write: !command !theCommand what to say in response' )


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

        print( 'Lost Connection {}, reconnecting.'.format( reason ) )
        print( reason.printTraceback() )

        connector.connect()


    def clientConnectionFailed( self, connector, reason ):

        print( 'Could not connect: {}'.format( reason ) )


class Ui( protocol.Protocol ):

    def __init__(self, factory):
        self.factory = factory


    def dataReceived(self, dataStr):

        data = json.loads( dataStr )
        bot = self.factory.bot_factory.bot

        if data[ 'message' ]:

            channel = str( data[ 'channel' ] )
            message = str( data[ 'message' ] )

            if data[ 'printMessage' ]:
                bot.sendMessage( channel, message )

            bot.commands( channel, message )


class UiFactory( protocol.Factory ):

    def __init__(self, bot_factory):

        self.bot_factory = bot_factory

    def buildProtocol(self, addr):
        return Ui( self )


if __name__ == '__main__':

    parser = argparse.ArgumentParser( description= 'Chat Bot.' )

    parser.add_argument( 'configPath', help= 'Path to the configuration file.', nargs= '?', default= 'config.json' )

    args = parser.parse_args()

    with open( args.configPath, 'r' ) as f:
        content = f.read()

    configJson = json.loads( content )
    configJson = utilities.fromUnicodeToStr( configJson )

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
            print( 'test' )
            pass

        reactor.stop()
        sys.exit()


        # catch sigint (ctrl + c), and save then
    signal.signal( signal.SIGINT, signal_handler )

    uiFactory = UiFactory( botFactory )

    reactor.connectTCP( server, 6667, botFactory, timeout= 2 )  # client
    reactor.listenTCP( 8001, uiFactory )  # server
    reactor.run()
