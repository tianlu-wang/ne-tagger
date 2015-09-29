"""Classes supporting alignment between a tokenization and text.
"""
try:
    import regex as re 
    RE_FLAGS = re.VERSION0 | re.UNICODE 
except ImportError:
    import re 
    RE_FLAGS = re.UNICODE 

__all__ = ['AlignmentFailed', 'Aligner'] 


class AlignmentFailed(Exception):
    pass


class Aligner(object):
    """Aligns raw XML with tokenized version of its text content.
    """
    def align(self, txt, tokens):
        """Align txt with tokenized content.

        Inputs
        ------
        txt : unicode
            Raw, untokenized text.

        tokens : list of unicode
            Tokenization, stored as list of tokens.

        Outputs
        -------
        spans : list of tuples
            List of token spans, each represented as a (begin_index, end_index)
            tuple, where begin_index is the 0-indexed character onset of the
            token and end_index the 0-indexed character offset of the token.
        """
        spans = [] 
        bi = 0 
        for token in tokens:
            try:
                # Find token span.
                token_len = len(token) 
                token_bi = bi + txt[bi:].index(token) 
                token_ei = token_bi + token_len - 1 
                spans.append([token_bi, token_ei]) 

                # Advance in text.
                bi = token_ei + 1 
            except ValueError:
                raise AlignmentFailed(token) 

        return spans 
