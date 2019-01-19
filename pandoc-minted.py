#!/usr/bin/env python
''' A pandoc filter that has the LaTeX writer use minted for typesetting code.

Usage:
    pandoc --filter ./minted.py -o myfile.tex myfile.md
'''

import string
from string import Template
from pandocfilters import toJSONFilter, RawBlock, RawInline


def unpack_code(value, language):
    ''' Unpack the body and language of a pandoc code element.

    Args:
        value       contents of pandoc object
        language    default language
    '''
    [[_, classes, attributes], contents] = value

    if len(classes) > 0:
        language = classes[0]

    attributes = ', '.join('='.join(x) for x in attributes)

    return {'contents': contents, 'language': language,
            'attributes': attributes}


def unpack_metadata(meta):
    ''' Unpack the metadata to get pandoc-minted settings.

    Args:
        meta    document metadata
    '''
    settings = meta.get('pandoc-minted', {})
    if settings.get('t', '') == 'MetaMap':
        settings = settings['c']

        # Get language.
        language = settings.get('language', {})
        if language.get('t', '') == 'MetaInlines':
            language = language['c'][0]['c']
        else:
            language = None

        return {'language': language}

    else:
        # Return default settings.
        return {'language': 'text'}
    

def minted(key, value, format, meta):
    ''' Use minted for code in LaTeX.

    Args:
        key     type of pandoc object
        value   contents of pandoc object
        format  target output format
        meta    document metadata
    '''
    if format != 'latex':
        return

    if key not in ('CodeBlock', 'Code'):
        return

    settings = unpack_metadata(meta)

    code = unpack_code(value, settings['language'])

    # Determine what kind of code object this is.
    if key == 'CodeBlock':
        template = Template(
            '\\begin{minted}[$attributes]{$language}\n$contents\n\\end{minted}'
        )
        return [RawBlock(format, template.substitute(code))]

    elif key == 'Code':
        contents = code['contents']
        if '{' in contents or '}' in contents:
            # Try some other delimiter.
            for c in '|!@#^&*-=+' + string.digits + string.ascii_letters:
                if c not in contents:
                    code['start_delim'] = code['end_delim'] = c
                    break
            else:
                raise ValueError(
                    'Unable to determine delimiter to place around %r.' % (
                        contents, ))
        else:
            code['start_delim'] = '{'
            code['end_delim'] = '}'

        template = Template(
            '\\mintinline[$attributes]{$language}'
            '$start_delim$contents$end_delim')
        return [RawInline(format, template.substitute(code))]


if __name__ == '__main__':
    toJSONFilter(minted)

