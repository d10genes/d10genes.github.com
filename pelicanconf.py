#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals


AUTHOR = u'Chris Beard'
SITENAME = u'Blogistic Regression'
SITEURL = r''
# SITEURL = r'd10genes.github.io'

# TIMEZONE = 'America/New-York'

DEFAULT_LANG = u'en'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None

# Blogroll
LINKS =  (('IPython', 'http://ipython.org/'),
          ('Python.org', 'http://python.org/'),
          ('Pandas', 'http://pandas.pydata.org/'),
          )

# Social widget
# SOCIAL = (('You can add links in your config file', '#'),
#           ('Another social link', '#'),)
SOCIAL = ()

DEFAULT_PAGINATION = False

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True

#https://github.com/danielfrg/pelican-ipythonnb
PLUGIN_PATH = 'custom_plugins_dir'
PLUGINS = ['custom_plugins_dir.ipythonnb']
MARKUP = ('md', 'ipynb')

GOOGLE_ANALYTICS = 'UA-40869107-1'

DISQUS_SITENAME = 'blogistic'


