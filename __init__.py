import praw, config
from flask import Flask, render_template, request, redirect
from imgurpython import ImgurClient

app = Flask(__name__)

r = praw.Reddit(user_agent='redpics')

client = ImgurClient(config.client_id, config.client_secret)


def fetch_saved(limit, nsfw):
    saved_posts = r.user.get_saved(limit=limit)
    result = []

    for post in saved_posts:
        if (hasattr(post, 'domain') and hasattr(post, 'url') and 'imgur.com' in post.domain and
                post.over_18 == nsfw):
            temp = {}
            temp['url'] = post.url
            temp['thumbnail'] = set_thumbnail(post)
            result.append(temp)
    return result


def set_thumbnail(post):
    post_id = post.url.rpartition('/')[2]
    if 'i.imgur.com' in post.url:
        result = post.url
    elif post.media is not None:
        result = post.media['oembed']['thumbnail_url']
    elif check_album(post.url):
        image_id = client.get_album(post_id).cover
        result = client.get_image(image_id).link
    else:
        try:
            result = client.get_image(post_id).link
        except:
            result = post.thumbnail

    return result


def check_album(url):
    return '/a/' in url


def check_limit_set(limit):
    if limit:
        return int(limit)
    else:
        return int(config.default_limit)


@app.route("/")
def hello():
    if r.is_logged_in():
        return redirect("/explore")
    else:
        return render_template('hello.html')


@app.route("/", methods=['POST'])
def process_form():
    username = request.form['username'].lower()
    password = request.form['password'].lower()

    limit = check_limit_set(request.form['limit'])
    try:
        r.login(username, password, disable_warning=True)
    except praw.errors.InvalidUserPass:
        return render_template('hello.html', failed_login=True)

    return redirect("/explore?limit=" + str(limit) + "&nsfw=False")


@app.route("/logout")
def logout():
    r.clear_authentication()
    return redirect("/")


@app.route("/explore", methods=['GET'])
def explore():
    if r.is_logged_in() is False:
        return redirect("/")

    limit = check_limit_set(request.args.get('limit'))
    nsfw = request.args.get('nsfw') == 'True'
    posts = fetch_saved(limit, nsfw)
    return render_template('explore.html', posts=posts)

if __name__ == "__main__":
    app.debug = True
    app.run()