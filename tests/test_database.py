#!/usr/bin/python
from justnobot import bot
import config

import unittest
import sqlite3
import sys
import os

#TODO: Turn this into an actual test file
class TestDatabase(unittest.TestCase):
        def setUp(self):
                print("\nSetting up", file=sys.stderr)
                self.posters = ["Test_Poster0", "Test_Poster1", "Test_Poster2"]
                self.subscribers = ["Test_Subscriber0", "Test_Subscriber1", "Test_Subscriber2"]
                self.subreddits = ["Test_Subreddit0", "Test_Subreddit1", "Test_Subreddit2"]

                self.testBot = bot(True)

        # Test adding subscribers
        def test_addSubscriber(self):
                self.testBot.addSubscriber(self.subscribers[0], self.posters[0], self.subreddits[0])
                self.assertEqual(self.checkSubscribers(), [self.subscribers[0]])
                self.assertEqual(self.checkPosters(), [self.posters[0]])

                self.testBot.addSubscriber(self.subscribers[0], self.posters[0], self.subreddits[1])
                self.assertEqual(self.checkSubscribers(), [self.subscribers[0]])
                self.assertEqual(self.checkPosters(), [self.posters[0]])

                self.testBot.addSubscriber(self.subscribers[2], self.posters[1], self.subreddits[1])
                self.assertEqual(self.checkSubscribers(), [self.subscribers[0], self.subscribers[2]])
                self.assertEqual(self.checkPosters(), [self.posters[0], self.posters[1]])

                self.testBot.addSubscriber(self.subscribers[1], self.posters[1], self.subreddits[1])
                self.assertEqual(self.checkSubscribers(), [self.subscribers[0], self.subscribers[2], self.subscribers[1]])
                self.assertEqual(self.checkPosters(), [self.posters[0], self.posters[1]])

                self.testBot.addSubscriber(self.subscribers[1], self.posters[0], self.subreddits[0])
                self.assertEqual(self.checkSubscribers(), [self.subscribers[0], self.subscribers[2], self.subscribers[1]])
                self.assertEqual(self.checkPosters(), [self.posters[0], self.posters[1]])

                self.testBot.addSubscriber(self.subscribers[2], self.posters[0], self.subreddits[1])
                self.assertEqual(self.checkSubscribers(), [self.subscribers[0], self.subscribers[2], self.subscribers[1]])
                self.assertEqual(self.checkPosters(), [self.posters[0], self.posters[1]])


        # Test retriving subscribers
        def test_getSubscribers(self):
                self.assertEqual(self.checkSubscribers(), [])
                self.testBot.addSubscriber(self.subscribers[0], self.posters[0], self.subreddits[0])
                self.assertEqual(self.testBot.getSubscribers(self.posters[0], self.subreddits[0]), [self.subscribers[0]])

                self.testBot.addSubscriber(self.subscribers[0], self.posters[0], self.subreddits[1])
                self.assertEqual(self.testBot.getSubscribers(self.posters[0], self.subreddits[1]), [self.subscribers[0]])

                self.testBot.addSubscriber(self.subscribers[1], self.posters[1], self.subreddits[1])
                self.assertEqual(self.testBot.getSubscribers(self.posters[1], self.subreddits[1]), [self.subscribers[1]])

                self.testBot.addSubscriber(self.subscribers[2], self.posters[1], self.subreddits[1])
                self.assertEqual(self.testBot.getSubscribers(self.posters[1], self.subreddits[1]), [self.subscribers[1], self.subscribers[2]])

                self.testBot.addSubscriber(self.subscribers[1], self.posters[0], self.subreddits[0])
                self.assertEqual(self.testBot.getSubscribers(self.posters[0], self.subreddits[0]), [self.subscribers[0], self.subscribers[1]])

                self.testBot.addSubscriber(self.subscribers[2], self.posters[0], self.subreddits[1])
                self.assertEqual(self.testBot.getSubscribers(self.posters[0], self.subreddits[1]), [self.subscribers[0], self.subscribers[2]])


        # Test deleting subscribers
        def test_removeSubscriber(self):
                self.testBot.addSubscriber(self.subscribers[0], self.posters[0], self.subreddits[0])
                self.testBot.addSubscriber(self.subscribers[0], self.posters[0], self.subreddits[2])
                self.testBot.addSubscriber(self.subscribers[0], self.posters[1], self.subreddits[0])
                self.testBot.addSubscriber(self.subscribers[0], self.posters[2], self.subreddits[1])
                self.testBot.addSubscriber(self.subscribers[1], self.posters[1], self.subreddits[0])
                self.testBot.addSubscriber(self.subscribers[2], self.posters[0], self.subreddits[2])
                self.testBot.addSubscriber(self.subscribers[1], self.posters[2], self.subreddits[1])
                self.testBot.addSubscriber(self.subscribers[2], self.posters[1], self.subreddits[1])

                self.assertEqual(self.checkSubscribers(), self.subscribers)
                self.assertEqual(self.checkPosters(), self.posters)

                self.assertEqual(self.testBot.getSubscribers(self.posters[0], self.subreddits[0]), [self.subscribers[0]])
                self.testBot.removeSubscription(self.subscribers[0], self.posters[0], self.subreddits[0])
                self.assertEqual(self.checkSubscribers(), self.subscribers)
                self.assertEqual(self.checkPosters(), self.posters)
                self.assertEqual(self.testBot.getSubscribers(self.posters[0], self.subreddits[0]), [])

                self.assertEqual(self.testBot.getSubscribers(self.posters[1], self.subreddits[0]), [self.subscribers[0], self.subscribers[1]])
                self.testBot.removeSubscription(self.subscribers[0], self.posters[1], self.subreddits[0])
                self.assertEqual(self.checkSubscribers(), self.subscribers)
                self.assertEqual(self.checkPosters(), self.posters)
                self.assertEqual(self.testBot.getSubscribers(self.posters[1], self.subreddits[0]), [self.subscribers[1]])

        def checkSubscribers(self):
                subs = []
                for subscriber in self.testBot.db_connection.execute('''SELECT * FROM subscribers''').fetchall():
                        subs.append(subscriber[1])
                return subs

        def checkPosters(self):
                posters = []
                for poster in self.testBot.db_connection.execute('''SELECT * FROM posters''').fetchall():
                        posters.append(poster[1])
                return posters

        def tearDown(self):
                print("Cleaning up", file=sys.stderr)
                self.testBot.db_connection.close()
                os.remove(config.test_db)


if __name__ == '__main__':
        unittest.main()
