#!/usr/bin/python
import config

import praw
import time
import threading
import sys
import psycopg2


# TODO: un-OO this? The indentations are ridiculous
# TODO: rework comment strings
class bot():
    # define variables
    def __init__(self, isTest):
        self.reddit = praw.Reddit(username=config.username,
                                  password=config.password,
                                  client_id=config.client_id,
                                  client_secret=config.client_secret,
                                  user_agent=config.user_agent,
                                  )

        if isTest:
            self.subreddits = config.test_subs
            self.dbConn = self.initDB(config.test_db)
        else:
            self.subreddits = config.subreddits
            self.dbConn = self.initDB(config.db_name)

        if self.dbConn:
            self.dbCur = self.dbConn.cursor()
        else:
            sys.exit("Database failure")

        self.network = self.subreddits[0]
        for i in range(1, len(self.subreddits)):
            self.network = f"{self.network}+{self.subreddits[i]}"

    # Initiate PostgreSQL Database
    def initDB(self, database):
        try:
            conn = psycopg2.connect(database=database,
                                    user=config.db_user,
                                    password=config.db_password,
                                    host='postgresql',
                                    )
            cur = conn.cursor()

            cur.execute('''CREATE TABLE IF NOT EXISTS posters(
                            poster_id SERIAL PRIMARY KEY,
                            poster_name VARCHAR(80) UNIQUE NOT NULL
                        )'''
                        )

            cur.execute('''CREATE TABLE IF NOT EXISTS subscribers(
                            subscriber_id SERIAL PRIMARY KEY,
                            subscriber_name VARCHAR(80) UNIQUE NOT NULL
                        )'''
                        )

            cur.execute('''CREATE TABLE IF NOT EXISTS subreddits(
                            subreddit_id SERIAL PRIMARY KEY,
                            subreddit_name VARCHAR(80) UNIQUE NOT NULL
                            )'''
                        )

            cur.execute('''CREATE TABLE IF NOT EXISTS subscription(
                            ID SERIAL PRIMARY KEY,
                            poster_id INT NOT NULL,
                            subscriber_id INT NOT NULL,
                            subreddit_id INT NOT NULL,
                            FOREIGN KEY (poster_id) references
                                posters(poster_id) ON DELETE CASCADE,
                            FOREIGN KEY (subscriber_id) references
                                subscribers(subscriber_id) ON DELETE CASCADE,
                            FOREIGN KEY (subreddit_id) references
                                subreddits(subreddit_id) ON DELETE CASCADE
                          )'''
                        )

            for sub in self.subreddits:
                cur.execute('''INSERT INTO
                                    subreddits (subreddit_name)
                                VALUES
                                    (%s)
                                ON CONFLICT DO NOTHING''',
                            (str(sub),)
                            )

            conn.commit()
            print("Connected to PostgreSQL database", file=sys.stderr)
            return conn

        except Exception as e:
            print(f"Failed to connect to database: {e}", file=sys.stderr)
            return False

    # takes poster and subreddit,
    # searches database returns hits
    def getSubscribers(self, poster, subreddit):
        # Only does specific sub
        # TODO: query for all subs
        # separate queries or use IN?
        self.dbCur.execute('''SELECT
                                subscriber_id
                              FROM
                                subscription
                              WHERE
                                poster_id =
                                (
                                    SELECT
                                        poster_id
                                    FROM
                                        posters
                                    WHERE poster_name = (%s)
                                )
                                AND
                                  subreddit_id =
                                  (
                                    SELECT
                                        subreddit_id
                                    FROM
                                        subreddits
                                    WHERE
                                        subreddit_name = (%s)
                                  )''',
                           (poster, subreddit)
                           )

        sub_ids = []
        subscribers = []
        # TODO: this is redundant, figure out fewer for loops
        for sub in self.dbCur:
            sub_ids.append(sub)

        # TODO: use IN instead of =
        for sub in sub_ids:
            self.dbCur.execute('''SELECT
                  subscriber_name
                 FROM
                  subscribers
                 WHERE
                  subscriber_id = (%s)''',
                               (sub,))
            for result in self.dbCur:
                subscribers.append(result[0])

        return subscribers

    # takes subscriber, poster, and subreddit
    # adds poster to database if it's not there
    # adds subscriber to database
    # adds entry to relational table
    # returns boolean
    # TODO: Prevent duplicates
    def addSubscriber(self, subscriber, poster, subreddit):
        try:
            self.dbCur.execute(
              '''INSERT INTO
                    posters (poster_name)
                VALUES
                    (%s)
                ON CONFLICT DO NOTHING''',
              (poster,)
            )

            self.dbCur.execute(
              '''INSERT INTO
                    subscribers (subscriber_name)
                VALUES
                    (%s)
                ON CONFLICT DO NOTHING''',
              (subscriber,)
            )

            self.dbCur.execute(
              '''INSERT INTO subscription
                  (poster_id, subscriber_id, subreddit_id)
                VALUES
                (
                  (
                  SELECT
                    poster_id
                  FROM
                    posters
                  WHERE
                    poster_name = %s
                  ),
                  (
                    SELECT
                      subscriber_id
                    FROM
                      subscribers
                    WHERE
                      subscriber_name = %s
                  ),
                  (
                    SELECT
                      subreddit_id
                  FROM
                    subreddits
                  WHERE
                    subreddit_name = %s
                  )
                     )
                    ON CONFLICT DO NOTHING''',
              (poster, subscriber, subreddit)
            )

        except Exception as e:
            print(f"Failed to add subscription: {e}", file=sys.stderr)
            return False

        self.dbConn.commit()

        return True

    # takes subscriber
    # removes subscriber
    # returns boolean
    def removeSubscription(self, subscriber, poster, subreddit):
        try:
            self.dbCur.execute(
              '''DELETE FROM subscription WHERE ID =
                (
                  SELECT
                    ID
                  FROM
                    subscription
                  WHERE
                    poster_id =
                    (
                      SELECT
                        poster_id
                      FROM
                        posters
                      WHERE
                        poster_name = %s
                    )
                    AND
                      subscriber_id =
                      (
                        SELECT
                          subscriber_id
                        FROM
                          subscribers
                        WHERE
                          subscriber_name = %s
                      )
                      AND
                        subreddit_id =
                      (
                        SELECT
                          subreddit_id
                        FROM
                          subreddits
                        WHERE
                          subreddit_name = %s
                      )
                )''',
              (poster, subscriber, subreddit)
            )

        except Exception as e:
            print(f"Failed to delete subscription: {e}", file=sys.stderr)
            return False

        self.dbConn.commit()

        return True

    # Check if the post has already been responded to
    def stickyChecker(self, post):
        bot = False
        stickied = False
        for comment in list(post.comments):
            # Check for a sticky
            if comment.stickied is True:
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

    def lockComment(self, comment_id):
        try:
            self.reddit.comment(str(comment_id)).mod.lock()
        except Exception as e:
            print(e, file=sys.stderr)
            pass

    # Make sure the user exists
    # TODO: this check doesn't actual do anything?
    # Though it might error out if the user isn't found
    def userExists(self, name):
        try:
            self.reddit.redditor(str(name)).id
        except Exception as e:
            print(e, file=sys.stderr)
            return False
        return True

    # Get all the posts from the sub in OP's history
    def getHistory(self, user, subreddit):
        history = []
        for link in user.submissions.new(limit=100):
            if link.subreddit == subreddit.display_name:
                history.append(link)

        welcome = ''
        # First time poster
        if len(history) <= 1:
            welcome = f"Welcome to /r/{subreddit}!\n\nI'm JustNoBot. " \
                  "I help people follow your posts!\n\n"
        # Previous poster
        else:
            welcome = f"Other posts from /u/{user}:\n\n\n"

            count = 0
            longer = False
            # Construct the history part of the comment
            for entry in history[1:]:
                post_time = time.strftime(
                  '%x %X',
                  time.localtime(entry.created_utc)
                )
                welcome = welcome + (
                  f"* [{post_time}: {entry.title}]({entry.permalink})\n\n"
                )
                count += 1
                if count == 10:
                    longer = True
                    break
            if longer:
                # Add the statement if the history is too long
                welcome = welcome + \
                  "^(This user has more than 10 posts in their history." \
                  "To see the rest of their posts,)" \
                  f"[^(click here)](/u/{user}/submitted)\n\n"

        return welcome

    # TODO: refactor/simplify
    # Post the actual comment
    def postComment(self, post, message, sticky):
        try:
            comment = post.reply(message)
            print("Commented", file=sys.stderr)
        except praw.exceptions.APIException as e:
            print(e, file=sys.stderr)

            if e == "RATELIMIT: 'you are doing that too much. " \
                    "try again in 5 seconds.' on field 'ratelimit'":
                try:
                    comment = post.reply(message)
                except praw.exceptions.APIException as e:
                    print(e, file=sys.stderr)

    # Double check that there isn't already a sticky
        if sticky[0] is False and sticky[1] is False:
            try:
                comment.mod.distinguish(sticky=True)
            except Exception as e:
                print(e, file=sys.stderr)
        # If there is a sticky that isn't the bot, don't sticky the new
        # comment
        elif sticky[0] is False and sticky[1] is True:
            try:
                comment.mod.distinguish()
            except Exception as e:
                print(e, file=sys.stderr)

        # Lock the comment so people stop accidentally replying to it
        try:
            self.lockComment(comment)
        except Exception as e:
            print(e, file=sys.stderr)

    def pingSubscribers(self, post, subreddit):
        print("Getting subscribers", file=sys.stderr)
        # Get subscribers
        subscribers = self.getSubscribers(str(post.author), str(subreddit))

        subject = f"New submission by /u/{post.author}"
        # Send a message to each subscriber
        for subscriber in subscribers:
            body = f"Hello /u/{subscriber},\n\n/u/{post.author} has a new " \
                "submission in {subreddit}: [{post.title}]" \
                "({post.permalink})\n\n \n\n*****\n\n\n\n" \
                "^(To unsubscribe) " \
                "[^click ^here](http://www.reddit.com/message/compose/" \
                "?to={config.username}&subject=Unsubscribe&message=" \
                "{post.author} {subreddit})"

            try:
                self.reddit.redditor(subscriber).message(
                  subject=subject,
                  message=body
                )
                print("Subscription message sent", file=sys.stderr)
            except Exception as e:
                print(e, file=sys.stderr)

    # TODO: refactor/simplify?
    # Get subscription/unsubscription requests
    def getMessages(self):
        print("Getting messages", file=sys.stderr)
        while True:
            try:
                for message in self.reddit.inbox.stream():
                    print("In inbox stream", file=sys.stderr)
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
                        body = "You have successfully been subscribed to " \
                            f"{poster} in {subreddit}! " \
                            "I will notify you whenever they post."
                        try:
                            self.reddit.redditor(subscriber).message(
                              subject=subject,
                              message=body
                            )
                            print("Subscriber notified", file=sys.stderr)
                        except Exception as e:
                            print(e, file=sys.stderr)
                            pass

                    # Should really regex this
                    elif message.subject == "Unsubscribe" and len(parts) > 1:
                        print("Removing subscriber", file=sys.stderr)
                        self.removeSubscription(subscriber, poster, subreddit)

                        subject = f"Successfully unsubscribed from {poster}"
                        body = "You have successfully been unsubscribed " \
                            f"from {poster} in {subreddit}! You will no " \
                            "longer be notified when they post."

                        try:
                            self.reddit.redditor(subscriber).message(
                              subject=subject,
                              message=body
                            )
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

    # TODO: refactor: simplify!
    # Go though all the posts on the sub
    def getPosts(self):
        print("Getting posts", file=sys.stderr)

        while True:
            try:
                for post in self.reddit.subreddit(
                        self.network).stream.submissions():
                    # Don't try to comment on archived posts
                    if post.archived:
                        continue

                    # Check for stickies
                    sticky = self.stickyChecker(post)

                    # Make sure the author has not deleted their account,
                    # the post isn't locked, and we haven't already posted
                    # on it
                    if (self.userExists(post.author) is True) and (
                            sticky[0] is False):
                        subreddit = post.subreddit
                        # TODO: Seriously rewrite this
                        all_rules = "**Quick Rule Reminders:**" \
                            "\n\nOP's needs come first, " \
                            "avoid dramamongering, respect the flair, " \
                            "and don't be an asshole. If your only " \
                            "advice is to jump straight to NC " \
                            "or divorce, your comment may be subject " \
                            "to removal at moderator discretion.\n\n" \
                            "[**^(Full Rules)**]" \
                            f"(https://www.reddit.com/r/{subreddit}/wiki/"\
                            "index#wiki_rules) ^(|) [^(Acronym Index)]" \
                            f"(https://www.reddit.com/r/{subreddit}" \
                            "/wiki/index#wiki_acronym_dictionary) ^(|) " \
                            "[^(Flair Guide)](https://www.reddit.com" \
                            f"/r/{subreddit}/wiki/index#wiki_post_flairs)"\
                            "^(|) [^(Report PM Trolls)]" \
                            f"(https://www.reddit.com/r/{subreddit}" \
                            "/wiki/index#wiki_trolls_suck)\n\n" \
                            "**Resources:** [^(In Crisis?)]" \
                            "(https://www.reddit.com/r/JustNoNetwork/" \
                            "wiki/links#wiki_crisis_links." \
                            "3A_because_there." \
                            "2019s_more_than_one_type_of_crisis) ^(|) " \
                            "[^(Tips for Protecting Yourself)]" \
                            "(https://www.reddit.com/r/JUSTNOMIL/wiki/" \
                            "index#wiki_protecting_yourself) ^(|) " \
                            "[^(Our Book List)](https://www.reddit.com" \
                            "/r/JustNoNetwork/wiki/books) ^(|) "\
                            "[^(This Sub's Wiki)](https://www.reddit.com" \
                            f"/r/{subreddit}/wiki/) ^(|) " \
                            "[^(General Resources)]" \
                            "(https://www.reddit.com/r/" \
                            "JustNoNetwork/wiki/tos)\n\n"

                        # Get OP's history in the sub
                        welcome = self.getHistory(post.author, subreddit)

                        # How to subscribe
                        update = "\n\n*****\n\n\n\n^(To be notified as " \
                            f"soon as {post.author} posts an update) " \
                            "[^click ^here.](http://www.reddit.com/" \
                            f"message/compose/?to={config.username}" \
                            f"&subject=Subscribe&message={post.author} " \
                            f"{subreddit})\n*****\n\n\n"

                        # Reminding people that getting angry at the
                        # comment is useless as the bot doesn't give a shit
                        bot = "\n\n*^(I am a bot, and this action " \
                            "was performed automatically. Please)* " \
                            "[*^(contact the moderators of this " \
                            "subreddit)*](/message/compose/?to=/r/" \
                            f"{subreddit}) *^(if you have any questions " \
                            "or concerns.)*\n\n"

                        # Construct the comment
                        message = f"{all_rules}{welcome}{update}{bot}"

                        # Post the comment
                        self.postComment(post, message, sticky)

                        # Inform subscribers
                        self.pingSubscribers(post, subreddit)

            except Exception as e:
                print(f"Restarting posts: {e}", file=sys.stderr)
                time.sleep(60)
                continue

    # uses threading to check messages and posts in parallel
    def threading(self):
        a = threading.Thread(
          target=self.getPosts,
          name='Posts',
          daemon=True
        )
        b = threading.Thread(
          target=self.getMessages,
          name='Messages',
          daemon=True
        )

        a.start()
        b.start()

        a.join()
        b.join()


if __name__ == '__main__':
    print("Booting up", file=sys.stderr)
    bot(False).threading()
