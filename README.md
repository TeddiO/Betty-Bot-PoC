# Betty-Bot

A good while back I was looking to make a Discord bot for my own servers that could be easily reused, however many a Discord library for Python 
is fairly large, sometimes not well maintained and often with features that don't really matter.

With that in mind, I set out to produce the absolute baseline to see what it takes to make a basic Discord bot in Python 3.6.
We use already well-established libraries in Python that themselves are fairly lightweight and portable to do a chunk of the heavy lifting
allowing us to focus on the nitty-gritty of the Discord API itself.

## Using

You'll need to make a Bot user in the [Discord app section](https://discordapp.com/developers/applications/me) to get your API key / user ID to authenticate the bot on the server.
From there it's a case of firing up the bot (Assuming below dependancies are met) and you should be good to go!

## Requirements
- Python 3.6
- [Requests](http://docs.python-requests.org/en/master/)
- [Websockets](https://github.com/aaugustin/websockets)
