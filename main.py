# python 2.7

from __future__ import print_function
import sys
import json
import random
import argparse
import re
from collections import Counter

from twisted.words.protocols import irc
from twisted.internet import protocol
from twisted.internet.task import LoopingCall
from twisted.internet import reactor

import utilities


class Bot( irc.IRCClient ):

    def _get_username( self ):
        return self.factory.config[ 'username' ]

    def _get_password( self ):
        return self.factory.config[ 'password' ]


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

            # need to have admin rights to use these commands
        self.admin_commands = [ '!command', '!topic' ]


    def init( self ):
        """
            This is not in __init__() because when that runs the properties of factory aren't accessible yet (self.factory.config for example)
        """
        config = self.factory.config

        for channel in config[ 'channels' ]:

            try:
                channelCommands = config[ 'commands' ][ channel ]

            except KeyError:
                channelCommands = {}

            wordsToCount = {}

            for countWord in config[ 'count_per_minute' ]:
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

        for channel in self.factory.config[ 'channels' ]:
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

        username = user.split( '!' )[ 0 ]
        channelConfig = self.channels[ channel ]

            # count of words per minute
        for word, stuff in channelConfig[ 'words_to_count' ].items():

                # count the occurrences #HERE it counts even when there's symbols next to the word, for example !word $word
            allOccurrences = re.findall( r'\b{}\b'.format( word ), message )
            stuff[ 'count_occurrences' ] += len( allOccurrences )


            # count the occurrence of all words, to get a top5
        splitWords = message.split()

        channelConfig[ 'counter' ].update( splitWords )

        self.commands( channel, username, message )


    def commands( self, channel, username, message ):
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

                if (not builtInCommand in self.admin_commands) or (username in self.factory.config[ 'admins' ]):
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
            command = '!' + match.group( 1 )
            response = match.group( 2 )

            self.channels[ channel ][ 'commands' ][ command ] = response

                # the dictionary may not be initialized yet
            channelCommands = self.factory.config[ 'commands' ].setdefault( channel, {} )
            channelCommands[ command ] = response
            self.save()

        else:
            self.sendMessage( channel, 'Invalid syntax, write: !command !theCommand what to say in response' )


    def save( self ):
        """
            Save the current configuration in memory to the `config.json` file.
        """
        with open( 'config.json', 'w' ) as f:
            json.dump( self.factory.config, f, indent= 4 )


class BotFactory( protocol.ClientFactory ):

    protocol = Bot

    def __init__( self, config ):
        self.config = config


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

            bot.commands( channel, '', message )    #HERE


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
        configJson = json.load( f )

        # `twisted` doesn't like `unicode` in some configuration values
        # need to convert to `str`
    configJson[ 'username' ] = str( configJson[ 'username' ] )
    configJson[ 'password' ] = str( configJson[ 'password' ] )
    configJson[ 'server' ] = str( configJson[ 'server' ] )

    for index, channel in enumerate( configJson[ 'channels' ] ):
        configJson[ 'channels' ][ index ] = str( channel )


    server = configJson[ 'server' ]

    botFactory = BotFactory( configJson )
    uiFactory = UiFactory( botFactory )

    reactor.connectTCP( server, 6667, botFactory, timeout= 2 )  # client
    reactor.listenTCP( 8001, uiFactory )  # server
    reactor.run()
