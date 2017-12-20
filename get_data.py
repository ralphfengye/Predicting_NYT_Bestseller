# -*- coding: utf-8 -*-
"""
Created on Wed Dec 20 16:13:32 2017

@author: Feng Ye
"""

import urllib, json
import pandas as pd
from datetime import datetime, timedelta
from pandas.io.json import json_normalize  

offset = 0
date = "2017-11-11"
df_nyt = pd.DataFrame()
date2 = datetime.strptime(date, "%Y-%m-%d")

#Pulled data from NYT Books API between 2009.10 and 2017.11
#Some hardcover fictions in 2008-2009 were not included due to limit
#of pull requests  
while (date >= "2008-07-01"):
             
    for j in xrange(2):
        try:
            offset = j*20
            url = "https://api.nytimes.com/svc/books/v3/lists.json?offset="+str(offset)+ \
            "&api_key=a03f262051d0419d8d070c60258a6fef&list=hardcover-fiction&date="+date
            response = urllib.urlopen(url)
            data = json.loads(response.read())
            #Flatten the resulting json file to fit into a Pandas dataframe
            df_temp = json_normalize(data["results"], record_path=["book_details"], meta=["list_name", "display_name", \
            "bestsellers_date", "published_date", "rank", "rank_last_week", "weeks_on_list", "amazon_product_url", \
            "isbns", "reviews"])
            df_nyt = df_nyt.append(df_temp)
        except:
            print "error"
            continue
    
    date2 -= timedelta(days=7)
    date = date2.strftime("%Y-%m-%d")
    print date

print len(df_nyt['primary_isbn13'].unique())
print len(df_nyt['title'].unique())

#Group dataframe by title and author, with max of weeks and mean of rank
df_groupby = df_nyt.groupby(["title", "author"], as_index=False).agg({"published_date": "max", "bestsellers_date": "max", \
"publisher": "max", "description": "max", "primary_isbn10": "max", "list_name": "max", "weeks_on_list": "max", "rank": "mean", \
"amazon_product_url": "max", "isbns": "max", "primary_isbn13": "max"})

df_nyt2 = pd.read_pickle("NYT_BestSeller.pkl")

def extract_isbn(isbn, isbn_type):
    isbn_str = ""
    for edition in isbn:
        isbn_str+=(edition[isbn_type]+" ")
    
    return isbn_str.strip()

#Obtain ISBN numbers and store them in new columns
df_nyt2['isbn10'] = df_nyt2['isbns'].apply(extract_isbn, args=('isbn10',))
df_nyt2['isbn13'] = df_nyt2['isbns'].apply(extract_isbn, args=('isbn13',))

import urllib, json
from bs4 import BeautifulSoup

df_nyt2 = df_groupby
isbn13 = ""
df_nyt2["summary"] = ""
df_nyt2["author_info"] = ""
df_nyt2["critic_reviews"] = [[]] * len(df_nyt2)

#Pull critic reviews from API of iDreamBooks.com and store them in NYT dataframe
for index, row in df_nyt2.iterrows():
    reviews = []
    isbn13 = row['primary_isbn13']
   
    try:    
        url = "http://idreambooks.com/api/books/reviews.json?q="+isbn13+"&key=a6327670f6204769a76187ad943d1272eb44fe6b"
        html = urllib.urlopen(url).read()
        url_book = json.loads(html)['book']['detail_link']
        html_book = urllib.urlopen(url_book).read()
     
        #Parse and extract book description, author description, and critic reviews
        soup = BeautifulSoup(html_book, "html.parser")
        summary = soup.find("div", {"class": "book_description_truncated"}).text
        #Replace non-ASCII characters
        summary_clean = ''.join([i if ord(i) < 128 else ' ' for i in summary])
        df_nyt2.set_value(index,'summary', summary_clean.strip())
        author = soup.find("div", {"class": "author_description_truncated"}).text
        author_clean = ''.join([i if ord(i) < 128 else ' ' for i in author])
        df_nyt2.set_value(index, 'author_info', author_clean.strip())
        
        for item in soup.find_all("div", {"class": "critic_boxes_text"}):
            one_review = ''.join([i if ord(i) < 128 else ' ' for i in item.p.text])
            one_review = one_review.replace('...', ' ')
            reviews.append(one_review.strip())
        
        reviews = list(set(reviews))
        df_nyt2.set_value(index, 'critic_reviews', reviews)
    except:
        continue

df_nyt2.to_pickle("NYT_Combined.pkl")

df = pd.read_pickle("NYT_Combined_Fiction.pkl")

from bs4 import BeautifulSoup
import urllib
import re

#Scrape top customer reviews based on amazon product url 
df['amazon_product_url'] = df['amazon_product_url'].str.replace("http", "https")
df['amazon_product_url'] = df['amazon_product_url'].str.replace("httpss", "https")

df['amazon_rating'] = 0.0
df['amazon_review_count'] = 0.0
df['amazon_reviews'] = [[]] * len(df)

token = "-vrwhgKRIo2RXk2_MFXo0w"
for index, row in df.iterrows():
    try:
        #proxycrawl.com was used to mask IP addresses as Amazon detects automated scrapers
        url = "https://api.proxycrawl.com/?token="+token+"&url="+row['amazon_product_url']
        html = urllib.urlopen(url).read()
        soup = BeautifulSoup(html, "html.parser")
        
        reviews = []
        rating = 0
        for item in soup.find_all("span", {"data-hook": "rating-out-of-text"}):
            rating = item.text.split()[0]
        df.at[index, 'amazon_rating'] = rating
    
        num_reviews = 0
        for item in soup.find_all("span", {"data-hook": "total-review-count"}):
            num_reviews = item.text.replace(",", "")
        df.at[index, 'amazon_review_count'] = num_reviews
        
        for item in soup.find_all("div", {"data-hook": "review-collapsed"}):
            one_review = ''.join([i if ord(i) < 128 else '' for i in item.text])
            #Remove special characters from reviews with regex
            one_review = re.sub("[@#$%^&*()[]{};:,/<>\|`~-=_+]", " ", one_review)
            reviews.append(one_review.strip())
        df.at[index, 'amazon_reviews'] = reviews
        print index   
    except:
        print "error"
        continue

df.to_csv("combined_fiction_new3.csv", encoding="utf-8")
df.to_pickle("combined_fiction_new3.pkl")