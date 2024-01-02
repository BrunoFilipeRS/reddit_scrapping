# Imports necessários para o funcionamento do código
import time
import json
from typing import Optional, Annotated
import sys
import os
import csv

# Imports que não são parte da instalação original do python
from seleniumwire import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.firefox.options import Options
from selenium.common import exceptions as selenium_exceptions
import typer

# Criação de uma app do Typer
app = typer.Typer()

# Função que extrai informação de um post, leva como argumentos o post e opcionalmente a relevancia e o post_url
def post_info(post,relevancia:Optional[bool] = False,post_url:Optional[bool] = False):
    subreddit = post['subreddit-prefixed-name'] #Nome do subreddit
    title = post['post-title'] #Titulo do Post
    score = post['score'] #Score do post
    num_comments = post['comment-count'] #Número de comentários
    # No caso do "relevancia" ser True, é usada a função calculate_relevance para adicionar ao output
    if relevancia == True:
        return {'subreddit':subreddit,'título':title,'score':score,'número de comentários':num_comments,'relevancia':calculate_relevance(score,num_comments)}
    # No caso do argumento post_url ser True, é acrescentado o permalink do post ao output
    elif post_url:
        post_url = post['permalink'] #Permalink do post
        return {'subreddit':subreddit,'título':title,'score':score,'número de comentários':num_comments,'url':post_url}
    # Se nenhum dos argumentos opcionais for True, o output contém apenas o subreddit, o título, o score e o número de comentários
    else:
        return {'subreddit':subreddit,'título':title,'score':score,'número de comentários':num_comments}


# Função para obter um URL usando os parametros, driver (instância do selenium.webdriver) e url
def get_url(driver,url):
    try:
        driver.get(url) #obter URL
        time.sleep(sleep) # Introduz uma pausa/delay
    #caso o url não seja válido
    except selenium_exceptions.InvalidArgumentException as error:
        print(f'Erro no Url:{error}')
        shutdown(driver)
    # Caso o URL dê timeout
    except selenium_exceptions.TimeoutException as error:
        print(f"O url deu timeout: {error}")
        shutdown(driver)

# Função para obter a lista e o número de posts de um URL, usando os parametros URL (o URL que será acessado) e start_index que serve para realizar um scroll na pagina antes de continuar
def loop(url,start_index):
    #se start_index for True, usa uma script javaScript para dar scroll até ao final da página
    if start_index:
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        time.sleep(sleep)
    #se start_index for falso chama a função 'get_url' para obter o URL
    else:
        get_url(driver,url)
    
    page = driver.page_source # Obtem o HTML da página
    soup = BeautifulSoup(page,'lxml') # Usa o BeautifulSoup para estruturar os dados do HTML
    posts_list = soup.find_all('shreddit-post') # obter todos os shreddit posts da página
    num_posts = len(posts_list) # Obtém o número de posts apartir do tamanho da lista de shreddit posts
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


# Função para calcular o valor de relevância de um post, usando como argumentos o score e o num de comentários de um Post
def calculate_relevance(score,num_comments):
    #definir a contribuição de cada um destes fatores para o resultado final
    peso_score,peso_comment = 0.6,0.4
    #calculo final do valor de relevância
    return (int(score)*peso_score) + (int(num_comments)*peso_comment)


# Função garante que um número especifico de posts é obtido de um URL, usando os argumentos url (a url a ser usada) e n o número de posts
def getting_posts(url,n):
    posts_tuple = loop(url,0) #chama a função loop para obter os posts e o seu número
    num_posts = posts_tuple[1] #guarda o número de posts obtido
    #Verifica se a comunidade é privada e se foi possível obter o número de posts
    if not num_posts:
        print('Comunidade privada')
        shutdown(driver)
    # Loop para obter o número definido de posts, entra em loop enquanto que o número de posts obtidos seja menor do que o Número especcificado
    while num_posts < n:
        posts_tuple = loop(url,num_posts)
        num_posts = posts_tuple[1]
    plus = n - num_posts #diferença entre o número desejado e o numerpo total de posts
    #se não houver plus a função retorna todos os posts obtidos
    if not plus:
        return posts_tuple[0]
    #se houver plus, a função retorna apenas os primeiros plus posts da lista
    else:
        return posts_tuple[0][:plus]


# Função usada para fechar o Webdriver e encerrar o script
def shutdown(driver):
    driver.close() #fecha o webdriver encerrando a sessão do navegador
    sys.exit(1) #encerra o script


@app.command()  
def top5(csv:Annotated[Optional[bool],typer.Argument()] = False):# leva de argumento a escolha de guardar em csv ou n
    posts = []# serao guardados os posts aqui
    most_popular_url = f'{url_reddit}r/all/top/?t=all'# url para os mais votados de todos
    get_url(driver,most_popular_url)# abrir o url no browser
    page = driver.page_source # retirar os conteudos do browser
    soup = BeautifulSoup(page,'lxml')# transformar em lxml o conteudo
    post_list = soup.find_all('shreddit-post',limit=5)# encontrar todos os posts
    for post in post_list:
        posts.append(post_info(post))# colcoar todos os posts numa lista em forma de dicionario
    if csv:# guardar em csv ou dar print
        csv_saver(posts,'top5')
    else:
        posts_json = json.dumps(posts, indent=2, ensure_ascii=False)# transformar os posts em json
        typer.echo(posts_json)# print do typer dos posts


@app.command()
def recent(
    score: Optional[bool] = typer.Argument(False, help="Score"),# bool para decidir a adição de relevancia
    n: int = typer.Argument(3, help="N"),# número de posts para ir buscar
    category: str = typer.Argument('portugueses', help="Category"),# nome do subreddit
    csv: Optional[bool] = typer.Argument(False, help="CSV"),# leva de argumento a escolha de guardar em csv ou nao
    print_json:Optional[bool] = typer.Argument(True, help="Print")# escolha de print ou nao, isto porque a função é usada no auxilio do compare
):
    posts = []# serao guardados os posts aqui
    most_recent_url = f'{url_reddit}r/{category}/new/'# url para os mais recentes da categoria
    wanted_posts = getting_posts(most_recent_url,n)# Obter os n posts
    if score:# caso a relevancia seja selecionada é calculada e ordenada por ela a lista de posts
        for post in wanted_posts:
            posts.append(post_info(post,True))
        posts.sort(key=lambda x: x["relevancia"],reverse=True)
    else:# ao contrário apenas é adicionada a informação normal ao posts
        for post in wanted_posts:
            posts.append(post_info(post))
    if csv:# guardar em csv caso solicitado
        if score:
            csv_saver(posts,f'recent_score_{n}_{category}')
        else:
            csv_saver(posts,f'recent_{n}_{category}')
    else:
        posts_json = json.dumps(posts, indent=2, ensure_ascii=False)# transformar os posts em json
        if print_json:
            typer.echo(posts_json)# print do typer dos posts
        else:
            return posts_json# para o auxilio da função compare


@app.command()
def compare(n: int = typer.Argument(3, help="N"),# número de posts para ir buscar
            category: str = typer.Argument('portugueses', help="Category")):# nome do subreddit
    posts = []# serao guardados os posts aqui
    hot_url = f'{url_reddit}r/{category}/hot/'# url para os mais relevantes
    wanted_posts = getting_posts(hot_url,n)# Obter os n posts
    for post in wanted_posts:# adicionada a informação dos posts
        posts.append(post_info(post))
    posts_json_recent = recent(score=True,n=n,category=category,csv=False,print_json=False)# uso da funçào recent com relevancia para comparação
    posts_recent = json.loads(posts_json_recent)# transformar os posts em json
    typer.echo("1-Em destaque\t\t2-Recentes com relevância")# usando o typer fazer um print de comparação
    typer.echo(f'Categoria é {category}')
    typer.echo("=" * 100)
    for item1, item2 in zip(posts, posts_recent):# um zip para juntar cada atributo das 2 funções
        typer.echo(f"Título 1: {item1['título']}\t|\tTítulo 2: {item2['título']}")
        typer.echo(f"Score 1: {item1['score']}\t|\tScore 2: {item2['score']}")
        typer.echo(f"Nº de Comentários 1: {item1['número de comentários']}\t|\tNº de Comentários 2: {item2['número de comentários']}")
        typer.echo("=" * 100)


@app.command()
def top(n:int = typer.Argument(3, help="N"),# número de posts para ir buscar
        withcomments: Optional[bool] = typer.Argument(False, help="WithComments"),# decidir usar ou n os 5 primeiros comentários
        csv: Optional[bool] = typer.Argument(False, help="CSV")):# leva de argumento a escolha de guardar em csv ou nao
    posts = []# serao guardados os posts aqui
    most_popular_url = f'{url_reddit}r/all/top/?t=all'# url para os mais votados de todos
    wanted_posts = getting_posts(most_popular_url,n)# Obter os n posts
    if withcomments:# caso sejam precisos os comentários
        for post in wanted_posts:# post a post
            post_info_data = post_info(post,post_url=True)# buscar o link do post
            get_url(driver,url_reddit[:-1]+post_info_data['url'])# atualizar a página para o post
            post_page = driver.page_source# conteudo da pagina
            soup_page = BeautifulSoup(post_page,'lxml')# transformar o conteudo em lxml
            tree = soup_page.find('shreddit-comment-tree')# ir buscar todos os comentários juntos
            comments = tree.find_all('shreddit-comment',limit=5)# procurar os 5 primeiros comentários apenas
            comments_list = []# aqui vao ser guardados
            for comment in comments:# comentário a comentário
                text = comment.find('p').text.strip()# "limpar" os comentários
                comments_list.append(text)# adicionar a lista
            post_info_data['5 primeiros comentários'] = comments_list# adicionar aos dados do post
            post_info_data.pop('url')# retirar o url do post
            posts.append(post_info_data)# adicionar o post com comentários ao dicionário
    else:
        for post in wanted_posts:# adicionada a informação dos posts
            post_info_data = post_info(post)
            posts.append(post_info_data)
    if csv:# guardar em csv caso solicitado
        if withcomments:
            csv_saver(posts,f'top{n}_comments')# com comentários
        else:
            csv_saver(posts,f'top{n}')# sem comentários
    else:
        posts_json = json.dumps(posts, indent=2, ensure_ascii=False)# transformar em json
        typer.echo(posts_json) # print do json



# Lugar onde o objeto do typer é ativado
if __name__ == '__main__':
    try:
        sleep = 0.5# tempo de espera para carregar uma página, pode ser maior ou menor dependendo da internet e/ou computador a usar o código
        url_reddit = 'https://www.reddit.com/'# url base do reddit
        options = Options()# opções do browser do firefox como visto nos imports
        options.add_argument("--headless") # criar um broswer no fundo
        driver = webdriver.Firefox(options = options) # aplicar as definições ao browser
        app() # iniciar o typer
    finally:
        driver.quit()# garantir sempre o fechamento do browser