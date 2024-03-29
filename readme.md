An irc bot that can count the rate that some words are being written in the chat. Also able to save some messages that can be brought back  given the appropriate command.


Configuration
=============


Add a `config.json` file in the root directory, with this format.

    {
        "username": "the_username",
        "password": "the_password",
        "server": "irc.server.pt",
        "channels": [ "#one", "#two" ],
        "admins": [ "username" ],
        "random_message": true,
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
    
The `commands` can be added through the chat, with the `!add` command (or removed with the `!remove` command).
    
    
Run
===
   
    
- `python main.py` -- If the config file is named `config.json`. 
- `python main.py specify_config_name.json` -- To use a different one.
   
    
Commands
========


- `!top5` -- Top 5 words written in the channel. 
- `!time` -- The uptime of the bot (time the bot has been active).
- `!topic <the topic>` -- Change the topic of the channel (requires `moderator` rights).
- `!help` -- Prints a list off all the available commands in that channel.
- `!add <!command> <response>` -- Add custom commands to that channel (requires `moderator` rights).
- `!remove <!command>` -- Remove a previously added command (requires `moderator` rights).
- There may be other custom commands added with the `!add` command, depends on each channel.
      
    
Requirements
============


Uses `python 2.7` and `twisted`.