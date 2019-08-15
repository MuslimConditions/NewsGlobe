import datetime
import glob
import os
import sys
from functools import wraps
from hashlib import md5

import flask
import requests
import simplejson as json
from flask import Flask
from flask import g
from flask import redirect
from flask import request, Response
from flask import session
from flask import url_for, abort, render_template, flash, send_from_directory
from flask_recaptcha import ReCaptcha
from itsdangerous import URLSafeTimedSerializer
from peewee import *

from email_sender import send_gmail

# config - aside from our database, the rest is for use by Flask
FILE_PATH = os.path.dirname(os.path.realpath(__file__))
DATABASE = os.path.join(FILE_PATH, 'obj', 'users.db')
ABUSEIPDB_KEY = ""

DEBUG = True
SECRET_KEY = ""

# create a flask application - this ``app`` object will be used to handle
# inbound requests, routing them to the proper 'view' functions, etc
app = Flask(__name__, static_url_path='')
app.config.from_object(__name__)
app.config.update(dict(
    RECAPTCHA_ENABLED=True,
    RECAPTCHA_SITE_KEY="",
    RECAPTCHA_SECRET_KEY="",
    SECURITY_PASSWORD_SALT="",
))
recaptcha = ReCaptcha(app=app)

# create a peewee database instance -- our models will use this database to
# persist information
database = SqliteDatabase(DATABASE)


class Blacklist:
    def __init__(self):
        self.data = None
        self.file_path = os.path.join(FILE_PATH, "obj", 'ip_allowedlist.json')
        self.load_from_file()

    def load_from_file(self):
        try:
            self.data = json.loads(open(self.file_path, 'rb').read())
        except FileNotFoundError:
            self.data = {}
            with open(self.file_path, 'w') as outfile:
                json.dump(self.data, outfile)
        except:
            raise

    def check(self, ip):
        # self.load_from_file()
        whitelist = ["192.168.1.", "127.0.0.", "0.0.0."]
        for w in whitelist:
            if w in ip:
                print("Ip is in whitelist:", ip, file=sys.stderr)
                return True
        if ip in self.data:
            return self.data[ip]
        else:
            self.load_from_file()
            should_be_allowed = self.check_online(ip)
            if should_be_allowed:
                self.add_ip(ip, True)
                self.store_to_file()
                return True
            elif not should_be_allowed:
                self.add_ip(ip, False)
                self.store_to_file()
                return False
            elif should_be_allowed is None:
                return None

    def store_to_file(self):
        # json_file_path = os.path.join(FILE_PATH, 'static', 'thematics.json')
        with open(self.file_path, 'w') as outfile:
            json.dump(self.data, outfile)

    def add_ip(self, ip, boolean):
        if ip not in self.data:
            self.data[ip] = boolean
        return

    @staticmethod
    def check_online(ip):
        try:
            url = "https://www.abuseipdb.com/check/%s/json?key=%s" % (ip, ABUSEIPDB_KEY)
            response = requests.post(url)
            if response.ok:
                try:
                    data = response.json()
                except json.errors.JSONDecodeError:
                    print("Abuse IP DB not working...")
                    return None
                if isinstance(data, list):
                    if len(data) == 0:
                        return True
                    else:
                        first_entry = data[0]
                        if "isBlacklisted" in first_entry:
                            if not first_entry['isBlacklisted']:
                                return True
                            else:
                                return False
                        if first_entry['isWhitelisted']:
                            return True
                        else:
                            return False
                elif isinstance(data, dict):
                    # 'ip': '162.243.245.57', 'country': 'United States', 'isoCode': 'US', 'category': [14, 18, 21], 'created': 'Sat, 03 Feb 2018 04:56:47 +0000', 'isWhitelisted': False
                    if "isWhiteListed" in data:
                        if data["isWhiteListed"] == False:
                            return False
                        else:
                            return True
                    else:
                        print("Weird data from abuseipdb... Type:", type(data), file=sys.stderr)
                        print(data, file=sys.stderr)
                        return None
                else:
                    print("Weird data from abuseipdb... Type:", type(data), file=sys.stderr)
                    print(data, file=sys.stderr)
                    return None
            else:
                print("Response from Abusipdb is not 200:", response)
                return None
        except:
            raise


blacklist = Blacklist()


# model definitions -- the standard "pattern" is to define a base model class
# that specifies which database to use.  then, any subclasses will
# automatically use the correct storage. for more information, see:
# http://charlesleifer.com/docs/peewee/peewee/models.html#model-api-smells-like-django


class BaseModel(Model):
    class Meta:
        database = database


# the user model specifies its fields (or columns) declaratively, like django
class User(BaseModel):
    username = CharField(unique=True)
    password = CharField()
    email = CharField(unique=True)
    join_date = DateTimeField()
    confirmed = BooleanField(default=False)
    admin = BooleanField(default=False)

    class Meta:
        order_by = ('username',)

    # it often makes sense to put convenience methods on model instances, for
    # example, "give me all the users this user is following":
    def following(self):
        # query other users through the "relationship" table
        return User.select().join(
            Relationship, on=Relationship.to_user,
        ).where(Relationship.from_user == self)

    def followers(self):
        return User.select().join(
            Relationship, on=Relationship.from_user,
        ).where(Relationship.to_user == self)

    def is_following(self, user):
        return Relationship.select().where(
            (Relationship.from_user == self) &
            (Relationship.to_user == user)
        ).count() > 0


# this model contains two foreign keys to user -- it essentially allows us to
# model a "many-to-many" relationship between users.  by querying and joining
# on different columns we can expose who a user is "related to" and who is
# "related to" a given user
class Relationship(BaseModel):
    from_user = ForeignKeyField(User, related_name='relationships')
    to_user = ForeignKeyField(User, related_name='related_to')

    class Meta:
        indexes = (
            # Specify a unique multi-column index on from/to-user.
            (('from_user', 'to_user'), True),
        )


# a dead simple one-to-many relationship:
# one user has 0..n messages, exposed by
# the foreign key.  because we didn't specify,
# a users messages will be accessible
# as a special attribute, User.message_set
class Message(BaseModel):
    user = ForeignKeyField(User)
    content = TextField()
    pub_date = DateTimeField()

    class Meta:
        order_by = ('-pub_date',)


# simple utility function to create tables
def create_tables():
    database.connect()
    database.create_tables([User, Relationship, Message])


# flask provides a "session" object, which allows us
# to store information across requests
# (stored by default in a secure cookie).
# This function allows us to mark a user
# as being logged-in by setting some values in the session data:
def auth_user(user):
    session['logged_in'] = True
    session['user_id'] = user.id
    session['username'] = user.username
    flash('You are logged in as %s' % user.username)


# get the user from the session
def get_current_user():
    if session.get('logged_in'):
        return User.get(User.id == session['user_id'])


def admin_required(f):
    @wraps(f)
    def inner(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        if not get_current_user().admin:
            flash("Admin credentials required..")
            return render_template("login.html")
        return f(*args, **kwargs)

    return inner


# view decorator which indicates that the requesting user must be authenticated
# before they can access the view.  it checks the session to see if they're
# logged in, and if not redirects them to the login view.
def login_required(f):
    @wraps(f)
    def inner(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return inner


# given a template and a SelectQuery instance, render a paginated list of
# objects from the query inside the template
def object_list(template_name, qr, var_name='object_list', **kwargs):
    kwargs.update(
        page=int(request.args.get('page', 1)),
        pages=qr.count() / 20 + 1
    )
    kwargs[var_name] = qr.paginate(kwargs['page'])
    return render_template(template_name, **kwargs)


# retrieve a single object matching the specified query or 404 -- this uses the
# shortcut "get" method on model, which retrieves a single object or raises a
# DoesNotExist exception if no matching object exists
# http://charlesleifer.com/docs/peewee/peewee/models.html#Model.get)
def get_object_or_404(model, *expressions):
    try:
        return model.get(*expressions)
    except model.DoesNotExist:
        abort(404)


# custom template filter -- flask allows you to define these functions and then
# they are accessible in the template -- this one returns a boolean whether the
# given user is following another user.
@app.template_filter('is_following')
def is_following(from_user, to_user):
    return from_user.is_following(to_user)


# Request handlers -- these two hooks are provided by flask and we will use them
# to create and tear down a database connection on each request.
@app.before_request
def before_request():
    g.db = database
    g.db.connect(reuse_if_open=True)
    # print(request.remote_addr,file=sys.stderr)
    if not blacklist.check(request.remote_addr):
        print("Blocking", request.remote_addr, file=sys.stderr)
        abort(403)


@app.after_request
def after_request(response):
    g.db.close()
    return response


@app.route('/googlee32aea43ad8b6f83.html')
def google_analytics():
    return send_from_directory('static', 'googlee32aea43ad8b6f83.html')


@app.route('/logs')
@admin_required
def logs():
    # * means all if need specific format then *.csv
    list_of_files = glob.glob(os.path.join(
        FILE_PATH, "logs", "locations", "*.log"))
    latest_file = max(list_of_files, key=os.path.getctime)
    file = open(os.path.join(FILE_PATH, 'logs', 'locations',
                             latest_file.split("\\")[-1]), 'rb')
    txt = file.read()
    return Response(txt, mimetype='text/plain')


@app.route('/avoid/', methods=['GET', 'POST'])
@admin_required
def avoid():
    path = os.path.join(FILE_PATH, "obj", "avoid_locations.json")
    fi = open(path, 'rb').read()
    data = json.loads(fi)
    if request.method == 'POST':
        if "keyword" in request.form:
            string = request.form['keyword']
            # print(string,file=sys.stderr)
            if not string in data:
                data.append(string)
            with open(os.path.join(FILE_PATH, "obj", "avoid_locations.json"), 'w') as outfile:
                json.dump(data, outfile)
        elif 'delete' in request.form:
            if request.form['delete'].split('|')[1] == data[int(request.form['delete'].split('|')[0])]:
                del data[int(request.form['delete'].split('|')[0])]
            with open(os.path.join(FILE_PATH, "obj", "avoid_locations.json"), 'w') as outfile:
                json.dump(data, outfile)
    return render_template("avoid.html", data=data, i=0)


# noinspection PyUnusedLocal
@app.route('/avoid/remove/<index>', methods=['POST'])
@admin_required
def remove_from_avoid(index):
    path = os.path.join(FILE_PATH, "obj", "avoid_locations.json")
    fi = open(path, 'rb').read()
    data = json.loads(fi)

    return render_template("avoid.html", data=data, i=0)


@app.route('/')
def homepage():
    return send_from_directory('static', "index.html")


@app.route('/static/', defaults={'path': 'index.html'})
@app.route('/static/<path:path>')
def homepage_static(path):
    if session.get('logged_in'):
        return send_from_directory('static', path)
    else:
        return send_from_directory('static', path)


@app.route('/join/', methods=['GET', 'POST'])
def join():
    if request.method == 'POST' and request.form['username']:
        if recaptcha.verify():
            try:
                with database.transaction():
                    # Attempt to create the user. If the username is taken, due to the
                    # unique constraint, the database will raise an IntegrityError.
                    user = User.create(
                        username=request.form['username'],
                        password=md5((request.form['password']).encode(
                            'utf-8')).hexdigest(),
                        email=request.form['email'],
                        join_date=datetime.datetime.now())

                # generate token for email handling
                _token = generate_confirmation_token(user.email)

                confirm_url = url_for(
                    'confirm_email', token=_token, _external=True)

                html = render_template(
                    'activate.html', confirm_url=confirm_url, username=user.username)

                subject = "Please confirm your email"

                send_gmail(html, user.email,
                           'autosender9999@gmail.com', 'tqUbLwGj485q', subject=subject)

                # auth_user(user)
                # mark the user as being 'authenticated' by setting the session vars
                flash("A confirmation email has been sent!")
                # return redirect(url_for('homepage'))

            except IntegrityError:
                flash('That username is already taken')
        else:
            flash('ReCaptcha error...')

    return render_template('join.html')


def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])


# noinspection PyBroadException
def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except:
        return False
    return email


@app.route("/confirm/<token>")
def confirm_email(token):
    print("confirming", file=sys.stderr)

    # noinspection PyBroadException
    try:
        print("trying to confirm token %s" % token, file=sys.stderr)
        email = confirm_token(token)
        print("token confirmed!", file=sys.stderr)
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')
    print("getting user", file=sys.stderr)

    # noinspection PyUnboundLocalVariable
    user = get_object_or_404(User, User.email == email)

    if user.confirmed:
        print("user %s already confirmed" % user.username, file=sys.stderr)
        flash('Account already confirmed. Please login.', 'success')
    else:
        print("trying to confirm user", file=sys.stderr)
        user.confirmed = True
        user.save()
        flash('You have confirmed your account. Thanks!', 'success')
        # auth_user(user)
    return render_template("login.html")


@app.route('/login/', methods=['GET', 'POST'])
def login():
    print("logging in", file=sys.stderr)
    if request.method == 'POST' and request.form['username']:
        try:
            user = User.get(
                username=request.form['username'],
                password=md5((request.form['password']).encode('utf-8')).hexdigest())
        except User.DoesNotExist:
            flash('The password entered is incorrect')
        else:
            if user.confirmed:
                auth_user(user)
                return redirect(url_for('homepage'))
            else:
                flash("The user has not yet confirmed their email...")

    return render_template('login.html')


@app.route('/logout/')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('homepage'))


@app.route('/users/')
def user_list():
    users = User.select()
    return object_list('user_list.html', users, 'user_list')


# noinspection PyTypeChecker
@app.route('/users/<username>/')
def user_detail(username):
    # using the "get_object_or_404" shortcut here to get a user with a valid
    # username or short-circuit and display a 404 if no user exists in the db
    user = get_object_or_404(User, User.username == username)

    # get all the users messages ordered newest-first -- note how we're accessing
    # the messages -- user.message_set.  could also have written it as:
    # Message.select().where(user=user).order_by(('pub_date', 'desc'))
    messages = user.message_set
    return object_list('user_detail.html', messages, 'message_list', user=user)


@app.route("/logged_in")
def home():
    if session.get('logged_in'):
        resp = flask.Response("")
        resp.headers['logged_in'] = 'true'
        return resp
    else:
        resp = flask.Response("")
        resp.headers['logged_in'] = 'false'
        return resp


@app.context_processor
def _inject_user():
    return {'current_user': get_current_user()}


if __name__ == "__main__":
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(port=80, host='0.0.0.0')
