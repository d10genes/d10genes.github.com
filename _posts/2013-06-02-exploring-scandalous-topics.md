---
layout: post
title: "Exploring scandalous topics with python and gensim"
description: ""
category:
tags: [python, gensim, nlp]
---
{% include JB/setup %}

June 1

Using the [New York Times developer API](http://developer.nytimes.com/) and mongodb to track down articles, and [gensim](http://radimrehurek.com/gensim/) and [pandas](http://pandas.pydata.org/) to analyze them, I looked to see if it was possible to automatically detect distinct scandals from within NYT articles from 1992 to 2013 through topic modeling.

# Scraping
Some preliminary installations for web scraping I used were:

	pip install pymongo
	pip install requests
	pip install lxml
	pip install cssselect

After these imports, you need to create a mongodb connection, and get to work constructing the query. Using some nifty aspects of the API, you can restrict the query to search the body of the articles, and limit the geography, subject and dates to the United States, politics and 1992-2013, and get it to return the title, URL, and date of the article.

It grabs 10 results at a time, so each time you want to get the next set of 10 results, you need to increment the offset by one (I use python's `itertools.count` to get an indefinite  loop counter). This loop fetches all the results, and stores them to a mongodb collection:
	
	connection = pymongo.Connection( "localhost", 27017 )
	db = connection.nyt
	page = 0
	party = 'republican'
	#party = 'democrat'
	#I couldn't find a way to do OR in the query, so searched once for republican and once for 	#democrat...kinda hacky though
	
	q = 'http://api.nytimes.com/svc/search/v1/article?'
	params = {'query': 'body:scandal+{} geo_facet:[UNITED STATES]'.format(party),
	            'begin_date': '19920101',
	            'end_date': '20131201',
	            'fields': 'title,url,date',
	            'offset': page,
	            'api-key': apikey
			  }
			  
	fdate = lambda d: dt.datetime.strptime(d, '%Y%m%d')
	
	for page in count():
	    params.update({'offset': page})  #fetch another ten results from the next page
	    r = requests.get(q, params=params)
	    res = json.loads(r.content)["results"]
	    if res:
	        for dct in res:
	            url = dct.pop('url')
	            dct['date'] = fdate(dct['date'])  #string -> format as datetime object
	            db.raw_text.update({'url': url}, {'$set': dct}, upsert=True)
	    else:  #no more results
	        break
	    print page,
	    sleep(.2)  #nyt doesn't like it if you ask for stuff too often
	    
There's lots of other cool things you can do with facets and such, but this will be enough for now (and by the way, you need an [API key](http://developer.nytimes.com/apps/register) to do this). Anyways, here's a sample of the resulting urls:

	>>> [doc['url'] for doc in db.raw_text.find()][:5]
	[u'http://www.nytimes.com/2007/08/15/opinion/15wed3.html',
	 u'http://www.nytimes.com/2007/03/16/washington/16cong.html',
	 u'http://www.nytimes.com/2006/03/11/politics/11lobby.html',
	 u'http://www.nytimes.com/2006/04/30/washington/30cunningham.html',
	 u'http://www.nytimes.com/2004/04/09/business/senate-panel-asked-to-give-sec-proposals-a-chance.html']
	
So we have the urls and titles, but still need the text for our analysis. Thanks to python's conciseness the basic scraping functionality is pretty straightforward:


	def get_text(e):
	    "Function to extract text from CSSSelector results"
	    try:
	        return ' '.join(e.itertext()).strip().encode('ascii', 'ignore')
	    except UnicodeDecodeError:
	        return ''
	
	
	def grab_text(url, verbose=True):
	    "Main scraping function--given url, grabs html, looks for and returns article text"
	    if verbose:  #page counter
	        print grab_text.c,
	    grab_text.c += 1
	    r = requests.get(url, params=all_pages)
	    content = fromstring(r.content)
	    for _sel in _sels:
	        text_elems = CSSSelector(_sel)(content)
	        if text_elems:
	            return '\n'.join(map(get_text, text_elems))
	    return ''
	
	#Selectors for finding text of articles within the DOM...quite a few patterns among NYT articles
	_sels =  ['p[itemprop="articleBody"]', "div.blurb-text", 'div#articleBody p', 'div.articleBody p', 'div.mod-nytimesarticletext p']
	all_pages = {'pagewanted': 'all'}
	

The rest of the code is in the repo [link], and it returns about 874 results (with more scandalous articles coming out every day!).


#Topic Model
I use the following `format` function to lowercase and split the words that should be useful for the analysis (the word counts would be too sparse if we didn't count upper and lower case versions as the same word):

	def format(txt):
	    tt = re.sub(r"'s\b", '', txt).lower()
	    tt = re.sub(r'[\.\,\;\:\'\"\(\)\&\%\*\+\[\]\=\?\!/]', '', tt)    
	    tt = re.sub(r' *\$[0-9]\S* ?', ' <money> ', tt)    
	    tt = re.sub(r' *[0-9]\S* ?', ' <num> ', tt)    
	    tt = re.sub(r'[\-\s]+', ' ', tt)
	    return tt.strip().split()
	
	dmap = lambda dct, a: [dct[e] for e in a]

(dmap works like the built-in map, but takes a dictionary instead of a function as an argument, like pandas' map method). 

We can use `format` and some built in gensim functionality to convert our list of document-dictionaries into a [tf-idf](http://en.wikipedia.org/wiki/Tf%E2%80%93idf) list of documents (set of word counts normalized by how frequently the words appear in all documents), ready for gensim to use.

	texts = [format(doc['text']) for doc in raw]
	dictionary = corpora.Dictionary(texts)
	corpus = [dictionary.doc2bow(text) for text in texts]
	tfidf = models.TfidfModel(corpus)
	tcorpus = dmap(tfidf, corpus)

We can then feed this tf-idf corpus into gensim's LSI model, and tell it to look for 7 different topics:

	model = models.lsimodel.LsiModel(corpus=tcorpus, id2word=dictionary, num_topics=7)

#Model evaluation/results

After `model` has been computed (which can take a bit of time), its `show_topics` method returns a list of `(score, word)` tuples for each topic, which we can use to get an idea of what the topic represents (we'll ignore the scores here):

[Code snippet] 

Accessing the model using python's get-item syntax with the document as the argument returns a list of the topics' indices along with the associated scores (model[document] => [(topic_i, score_i), ...]). We can use this method on each of the original input documents, and sort the output by the scores to give the topic most closely associated with each document, and can also get the topic_words list that shows the words associated with each topic:

	topic_words = [[w for _, w in tups] for tups in model.show_topics(**_kwargs)]


A dataframe will be useful for summarizing the words associated with each topic:

[Code snippet]

The first topic looks like a greatest hits list of scandal names, that doesn't really refer to any specific scandal. You have the two parties, names of presidents and speakers of the house (Gingrich and [the other] Foley), and words like "money", "voters", and "senator" that apparently tend to occur when the New York Times discusses political scandals.

Topic one looks like it has to do with campaign finance scandals/controversies from the early 90s, with names of politicians that supported campaign-finance reform like McCain, Meehan and Shays. Words like "finance", "contributions", "donations", "ban", "limits" and "soft" should also be tipoffs. 

This topic is probably similar to topic 2, which appears to be more closely associated with scandals and investigations ("department", "justice", "independent", "prosecutor") that led to the push for campaign-finance reform in the 90s. We see references to John Huang, Charlie Trie, and Clinton's Chief of Staff Harold Ickes, two supposedly resigned to take the fall for the donations scandal.

The financial nature of this scandal looks like it has at least some similarities (like the word "Huang") with the scandal of topic 3, the house bank overdraft scandal. It has words such as "bank", "overdrafts", and "checks" towards the top, along with names of politicians who were around during the time.

Topics 3, 4 and 5 look like they have a lot in common with previous scandals, as well as the house bank overdraft scandal, with some of the Enron and Mark Foley scandal mixed in. You've got "Enron", "accounting", "stock", "investors", as well as the words "page", "Foley", and "Fordham" as significant topic works in some of these.

Topic six website it has a lot in common with previous topics, but with some advices but Rostenkowski and apricot.


The topic_data a list from the code above allows us to construct a dataframe with the title of each article, and topic that best represents it according to the model. This dataframe can then used for some basic analysis of the model's performance.

[Code Snippet]


As the value count shows, the 0th topic is extremely under represented within the documents that were fed into the model. 




Surprising how many candidates were around that I still recognize




