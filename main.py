import praw, config
from flask import Flask, render_template, request, redirect
from pprint import pprint
from imgurpython import ImgurClient

app = Flask(__name__)

r = praw.Reddit(user_agent='redpics')

client = ImgurClient(config.client_id, config.client_secret)

def fetch_saved(limit):
	savedposts = r.user.get_saved(limit=limit)
	result = []

	for post in savedposts:
		if hasattr(post, 'domain') and hasattr(post, 'url') and 'imgur.com' in post.domain and post.over_18 == config.over_18:
			temp = {}
			temp['url'] = post.url
			temp['thumbnail'] = set_thumbnail(post)
			result.append(temp)
	return result

def set_thumbnail(post):
	result = post.thumbnail
	post_id = post.url.rpartition('/')[2]
	if 'i.imgur.com' in post.url:
		result = post.url
	elif post.media != None:
		result = post.media['oembed']['thumbnail_url']
	elif checkalbum(post.url):
		image_id = client.get_album(post_id).cover
		result = client.get_image(image_id).link
	else:
		try:
			result = client.get_image(post_id).link
		except:
			result = post.thumbnail

	return result

def checkalbum(url):
	return '/a/' in url


@app.route("/")
def hello():
	return render_template('hello.html', logged_in=False)

@app.route("/", methods=['POST'])
def process_form():
	username = request.form['username'].lower()
	password = request.form['password'].lower()
	limit = int(request.form['limit'])
	try:
		r.login(username, password, disable_warning=True)
	except praw.errors.InvalidUserPass:
		return render_template('hello.html', failed_login=True)

	posts = fetch_saved(limit)
	return render_template('hello.html', posts=posts, logged_in=True, username=username)

@app.route("/logout")
def logout():
	r.clear_authentication()
	return redirect("/")

if __name__ == "__main__":
	app.debug = True
	app.run()