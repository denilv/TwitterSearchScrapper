from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from time import sleep
import json
import urllib
import sys
import datetime
from urllib import parse
import requests
from bs4 import BeautifulSoup
from random import randint
import os

def format_day(date):
    day = '0' + str(date.day) if len(str(date.day)) == 1 else str(date.day)
    month = '0' + str(date.month) if len(str(date.month)) == 1 else str(date.month)
    year = str(date.year)
    return '-'.join([year, month, day])

def form_url(ticker, since, until):
#https://twitter.com/search?
#    l=en&q=%24AAPL%20OR%20%23AAPL%20since%3A2017-02-14%20until%3A2017-02-15&src=typd%20include%3Aretweets&src=typd
    #'https://twitter.com/search?
    p1 = 'l=en&q=%24' + ticker + '%20OR%20%23' + ticker
    p2 =  '%20since%3A' + since + '%20until%3A' + until + '%20include%3Aretweets&src=typd'
    return p1 + p2

def increment_day(date, i):
    return date + datetime.timedelta(days=i)

def str2bool(s):
    if s in ['True', 'true', 'TRUE', 'T']:
        return True
    else:
        return False

def construct_url(query, since, until, max_position=None):
    url = "https://twitter.com/i/search/timeline?q=%s&src=typd&%smax_position=%s"
        
    urlGetData = ''
    urlGetData += ' since:' + since
    urlGetData += ' until:' + until
    urlGetData += ' ' + query
    urlLang = 'l=en&'
    url = url % (urllib.parse.quote(urlGetData), urlLang, max_position)
    return url
    
def parse_tweets(html_items):
    soup = BeautifulSoup(html_items, 'lxml')
    tweets = []
    for li in soup.find_all('li', class_='stream-item'):
        if 'data-item-id' not in li.attrs:
            continue
        
        tweet = {
            'text': None,
            'id': int(li['data-item-id']),
            'link': None,
            'timestamp': None,
            'reply_id' : 0,
            'reply' : False,
            'retweet_id' : 0,
            'retweet' : False,
            'retweets': 0,
            'quote': False,
            'quote_id': 0,
            'favorites': 0,
            'replies': 0,
            'attach' : False,
#             'attach_link': None,
            'mentions' : [],
            'user_id': None,
            'user_username': None,
            'user_name': None,
        }
        text_p = li.find("p", class_="tweet-text")
        if text_p is not None:
            tweet['text'] = text_p.get_text()

        user_details_div = li.find("div", class_="tweet")
        if user_details_div is not None:
            tweet['link'] = 'https://twitter.com' + user_details_div['data-permalink-path']
            tweet['user_id'] = user_details_div['data-user-id']
            tweet['user_username'] = user_details_div['data-screen-name']
            tweet['user_name'] = user_details_div['data-name']
            if 'data-mentions' in user_details_div.attrs:
                tweet['mentions'] = user_details_div['data-mentions'].split()
            tweet['reply_id'] = int(user_details_div['data-conversation-id'])
            if tweet['reply_id'] != tweet['id']:
                tweet['reply'] = True
            if 'data-retweeter-id' in user_details_div.attrs:
                tweet['retweet'] = True
            
        quote_details = li.find("a", class_="QuoteTweet-link")
        if quote_details is not None:
            tweet['quote'] = True
            tweet['quote_id'] = quote_details['data-conversation-id']
            
        attach_details = li.find('div', class_='card2')
        if attach_details is not None:
            tweet['attach'] = True
#             attach_link_details = attach_details.find('span', class_='TwitterCardsGrid-col--spacerTop SummaryCard-destination').text
        
        
        # Tweet timestamp
        date_span = li.find("span", class_="_timestamp")
        if date_span is not None:
            tweet['timestamp'] = int(date_span['data-time'])

        # Tweet Replies
        reply_span = li.select("span.ProfileTweet-action--reply > span.ProfileTweet-actionCount")
        if reply_span is not None and len(reply_span) > 0:
            tweet['replies'] = int(reply_span[0]['data-tweet-stat-count'])
            
        # Tweet Retweets
        retweet_span = li.select("span.ProfileTweet-action--retweet > span.ProfileTweet-actionCount")
        if retweet_span is not None and len(retweet_span) > 0:
            tweet['retweets'] = int(retweet_span[0]['data-tweet-stat-count'])

        # Tweet Favourites
        favorite_span = li.select("span.ProfileTweet-action--favorite > span.ProfileTweet-actionCount")
        if favorite_span is not None and len(retweet_span) > 0:
            tweet['favorites'] = int(favorite_span[0]['data-tweet-stat-count'])

        tweets.append(tweet)
    
    return tweets

error_delay = 20
def get_search_data(url):
    headers = {
        'Host': "twitter.com",
        'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36",

        'Accept': "application/json, text/javascript, */*; q=0.01",
        'Accept-Language': "en-US;q=0.7,en;q=0.3",
        'X-Requested-With': "XMLHttpRequest",
        'Referer': url,
        'Connection': "keep-alive"
    }
    try:
        req = requests.get(url, headers=headers)
        data = json.loads(req.text)
        return data
    except Exception as e:
        print(e)
        print("Sleeping for %i" % error_delay)
        sleep(error_delay)
#         return get_search_data(url)
        headers = {
	        'Host': "twitter.com",
       		'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
	        'Accept': "application/json, text/javascript, */*; q=0.01",
	        'Accept-Language': "en-US;q=0.7,en;q=0.3",
	        'X-Requested-With': "XMLHttpRequest",
	        'Referer': url,
	        'Connection': "keep-alive"
	    }
        req = requests.get(url, headers=headers)
        data = json.loads(req.text)
        return data
    return 

max_delay = 1
def get_tweets(query, since, until):
    all_tweets = []
    days = (until - since).days
    for day in range(days):
        tweets_per_day = []
        d1 = format_day(increment_day(since, 0))
        d2 = format_day(increment_day(since, 1))
        url = construct_url(query, d1, d2)
        print(url)
        min_tweet = None
        continue_search = True
        response = get_search_data(url)
        if not('items_html' in response):
        	print('Slepping for {} seconds'.format(error_delay))
        	sleep(error_delay)
        	response = get_search_data(url)
        while response is not None and continue_search and response['items_html'] is not None:
            tweets = parse_tweets(response['items_html'])
            print('Collected {} tweets'.format(len(tweets)))
            tweets_per_day += tweets
            print('Tweets per day {} tweets'.format(len(tweets_per_day)))
            if len(tweets) == 0:
                break
            if min_tweet is None:
                min_tweet = tweets[0]
            max_tweet = tweets[-1]
            if min_tweet['id'] is not max_tweet['id']:
                if "min_position" in response.keys():
                    max_position = response['min_position']
                else:
                    max_position = "TWEET-%s-%s" % (max_tweet['tweet_id'], min_tweet['tweet_id'])
                url = construct_url(query, d1, d2, max_position=max_position)
                # Sleep for our rate_delay
                sleep(randint(5, max_delay * 10) / 10) #sleep random(0.5, max_delay)
                response = get_search_data(url)
        filename = ticker + '_' + str(since)
        path = 'tweetsPerDay/' + ticker.upper() + '/' + str(since.year) + '/'
        save(path, filename, tweets_per_day)
        all_tweets += tweets_per_day
        print("TOTAL {} TWEETS".format(len(all_tweets)))        
        since = increment_day(since, 1)
    return all_tweets

def generate_query(ticker):
    query = '$' + ticker + ' OR ' + '#' + ticker
    return query

def save(path, filename, file):
    if not os.path.exists(path):
        os.makedirs(path)
    try:
        with open(path + filename, 'w') as outfile:
            json.dump(file, outfile)
    except Exception as e:
        print(e)
        print('Oooops')


ticker = sys.argv[1]#'AMZN'
begin = datetime.datetime.strptime(sys.argv[2], '%Y-%m-%d').date()
end = datetime.datetime.strptime(sys.argv[3], '%Y-%m-%d').date()

q = generate_query(ticker)
tweets = get_tweets(q, begin, end)

filename = ticker + '_' + str(begin) + '_' + str(end)
path = 'dump/' + ticker.upper() + '/'
save(path, filename, tweets)