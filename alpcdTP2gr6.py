from seleniumwire import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.firefox.options import Options
import time
import json

options = Options()
options.add_argument("--headless") # criar um broswer no fundo
driver = webdriver.Firefox(options = options)
""" driver.get(url)
a = driver.page_source
soup = BeautifulSoup(a,'lxml')
post = soup.find_all('shreddit-post')
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(2)

upd = driver.page_source
soup2 = BeautifulSoup(upd,'lxml')
posts2 = soup2.find_all('shreddit-post')[:] """


def top5():
    most_popular_url = 'https://www.reddit.com/r/all/top/?t=all'
    driver.get(most_popular_url)
    page = driver.page_source
    soup = BeautifulSoup(page,'lxml')
    post_list = soup.find_all('shreddit-post',limit=5)
    return post_list


def post_info(posts_list):
    subreddit = posts_list['subreddit-prefixed-name']
    title = posts_list['post-title']
    score = posts_list['score']
    num_comments = posts_list['comment-count']
    return {'subreddit':subreddit,'título':title,'score':score,'número de comentários':num_comments}


def loop(url,start_index):
    if start_index:
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        time.sleep(2)
    else:
        driver.get(url)
    page = driver.page_source
    soup = BeautifulSoup(page,'lxml')
    posts_list = soup.find_all('shreddit-post')
    num_posts = len(posts_list)
    print(num_posts)
    return (posts_list,num_posts)


""" dic = []
posts = top5(driver)
for post in posts:
    dic.append(post_info(post)) """

""" print(json.dumps(dic, indent=2, ensure_ascii=False)) """

def recent(n,category):
    most_recent_url = ''+category
    begin = loop(most_recent_url,0)
    num_posts = begin[1]
    while num_posts < n:
        # meter vela
        posts = loop(most_recent_url,num_posts)
        num_posts = posts[1]
    plus = n - num_posts
    wanted_posts = posts[0][:plus]
    print(len(wanted_posts))
recent(100,0)
driver.quit()
# Lugar onde o objeto do typer é ativado
""" if _name_ == '_main_':
    #meter coisas que roda em todas as apps aqui
    app() """