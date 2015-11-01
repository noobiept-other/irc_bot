Configuration
=============


Add a `config.json` file in the root directory, with this format.

    {
        "username": "the_username",
        "password": "the_password",
        "server": "irc.server.pt",
        "channels": [ "#one", "#two" ],
        "admins": [ "username" ],
        "count_per_minute:
            [
                { "word": "test", "command": "!test" }
            ],
        "commands": {
            "#channelName": {
                "!command": "response"
            }    
        }
    }
    
The `commands` can be added through the chat, with the `!add` command.
    
    
Requirements
============


Uses `python 2.7` and `twisted`.