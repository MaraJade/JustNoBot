#!/usr/bin/python
import praw
import time
import string
import sqlite3

USER_AGENT = "bot1"
BOT_NAME = "TheJustNoBot" 
DATABASE = "justno.db"

MIL_RULES = "**Quick Rules Guide**\n\n [Acronym index](https://www.reddit.com/r/JUSTNOMIL/wiki/index#wiki_acronym_dictionary) | [MIL in the Wild guide](https://www.reddit.com/r/JUSTNOMIL/wiki/index#wiki_mil_in_the_wild_rules) | [JNM nickname policy](https://www.reddit.com/r/JUSTNOMIL/wiki/index#wiki_2._nicknames_are_for_mils.2Fmoms_only)\n\n [No shaming](https://www.reddit.com/r/JUSTNOMIL/wiki/index#wiki_4._shaming_is_not_okay) | [1 post per day](https://www.reddit.com/r/JUSTNOMIL/wiki/index#wiki_10._one_post_per_day) | [Report rulebreaking](https://www.reddit.com/r/JUSTNOMIL/wiki/index#wiki_6._no_backseat_modding) | [MILuminati](https://ml.reddit.com/r/JUSTNOMIL)\n\n [JNM Book List](https://www.reddit.com/r/JUSTNOMIL/wiki/books) | [MILimination Tactics](https://www.reddit.com/r/JUSTNOMIL/wiki/milimination_tactics)  | [Hall o MILs](https://www.reddit.com/r/JUSTNOMIL/wiki/directory) | [Worst Wiki](https://www.reddit.com/r/JUSTNOMIL/wiki/worst)\n\n [MILITW Only](https://www.reddit.com/r/JUSTNOMIL/search?sort=new&restrict_sr=on&q=flair%3AMIL%2Bin%2Bthe%2Bwild) | [JNM Without MILITW](https://www.reddit.com/r/JUSTNOMIL/search?q=NOT+MIL%2Bin%2Bthe%2Bwild&restrict_sr=on&sort=new&t=all) | [Report PM Trolls](https://www.reddit.com/r/JUSTNOMIL/wiki/trolls)\n\n NO CONTACT! or DIVORCE! is generally not good advice and will be removed.\n\n Resist the urge to share your armchair diagnoses or have your comment removed.\n\n [Fear mongering new posters will result in a temp ban.](https://www.reddit.com/r/JUSTNOMIL/comments/8z73mv/who_loves_a_pie_chart_i_do_i_do_survey_results/e2glikt/)\n\n Crisis Resources [U.S.](https://suicidepreventionlifeline.org/) | [U.K.](https://www.samaritans.org/how-we-can-help-you) | [Australia](https://www.lifeline.org.au/get-help/get-help-home) | [Canada](https://suicideprevention.ca/need-help/) | [Denmark](https://www.livslinien.dk/)\n\n******\n\n"

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

    #c.execute('''
    #        CREATE TABLE IF NOT EXISTS locked_posts (
    #            ID INTEGER PRIMARY KEY AUTOINCREMENT,
    #            PostID VARCHAR(80) NOT NULL
    #        )
    #''')

    #dbConn.commit()

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
    print("Subscription removed")

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
        if message.subject == "Subscribe" and len(parts) > 2:
            addSubscriber(message.author, parts[1], parts[2])
        elif message.subject == "Unsubscribe" and len(parts) > 2:
            removeSubscriber(message.author, parts[1], parts[2])

        message.mark_read()
        time.sleep(30)

def get_posts(subreddit):
    for post in subreddit.new(limit=100):
        print(type(post))
        if duplicate_preventer(post):
            continue
        elif post.author is not None:
            history = []
            for link in post.author.submissions.new(limit=100):
                if link.subreddit == subreddit.display_name:
                    history.append(link)

            message = ''            
            if len(history) <= 1:
                welcome = "Welcome to /r/{}!\n\nI'm JustNoBot. I help people follow your posts!\n\n".format(post.subreddit)
                if subreddit == "JUSTNOMIL":
                    message = MIL_RULES + welcome
                else:
                    message = welcome
            else:
                welcome = "Other posts from /u/{}:\n\n\n".format(str((post.author)))
                if subreddit == "JUSTNOMIL":
                    message = MIL_RULES + welcome
                else:
                    message = welcome

                count = 0
                longer = False
                for entry in history:
                    message = message + ("* [{}]({})\n\n".format(str((entry.title).encode('utf-8')), str((entry.permalink).encode('utf-8'))))
                    count = count + 1 
                    if count == 10:
                        longer = True
                        break

                if longer:
                    message = message + ("This user has more than 10 posts in their history. To see the rest of their posts, click [here](/u/{}/submitted)\n\n".format(str((post.author))))

            message = message + ("\n\n*****\n\n\n\n^(To be notified as soon as {} posts an update) [^click ^here.](http://www.reddit.com/message/compose/?to={}&subject=Subscribe&message=Subscribe {} {})".format(str((post.author)), BOT_NAME, str((post.author)), str((post.subreddit))))
            #message = message + ("^(Subscriptions are in progress. Please stand by)")


            message = message + "\n\n*I am a bot, and this action was performed automatically.  Please [contact the moderators of this subreddit](/message/compose/?to=/r/{}) if you have any questions or concerns.*\n\n".format(post.subreddit)

            print(post.locked)
            if post.locked != True:
                try:
                    comment = post.reply(message)
                    print("Post replied to")
                except praw.exceptions.APIException as e:
                    print(e)
                    time.sleep(60)
                    if e == "RATELIMIT: 'you are doing that too much. try again in 5 seconds.' on field 'ratelimit'":
                        try:
                            comment = post.reply(message)
                            print("Post replied to on second attempt")
                        except praw.exceptions.APIException as e:
                            print(e)
                if post.subreddit == "JUSTNOMIL":
                    comment.mod.distinguish(sticky=True)

            time.sleep(30)

            subscribers = dbsearch(post.author)

            if subscribers is not None:
                subject = "New submission by /u/{}".format(str((post.author)))
                for subscriber in subscribers:
                    body = "Hello /u/{},\n\n/u/{} has a new submission: [{}]({})\n\n \n\n*****\n\n\n\n^(To unsubscribe) [^click ^here](http://www.reddit.com/message/compose/?to={}&subject=Unsubscribe&message=Unsubscribe {} {})".format(str(subscriber[0]), str((post.author)), str((post.title)), str((post.permalink).encode('utf-8')), BOT_NAME, str((post.author)), str((post.subreddit)))
                    reddit.redditor(str(subscriber[0])).message(subject=subject, message=body) 
                    print("Subsriber notified")

                    time.sleep(30)


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

