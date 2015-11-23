#
# Copyright (C) 2015 Zubax Robotics <info@zubax.com>.
# Author: Pavel Kirienko <pavel.kirienko@zubax.com>
#

import os
from functools import wraps
from flask import Flask, render_template, send_from_directory, request, Markup
from flask_menu import Menu
from flask.ext.assets import Environment
from flask.ext.misaka import Misaka
from werkzeug.contrib.cache import SimpleCache
from bs4 import BeautifulSoup
import pygments, pygments.lexers, pygments.formatters
import misaka

app = Flask(__name__.split('.')[0])

app.config.from_object('config')

assets = Environment(app)

menu = Menu(app)

misaka_instance = Misaka(app)

cache = SimpleCache()


class MarkdownRenderer(misaka.HtmlRenderer, misaka.SmartyPants):
    def block_code(self, text, lang):
        if not lang:
            return '\n<pre><code>%s</code></pre>\n' % Markup.escape(text)
        lexer = pygments.lexers.get_lexer_by_name(lang, stripall=True)
        formatter = pygments.formatters.HtmlFormatter()
        return pygments.highlight(text, lexer, formatter)


def render_markdown(source):
    # Rendering the hard way because we need pygments
    renderer = MarkdownRenderer()
    md = misaka.Markdown(renderer, extensions=misaka.EXT_TABLES | misaka.EXT_FENCED_CODE | misaka.EXT_AUTOLINK |
                         misaka.EXT_STRIKETHROUGH)
    rendered = md.render(source)

    # Yay slowest markdown renderer ever
    hygiene = BeautifulSoup(rendered, 'html5lib')
    for tag in hygiene.find_all('table'):
        tag.attrs['class'] = 'table table-striped table-condensed'

    # Oi moroz moroz ne moroz mena
    return Markup(str(hygiene))  # Ne moroz mena moigo kona


def cached(timeout=None, key=None):
    timeout = timeout or 99999999999
    key = key or 'view/%s'

    if app.config.get('DEBUG', False):
        timeout = min(timeout, 3)

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = key % request.path
            rv = cache.get(cache_key)
            if rv is not None:
                return rv
            rv = f(*args, **kwargs)
            cache.set(cache_key, rv, timeout=timeout)
            return rv
        return decorated_function

    return decorator


from app import main


@app.errorhandler(404)
def not_found(_error):
    return render_template('404.html'), 404


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/x-icon')


@app.route('/favicon-152.png')
def favicon_152():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon-152.png', mimetype='image/png')