#!/usr/bin/python
import sqlite3
import os

#TODO: Turn this into an actual test file
class test():
    # define variables
    def __init__(self):
        self.posters = ["Test_Poster0", "Test_Poster1", "Test_Poster2"]
        self.subscribers = ["Test_Subscriber0", "Test_Subscriber1", "Test_Subscriber2"]
        self.subreddits = ["Test_Subreddit0", "Test_Subreddit1", "Test_Subreddit2"]

        self.db_name = "test.db"

        self.db_conn = self.db_init()

    # Set up database
    def db_init(self):
        conn = sqlite3.connect(self.db_name)

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
            conn.execute('''INSERT OR IGNORE INTO subreddits(subreddit_name) VALUES(?)''', (sub,))

        conn.commit()
        return conn

    def addSubscriber(self, subscriber, poster, subreddit):
        self.db_conn.execute('''INSERT OR IGNORE INTO posters(poster_name)
                        VALUES(?)''', (poster,))
        self.db_conn.execute('''INSERT OR IGNORE INTO subscribers(subscriber_name)
                        VALUES(?)''', (subscriber,))
        self.db_conn.execute('''INSERT OR IGNORE INTO subscription
                        (poster_id, subscriber_id, subreddit_id)
                        VALUES(
                        (SELECT poster_id FROM posters WHERE poster_name = ?),
                        (SELECT subscriber_id FROM subscribers WHERE subscriber_name = ?),
                        (SELECT subreddit_id FROM subreddits WHERE subreddit_name = ?)) ''',
                        (poster, subscriber, subreddit))

        self.db_conn.commit()

    # Test adding subscribers
    def test_addSubscriber(self):
        self.addSubscriber(self.subscribers[0], self.posters[0], self.subreddits[0])
        self.addSubscriber(self.subscribers[0], self.posters[0], self.subreddits[1])
        self.addSubscriber(self.subscribers[2], self.posters[1], self.subreddits[1])
        self.addSubscriber(self.subscribers[1], self.posters[1], self.subreddits[1])
        self.addSubscriber(self.subscribers[1], self.posters[0], self.subreddits[0])
        self.addSubscriber(self.subscribers[2], self.posters[0], self.subreddits[1])

    # Test retriving subscriber
    def getSubscribers(self):
        output = []
        #subs_ids = self.db_conn.execute('''SELECT d.subscriber_id FROM subscription d
        #                                            INNER JOIN posters p ON p.poster_name = ?
        #                                            INNER JOIN subreddits u ON u.subreddit_name = ?''',
        #                                            (self.posters[0], self.subreddits[0]))

        subs_ids = self.db_conn.execute('''SELECT subscriber_id FROM subscription WHERE poster_id =
                                            (SELECT poster_id FROM posters WHERE poster_name = ?) AND subreddit_id =
                                            (SELECT subreddit_id FROM subreddits WHERE subreddit_name = ?)''',
                                                    (self.posters[0], self.subreddits[0]))
        for sub_id in subs_ids:
            #print(sub_id)
            output.append(self.db_conn.execute('''SELECT subscriber_name FROM subscribers WHERE subscriber_id = ?''', (sub_id)).fetchall()[0][0])

        #print(output)
        for out in output:
            print(out)
            #for o in out:
                #print(o)

    # Test deleting subscriber
    def delSubscriber(self):
        self.db_conn.execute('''DELETE FROM subscription WHERE ID = 
                                        (SELECT ID FROM subscription WHERE poster_id = 
                                        (SELECT poster_id FROM posters WHERE poster_name = ?) AND subscriber_id = 
                                        (SELECT subscriber_id FROM subscribers WHERE subscriber_name = ?) AND subreddit_id = 
                                        (SELECT subreddit_id FROM subreddits WHERE subreddit_name = ?))''',
                                        (self.posters[0], self.subscribers[0], self.subreddits[0]))
    
        self.db_conn.commit()

    def checkDB(self):
        #print("Posters:")
        #p = self.db_conn.execute('''SELECT * FROM posters''')
        #for i in p:
        #    print(i)

        #print("Subreddits:")
        #u = self.db_conn.execute('''SELECT * FROM subreddits''')
        #for i in u:
        #    print(i)

        #print("Subscribers:")
        #s = self.db_conn.execute('''SELECT * FROM subscribers''')
        #for i in s:
        #    print(i)

        print("Subscriptions:")
        d = self.db_conn.execute('''SELECT * FROM subscription''')
        for i in d:
            print(i)

    def cleanup(self):
        self.db_conn.close()
        os.remove(self.db_name)


if __name__ == '__main__':
    print("Starting tests")
    print("Adding subscribers")
    test().test_addSubscriber()
    #test().addSubscriber()
    print("Testing DB:")
    test().checkDB()
    print("Getting subscribers:")
    test().getSubscribers()
    print("Deleting subscribers")
    test().delSubscriber()
    print("Testing DB:")
    test().checkDB()
    print("Getting subscribers:")
    test().getSubscribers()
    print("Cleaning up")
    test().cleanup()
    print("Tests complete")
