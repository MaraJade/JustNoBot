#!/usr/bin/python
import config

# IDEAS:
#   String functions:
#       * table-izer
#       * linkifier: take text and link
#       * italisizer

a = "temp"

subreddit = a
user = a
post_time = a
entry = a
post = a
poster = a
subscriber = a

lineBreak = "\n\n"
doubleBreak = "\n\n\n\n"
tableBreak = " ^(|) "


# Welcome options: first time poster or returning poster
newWelcome = f"Welcome to /r/{subreddit}!{lineBreak}I'm JustNoBot. I help people follow your posts!{lineBreak}"
returnWelcome = f"Other posts from /u/{user}:{doubleBreak}"

# User history
entry = f"* [{post_time}: {entry.title}]({entry.permalink})"
longer = "^(This user has more than 10 posts in their history." \
        "To see the rest of their posts,)" \
        f"[^(click here)](/u/{user}/submitted){linebreak}"

quickRules = f"**Quick Rule Reminders:**{lineBreak}" \
    "OP's needs come first, avoid dramamongering, respect the flair, " \
    "and don't be an asshole. If your only advice is to jump straight to NC " \
    "or divorce, your comment may be subject to removal at moderator " \
    "discretion."

fullRules = f"[**^(Full Rules)**](https://www.reddit.com/r/{subreddit}/wiki/index#wiki_rules) "
acronymIndex = f"{tableBreak}^[^(Acronym Index)](https://www.reddit.com/r/{subreddit}/wiki/index#wiki_acronym_dictionary) "
flairGuide = f"{tableBreak}[^(Flair Guide)](https://www.reddit.com/r/{subreddit}/wiki/index#wiki_post_flairs)"
reportTrolls = f"{tableBreak}[^(Report PM Trolls)](https://www.reddit.com/r/{subreddit}/wiki/index#wiki_trolls_suck)"

resources = "{lineBreak}**Resources:**"
crisis = "{tableBreak}[^(In Crisis?)](https://www.reddit.com/r/JustNoNetwork/wiki/links#wiki_crisis_links.3A_because_there.2019s_more_than_one_type_of_crisis)"
protection = "{tableBreak}[^(Tips for Protecting Yourself)](https://www.reddit.com/r/JUSTNOMIL/wiki/index#wiki_protecting_yourself)"
bookList = "{tableBreak}[^(Our Book List)](https://www.reddit.com/r/JustNoNetwork/wiki/books)"
wiki = f"{tableBreak}[^(This Sub's Wiki)](https://www.reddit.com/r/{subreddit}/wiki/)"
general = "{tableBreak}[^(General Resources)](https://www.reddit.com/r/JustNoNetwork/wiki/tos){lineBreak}"

update = "{lineBreak}*****{doubleBreak}^(To be notified as soon as {post.author} posts an update) " \
    "[^click ^here.](http://www.reddit.com/message/compose/?to={config.username}&subject=Subscribe&message={post.author} {subreddit}){lineBreak}*****{doubleBreak}"

bot = "{lineBreak}*^(I am a bot, and this action was performed automatically. " \
    "Please)* [*^(contact the moderators of this subreddit)*](/message/compose/?to=/r/{subreddit}) " \
    "*^(if you have any questions or concerns.)*{lineBreak}"

# Subscriber notification
subject = f"New submission by /u/{post.author}"
body = f"Hello /u/{subscriber},{linebreak}" \
    f"/u/{post.author} has a new submission in {subreddit}: " \
    f"[{post.title}]({post.permalink}){doubleBreak}*****{doubleBreak}" \
    "^(To unsubscribe) [^click ^here]" \
    f"(http://www.reddit.com/message/compose/?to={config.username}&subject=Unsubscribe&message={post.author} {subreddit})"

# Subscribe response
subject = f"Successfully subscribed to {poster}"
body = f"You have successfully been subscribed to {poster} in {subreddit}! " \
        "I will notify you whenever they post."

# Unsubscribe response
subject = f"Successfully unsubscribed from {poster}"
body = f"You have successfully been unsubscribed from {poster} in " \
    f"{subreddit}! You will no longer be notified when they post."

