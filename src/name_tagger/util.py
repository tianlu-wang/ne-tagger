"""Utility functions.
"""
__all__ = ['convert_extents', 'sort_mentions'] 

from bisect import bisect, bisect_left 


def convert_extents(char_onsets, char_offsets, token_onsets, token_offsets):
    """Convert from char onset/offset extends to token onset/offset extents.

    Maps to the minimal enclosing span of tokens in the supplied tokenization.
    All onsets/offsets assume zero-indexing.

    Inputs
    ------
    char_onsets : list
        Character onsets of mentions.
        
    char_offsets : list
        Character offsets of mentions

    token_onsets : list
        Character onsets of tokens in supplied tokenization.
    
    token_offsets : list
        Character offsets of tokens in supplied tokenization.
    """
    mention_token_onsets = [bisect(token_onsets, char_onset) - 1 for char_onset in char_onsets]
    mention_token_offsets = [bisect_left(token_offsets, char_offset) for char_offset in char_offsets] 
    return mention_token_onsets, mention_token_offsets 


def sort_mentions(mentions):
    """Sort mentions in place in ascending order of token_onset, then
    token_offset.

    Inputs
    ------
    mentions : list of tuples
        List of mentions, each represented as a tuple of form (tag, token_onset, token_offset).
    """
    mentions.sort(key=lambda x: (x[1], x[2])) 
