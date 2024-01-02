import time
import json
from typing import Optional, Annotated
import sys
import os
import csv

from seleniumwire import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.firefox.options import Options
from selenium.common import exceptions as selenium_exceptions
import typer

app = typer.Typer()


def post_info(post,relevancia:Optional[bool] = False,post_url:Optional[bool] = False):
    subreddit = post['subreddit-prefixed-name']
    title = post['post-title']
    score = post['score']
    num_comments = post['comment-count']
    if relevancia == True:
        return {'subreddit':subreddit,'título':title,'score':score,'número de comentários':num_comments,'relevancia':calculate_relevance(score,num_comments)}
    elif post_url:
        post_url = post['permalink']
        return {'subreddit':subreddit,'título':title,'score':score,'número de comentários':num_comments,'url':post_url}
    else:
        return {'subreddit':subreddit,'título':title,'score':score,'número de comentários':num_comments}


def get_url(driver,url):
    try:
        driver.get(url)
        time.sleep(sleep)
    except selenium_exceptions.InvalidArgumentException as error:
        print(f'Erro no Url:{error}')
        shutdown(driver)
    except selenium_exceptions.TimeoutException as error:
        print(f"O url deu timeout: {error}")
        shutdown(driver)

def loop(url,start_index):
    if start_index:
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        time.sleep(sleep)
    else:
        get_url(driver,url)
        
    page = driver.page_source
    soup = BeautifulSoup(page,'lxml')
    posts_list = soup.find_all('shreddit-post')
    num_posts = len(posts_list)
    return (posts_list,num_posts)
 

def file_directory():
    # Dá o diretório do script
    file_path = os.path.abspath(sys.argv[0])
    # Remove do diretório do script o nome do scrip
    file_directory = os.path.dirname(file_path)
    return file_directory


def csv_saver(dict_list:list,command:str):
    # Guardar as chaves que serão usadas como colunas
    columns = [key for key in dict_list[0].keys()]
    counter = 0
    # Criar um nome do ficheiro, quando este existe é criado um contador para garantir que seja único
    while True:
        filename = f'reddit_{command}.csv' if counter == 0 else f'reddit_{command}({counter}).csv'
        # Onde se obtém o booleano de se o ficheiro já existe
        if not os.path.exists(filename):
            break
        counter += 1
    # Cria-se um csv com as colunas sendo as keys dos dicionários e onde cada linha é um dicionário    
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for row in dict_list:
            writer.writerow(row)
    # Confirmação do salvamento e a amostragem do caminho do diretório do ficheiro
    path = file_directory()
    print(f'Arquivo "{filename}" guardado com sucesso no mesmo local do programa em "{path}"')


def calculate_relevance(score,num_comments):
    peso_score,peso_comment = 0.6,0.4
    return (int(score)*peso_score) + (int(num_comments)*peso_comment)


def shutdown(driver):
    driver.close()
    sys.exit(1)


@app.command()
def top5(csv:Annotated[Optional[bool], typer.Argument()] = False):
    posts = []
    most_popular_url = f'{url_reddit}r/all/top/?t=all'
    get_url(driver,most_popular_url)   
    page = driver.page_source
    soup = BeautifulSoup(page,'lxml')
    post_list = soup.find_all('shreddit-post',limit=5)
    for post in post_list:
        posts.append(post_info(post))
    posts_json = json.dumps(posts, indent=2, ensure_ascii=False)
    if csv:
        csv_saver(posts,'top5')
    else:
        typer.echo(posts_json)


@app.command()
def recent(
    score: Optional[bool] = typer.Argument(False, help="Score"),
    n: int = typer.Argument(3, help="N"),
    category: str = typer.Argument('portugueses', help="Category"),
    csv: Optional[bool] = typer.Argument(False, help="CSV"),
    print_json:Optional[bool] = True
):
    posts = []
    most_recent_url = f'{url_reddit}r/{category}/new/'
    posts_tuple = loop(most_recent_url,0)
    num_posts = posts_tuple[1]
    if not num_posts:
        print('Comunidade privada')
        shutdown(driver)
    while num_posts < n:
        posts_tuple = loop(most_recent_url,num_posts)
        num_posts = posts_tuple[1]
    plus = n - num_posts
    if not plus:
        wanted_posts = posts_tuple[0]
    else:
        wanted_posts = posts_tuple[0][:plus]
    if score:
        for post in wanted_posts:
            posts.append(post_info(post,True))
        posts.sort(key=lambda x: x["relevancia"],reverse=True)
    else:
        for post in wanted_posts:
            posts.append(post_info(post))
    posts_json = json.dumps(posts, indent=2, ensure_ascii=False)
    if csv:
        if score:
            csv_saver(posts,'recent_score')
        else:
            csv_saver(posts,'recent')
    else:
        if print_json:
            typer.echo(posts_json)
    return posts_json


@app.command()
def compare(n: int = typer.Argument(3, help="N"),
            category: str = typer.Argument('portugueses', help="Category")):
    posts = []
    hot_url = f'{url_reddit}r/{category}/hot/'
    posts_tuple = loop(hot_url,0)
    num_posts = posts_tuple[1]
    if not num_posts:
        print('Comunidade privada')
        shutdown(driver)
    typer.echo(num_posts)
    while num_posts < n:
        posts_tuple = loop(hot_url,num_posts)
        num_posts = posts_tuple[1]
    plus = n - num_posts
    if not plus:
        wanted_posts = posts_tuple[0]
    else:
        wanted_posts = posts_tuple[0][:plus]
    for post in wanted_posts:
        posts.append(post_info(post))
    print(wanted_posts)
    posts_json_recent = recent(True,n,category,False,False)
    posts_recent = json.loads(posts_json_recent)
    typer.echo("Em destaque\t\tRecentes com relevância")
    typer.echo("=" * 100)
    typer.echo(f'Categoria é {category}')
    for item1, item2 in zip(posts, posts_recent):
        typer.echo(f"Título 1: {item1['título']}\t\tTítulo 2: {item2['título']}")
        typer.echo(f"Score 1: {item1['score']}\t\tScore 2: {item2['score']}")
        typer.echo(f"Nº de Comentários 1: {item1['número de comentários']}\t\tNº de Comentários 2: {item2['número de comentários']}")
        typer.echo("=" * 100)


@app.command()
def top(n: int, withComments: bool = True):
    posts = []
    most_popular_url = f'{url_reddit}r/all/top/?t=all'
    posts_tuple = loop(most_popular_url,0)
    num_posts = posts_tuple[1]
    if not num_posts:
        print('Comunidade privada')
        shutdown(driver)
    while num_posts < n:
        posts_tuple = loop(most_recent_url,num_posts)
        num_posts = posts_tuple[1]
    plus = n - num_posts
    if not plus:
        wanted_posts = posts_tuple[0]
    else:
        wanted_posts = posts_tuple[0][:plus]

    if withComments:
        for post in post_list:
            post_info_data = post_info(post,post_url=True)
            get_url(driver,url_reddit[:-1]+post_info_data['url'])
            post_page = driver.page_source
            soup_page = BeautifulSoup(post_page,'lxml')
            tree = soup_page.find('shreddit-comment-tree')
            comments = tree.find_all('shreddit-comment',limit=5)
            comments_list = []
            for comment in comments:
                text = comment.find('p').text
                comments_list.append(text)
            post_info_data['Comentários'] = comments_list
            posts.append(post_info_data)
    else:
        for post in post_list:
            post_info_data = post_info(post)
            posts.append(post_info_data)

    posts_json = json.dumps(posts, indent=2, ensure_ascii=False)
    print(posts_json)


# Lugar onde o objeto do typer é ativado
if __name__ == '__main__':
    sleep = 0.3
    url_reddit = 'https://www.reddit.com/'
    options = Options()
    options.add_argument("--headless") # criar um broswer no fundo
    driver = webdriver.Firefox(options = options) # aplicar as definições ao browser
    app() # iniciar o typer
    driver.quit()
    # fechar o browser depois de iniciar o typer para n fechar o browser antes de fazer as funcionalidades