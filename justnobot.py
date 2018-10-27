#!/usr/bin/python
import praw
import time

SUBREDDIT = "MaraTesting"
USER_AGENT = "bot1"

def duplicate_preventer(post):
    for comment in list(post.comments):
        if comment.author == "Mara_Jade_Skywalker":
            return True

    return False

def get_posts():
    for post in subreddit.stream.submissions():
        if duplicate_preventer(post):
            continue
        history = []
        for link in post.author.submissions.new():
            print(link.subreddit)
            if link.subreddit == "MaraTesting":
                history.append(link)

        message = "Other posts from /u/{}:\n\n\n".format(str(post.author))

        count = 0
        longer = False
        for entry in history:
            message = message + ("* [{}]({})\n\n".format(str(entry.title), str(entry.permalink)))
            count = count + 1 
            if count == 10:
                longer = True
                break

        if longer:
            message = message + ("This user has more than 10 posts in their history. To see the rest of their posts, click [here](/u/{}/submitted)\n\n".format(str(post.author)))

        #message = message + ("^(To be notified as soon as {} posts an update) [^click ^here.](http://www.reddit.com/message/compose/?to=MilBitchBot&subject=subscribe&message=subscribe {})".format(str(post.author), str(post.author)))
        message = message + ("Subscriptions are in progress. Please stand by")

        post.reply(message)

        time.sleep(2)

if __name__ == '__main__':
    reddit = praw.Reddit('bot1')
    subreddit = reddit.subreddit("MaraTesting")
    get_posts()
