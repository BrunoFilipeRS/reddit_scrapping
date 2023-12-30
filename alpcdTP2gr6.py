from seleniumwire import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.firefox.options import Options
import time
import json
import typer


processed_identifiers = set()
app = typer.Typer()


def post_info(post):
    subreddit = post['subreddit-prefixed-name']
    title = post['post-title']
    score = post['score']
    num_comments = post['comment-count']
    return {'subreddit':subreddit,'título':title,'score':score,'número de comentários':num_comments}


def scroll_within_new_html(new_html):
    # Execute JavaScript code to scroll within the new HTML content
    scroll_script = """
    var newContainer = document.createElement('div');
    newContainer.innerHTML = arguments[0];
    newContainer.style.overflow = 'auto';
    newContainer.style.height = '500px';  // Adjust the height as needed

    // Replace the current body with the new container
    document.body.innerHTML = '';
    document.body.appendChild(newContainer);

    // Scroll to the bottom of the new container
    newContainer.scrollTop = newContainer.scrollHeight;
    """

    # Execute the scroll script with the new HTML content
    driver.execute_script(scroll_script, new_html)

def extract_new_posts(processed_identifiers):
    # Convert the set to a list before passing to execute_script
    processed_identifiers_list = list(processed_identifiers)

    # Execute JavaScript code to extract new posts
    script = """
    var newPosts = [];
    var posts = document.querySelectorAll('shreddit-post');
    for (var i = 0; i < posts.length; i++) {
        var postId = posts[i].getAttribute('unique-identifier');
        if (processed_identifiers_list.indexOf(postId) === -1) {
            newPosts.push(posts[i].outerHTML);
            processed_identifiers_list.push(postId);
        }
    }
    return newPosts.join('');
    """

    # Execute the script and retrieve the HTML content of the new posts
    new_posts_html = driver.execute_script(script, processed_identifiers_list)

    return new_posts_html





def loop(url, start_index):
    global processed_identifiers  # Use the global set
    if start_index:
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        time.sleep(2)
    else:
        driver.get(url)

    # Extract new HTML content using JavaScript
    new_html = extract_new_posts(processed_identifiers)

    # Scroll within the new HTML content
    scroll_within_new_html(new_html)

    # Process the new HTML content
    soup = BeautifulSoup(new_html, 'lxml')
    new_posts = soup.find_all('shreddit-post')

    # Update the set of processed identifiers
    new_identifiers = [post['unique-identifier'] for post in new_posts]
    processed_identifiers.update(new_identifiers)

    num_posts = len(new_posts)
    print(num_posts)
    return new_posts, num_posts
 


@app.command()
def top5():
    posts = []
    most_popular_url = f'{url_reddit}r/all/top/?t=all'
    driver.get(most_popular_url)
    page = driver.page_source
    soup = BeautifulSoup(page,'lxml')
    post_list = soup.find_all('shreddit-post',limit=5)
    for post in post_list:
        posts.append(post_info(post))
    posts_json = json.dumps(posts, indent=2, ensure_ascii=False)
    print(posts_json)

""" dic = []
posts = top5(driver)
for post in posts:
    dic.append(post_info(post)) """

""" print(json.dumps(dic, indent=2, ensure_ascii=False)) """

@app.command()
def recent(n:int,category):
    posts = []
    most_recent_url = f'{url_reddit}r/{category}'
    begin = loop(most_recent_url,0)
    num_posts = begin[1]
    while num_posts < n:
        # meter vela
        posts = loop(most_recent_url,num_posts)
        num_posts = posts[1]
    plus = n - num_posts
    wanted_posts = posts[0][:plus]
    print(wanted_posts)
    for post in wanted_posts:
        posts.append(post_info(post))
    posts_json = json.dumps(posts, indent=2, ensure_ascii=False)
    print(posts_json)

# Lugar onde o objeto do typer é ativado
if __name__ == '__main__':
    url_reddit = 'https://www.reddit.com/'
    options = Options()
    options.add_argument("--headless") # criar um broswer no fundo
    driver = webdriver.Firefox(options = options) # aplicar as definições ao browser
    app() # iniciar o typer
    driver.quit()
    # fechar o browser depois de iniciar o typer para n fechar o browser antes de fazer as funcionalidades