#!/usr/bin/python
import praw
import time
import string
import sqlite3
import threading
import config


class bot():
        # define variables
        def __init__(self):
                self.reddit = praw.Reddit(username = config.username,
                                                                  password = config.password,
                                                                  client_id = config.client_id,
                                                                  client_secret = config.client_secret,
                                                                  user_agent = config.user_agent)

                self.db_connection = self.initiate_database()


        # initiates database
        def initiate_database(self):
                """ create a database connection to a database that resides
                in justno.db file
                """
                try:
                        conn = sqlite3.connect(config.db_name, check_same_thread=False)

                        conn.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
                                        ID INTEGER PRIMARY KEY AUTOINCREMENT,
                                        Subscriber VARCHAR(80) NOT NULL,
                                        SubscribedTo VARCHAR(80) NOT NULL,
                                        Subreddit VARCHAR(80) NOT NULL)''')

                        conn.execute('''CREATE TABLE IF NOT EXISTS marked_posts (
                                        ID INTEGER PRIMARY KEY AUTOINCREMENT,
                                        PostID VARCHAR(80) NOT NULL)''')

                        print("Connected to SQLITE database " + sqlite3.version)
                        return conn
                except Error as e:
                        print("Failed to connect to database")
                        print(e)


        # takes poster and subreddit, 
        # searches database returns hits
        def dbsearch(self, poster, subreddit):
                return self.db_connection.execute('''SELECT Subscriber
                                                                 FROM subscriptions
                                                                 WHERE SubscribedTo = ?
                                                                 AND Subreddit = ?''', 
                                                                 (str(poster), 
                                                                   str(subreddit)))


        # takes subscriber, subscribedTo and subreddit
        # adds subscriber to database
        # returns boolean
        def addSubscriber(self, subscriber, subscribedTo, subreddit):
                try:
                        self.db_connection.execute('''INSERT INTO subscriptions
                                                                          (Subscriber, SubscribedTo, Subreddit)
                                                                          VALUES (?, ?, ?)''', 
                                                                          (str(subscriber.name), 
                                                                                str(subscribedTo), 
                                                                                str(subreddit)))
                except sqlite3.IntegrityError:
                        print("Failed to add subscription")
                        return False

                self.db_connection.commit()
                
                return True


        # takes subscriber, subscribedTo and subreddit
        # removes subscriber
        # returns boolean
        def removeSubscriber(self, subscriber, subscribedTo, subreddit):
                try:
                        self.db_connection.execute('''DELETE FROM subscriptions
                                                                          WHERE Subscriber = ?
                                                                          AND SubscribedTo = ?
                                                                          AND Subreddit = ?''', 
                                                                          (str(subscriber), 
                                                                                str(subscribedTo), 
                                                                                str(subreddit)))
                except sqlite3.IntegrityError:
                        print("Failed to delete subscription")
                        return False

                self.db_connection.commit()

                return True


        # Marking a post as locked so as to not spam subscribers
        def mark_post(self, post):
                try:
                        self.db_connection.execute('''INSERT INTO marked_posts
                                                                          (PostID)
                                                                          VALUES (?)''', 
                                                                          (str(post),))
                except sqlite3.IntegrityError:
                        print("Failed to add marked post")
                        return False

                self.db_connection.commit()
                
                return True


        # Saving time by checking if we've already looked at the post
        def is_marked(self, post):
                self.db_connection.cursor().execute('''SELECT count (*) FROM marked_posts WHERE PostID = ?''', (str(post),))

                return self.db_connection.cursor().fetchone()


        # Checking if the post has already been responded to
        def sticky_checker(self, post):
            bot = False
            stickied = False
            for comment in list(post.comments):
                # Switch statement?
                # Check for a sticky
                if comment.stickied == True:
                    stickied = True
                    # Is it the bot?
                    if comment.author == config.username:
                        bot = True
                        return (bot, stickied)
                else:
                    # If the sticky isn't the bot, check for a comment elsewhere
                    if comment.author == config.username:
                        bot = True
                        return (bot, stickied)
            return (bot, stickied)


        def lock_comment(self, comment_id):
            try:
                self.reddit.comment(str(comment_id)).mod.lock()
            except Exception as e:
                print(e)
                pass

        # Get subscription/unsubscription requests
        def get_messages(self):
                for message in self.reddit.inbox.stream():
                        message.body = message.body.replace(u'\xa0', u' ')
                        parts = message.body.split(' ')
                        if message.subject == "Subscribe" and len(parts) > 2:
                                self.addSubscriber(message.author, parts[1], parts[2])

                                subject = "Successfully subscribed to {}".format(parts[1])
                                body = "You have successfully been subscribed to {} in {}! I will notify you whenever they post.".format(str(parts[1]), str(parts[2]))

                                self.reddit.redditor(str(message.author)).message(subject=subject, message=body) 
                        elif message.subject == "Unsubscribe" and len(parts) > 2:
                                self.removeSubscriber(message.author, parts[1], parts[2])

                                subject = "Successfully unsubscribed from {}".format(parts[1])
                                body = "You have successfully been unsubscribed from {} in {}! You will no longer be notified when they post.".format(str(parts[1]), str(parts[2]))

                                self.reddit.redditor(str(message.author)).message(subject=subject, message=body) 
                                print("Subscriber notified")

                        message.mark_read()


        # Go though all the posts on the sub
        def get_posts(self):
                for post in self.reddit.subreddit('MaraTesting+MaraTesting2').stream.submissions(skip_existing=True):
                        # Check for stickies
                        sticky = self.sticky_checker(post)

                        # Make sure the author has not deleted their account,
                        # the post isn't locked, and we haven't already posted
                        # on it
                        if post.author is not None and self.is_marked(post) is None and sticky[0] == False:
                                subreddit = post.subreddit
                                all_rules = "**Quick Rule Reminders:**\n\nOP's needs come first, avoid dramamongering, respect the flair, and don't be an asshole. If your only advice is to jump straight to NC or divorce, your comment may be subject to removal at moderator discretion.\n\n[**^(Full Rules)**](https://www.reddit.com/r/{}/wiki/index#wiki_rules) ^(|) [^(Acronym Index)](https://www.reddit.com/r/{}/wiki/index#wiki_acronym_dictionary) ^(|) [^(Flair Guide)](https://www.reddit.com/r/{}/wiki/index#wiki_post_flairs)^(|) [^(Report PM Trolls)](https://www.reddit.com/r/{}/wiki/index#wiki_trolls_suck)\n\n**Resources:** [^(In Crisis?)](https://www.reddit.com/r/JustNoNetwork/wiki/links#wiki_crisis_links.3A_because_there.2019s_more_than_one_type_of_crisis) ^(|) [^(Tips for Protecting Yourself)](https://www.reddit.com/r/JUSTNOMIL/wiki/index#wiki_protecting_yourself) ^(|) [^(Our Book List)](https://www.reddit.com/r/JustNoNetwork/wiki/books) ^(|) [^(This Sub's Wiki)](https://www.reddit.com/r/{}/wiki/) ^(|) [^(General Resources)](https://www.reddit.com/r/JustNoNetwork/wiki/tos)\n\n".format(subreddit, subreddit, subreddit, subreddit, subreddit)

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
                                                count += 1
                                                if count == 10:
                                                    longer = True
                                                    break
                                        if longer:
                                            # Add the statement if the history is too long
                                            welcome = welcome + ("^(This user has more than 10 posts in their history. To see the rest of their posts,) [^(click here)](/u/{}/submitted)\n\n".format(str(post.author)))

                                # How to subscribe/unsubscribe
                                update = ("\n\n*****\n\n\n\n^(To be notified as soon as {} posts an update) [^click ^here.](http://www.reddit.com/message/compose/?to={}&subject=Subscribe&message=Subscribe {} {})\n*****\n\n\n".format(str(post.author), config.username, str(post.author), str(post.subreddit), str(post.author), str(post.subreddit)))

                                # Reminding people that getting angry at the comment is useless as
                                # the bot doesn't give a shit
                                bot = "\n\n*^(I am a bot, and this action was performed automatically. Please)* [*^(contact the moderators of this subreddit)*](/message/compose/?to=/r/{}) *^(if you have any questions or concerns.)*\n\n".format(post.subreddit)

                                # Construct the comment
                                message = all_rules + welcome + update + bot

                                # Try catch due to a lot of errors
                                try:
                                        comment = post.reply(message)
                                except praw.exceptions.APIException as e:
                                        print(e)

                                        if e == "RATELIMIT: 'you are doing that too much. try again in 5 seconds.' on field 'ratelimit'":
                                                try:
                                                        comment = post.reply(message)
                                                except praw.exceptions.APIException as e:
                                                        print(e)
                                        elif e == "TOO_OLD: 'that's a piece of history now; it's too late to reply to it' on field 'parent'":
                                                self.mark_post(post)

                                # Double check that there isn't already a sticky
                                if sticky[0] == False and sticky[1] == False:
                                        try:
                                           comment.mod.distinguish(sticky=True)
                                        except Exception as e:
                                           print(e)

                                # If there is a sticky that isn't the bot, don't sticky the new
                                # comment
                                elif sticky[0] == False and sticky[1] == True:
                                        comment.mod.distinguish()

                                # Lock the comment so people stop accidentaly replying to it
                                self.lock_comment(comment)

                                # Get subscribers
                                subscribers = self.dbsearch(post.author, post.subreddit)

                                subject = "New submission by /u/{}".format(str((post.author)))
                                # Send a message to each subscriber
                                for subscriber in subscribers:
                                        body = "Hello /u/{},\n\n/u/{} has a new submission in {}: [{}]({})\n\n \n\n*****\n\n\n\n^(To unsubscribe) [^click ^here](http://www.reddit.com/message/compose/?to={}&subject=Unsubscribe&message=Unsubscribe {} {})".format(subscriber[0], post.author, str(post.subreddit), str((post.title)), str((post.permalink)), config.username, post.author, str((post.subreddit)))

                                        try:
                                                self.reddit.redditor(subscriber[0]).message(subject=subject, message=body) 
                                        except Exception as e:
                                                print(e)


        # uses   to check messages and posts in parallel
        def threading(self):
                a = threading.Thread(target=self.get_posts, name='Thread-a', daemon=True)
                b = threading.Thread(target=self.get_messages, name='Thread-b', daemon=True)

                a.start()
                b.start()

                a.join()
                b.join()


if __name__ == '__main__':
        bot().threading()
