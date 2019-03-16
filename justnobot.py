#!/usr/bin/python
import praw
import time
import string
import sqlite3

USER_AGENT = "bot1"
BOT_NAME = "TheJustNoBot" 
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

def is_marked(post):
    c = dbConn.cursor()

    c.execute('''
            SELECT count (*)
            FROM marked_posts
            WHERE PostID = ?
    ''', (str(post),))

    return c.fetchone()[0]

def sticky_checker(post):
    for comment in list(post.comments):
        if comment.stickied == True:
            if comment.author == BOT_NAME:
                return (True, True)
            else:
                return (True, False)

    return (False, False)

def get_messages():
    for message in reddit.inbox.unread(limit=100):
        print(message.body.encode('utf-8'))
        message.body = message.body.replace(u'\xa0', u' ')
        parts = message.body.split(' ')
        if message.subject == "Subscribe" and len(parts) > 2:
            addSubscriber(message.author, parts[1], parts[2])

            subject = "Successfully subscribed to {}".format(parts[1])
            body = "You have successfully been subscribed to {} in {}! I will notify you whenever they post.".format(str(parts[1]), str(parts[2]))

            reddit.redditor(str(message.author)).message(subject=subject, message=body) 
        elif message.subject == "Unsubscribe" and len(parts) > 2:
            removeSubscriber(message.author, parts[1], parts[2])

            subject = "Successfully unsubscribed from {}".format(parts[1])
            body = "You have successfully been unsubscribed from {} in {}! You will no longer be notified when they post.".format(str(parts[1]), str(parts[2]))

            reddit.redditor(str(message.author)).message(subject=subject, message=body) 

        message.mark_read()
        time.sleep(5)

def get_posts(subreddit):
    all_rules = "**Quick Rules Guide**\n\n[Acronym Index](https://www.reddit.com/r/{}/wiki/index#wiki_acronym_dictionary) | [JN nickname policy](https://www.reddit.com/r/{}/wiki/index#wiki_2._nicknames) | [No shaming](https://www.reddit.com/r/{}/wiki/index#wiki_3._no_shaming.3B_be_supportive)\n---|---|---\n[Report rulebreaking](https://www.reddit.com/r/{}/wiki/index#wiki_5._no_backseat_modding) | [JN Book List](https://www.reddit.com/r/JUSTNOMIL/wiki/books) | [Report PM Trolls](https://www.reddit.com/r/{}/wiki/trolls)\n\nNO CONTACT! or DIVORCE! is generally not good advice and will be removed.\n\nResist the urge to share your armchair diagnoses or have your comment removed.\n\n**Fear mongering new posters will result in an automatic 2 day ban.**\n\nThe posting of political information/topics whatsoever is against the rules without receiving a prior approval from the mod team via Modmail. Any variation from this can result in a permanent ban.\n\n**Crisis Resources [U.S.](https://suicidepreventionlifeline.org/) | [U.K.](https://www.samaritans.org/how-we-can-help-you) | [Australia](https://www.lifeline.org.au/get-help/get-help-home) | [Canada](https://suicideprevention.ca/need-help/) | [Denmark](https://www.livslinien.dk/)**\n\n[More Crisis Resources Here](https://www.reddit.com/r/Justnofil/wiki/crisis-resources)\n\nFor tips protecting yourself, the resources are also on the sidebar on the right or click [here](https://www.reddit.com/r/Justnofil/wiki/protecting-yourself)\n\n******\n\n^(Not all links are working properly, sorry)\n\n********\n\n".format(subreddit, subreddit, subreddit, subreddit, subreddit, subreddit, subreddit, subreddit)

    for post in subreddit.new(limit=100):
        sticky = sticky_checker(post)
        if sticky[1]:
            continue
        elif post.author is not None and is_marked(post) == 0:
            history = []
            for link in post.author.submissions.new(limit=100):
                if link.subreddit == subreddit.display_name:
                    history.append(link)

            message = ''            
            if len(history) <= 1:
                welcome = "Welcome to /r/{}!\n\nI'm JustNoBot. I help people follow your posts!\n\n".format(post.subreddit)
            else:
                welcome = "Other posts from /u/{}:\n\n\n".format(str((post.author)))

                count = 0
                longer = False
                for entry in history[1:]:
                    welcome = welcome + ("* [{}]({})\n\n".format(str((entry.title).encode('utf-8')), str((entry.permalink).encode('utf-8'))))
                    count = count + 1 
                    if count == 10:
                        longer = True
                        break

                if longer:
                    welcome = welcome + ("This user has more than 10 posts in their history. To see the rest of their posts, click [here](/u/{}/submitted)\n\n".format(str(post.author)))

            update = ("\n\n*****\n\n\n\n^(To be notified as soon as {} posts an update) [^click ^here.](http://www.reddit.com/message/compose/?to={}&subject=Subscribe&message=Subscribe {} {})\n\n^(If the link is not visible or doesn't work, send me a message with the subject:)\n\n\tSubscribe\n\n^and ^body\n\n\tSubscribe {} {}\n\n".format(str(post.author), BOT_NAME, str(post.author), str(post.subreddit), str(post.author), str(post.subreddit)))

            bot = "\n\n*I am a bot, and this action was performed automatically. Please [contact the moderators of this subreddit](/message/compose/?to=/r/{}) if you have any questions or concerns.*\n\n".format(post.subreddit)

            message = all_rules + welcome + update + bot

            print(post.locked)
            if post.locked != True and post.archived != True:
                try:
                    comment = post.reply(message)
                    print("Post replied to")
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

                if sticky[0] == False:
                    comment.mod.distinguish(sticky=True)
            else:
                mark_post(post)
                print("Post marked")

            time.sleep(5)

            subscribers = dbsearch(post.author, post.subreddit)

            if subscribers is not None:
                subject = "New submission by /u/{}".format(str((post.author)))
                for subscriber in subscribers:
                    body = "Hello /u/{},\n\n/u/{} has a new submission: [{}]({})\n\n \n\n*****\n\n\n\n^(To unsubscribe) [^click ^here](http://www.reddit.com/message/compose/?to={}&subject=Unsubscribe&message=Unsubscribe {} {})".format(subscriber[0], post.author, str((post.title).encode('utf-8')), str((post.permalink).encode('utf-8')), BOT_NAME, post.author, str((post.subreddit)))

                    try:
                        reddit.redditor(subscriber[0]).message(subject=subject, message=body) 
                        print("Subsriber notified")
                    except praw.exceptions.APIException as e:
                            print(e)

                    time.sleep(5)


if __name__ == '__main__':
    print("Initializing bot")
    global reddit

    dbinit()

    reddit = praw.Reddit(USER_AGENT)

    subs = ["Justnofil", "JustNoSO", "JustNoFriends", "JustNoFamFiction", "JUSTNOFAMILY", "LetterstoJNMIL", "JustNoDIL", "JUSTNOMIL"]
    while True:
        get_messages()
        print("Messages gotten, getting posts")

        for sub in subs:
            print(sub)
            subreddit = reddit.subreddit(sub)
            get_posts(subreddit)

        print("Posts gotten, getting messages")

