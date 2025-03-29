from markdownify import MarkdownConverter

class IgnoreTitleConverter(MarkdownConverter):
    '''
    Create a custiom MarkdownConverter to ignore <title> tag
    '''
    def convert_title(self, el, text, parent_tags):
        return ''
    
def convert_to_markdown(html, **options):
    return IgnoreTitleConverter(**options).convert(html)