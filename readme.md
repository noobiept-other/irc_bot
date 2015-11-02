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
    
The `commands` can be added through the chat, with the `!add` command.
    
    
Commands
========


- `!top5` -- Top 5 words written in the channel. 
- `!time` -- The uptime of the bot (time the bot has been active).
- `!topic <the topic>` -- Change the topic of the channel (requires `moderator` rights).
- `!help` -- Prints a list off all the available commands in that channel.
- `!add <!command> <response>` -- Add custom commands to that channel (requires `moderator` rights).
- There may be other custom commands added with the `!add` command, depends on each channel.
    
    
Requirements
============


Uses `python 2.7` and `twisted`.