from pelican import signals
from pelican.readers import EXTENSIONS, Reader

try:
    import json
    import IPython
    from datetime import datetime
    from nbconverter.html import ConverterHTML
except:
    IPython = False

class iPythonNB(Reader):
    enabled = True
    file_extensions = ['ipynb']

    def read(self, filename):
        import collections
        import simplejson

        text = open(filename)
        # my_ordered_dict = json.loads(json_str, object_pairs_hook=collections.OrderedDict)
        json_txt = json.load(text, object_pairs_hook=collections.OrderedDict)
        metadata_uni = json_txt['metadata']
        first_cell = json_txt['worksheets'][0]['cells'].pop(0)
        metadata_uni_new = first_cell['source']
        metadata_uni_new = json.loads(''.join(metadata_uni_new))
        metadata_uni.update(metadata_uni_new)
        print metadata_uni

        # Creating temp file to read from after manipulating some json
        import tempfile
        tmp_filename = '/tmp/rendering_notebook.ipynb'
        with open(tmp_filename, 'w+b') as temp:
            temp.write(simplejson.dumps(json_txt, indent=2))
            print 'temp:', temp
            print 'temp.name:', temp.name

        converter = ConverterHTML(tmp_filename)
        converter.read()


        # print metadata_uni_new
        # with open('crap.txt', 'wb') as f:
        #     f.write(json.dumps(metadata_uni))

        # metadata_uni = metadata_uni_new
        metadata2 = {}
        # Change unicode encoding to utf-8
        for key, value in metadata_uni.iteritems():
          if isinstance(key, unicode):
            key = key.encode('utf-8')
          if isinstance(value, unicode):
            value = value.encode('utf-8')
          metadata2[key] = value

        metadata = {}
        for key, value in metadata2.iteritems():
            key = key.lower()
            metadata[key] = self.process_metadata(key, value)
        metadata['ipython'] = True

        # import ipdb; ipdb.set_trace()
        content = converter.main_body() # Use the ipynb converter
        # change ipython css classes so it does not mess up the blog css
        content = '\n'.join(converter.main_body())
        # replace the highlight tags
        content = content.replace('class="highlight"', 'class="highlight-ipynb"')
        # specify <pre> tags
        content = content.replace('<pre', '<pre class="ipynb"')
        # create a special div for notebook
        content = '<div class="ipynb">' + content + "</div>"
        # Modify max-width for tables
        content = content.replace('max-width:1500px;', 'max-width:540px;')
        # h1,h2,...
        for h in '123456':
          content = content.replace('<h%s' % h, '<h%s class="ipynb"' % h)
        return content, metadata


def add_reader(arg):
    EXTENSIONS['ipynb'] = iPythonNB


def register():
    signals.initialized.connect(add_reader)