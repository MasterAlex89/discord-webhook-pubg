import requests
import json
import sqlite3
import feedparser
from datetime import datetime, timedelta

_version = "0.3-krabbetein"

# sqlite3 setup
conn = sqlite3.connect('pubg.db', detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
c = conn.cursor()
try:
    c.execute('''CREATE TABLE news (id text, date timestamp)''')
except sqlite3.OperationalError:
    print("sqlite table already exists")


class Webhook:

    def __init__(self, id, token, username):
        self.hookId = id
        self.token = token
        self.url = "https://discordapp.com/api/webhooks/" + self.hookId + "/" + self.token
        self.headers = {
            'user-agent': 'discord-webhook-pubg ' + _version,
            'content-type': 'application/x-www-form-urlencoded'
        }
        self.username = username

    def postWebhook(self, message):
        w = {'content': message, 'username': self.username}
        r = requests.post(self.url, headers=self.headers, data=json.dumps(w))

    def checkDate(self, post_date, how_old=3):
        """
         Checks if the post are not more than x (3 is default) days old.
         """
        date = datetime.now() - timedelta(days=how_old)
        # timezones is not supported well
        post = datetime.strptime(post_date.rsplit(' ', 1)[0], "%a, %d %b %Y %H:%M:%S")
        if (date < post):
            return True
        else:
            return False

    def lastPost(self, interval=2):
        """
         checks if theres already been posted since (default) 2 hours ago.
         """
        date = datetime.now() - timedelta(hours=interval)
        c.execute('''SELECT date as "date [timestamp]" FROM news ORDER BY date DESC LIMIT 1''')
        data = c.fetchone()
        if (date > data[0]):
            return True
        else:
            return False

    def checkForum(self, url):
        pubg_news = feedparser.parse(url)

        # check 5 last news
        n = 5
        for x in range(0, n):
            entry = pubg_news['entries'][x]['link']
            id = pubg_news['entries'][x]['id']
            post_date = pubg_news['entries'][x]['published']

            c.execute('SELECT id FROM news WHERE id = ?', (id,))
            data = c.fetchone()

            if (data is None):
                if (self.checkDate(post_date) is True):
                    self.postWebhook(entry)
                    c.execute('INSERT INTO news VALUES (?, ?)', (id, datetime.now()))
                    conn.commit()

    def run(self):
        self.checkForum('https://forums.pubg.com/forum/10-bug-reports-known-issues.xml/')
        self.checkForum('https://forums.pubg.com/forum/5-pc-news-patch-notes.xml/')
