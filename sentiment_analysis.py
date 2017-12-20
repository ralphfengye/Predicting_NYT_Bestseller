# -*- coding: utf-8 -*-
"""
Created on Wed Dec 20 16:41:20 2017

@author: Feng Ye
"""

import pandas as pd

df = pd.read_pickle("NYT_Combined_Fiction.pkl")

#Sentiment comparison were made on sample data between Vader and TextBlob
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

for review in df['critic_reviews'][0]:
    print review
    scores = analyzer.polarity_scores(review)
    for item in scores:
         print item, scores[item]
    print

from textblob import TextBlob

#positive: polarity > 0 and polarity <= 1
#negative : poliarity < 0 and polarity >= -1
#neutral: polarity = 0
for review in df['critic_reviews'][0]:
    analysis = TextBlob(review)
    print review
    print analysis.sentiment.polarity

from __future__ import division, unicode_literals
import math
from textblob import TextBlob as tb

def tf(word, blob):
    return blob.words.count(word) / len(blob.words)

def n_containing(word, bloblist):
    return sum(1 for blob in bloblist if word in blob.words)

def idf(word, bloblist):
    return math.log(len(bloblist) / (1+n_containing(word, bloblist)))

def tfidf(word, blob, bloblist):
    return tf(word, blob) * idf(word, bloblist)

from nltk.corpus import stopwords

#TF-IDF was calculated to weigh importance of each word in reviews
for index, row in df.iterrows():
   
    bloblist = []
    for review in row['critic_reviews']:
        blob = tb(review)
        temp = [word for word in blob.words if word not in stopwords.words('english')]
        review = ' '.join(temp)
        bloblist.append(tb(review))
    
    for i, blob in enumerate(bloblist):
        print 'Top words in review', i+1
        scores = {word: tfidf(word, blob, bloblist) for word in blob.words}
        sorted_words = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        for word, score in sorted_words[:3]: 
            print 'Word:', word, 'TF-IDF:', round(score, 5) 
    if index == 2:
        break

#RAKE package was used to extract keywords
import RAKE
import operator

rake_object = RAKE.Rake('SmartStoplist.txt')
reviews = ' '.join(df['critic_reviews'][0])
keywords = rake_object.run(reviews)

for keyword in keywords:
    if keyword[1] < 4.0:
        break
    print keyword[0], keyword[1]

#
# Code above were utilized to explore and experiment with different approaches
# Code below were employed to produce the final datafame
#
def add_polarity(polarity_for):
    
    #Generate new columns and calculate average polarity scores for both critic
    #and customer reviews
    col = polarity_col = count_col = ''
    if polarity_for == 'critics':
        col = 'critic_reviews'
        polarity_col = 'polarity_mean'
        count_col = 'critic_review_count'
    elif polarity_for == 'customers':
        col = 'amazon_reviews'
        polarity_col = 'polarity_mean_cust'
        count_col = 'cust_review_count'
    else:
        return

    df[count_col] = 0.0
    df[polarity_col] = 0.0
    for index, row in df.iterrows():
    
        if len(row[col])==0:
            continue
    
        total_polarity = 0
        review_count = 0
        for review in row[col]:
            analysis = TextBlob(review)
            total_polarity += analysis.sentiment.polarity
            review_count += 1
    
        df.at[index, polarity_col] = total_polarity/review_count
        df.at[index, count_col] = review_count

add_polarity('critics')
add_polarity('customers')

import inflect
p = inflect.engine()

#Hard coded synonym list for each attribute of fiction
syn_character = ['character', 'antihero', 'hero', 'heroine', 'narrator', 'protagonist', \
'villain', 'figure', 'person', 'role', 'persona', 'antagonist', 'relationship', 'cast']
syn_plot = ['plot', 'story', 'storyline', 'event', 'conflict','content', \
'ending', 'plothole', 'prologue', 'scene', 'narrative', 'climax', 'resolution', \
'sequel', 'aftermath', 'pacing', 'pace', 'subplot', 'storytelling', 'storyteller', \
'point', 'tale']
syn_theme = ['theme', 'subject', 'issue', 'topic', 'motif', \
'thought', 'thesis', 'moral', 'element', 'message'] 
syn_setting = ['setting', 'context', 'backdrop', 'environment', 'surroundings', \
'perspective', 'framework', 'locale', 'location', 'milieu', 'atmosphere', 'mood', \
'detail'] 
syn_style = ['style', 'genre', 'pattern', 'technique', 'tone', 'trend', 'variety', \
'approach', 'characteristic', 'design', 'form', 'method', 'mode', 'trait', \
'voice', 'structure', 'texture', 'dialogue']
syn_overall = ['read', 'novel', 'fiction', 'experience', 'author', 'work', \
'book', 'writer']

def add_plural(word_list):
    temp = []
    for word in word_list:
        temp.append(p.plural(word))
    word_list.extend(temp)
    return word_list

syn_character = add_plural(syn_character)
syn_plot = add_plural(syn_plot)
syn_theme = add_plural(syn_theme)
syn_setting = add_plural(syn_setting)
syn_style = add_plural(syn_style)
syn_overall = add_plural(syn_overall)

syn_all = syn_character + syn_plot + syn_theme + syn_setting + syn_style + syn_overall
print syn_all


#Used spacy package to do dependency parsing on the reviews
import spacy
from spacy.symbols import amod, NOUN, oprd, acomp, nsubj, nsubjpass, advmod, VERB

def add_keyword_pair(keyword_for):

    nlp = spacy.load('en_core_web_sm')
    
    if keyword_for == 'critics':
        col = 'critic_reviews'
        keyword_col = 'keyword_pair'
    elif keyword_for == 'customers':
        col = 'amazon_reviews'
        keyword_col = 'keyword_pair_cust'
    else:
        return

    df[keyword_col] = [[]] * len(df)

    for index, row in df.iterrows():
        keyword_pair = []
        for review in row[col]:
            doc = nlp(review.lower())
            for token in doc:
                #extract adjective followed by a noun
                if token.dep==amod and token.head.pos==NOUN and \
                token.head.text in syn_all:
                    keyword_pair.append(token.text+" "+token.head.text)
            
                #extract noun followed by a verb and then an adverb
                first = ""
                if (token.dep==oprd or token.dep==acomp or token.dep==advmod) and \
                token.head.pos==VERB:
                    first = token
                    verb = token.head
                    second = [child for child in verb.children if child.text in syn_all \
                    and (child.dep==nsubj or child.dep==nsubjpass)]
                    if len(second)!=0:
                        keyword_pair.append(first.text+" "+second[0].text)
                    
        print index
        print keyword_pair
        df.at[index, keyword_col] = keyword_pair

add_keyword_pair('customers')
add_keyword_pair('critics')


#Add attribute scores based on keyword pairs, for both critic and customer reviews
def add_attribute_score(score_for):
    if score_for == 'critics':
        char_col = 'character_critic'
        plot_col = 'plot_critic'
        theme_col = 'theme_critic'
        set_col = 'setting_critic'
        style_col = 'style_critic'
        overall_col = 'overall_critic'
        keyword_col = 'keyword_pair'
    elif score_for == 'customers':
        char_col = 'character_cust'
        plot_col = 'plot_cust'
        theme_col = 'theme_cust'
        set_col = 'setting_cust'
        style_col = 'style_cust'
        overall_col = 'overall_cust'
        keyword_col = 'keyword_pair_cust'
    else:
        return

    df[char_col] = 0.0
    df[plot_col] = 0.0
    df[theme_col] = 0.0
    df[set_col] = 0.0
    df[style_col] = 0.0
    df[overall_col] = 0.0

    for index, row in df.iterrows():
        if len(row[keyword_col])==0:
            continue
    
        polarity_char = polarity_plot = polarity_theme = \
        polarity_set = polarity_style = polarity_all = 0
        num_keyword_char = num_keyword_plot = num_keyword_theme = \
        num_keyword_set = num_keyword_style = num_keyword_all = 0
    
        for keyword in row[keyword_col]:
            attribute = keyword.split()[1] 
            polarity = TextBlob(keyword).sentiment.polarity
            if polarity != 0:
                if attribute in syn_character:
                    polarity_char += polarity
                    num_keyword_char += 1
                elif attribute in syn_plot:
                    polarity_plot += polarity
                    num_keyword_plot += 1
                elif attribute in syn_theme:
                    polarity_theme += polarity
                    num_keyword_theme += 1
                elif attribute in syn_setting:
                    polarity_set += polarity
                    num_keyword_set += 1
                elif attribute in syn_style:
                    polarity_style += polarity
                    num_keyword_style += 1
                elif attribute in syn_overall:
                    polarity_all += polarity
                    num_keyword_all += 1
    
        
        df.at[index, char_col] = (polarity_char / num_keyword_char) if num_keyword_char !=0 else 0
        df.at[index, plot_col] = (polarity_plot / num_keyword_plot) if num_keyword_plot != 0 else 0
        df.at[index, theme_col] = (polarity_theme / num_keyword_theme) if num_keyword_theme !=0 else 0 
        df.at[index, set_col] = (polarity_set / num_keyword_set) if num_keyword_set != 0 else 0
        df.at[index, style_col] = (polarity_style / num_keyword_style) if num_keyword_style != 0 else 0
        df.at[index, overall_col] = (polarity_all / num_keyword_all) if num_keyword_all != 0 else 0

add_attribute_score('customers')
add_attribute_score('critics')