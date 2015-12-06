#!/usr/bin/env python
import argparse
import cPickle
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import re

from features import OrthographicEncoder
from io_ import load_doc, LTFDocument, LAFDocument, write_crfsuite_file
from logger import configure_logger
from util import convert_extents, sort_mentions

logger = logging.getLogger()
configure_logger(logger) 


def write_train_data(lafs, ltf_dir, enc, trainf):
    """Extract features and target labels for each LTF/LAF pair and write to
    disk in CRFSuite data format.

    For details regarding this format, consult

    http://www.chokkan.org/software/crfsuite/manual.html

    Inputs
    ------
    lafs: list of str
        Paths to LAF files.

    ltf_dir : str
        Directory to search for LTF files.

    enc : features.Encoder
        Feature encoder.

    trainf : str
        CRFsuite training file.
    """
    with open(trainf, 'w') as f:
        for laf in lafs:
            # Check that the LTF and LAF are valid.
            bn = os.path.basename(laf) 
            ltf = os.path.join(ltf_dir, bn.replace('.laf.xml', '.ltf.xml')) 
            laf_doc = load_doc(laf, LAFDocument, logger) 
            ltf_doc = load_doc(ltf, LTFDocument, logger) 
            if laf_doc is None or ltf_doc is None:
                continue 
            
            # Extract features/targets.
            try:
                # Extract tokens.
                tokens, token_ids, token_onsets, token_offsets = ltf_doc.tokenized() 
                #print len(tokens)
                # Convert mentions to format expected by the encoder  that is,
                # (tag, token_onset, token_offset).
                mentions = laf_doc.mentions()
                #print mentions
                if len(mentions) == 0:
                    mentions_ = [] 
                else:
                    # Map to the minimal enclosing span of tokens in the
                    # supplied LTF.
                    entity_ids, tags, extents, char_onsets, char_offsets = zip(*mentions)
                    # print token_onsets
                    # print char_onsets
                    # print char_onsets
                    mention_onsets, mention_offsets = convert_extents(char_onsets, char_offsets,
                                                                      token_onsets, token_offsets)
                    #print mention_onsets
                    mentions_ = list(zip(tags, mention_onsets, mention_offsets)) 

                # Eliminate overlapping mentions, retaining whichever
                # is first when sorted in ascending order by (onset, offset).
                #print mentions_
                sort_mentions(mentions_) 
                prev_mention_offset = -1 
                temp_mentions_ = [] 
                for tag, mention_onset, mention_offset in mentions_:
                    if mention_onset > prev_mention_offset:
                        temp_mentions_.append([tag, mention_onset, mention_offset]) 
                    prev_mention_offset = mention_offset 
                mentions_ = temp_mentions_
                # print 'mentions:'
                #print mentions_
                #print tokens

                # Extract features/targets and write to file in CRFSuite
                # format.
                feats, targets = enc.get_feats_targets(tokens, mentions_)
                #print 'feats: \n'
                #print feats
                #print 'targets:'
                #print targets
            except KeyError:
                logger.warn('Feature extraction failed for %s. Skipping.' % laf) 
                continue 

            # Write to file.
            write_crfsuite_file(f, feats, targets) 

            
##########################
# Ye olde' main
##########################
if __name__ == '__main__':
    # Parse command line arguments.
    # print 123
    # cmd = ['crfsuite', '-h']
    # subprocess.call(cmd)
    parser = argparse.ArgumentParser(description='Train CRF-based named entity tagger using Passive Aggresive algorithm.',
                                     add_help=False,
                                     usage='%(prog)s [options] model_dir laf_dir lafs') 
    parser.add_argument('model_dir', nargs='?',
                        help='Model output2 dir')
    parser.add_argument('frequency', nargs='?',
                        help='frequency file')
    parser.add_argument('ltf_dir', nargs='?',
                        help='.ltf.xml file dir') 
    parser.add_argument('lafs', nargs='*',
                        help='.ltf.xml files to be processed')
    parser.add_argument('-S', nargs='?', default=None,
                        metavar='fn', dest='scpf',
                        help='Set script file (Default: None)') 
    parser.add_argument('--n_left', nargs='?', default=2,
                        type=int, metavar='n',
                        help='Length of left context (Default: %(default)s)') 
    parser.add_argument('--n_right', nargs='?', default=2,
                        type=int, metavar='n',
                        help='Length of right context (Default: %(default)s)') 
    parser.add_argument('--max_prefix_len', nargs='?', default=4,
                        type=int, metavar='n',
                        help='Length of largest prefix (Default: %(default)s)') 
    parser.add_argument('--max_suffix_len', nargs='?', default=4,
                        type=int, metavar='n',
                        help='Length of largest suffix (Default: %(default)s)') 
    parser.add_argument('--update', nargs='?', default=1, choices=[0,1,2],
                        type=int, metavar='n',
                        help='Feature weight update strategy. 0=without slack variables, 1=type1, 2=type. (Default: %(default)s)') 
    parser.add_argument('--disable_averaging', action='store_false',
                        dest="use_averaging", default=True,
                        help='Disable feature weight averaging.')
    parser.add_argument('--aggressiveness', nargs='?', default=1,
                        type=float, metavar='x',
                        help='Aggressiveness parameter. (Default: %(default)s)') 
    parser.add_argument('--epsilon', nargs='?', default=1e-5,
                        type=float, metavar='x',
                        help='Used to test for convergence. (Default: %(default)s)') 
    parser.add_argument('--max_iter', nargs='?', default=50,
                        type=int, metavar='n',
                        help='Maximum # of training iterations (Default: %(default)s)') 
    parser.add_argument('--display_progress', action='store_true',
                        default=False,
                        help='Display training progress.')
    args = parser.parse_args() 

    if len(sys.argv) == 1:
        parser.print_help() 
        sys.exit(1) 

    # Determine ltfs/lafs to process.
    if not args.scpf is None:
        with open(args.scpf, 'r') as f:
            args.lafs = [l.strip() for l in f.readlines()] 

    # Exit with error if model directory already exists.
    if not os.path.exists(args.model_dir):
        os.makedirs(args.model_dir) 
    else:
        logger.error('Model directory already exists. Exiting.') 
        sys.exit(1)

    # load frequency
    frequency = dict()
    if not os.path.exists(args.frequency):
        logger.error('can not find frequency file')
    else:
        f_fre = open(args.frequency,'r')
        for line in f_fre.readlines():
            match = re.match(r'(.*)\t(.*)\n', line)
            if not match is None:
                frequency[match.group(1)] = float(match.group(2))
            else:
                print 'match wrong in frequency file'
    # print frequency

    # Create working directory.
    temp_dir = tempfile.mkdtemp() 

    # Initialize and save encoder.
    enc = OrthographicEncoder(args.n_left, args.n_right,
                              args.max_prefix_len, args.max_suffix_len, frequency)
    encf = os.path.join(args.model_dir, 'tagger.enc') 
    with open(encf, 'w') as f:
        cPickle.dump(enc, f, protocol=2) 

    # Train.
    trainf = os.path.join(temp_dir, 'train.txt')
    # print temp_dir
    write_train_data(args.lafs, args.ltf_dir, enc, trainf)
    def is_empty(fn):
        return os.stat(fn).st_size == 0 
    if not is_empty(trainf):
        modelf = os.path.join(args.model_dir, 'tagger.crf') 
        cmd = ['/home/wangtianlu/local/bin/crfsuite', 'learn',
               '-m', modelf,
               '-a', 'pa', # Train with passive aggressive algorithm.
               '-p', 'type=%d' % args.update,
               '-p', 'c=%f' % args.aggressiveness,
               '-p', 'error_sensitive=%d' % True,
               '-p', 'averaging=%d' % args.use_averaging,
               '-p', 'max_iterations=%d' % args.max_iter,
               '-p', 'epsilon=%f' % args.epsilon,
               '-p', 'feature.possible_transitions=0',
               trainf] 
        with open(os.devnull, 'w') as f:
            if args.display_progress:
                subprocess.call(cmd, stderr=f)
            else:
                subprocess.call(cmd, stderr=f, stdout=f)
    else:
        logger.error('Training file contains no features/targets. Exiting.') 

    # Clean up.
    # os.system('mv' + ' ' + trainf + ' ' + '~/Desktop')

    shutil.rmtree(temp_dir)
