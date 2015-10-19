#!/usr/bin/env python
import argparse
import glob
import logging
import os
import sys

from io_ import load_doc, LTFDocument, LAFDocument
from logger import configure_logger
from util import convert_extents

logger = logging.getLogger()
configure_logger(logger)


def calc_stats(sys_laf, ref_dir, ltf_dir):
    """Return hits, false alarms, and misses for system output LAF relative
    to reference LAF located in ref_dir.
    
    Inputs
    ------
    sys_laf : str
        LAF file containing system output.

    ref_dir : str
        Directory containing reference LAF files.

    ltf_dir : str
        Directory containing LTF files.
    """
    # Check that LTF and system and reference LAF are valid.
    sys_doc = load_doc(sys_laf, LAFDocument, logger)
    bn = os.path.basename(sys_laf)
    ref_laf = os.path.join(ref_dir, bn)
    ref_doc = load_doc(ref_laf, LAFDocument, logger)
    ltf = os.path.join(ltf_dir, bn.replace('.laf.xml', '.ltf.xml'))
    ltf_doc = load_doc(ltf, LTFDocument, logger)
    if not all([ref_laf, sys_laf, ltf_doc]):
        return 0.0, 0.0, 0.0

    # Calculate hits, misses, and false alarms.
    try:
        tokens, token_ids, token_onsets, token_offsets = ltf_doc.tokenized()

        # Convert mentions to (token_onset, token_offset, tag) format.
        sys_mentions = sys_doc.mentions()
        if len(sys_mentions) > 0:
            sys_ids, sys_tags, sys_extents, sys_char_onsets, sys_char_offsets = zip(*sys_mentions)
            sys_mention_onsets, sys_mention_offsets = convert_extents(sys_char_onsets, sys_char_offsets,
                                                                      token_onsets, token_offsets)
            sys_mentions = zip(sys_tags, sys_mention_onsets, sys_mention_offsets)
            sys_mentions = set(map(tuple, sys_mentions))
        else:
            sys_mentions = set()

        ref_mentions = ref_doc.mentions()
        if len(ref_mentions) > 0:
            ref_ids, ref_tags, ref_extents, ref_char_onsets, ref_char_offsets = zip(*ref_mentions)
            ref_mention_onsets, ref_mention_offsets = convert_extents(ref_char_onsets, ref_char_offsets,
                                                                      token_onsets, token_offsets)
            ref_mentions = zip(ref_tags, ref_mention_onsets, ref_mention_offsets)
            ref_mentions = set(map(tuple, ref_mentions))
        else:
            ref_mentions = set()

        # Calculate.
        n_hit = len(sys_mentions & ref_mentions)
        n_fa = len(sys_mentions - ref_mentions)
        n_miss = len(ref_mentions - sys_mentions)
    except:
        logger.warn('Scoring failed for %s. Skipping.' % ref_laf)
        n_hit = n_fa = n_miss

    return n_hit, n_fa, n_miss


def convert_mentions(mentions, token_onsets, token_offsets):
    """Convert mentions format to set of tuples of form 
    (start_token, end_token, tag).

    Inputs
    ------
    mentions : sequence
        Sequence of mention tuples. For format, see LTFDocument.mentions.

    token_onsets : sequence of int
        Sequence of character onsets of tokens.

    token_offsets : sequence of int
        Sequence of character offsets of tokens.

    Outputs
    -------
    mentions_ : list of tuple
        List of mentions in DIFFERENT format from that of mentions. This
        format consists of a tuple of (TAG, TOKEN_ONSET, TOKEN_OFFSET),
        where TOKEN_ONSET and TOKEN_OFFSET are the token indices.
    """
    # Extract sys/ref mentions and represent as tuples of
    #
    #     (start_token, end_token, tag)
    if len(mentions) > 0:
        mention_ids, tags, char_onsets, char_offsets = zip(*mentions)
        mention_onsets, mention_offsets = convert_extents(char_onsets, char_offsets,
                                                          token_onsets, token_offsets)
        mentions_ = zip(tags, mention_onsets, mention_offsets)
        mentions_ = set(map(tuple, mentions_))
    else:
        mentions_ = set()

    return mentions_


##########################
# Ye olde main
##########################
if __name__ == '__main__':
    # Parse command line arguments.
    parser = argparse.ArgumentParser(description='Score named entity tagger output.',
                                     add_help=False,
                                     usage='%(prog)s [options] ref_dir sys_dir ltf_dir')
    parser.add_argument('ref_dir', nargs='?',
                        help='Dir containing reference .laf.xml files')
    parser.add_argument('sys_dir', nargs='?',
                        help='Dir containing system .laf.xml files')
    parser.add_argument('ltf_dir', nargs='?',
                        help='.ltf.xml file dir')
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    # Calculate hits, misses, and false alarms.
    sys_fns = glob.glob(os.path.join(args.sys_dir, '*.laf.xml'))  # select all *.laf.xml files in the system result
    n_hit = n_fa = n_miss = 0
    i = 0
    for sys_fn in sys_fns:
        n_hit_, n_fa_, n_miss_ = calc_stats(sys_fn, args.ref_dir,
                                            args.ltf_dir)
        n_hit += n_hit_
        n_fa += n_fa_
        n_miss += n_miss_
        i += 1


    # Calculate precision, recall, and f1.
    if n_hit > 0:
        recall = n_hit/float(n_hit + n_miss)
        precision = n_hit/float(n_hit + n_fa)
        f1 = 2*(precision*recall)/(precision+recall)
    else:
        recall = 0
        precision = 0
        f1 = 0
    result_path = './result.txt'
    f = open(result_path, 'a')
    f.write(str(precision)+'\t'+str(recall)+'\t'+str(f1)+'\n')
    f.close()
    logger.info('Hits: %d, Miss: %d, FA: %d' % (n_hit, n_miss, n_fa))
    logger.info('Precision: %f, Recall: %f, F1: %f' % (precision, recall, f1))
