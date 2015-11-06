# -*- coding: utf-8 -*-
#!/usr/bin/env python
__author__ = 'koala'
import sys
reload(sys)
sys.setdefaultencoding('utf8')
from functools import wraps
import re
import os
import codecs
from chunk import BILOUChunkEncoder

__all__ = ['OrthographicEncoder'] 


class Encoder(object):
    """Abstract base class for feature encoders.

    Inputs
    ------
    n_left : int, optional
        Number of tokens of left context to include.
        (Default: 2)

    n_right : int, optional
        Number of tokens of right context to include.
        (Default: 2)

    Attributes
    ----------
    chunker : chunk.ChunkEncoder
        ChunkEncoder instance used to generate tags.
    """
    def __init__(self, n_left=2, n_right=2):
        self.chunker = BILOUChunkEncoder() 
        self.n_left = n_left 
        self.n_right = n_right 

    def get_feats_for_token(self, token):
        """Return features for token.

        Inputs
        ------
        token : str
            Token.

        Outputs
        -------
        feats : tuple of str
            Features vector.
        """
        raise NotImplementedError 

    def get_feats(self, tokens):
        """Return features corresponding to token sequence.

        Inputs
        ------
        tokens : list of str
            Token sequence.

        Outputs
        -------
        feats : lsit of tuples
            Feature vector sequence.
        """
        feats = [self.get_feats_for_token(token) for token in tokens] 
        feats = zip(*feats) 
        new_feats = [] 
        for ii, feats_ in enumerate(feats):
            for pos in xrange(-self.n_left, self.n_right+1):
                feat_id = 'F%d[%d]' % (ii, pos) 
                k = -pos 
                new_feats.append(['%s=%s' % (feat_id, val) if val is not None else val for val in roll(feats_, k)])

        new_feats = zip(*new_feats)
        #print new_feats[0]
        #print '============================================================================================'

        # for ii,row in enumerate(new_feats):
        #     new_row = [v if not v is None else 'none' for v in row]
        #     new_feats[ii] = new_row
        # Filter out None vals in rows where they occur.
        for ii, row in enumerate(new_feats):
            new_row = [v for v in row if not v is None]
            new_feats[ii] = new_row
        # print new_feats[0]
        # print '**********************************************************************************************'
        return new_feats


    def get_targets(self, tokens, mentions):
        """Return tag sequence to train against.

        Inputs
        ------
        tokens : list of str
            Token sequence.

        mentions : list of list
            List of mention tuples, each of the form (tag, start_token_index,
            enc_token_index).

        Outputs
        -------
        targets : list of str
            Target label sequence.
        """
        tags = ['O' for token in tokens] 
        for tag, bi, ei in mentions:
            chunk = tokens[bi:ei+1] 
            tags[bi:ei+1] = self.chunker.chunk_to_tags(chunk, tag) 
        return tags 

    def get_feats_targets(self, tokens, mentions):
        """Return features/tag sequence to train against.

        Inputs
        ------
        tokens : list of str
            Token sequence.

        mentions : list of list
            List of mention tuples, each of the form (tag, start_token_index,
            enc_token_index).

        Outputs
        -------
        feats : list of tuples
            Feature vector sequence.

        targets : list of str
            Target label sequence.
        """
        feats = self.get_feats(tokens) 
        targets = self.get_targets(tokens, mentions) 
        return feats, targets 


class OrthographicEncoder(Encoder):
    """Encoder that assigns to each token a feature vector consisting of a
    basic set of lexical and orthographic features.

    Inputs
    ------
    n_left : int, optional
        Number of tokens of left context to include.
        (Default: 2)

    n_right : int, optional
        Number of tokens of right context to include.
        (Default: 2)

    max_prefix_len : int, optional
        Maximum length, in characters, of prefix features.
        (Default: 4)

    max_suffix_len : int, optional
        Maximum length, in characters, of suffic features.
        (Default: 4)

    Attributes
    ----------
    chunker : chunk.ChunkEncoder
        ChunkEncoder instance used to generate tags.

    prefix_lengths : list of int
        List of lengths of prefixes to be considered.

    suffix_lengths : list of int
        List of lengths of suffixes to be considered.
    """
    # dict_path = './dics'
    # lexicon = [[]]
    # for roots, dirs, files in os.walk(dict_path):
    #     for file in files:
    #         f = codecs.open(dict_path + '/'+file, 'r', encoding='utf-8')
    #         lexicon.append([line[:-1] for line in f.readlines()])
    # print 'this is lexicon[0]'
    # print lexicon.pop(0)
    # print str(len(lexicon))+'-----------this is len of lexicon'

    def __init__(self, n_left=2, n_right=2, max_prefix_len=4, max_suffix_len=4, frequency = {}):
        super(OrthographicEncoder, self).__init__(n_left, n_right) 
        self.prefix_lengths = range(1, max_prefix_len+1) 
        self.suffix_lengths = range(1, max_suffix_len+1)
        self.frequency = frequency

    @wraps(Encoder.get_feats_for_token)
    def get_feats_for_token(self, token):
        # print 'this is type of token:'
        # print type(token)
        feats = [token]
        feats.append(token.lower())  # Lowercase feature
        # Prefix features n=1,...,4 .
        n_char = len(token)
        for prefix_len in self.prefix_lengths:
            if prefix_len <= n_char:
                feats.append(token[:prefix_len])
            else:
                feats.append(None)

        # Suffix features n=1,...,4 .
        for suffix_len in self.suffix_lengths:
            if suffix_len <= n_char:
                feats.append(token[-suffix_len:]) 
            else:
                feats.append(None)

        # for i in range(len(self.lexicon)):
        #     feats.append(unicode(token) in self.lexicon[i])

        # if token[0] is 'o':
        # print token
        # print 'this is frequency:'
        # print self.frequency.get(token)
        feats.append(self.frequency.get(token))

        feats.extend(word_type(token))
        # print 'this is len of feats'
        # print feats
        return feats


ALL_DIGITS_REO = re.compile(r'\d+$')
ALL_NONLETTERS_REO = re.compile(r'[^a-zA-Z]+$')
HAVE_DIGITS_REO = re.compile(r'\d')

def word_type(word):
    """Determine word type of token.

    Inputs
    ------
    word : str
        A word token.

    Outputs
    -------
    begins_cap : bool
        Boolean indicating whether word begins with a capitalized letter.

    all_capitalized : bool
        Boolean indicating whether or not all letters of word are capitalized.

    all_digits : bool
        Boolean indicating whether word is composed entirely of digits.

    all_nonletters : bool
        Boolean indicating whether word is composed entirely of nonletters.

    contains_period : bool
        Boolean indicating whether word contains period.
    """
    begins_cap = word[0].isupper() 
    all_capitalized = word.isupper() 
    all_digits = word.isdigit() 
    all_nonletters = ALL_NONLETTERS_REO.match(word) is not None 
    contains_period = '.' in word
    contains_hyphen = '-' in word
    contains_comma = ',' in word
    contains_digit = bool(HAVE_DIGITS_REO.search(word))
    contains_single_quote = '\'' in word
    contains_asporophe = unicode('ʼ') in word


    return begins_cap, all_capitalized, all_digits, all_nonletters, contains_period, \
           contains_hyphen, contains_comma, contains_digit, contains_single_quote, contains_asporophe


def roll(feats, k=0):
    """Roll elements of list.

    Elements that rolle beyond the last position are NOT re-introduced at the
    first as with numpy.roll. Rather, they are replaced by None.

    Inputs
    ------
    feats : list of tuples                                                  
        Feature vector sequence.   

    k : int, optional
        Number of places by which elements are shifted.
        (Default: 0)
    """
    if k == 0:
        new_feats = list(feats) 
    elif k > 0:
        new_feats = [None]*k
        new_feats.extend(feats[:-k])
        for i in range(k):
            new_feats[i] = feats[len(feats)-k+i]
    else:
        new_feats = list(feats[-k:]) 
        new_feats.extend([None]*-k)
        for i in range(k):
            new_feats[len(feats)-k+i] = feats[i]
    return new_feats