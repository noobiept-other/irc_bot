# python 2.7

import sys
import json
import socket

from PySide.QtGui import QApplication, QLabel, QPushButton, QLineEdit, QGridLayout, QTextEdit, QWidget, QCheckBox


class Bot( QWidget ):
    def __init__(self, parent= None):

        super( Bot, self ).__init__( parent )

        showMessages = QTextEdit()
        channel = QLineEdit()
        channelLabel = QLabel( 'Channel' )
        writeMessage = QLineEdit()
        sendMessage = QPushButton( 'Send' )
        printMessage = QCheckBox( 'Print Message' )

        showMessages.setReadOnly( True )


            # layouts

        channelLayout = QGridLayout()

        channelLayout.addWidget( channelLabel, 0, 0 )
        channelLayout.addWidget( channel, 0, 1 )

        messageLayout = QGridLayout()

        messageLayout.addWidget( printMessage, 0, 0 )
        messageLayout.addWidget( writeMessage, 0, 1 )
        messageLayout.addWidget( sendMessage, 0, 2 )


        mainLayout = QGridLayout()
        mainLayout.addWidget( showMessages, 0, 0, 1, 2 )    # spans 2 columns
        mainLayout.addLayout( channelLayout, 1, 0 )
        mainLayout.addLayout( messageLayout, 2, 0 )

            # set events

        writeMessage.returnPressed.connect( self.sendMessage )
        sendMessage.clicked.connect( self.sendMessage )

            # main widget

        self.setLayout( mainLayout )
        self.setWindowTitle( 'Bot' )
        self.resize( 500, 300 )

            # save references to ui elements

        self.channel_ui = channel
        self.writeMessage_ui = writeMessage
        self.printMessage_ui = printMessage


    def sendMessage(self):

        message = self.writeMessage_ui.text()
        channel = self.channel_ui.text()
        printMessage = self.printMessage_ui.isChecked()

        data = {
                'message': str( message ),
                'channel': str( channel ),
                'printMessage': printMessage
            }

        dataStr = json.dumps( data )

        client = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        client.connect( ('localhost', 8001) )
        client.send( dataStr )



if __name__ == '__main__':

    app = QApplication( sys.argv )

    bot = Bot()
    bot.show()

    app.exec_()