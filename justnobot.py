#!/usr/bin/python
import praw
import time
import string
import sqlite3
import threading
import config
import pprint
import sys


class bot():
        # define variables
        def __init__(self):
                self.reddit = praw.Reddit(username = config.username,
                                                                  password = config.password,
                                                                  client_id = config.client_id,
                                                                  client_secret = config.client_secret,
                                                                  user_agent = config.user_agent)

                self.subreddits = config.subreddits

                self.db_connection = self.initiate_database()


        # initiates database
        def initiate_database(self):
                """ create a database connection to a database that resides
                in justno.db file
                """
                try:
                        conn = sqlite3.connect(config.db_name, check_same_thread=False)

                        conn.execute('''CREATE TABLE IF NOT EXISTS posters(
                                        poster_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        poster_name VARCHAR(80) UNIQUE NOT NULL
                                        )'''
                                    )

                        conn.execute('''CREATE TABLE IF NOT EXISTS subscribers(
                                        subscriber_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        subscriber_name VARCHAR(80) UNIQUE NOT NULL
                                        )'''
                                    )

                        conn.execute('''CREATE TABLE IF NOT EXISTS subreddits(
                                        subreddit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        subreddit_name VARCHAR(80) UNIQUE NOT NULL
                                        )'''
                                    )

                        conn.execute('''CREATE TABLE IF NOT EXISTS subscription(
                                        ID INTEGER PRIMARY KEY AUTOINCREMENT,
                                        poster_id INTEGER NOT NULL,
                                        subscriber_id INTEGER NOT NULL,
                                        subreddit_id INTEGER NOT NULL,
                                        FOREIGN KEY (poster_id) references posters(poster_id) ON DELETE CASCADE,
                                        FOREIGN KEY (subscriber_id) references subscribers(subscriber_id) ON DELETE CASCADE,
                                        FOREIGN KEY (subreddit_id) references subreddits(subreddit_id) ON DELETE CASCADE
                                        )'''
                                    )

                        for sub in self.subreddits:
                            conn.execute('''INSERT OR IGNORE INTO subreddits(subreddit_name) VALUES(?)''', (str(sub),))


                        conn.commit()
                        print(f"Connected to SQLITE database {sqlite3.version}", file=sys.stderr)
                        return conn

                except sqlite3.OperationalError as e:
                        print(f"Failed to connect to database: {e}", file=sys.stderr)


        # takes poster and subreddit,
        # searches database returns hits
        def dbsearch(self, poster, subreddit):
                #print("Getting subscribers", file=sys.stderr)
                # Only does specific sub
                # TODO: query for all subs
                subscriber_ids = self.db_connection.execute('''SELECT subscriber_id FROM subscription WHERE poster_id =
                                                                    (SELECT poster_id FROM posters WHERE poster_name = ?) AND subreddit_id =
                                                                    (SELECT subreddit_id FROM subreddits WHERE subreddit_name = ?)''',
                                                                    (poster, subreddit))
                subscribers = []
                for subscriber in subscriber_ids:
                    subscribers.append(self.db_connection.execute('''SELECT subscriber_name FROM subscribers WHERE subscriber_id = ?''', (subscriber)).fetchall()[0][0])

                return subscribers


        # takes subscriber, poster, and subreddit
        # adds poster to database if it's not there
        # adds subscriber to database
        # adds entry to relational table
        # returns boolean
        # TODO: Prevent duplicates
        def addSubscriber(self, subscriber, poster, subreddit):
                try:
                        self.db_connection.execute('''INSERT OR IGNORE INTO posters(poster_name)
                                                            VALUES(?)''', (poster,))
                        self.db_connection.execute('''INSERT OR IGNORE INTO subscribers(subscriber_name)
                                                            VALUES(?)''', (subscriber,))
                        self.db_connection.execute('''INSERT OR IGNORE INTO subscription
                                                            (poster_id, subscriber_id, subreddit_id)
                                                            VALUES(
                                                                    (SELECT poster_id FROM posters WHERE poster_name = ?),
                                                                    (SELECT subscriber_id FROM subscribers WHERE subscriber_name = ?),
                                                                    (SELECT subreddit_id FROM subreddits WHERE subreddit_name = ?)) ''',
                                                                            (poster, subscriber, subreddit))

                except sqlite3.IntegrityError:
                        print("Failed to add subscription", file=sys.stderr)
                        return False

                self.db_connection.commit()

                return True


        # takes subscriber
        # removes subscriber
        # returns boolean
        def removeSubscription(self, subscriber, poster, subreddit):
                try:
                        self.db_connection.execute('''DELETE FROM subscription WHERE ID =
                                                                    (SELECT ID FROM subscription WHERE poster_id =
                                                                    (SELECT poster_id FROM posters WHERE poster_name = ?) AND subscriber_id =
                                                                    (SELECT subscriber_id FROM subscribers WHERE subscriber_name = ?) AND subreddit_id =
                                                                    (SELECT subreddit_id FROM subreddits WHERE subreddit_name = ?))''',
                                                                        (poster, subscriber, subreddit))

                except sqlite3.IntegrityError:
                        print("Failed to delete subscription", file=sys.stderr)
                        return False

                self.db_connection.commit()

                return True


        # Checking if the post has already been responded to
        def sticky_checker(self, post):
            #print("Checking for sticky", file=sys.stderr)
            bot = False
            stickied = False
            for comment in list(post.comments):
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
                print(e, file=sys.stderr)
                pass

        # Get subscription/unsubscription requests
        def get_messages(self):
                print("Getting messages", file=sys.stderr)
                while True:
                        try:
                                for message in self.reddit.inbox.stream():
                                        message.body = message.body.replace(u'\xa0', u' ')
                                        parts = message.body.split(' ')
                                        if len(parts) != 2:
                                                try:
                                                        message.mark_read()
                                                except Exception as e:
                                                        print(e, file=sys.stderr)
                                                continue
                                        else:
                                            subscriber = str(message.author)
                                            poster = str(parts[0])
                                            subreddit = str(parts[1])

                                        # Should really regex this
                                        if message.subject == "Subscribe" and len(parts) > 1:
                                                print("Adding subscriber", file=sys.stderr)
                                                self.addSubscriber(subscriber, poster, subreddit)

                                                subject = f"Successfully subscribed to {poster}"
                                                body = f"You have successfully been subscribed to {poster} in {subreddit}! I will notify you whenever they post."
                                                try:
                                                        self.reddit.redditor(subscriber).message(subject=subject, message=body)
                                                        print("Subscriber notified", file=sys.stderr)
                                                except Exception as e:
                                                        print(e, file=sys.stderr)
                                                        pass


                                        # Should really regex this
                                        elif message.subject == "Unsubscribe" and len(parts) > 1:
                                                print("Removing subscriber", file=sys.stderr)
                                                self.removeSubscription(subscriber, poster, subreddit)

                                                subject = f"Successfully unsubscribed from {poster}"
                                                body = f"You have successfully been unsubscribed from {poster} in {subreddit}! You will no longer be notified when they post."

                                                try:
                                                        self.reddit.redditor(subscriber).message(subject=subject, message=body)
                                                        print("Subscriber notified", file=sys.stderr)
                                                except Exception as e:
                                                        print(e, file=sys.stderr)
                                                        pass


                                        try:
                                                message.mark_read()
                                        except Exception as e:
                                                print(e, file=sys.stderr)
                                                pass

                        except Exception as e:
                                print(f"Restarting messages: {e}", file=sys.stderr)
                                continue

        # Make sure the user exists
        def user_exists(self, name):
                try:
                        user = self.reddit.redditor(str(name)).id
                except Exception as e:
                        print(e, file=sys.stderr)
                        return False
                return True

        # Go though all the posts on the sub
        def get_posts(self):
                print("Getting posts", file=sys.stderr)
                network = self.subreddits[0]

                for i in range(1, len(self.subreddits)):
                    network = network + '+' + self.subreddits[i]

                while True:
                        try:
                                for post in self.reddit.subreddit(network).stream.submissions():

                                        # Don't try to comment on archived posts
                                        if post.archived:
                                            continue

                                        # Check for stickies
                                        sticky = self.sticky_checker(post)

                                        # Make sure the author has not deleted their account,
                                        # the post isn't locked, and we haven't already posted
                                        # on it
                                        if (self.user_exists(post.author) == True) and (sticky[0] == False):
                                                subreddit = post.subreddit
                                                all_rules = f"**Quick Rule Reminders:**\n\nOP's needs come first, avoid dramamongering, respect the flair, and don't be an asshole. If your only advice is to jump straight to NC or divorce, your comment may be subject to removal at moderator discretion.\n\n[**^(Full Rules)**](https://www.reddit.com/r/{subreddit}/wiki/index#wiki_rules) ^(|) [^(Acronym Index)](https://www.reddit.com/r/{subreddit}/wiki/index#wiki_acronym_dictionary) ^(|) [^(Flair Guide)](https://www.reddit.com/r/{subreddit}/wiki/index#wiki_post_flairs)^(|) [^(Report PM Trolls)](https://www.reddit.com/r/{subreddit}/wiki/index#wiki_trolls_suck)\n\n**Resources:** [^(In Crisis?)](https://www.reddit.com/r/JustNoNetwork/wiki/links#wiki_crisis_links.3A_because_there.2019s_more_than_one_type_of_crisis) ^(|) [^(Tips for Protecting Yourself)](https://www.reddit.com/r/JUSTNOMIL/wiki/index#wiki_protecting_yourself) ^(|) [^(Our Book List)](https://www.reddit.com/r/JustNoNetwork/wiki/books) ^(|) [^(This Sub's Wiki)](https://www.reddit.com/r/{subreddit}/wiki/) ^(|) [^(General Resources)](https://www.reddit.com/r/JustNoNetwork/wiki/tos)\n\n"

                                                history = []
                                                # Get all the posts from the sub in OP's history
                                                for link in post.author.submissions.new(limit=100):
                                                        if link.subreddit == subreddit.display_name:
                                                                history.append(link)

                                                message = ''
                                                # First time poster
                                                if len(history) <= 1:
                                                        welcome = f"Welcome to /r/{subreddit}!\n\nI'm JustNoBot. I help people follow your posts!\n\n"
                                                # Previous poster
                                                else:
                                                        welcome = f"Other posts from /u/{post.author}:\n\n\n"

                                                        count = 0
                                                        longer = False
                                                        # Construct the history part of the comment
                                                        for entry in history[1:]:
                                                                post_time = time.strftime('%x %X', time.localtime(entry.created_utc))
                                                                welcome = welcome + (f"* [{post_time}: {entry.title}]({entry.permalink})\n\n")
                                                                count += 1
                                                                if count == 10:
                                                                    longer = True
                                                                    break
                                                        if longer:
                                                                # Add the statement if the history is too long
                                                                welcome = welcome + f"^(This user has more than 10 posts in their history. To see the rest of their posts,) [^(click here)](/u/{post.author}/submitted)\n\n"

                                                # How to subscribe
                                                update = f"\n\n*****\n\n\n\n^(To be notified as soon as {post.author} posts an update) [^click ^here.](http://www.reddit.com/message/compose/?to={config.username}&subject=Subscribe&message={post.author} {subreddit})\n*****\n\n\n"

                                                # Reminding people that getting angry at the comment is useless as
                                                # the bot doesn't give a shit
                                                bot = f"\n\n*^(I am a bot, and this action was performed automatically. Please)* [*^(contact the moderators of this subreddit)*](/message/compose/?to=/r/{subreddit}) *^(if you have any questions or concerns.)*\n\n"

                                                # Construct the comment
                                                message = f"{all_rules}{welcome}{update}{bot}"
                                                # Try catch due to a lot of errors
                                                try:
                                                        comment = post.reply(message)
                                                        print("Commented", file=sys.stderr)
                                                except praw.exceptions.APIException as e:
                                                        print(e, file=sys.stderr)

                                                        if e == "RATELIMIT: 'you are doing that too much. try again in 5 seconds.' on field 'ratelimit'":
                                                                try:
                                                                        comment = post.reply(message)
                                                                except praw.exceptions.APIException as e:
                                                                        print(e, file=sys.stderr)

                                                # Double check that there isn't already a sticky
                                                if sticky[0] == False and sticky[1] == False:
                                                        try:
                                                               comment.mod.distinguish(sticky=True)
                                                        except Exception as e:
                                                               print(e, file=sys.stderr)

                                                # If there is a sticky that isn't the bot, don't sticky the new
                                                # comment
                                                elif sticky[0] == False and sticky[1] == True:
                                                        try:
                                                                comment.mod.distinguish()
                                                        except Exception as e:
                                                                print(e, file=sys.stderr)

                                                # Lock the comment so people stop accidentally replying to it
                                                try:
                                                        self.lock_comment(comment)
                                                except Exception as e:
                                                        print(e, file=sys.stderr)

                                                # Get subscribers
                                                subscribers = self.dbsearch(str(post.author), str(subreddit))

                                                subject = f"New submission by /u/{post.author}"
                                                # Send a message to each subscriber
                                                for subscriber in subscribers:
                                                        body = f"Hello /u/{subscriber},\n\n/u/{post.author} has a new submission in {subreddit}: [{post.title}]({post.permalink})\n\n \n\n*****\n\n\n\n^(To unsubscribe) [^click ^here](http://www.reddit.com/message/compose/?to={config.username}&subject=Unsubscribe&message={post.author} {subreddit})"

                                                        try:
                                                                self.reddit.redditor(subscriber).message(subject=subject, message=body)
                                                                #print("Subscription message sent", file=sys.stderr)
                                                        except Exception as e:
                                                                print(e, file=sys.stderr)

                        except Exception as e:
                                print(f"Restarting posts: {e}", file=sys.stderr)
                                continue


        # uses threading to check messages and posts in parallel
        def threading(self):
                a = threading.Thread(target=self.get_posts, name='Thread-a', daemon=True)
                b = threading.Thread(target=self.get_messages, name='Thread-b', daemon=True)

                a.start()
                b.start()

                a.join()
                b.join()


if __name__ == '__main__':
        print("Booting up", file=sys.stderr)
        bot().threading()
