import sys

if sys.version_info >= (3,):
    def isidentifier(ident):
        return ident.isidentifier()
else:
    # A bit hackier way for Python 2.x support
    import re, keyword
    def isidentifier(ident):
        return re.match("[_A-Za-z][_a-zA-Z0-9]*$", ident) and not keyword.iskeyword(ident) or False
