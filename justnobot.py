#!/usr/bin/python
import praw
import time
import string
import sqlite3

USER_AGENT = "bot1"
BOT_NAME = "" 
DATABASE = "justno.db"

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

def dbclose():
    dbConn.commit()
    dbConn.close()

def dbsearch(poster):
    c = dbConn.cursor()

    return c.execute('''
            SELECT Subscriber
            FROM subscriptions
            WHERE SubscribedTo = ?
    ''', (str(poster),))

def addSubscriber(subscriber, subscribedTo, subreddit):
    c = dbConn.cursor()

    try:
        c.execute('''
                INSERT INTO subscriptions
                (Subscriber, SubscribedTo, Subreddit)
                VALUES (?, ?, ?)
        ''', (str(subscriber), str(subscribedTo), str(subreddit)))
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

    if c.rowcount == 1:
        return True
    else:
        return False

def duplicate_preventer(post):
    for comment in list(post.comments):
        if comment.author == BOT_NAME:
            return True

    return False

def get_messages():
    for message in reddit.inbox.unread(limit=100):
        parts = message.body.split(' ')
        if message.subject == "Subscribe":
            addSubscriber(message.author, parts[1], parts[2])
        elif message.subject == "Unsubscribe":
            removeSubscriber(message.author, parts[1], parts[2])

        message.mark_read()
        time.sleep(1)

def get_posts(subreddit):
    for post in subreddit.new(limit=1000):
        if duplicate_preventer(post):
            continue
        else:
            history = []
            for link in post.author.submissions.new(limit=100):
                if link.subreddit == subreddit.display_name:
                    history.append(link)

            if len(history) < 1:
                message = "Welcome to /r/JUSTNOMIL!\n\n" \
                          "I'm JustNoBot. I help people follow your posts!\n\n"
            else:
                message = "Other posts from /u/{}:\n\n\n".format(str(post.author).encode('utf-8')

                count = 0
                longer = False
                for entry in history:
                    message = message + ("*
                        [{}]({})\n\n".format(str(entry.title).encode('utf-8'), str(entry.permalink).encode('utf-8')))
                    count = count + 1 
                    if count == 10:
                        longer = True
                        break

                if longer:
                    message = message + ("This user has more than 10 posts in their history. To see the rest of their posts, click [here](/u/{}/submitted)\n\n".format(str(post.author)))

            message = message + ("\n\n*****\n\n\n\n^(To be notified as soon as {} posts an update) [^click ^here.](http://www.reddit.com/message/compose/?to={}&subject=Subscribe&message=Subscribe {} {})".format(str(post.author), BOT_NAME, str(post.author), str(post.subreddit)))
            #message = message + ("^(Subscriptions are in progress. Please stand by)")

            post.reply(message)
            print("Post replied to")

            time.sleep(1)

            subscribers = dbsearch(post.author)

            if subscribers is not None:
                subject = "New submission by /u/{}".format(str(post.author))
                for subscriber in subscribers:
                    body = "Hello /u/{},\n\n/u/{} has a new submission: [{}]({})\n\n \n\n*****\n\n\n\n^(To unsubscribe) [^click ^here](http://www.reddit.com/message/compose/?to={}&subject=Unsubscribe&message=Unsubscribe {} {})".format(str(subscriber[0]), str(post.author), str(post.title), str(post.permalink), BOT_NAME, str(post.author), str(post.subreddit))
                    reddit.redditor(str(subscriber[0])).message(subject=subject, message=body)
                    time.sleep(1)


if __name__ == '__main__':
    print("Initializing bot")
    global reddit

    dbinit()

    reddit = praw.Reddit(USER_AGENT)

    subs = ["JUSTNOMIL", "Justnofil", "JustNoSO", "JustNoFriends", "JustNoFamFiction", "JUSTNOFAMILY", "LetterstoJNMIL", "JustNoDIL"]
    while True:
        for sub in subs:
            subreddit = reddit.subreddit(sub)
            get_posts(subreddit)

        get_messages()
