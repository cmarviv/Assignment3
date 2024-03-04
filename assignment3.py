# -*- coding: utf-8 -*-
"""Assignment3.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1_g6iw4Np1UuOi3TpbRvr275BZHtbEBnA
"""

import pandas as pd
import redis as r
import json
import requests
import yaml
from redis.commands.json.path import Path

def load_config():
    """Load configuration from the YAML file.

    Returns:
        dict: Configuration data.
    """
    with open("config.yaml", "r") as file:
        return yaml.safe_load(file)


config = load_config()


def get_redis_connection():
    """Create a Redis connection using the configuration.

    Returns:
        Redis: Redis connection object.
    """
    return r.Redis(
        host=config["redis"]["host"],
        port=config["redis"]["port"],
        db=0,
        decode_responses=True,
        username=config["redis"]["user"],
        password=config["redis"]["password"],
    )

class RedisAccessor:
    """
    Class: RedisAccessor
    Description: This class stores and retrieves data from Redis.
    """

    def __init__(self):

        """
        Function: Constructor
        Description: Creates an object of type RedisAccessor.
        Arguments: self - the class object
        Returns: None
        """
        self.__redis_connection = get_redis_connection()

        self.__redis_connection.flushall()

    def setArticles(self, key, articles):
        """
        Function Abstract: setArticles()
        Description: This function uses Redis' connection to set data in a Python dictionary
                     of articles.
        Arguments: self - the class object
                   key - the index for the articles
                   articles - the dictionary that contains a dictionary of the actual articles to store
        Returns: updated_key - the updated numerical key for the articles
        """
        true_articles = articles['articles']
        updated_key = key
        for article in true_articles:
            format_key = (f"article:{updated_key}")
            self.__redis_connection.json().set(format_key, Path.root_path(), json.dumps(article))
            updated_key = updated_key + 1
        return updated_key

    def getArticle(self, key):
        """
        Function: getArticle()
        Description: This function uses Redis' connection to get an article using a given key.
        Arguments: self - the class object
                   key - the key for the requested article
        Returns: article - the article obtained from Redis for the given key
        """
        article = self.__redis_connection.json().get(key)
        article_data = json.loads(article)
        return article_data

    def createDataFrame(self):
        """
        Function: createDataFrame()
        Description: This function returns data obtained from Redis as a dataframe.
        Arguments: self - the class object
        Returns: new_dataframe - a dataframe containing all the data stored on Redis.
        """
        article_list = []
        for key in self.__redis_connection.scan_iter("article:*"):
            article = self.getArticle(key)
            for item in article:
              pubdate = article['publishedAt'].split("T")
              pubdate = pubdate[0]
            sources = article["source"]
            for item in sources:
                source_name = sources['name']
            new_row = {
                "Article Title": article["title"],
                "Source Name": source_name,
                "Author": article["author"],
                "Publication Date": pubdate
            }
            article_list.append(new_row)
        new_dataframe = pd.DataFrame.from_dict(article_list)
        return new_dataframe

class NewsApiAccessor:
    """
    Class: NewsApiAccessor
    Description: This class gets data from newsapi
    """
    def __init__(self):
        """
        Function: Constructor
        Description: Creates an object of type RedisAccessor.
        Arguments: self - the class object
        Returns: None
        """
        self

    def getNewsData(self, category_id):
        """
        Function: getNewsData
        Description: Gets data from newsapi
        Arguments: self - the class object
                   category_id - the category of news to get the articles from (ie sports, business, entertainment, etc)
        Returns: json_request
        """
        cat_string = 'category=' + category_id + '&'
        url = ('https://newsapi.org/v2/top-headlines?'
              + cat_string +
              'apiKey=5fe8e2f54d2a408bb80b2d573ca73590')
        response = requests.get(url)
        json_request = response.json()
        if len(json_request) <= 0:
          print("ERROR: could not get json request, sorry about that")
          return None
        return json_request

def main():
  """
  Function: main
  Description: It's the main function that mainly functions.
  """
  newsDataAccessor = NewsApiAccessor()
  redisAccessor = RedisAccessor()

  business_news = newsDataAccessor.getNewsData('business')
  sports_news = newsDataAccessor.getNewsData('sports')
  enterainment_news = newsDataAccessor.getNewsData('enterainment')

  for i in range(3):
    if i == 0:
        redisAccessor.setArticles(i, business_news)
    elif i==1:
        redisAccessor.setArticles(i, sports_news)
    elif i==2:
        redisAccessor.setArticles(i, enterainment_news)

  article_df = redisAccessor.createDataFrame()
  source_frequency_df = article_df[["Source Name", "Publication Date"]].copy()
  author_frequency_df = article_df[["Author", "Publication Date"]].copy()
  author_employment_df = article_df[["Source Name", "Author"]].copy()


  source_frequency_df=source_frequency_df.groupby(["Publication Date", "Source Name"]).size()
  source_frequency_df=source_frequency_df.unstack()
  plot1 = source_frequency_df.plot(title = "Source Publication Frequency", kind ='barh')

  author_frequency_df=author_frequency_df.groupby(["Author", "Publication Date"]).size()
  author_frequency_df=author_frequency_df.unstack()
  plot2 = author_frequency_df.plot(title = "Author Publication Frequency", kind = 'barh')

  author_employment_df=author_employment_df.groupby(["Author", "Source Name"]).size()
  author_employment_df=author_employment_df.unstack()
  plot3 = author_employment_df.plot(title = 'Author Employment', kind = "barh")

main()