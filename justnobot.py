#!/usr/bin/python
import praw
import time
import string
import sqlite3

USER_AGENT = "bot1"
BOT_NAME = "TheJustNoBot" 
DATABASE = "justno.db"

# Sqlite database: will need changed to a better database
# Also needs reworked to be more relational
def dbinit():
    global dbConn
    dbConn = sqlite3.connect(DATABASE)

    dbsetup()

def dbsetup():
    c = dbConn.cursor()

    c.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Subscriber VARCHAR(80) NOT NULL,
                SubscribedTo VARCHAR(80) NOT NULL,
                Subreddit VARCHAR(80) NOT NULL
            )
    ''')

    dbConn.commit()

    c.execute('''
            CREATE TABLE IF NOT EXISTS marked_posts (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                PostID VARCHAR(80) NOT NULL
            )
    ''')

    dbConn.commit()

def dbclose():
    dbConn.commit()
    dbConn.close()

def dbsearch(poster, subreddit):
    c = dbConn.cursor()

    return c.execute('''
            SELECT Subscriber
            FROM subscriptions
            WHERE SubscribedTo = ?
            AND Subreddit = ?
    ''', (str(poster), str(subreddit)))

def addSubscriber(subscriber, subscribedTo, subreddit):
    c = dbConn.cursor()

    try:
        c.execute('''
                INSERT INTO subscriptions
                (Subscriber, SubscribedTo, Subreddit)
                VALUES (?, ?, ?)
        ''', (str(subscriber.name), str(subscribedTo), str(subreddit)))
    except sqlite3.IntegrityError:
        print("Failed to add subscription")
        return False

    dbConn.commit()
    print("Subscription added")
    
    return True

def removeSubscriber(subscriber, subscribedTo, subreddit):
    c  = dbConn.cursor()

    c.execute('''
            DELETE FROM subscriptions
            WHERE Subscriber = ?
            AND SubscribedTo = ?
            AND Subreddit = ?
    ''', (str(subscriber), str(subscribedTo), str(subreddit)))

    dbConn.commit()
    print("Subscription removed")

    if c.rowcount == 1:
        return True
    else:
        return False

# Marking a post as locked so as to not spam subscribers
def mark_post(post):
    c = dbConn.cursor()

    try:
        c.execute('''
                INSERT INTO marked_posts
                (PostID)
                VALUES (?)
        ''', (str(post),))
    except sqlite3.IntegrityError:
        print("Failed to add marked post")
        return False

    dbConn.commit()
    print("Post marked")
    
    return True

# Saving time by checking if we've already looked at the post
def is_marked(post):
    c = dbConn.cursor()

    c.execute('''
            SELECT count (*)
            FROM marked_posts
            WHERE PostID = ?
    ''', (str(post),))

    return c.fetchone()[0]

# Checking if the post has already been responded to
def sticky_checker(post):
    bot = False
    stickied = False
    for comment in list(post.comments):
        # Switch statement?
        # Check for a sticky
        if comment.stickied == True:
            stickied = True
            # Is it the bot?
            if comment.author == BOT_NAME:
                bot = True
                return (bot, stickied)
        else:
            # If the sticky isn't the bot, check for a comment elsewhere
            if comment.author == BOT_NAME:
                bot = True
                return (bot, stickied)
    return (bot, stickied)

# Get subscription/unsubscription requests
def get_messages():
    for message in reddit.inbox.unread(limit=100):
        print(message.author)
        print(message.body)
        message.body = message.body.replace(u'\xa0', u' ')
        parts = message.body.split(' ')
        if message.subject == "Subscribe" and len(parts) > 2:
            addSubscriber(message.author, parts[1], parts[2])

            subject = "Successfully subscribed to {}".format(parts[1])
            body = "You have successfully been subscribed to {} in {}! I will notify you whenever they post.".format(str(parts[1]), str(parts[2]))

            reddit.redditor(str(message.author)).message(subject=subject, message=body) 
            print("Subscriber notified")
        elif message.subject == "Unsubscribe" and len(parts) > 2:
            removeSubscriber(message.author, parts[1], parts[2])

            subject = "Successfully unsubscribed from {}".format(parts[1])
            body = "You have successfully been unsubscribed from {} in {}! You will no longer be notified when they post.".format(str(parts[1]), str(parts[2]))

            reddit.redditor(str(message.author)).message(subject=subject, message=body) 
            print("Subscriber notified")

        message.mark_read()
        time.sleep(5)

# Go though all the posts on the sub
def get_posts(subreddit):
    all_rules = "**Quick Rule Reminders:**\n\nOP's needs come first, avoid dramamongering, respect the flair, and don't be an asshole. If your only advice is to jump straight to NC or divorce, your comment may be subject to removal at moderator discretion.\n\n[**^(Full Rules)**](https://www.reddit.com/r/{}/wiki/index#wiki_rules) ^(|) [^(Acronym Index)](https://www.reddit.com/r/{}/wiki/index#wiki_acronym_dictionary) ^(|) [^(Flair Guide)](https://www.reddit.com/r/JUSTNOMIL/wiki/index#wiki_post_flair_guide)^(|) [^(Report PM Trolls)](https://www.reddit.com/r/JUSTNOMIL/wiki/trolls)\n\n**Resources:** [^(In Crisis?)](https://www.reddit.com/r/JUSTNOMIL/wiki/index#wiki_crisis_resources) ^(|) [^(Tips for Protecting Yourself)](https://www.reddit.com/r/JUSTNOMIL/wiki/index#wiki_protecting_yourself) ^(|) [^(Our Book List)](https://www.reddit.com/r/JUSTNOMIL/wiki/books) ^(|) [^(Our Wiki)](https://www.reddit.com/r/{}/wiki/)\n\n".format(subreddit, subreddit, subreddit)

    # Limited to 100 so as to not take forever
    for post in subreddit.new(limit=100):
        # Check if there is already a bot comment
        sticky = sticky_checker(post)
        # Make sure the author has not deleted their account, the post isn't
        # locked, and that there isn't already a bot comment
        if post.author is not None and is_marked(post) == 0 and sticky[0] == False:
            history = []
            # Get all the posts from the sub in OP's history
            for link in post.author.submissions.new(limit=100):
                if link.subreddit == subreddit.display_name:
                    history.append(link)

            message = ''
            # First time poster
            if len(history) <= 1:
                welcome = "Welcome to /r/{}!\n\nI'm JustNoBot. I help people follow your posts!\n\n".format(post.subreddit)
            # Previous poster
            else:
                welcome = "Other posts from /u/{}:\n\n\n".format(str((post.author)))

                count = 0
                longer = False
                # Construct the history part of the comment
                for entry in history[1:]:
                    welcome = welcome + ("* [{}]({})\n\n".format(str((entry.title)), str((entry.permalink))))
                    count = count + 1 
                    # There's limited space, only post 10
                    if count == 10:
                        longer = True
                        break

                # Add the statement if the history is too long
                if longer:
                    welcome = welcome + ("^(This user has more than 10 posts in their history. To see the rest of their posts,) [^(click here)](/u/{}/submitted)\n\n".format(str(post.author)))

            # How to subscribe/unsubscribe
            update = ("\n\n*****\n\n\n\n^(To be notified as soon as {} posts an update) [^click ^here.](http://www.reddit.com/message/compose/?to={}&subject=Subscribe&message=Subscribe {} {}) ^(|) ^(For help managing your subscriptions,) [^(click here.)](https://www.reddit.com/r/JUSTNOMIL/wiki/index#wiki_.2Fu.2Fthejustnobot)\n*****\n\n\n".format(str(post.author), BOT_NAME, str(post.author), str(post.subreddit), str(post.author), str(post.subreddit)))

            # Reminding people that getting angry at the comment is useless as
            # the bot doesn't give a shit
            bot = "\n\n*^(I am a bot, and this action was performed automatically. Please)* [*^(contact the moderators of this subreddit)*](/message/compose/?to=/r/{}) *^(if you have any questions or concerns.)*\n\n".format(post.subreddit)

            # Construct the comment
            message = all_rules + welcome + update + bot

            # Double checking that the post isn't locked or too old
            if post.locked != True and post.archived != True:
                # Try catch due to a lot of errors
                try:
                    comment = post.reply(message)
                    print("Replied to {}".format(post.author))
                except praw.exceptions.APIException as e:
                    print(e)
                    time.sleep(5)
                    if e == "RATELIMIT: 'you are doing that too much. try again in 5 seconds.' on field 'ratelimit'":
                        try:
                            comment = post.reply(message)
                            print("Post replied to on second attempt")
                        except praw.exceptions.APIException as e:
                            print(e)
                    elif e == "TOO_OLD: 'that's a piece of history now; it's too late to reply to it' on field 'parent'":
                        mark_post(post)
                        print("Post marked")

                # Double check that there isn't already a sticky
                if sticky[0] == False and sticky[1] == False:
                    try:
                        exception = comment.mod.distinguish(sticky=True)
                    except:
                        print(exception)
                # If there is a sticky that isn't the bot, don't sticky the new
                # comment
                elif sticky[0] == False and sticky[1] == True:
                    comment.mod.distinguish()

                # Lock the comment so people stop accidentaly replying to it
                comment.mod.lock()

            else:
                # If the post is locked/archived, mark it so we don't waste time
                # on it
                mark_post(post)
                print("Post marked")

            time.sleep(5)

            # Get subscribers
            subscribers = dbsearch(post.author, post.subreddit)

            # Needs a better check, subscribers is always not none
            if subscribers is not None:
                subject = "New submission by /u/{}".format(str((post.author)))
                # Send a message to each subscriber
                for subscriber in subscribers:
                    body = "Hello /u/{},\n\n/u/{} has a new submission in {}: [{}]({})\n\n \n\n*****\n\n\n\n^(To unsubscribe) [^click ^here](http://www.reddit.com/message/compose/?to={}&subject=Unsubscribe&message=Unsubscribe {} {})".format(subscriber[0], post.author, str(post.subreddit), str((post.title)), str((post.permalink)), BOT_NAME, post.author, str((post.subreddit)))

                    try:
                        reddit.redditor(subscriber[0]).message(subject=subject, message=body) 
                        print("{} notified".format(subscriber))
                    except praw.exceptions.APIException as e:
                        print(e)

                    time.sleep(5)


if __name__ == '__main__':
    print("Initializing bot")
    global reddit

    # Start up the database
    dbinit()

    # Connect to reddit
    reddit = praw.Reddit(USER_AGENT)

    # Figure out how to parallelize this
    subs = ["Justnofil", "JustNoSO", "JustNoFamFiction", "JustNoFriend", "JUSTNOFAMILY", "JustNoDIL", "JUSTNOMIL"]
    while True:
        get_messages()
        print("Messages gotten, getting posts")

        for sub in subs:
            print(sub)
            subreddit = reddit.subreddit(sub)
            get_posts(subreddit)

        print("Posts gotten, getting messages")

