# JustNoBot
Home of the bot for the JustNoNetwork on reddit

JustNoBot is the replacement for the previous subscription bots on the JustNo
network of subreddits. It posts a comment on every post made in the subs,
containing:

* Quick rules guide, with links to the wiki and crisis resources

* Post history of the OP in the sub they are posting in

* Subscription option

The bot has a database of subscribers, and notifies users when they have
subscribed to an OP, when that OP posts in a sub, and when they unsubscribe from
an OP.

**NOTE:** At the moment, a user has to subscribe to an OP in every sub they post
in. This will be updated in the future to allow users to subscribe to OPs
across the network, with an option to retain the original usage.

# Requirements

* Python 3

* pip3

* PRAW

* Sqlite3

# Development

If you want to run the bot yourself, follow these steps:

* Make sure you have the requirements installed

* Clone the repo

* If you don't have a reddit account, make one

* Go to preferences, then apps

* Click "create another app..."

* Give it a name, select script, enter a redirect url (http://127.0.0.1 works),
  hit create app

* Copy praw.ini.sample to praw.ini, and enter your login information, as well as
  the secrets you now have from creating the app.

* Run the bot! python3 justnobot.py

# PSA

**DO NOT RUN THIS BOT ON ANY SUB WITHOUT MODERATOR PERMISSION**

I am not responsible for you getting banned because you ran the bot on a sub
without permission. Make sure to change the sub(s) the bot is running on before
starting it.
