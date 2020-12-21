#!/usr/bin/python
import sqlite3
import string

subreddits = ['LetterstoJNMIL', 'JUSTNOFAMILY', 'JustNoFIL', 'JustNoFriend', 'JustNoCoParent', 'JustNoRoommate', 'JustNoChurch', 'JustNoDIL', 'JustFeedback']

conn = sqlite3.connect('justno.db')

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

for sub in subreddits:
    conn.execute('''INSERT OR IGNORE INTO subreddits(subreddit_name) VALUES(?)''', (str(sub),))
                
conn.commit()
print("Connected to SQLITE database " + sqlite3.version)


conn.execute('''INSERT OR IGNORE INTO posters(poster_name)
                    SELECT DISTINCT SubscribedTo
                    FROM subscriptions''')

conn.commit()

conn.execute('''INSERT OR IGNORE INTO subscribers(subscriber_name)
                    SELECT DISTINCT Subscriber
                    FROM subscriptions''')

conn.commit()

conn.execute('''INSERT OR IGNORE INTO subscription (poster_id, subscriber_id, subreddit_id)
                    SELECT p.poster_id, s.subscriber_id, u.subreddit_id
                    FROM subscriptions d
                    INNER JOIN posters p on d.SubscribedTo = p.poster_name
                    INNER JOIN subscribers s on d.Subscriber = s.subscriber_name
                    INNER JOIN subreddits u on d.Subreddit = u.subreddit_name''')

conn.commit()
