#!/usr/bin/env python
import argparse
import cPickle
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from chunk import BILOUChunkEncoder

from joblib.parallel import Parallel, delayed

from align import Aligner



# from features import OrthographicEncoder
from io_ import load_doc, LTFDocument, LAFDocument, write_crfsuite_file
from logger import configure_logger

logger = logging.getLogger() 
configure_logger(logger) 


def tag_file(ltf, aligner, enc, chunker, modelf, tagged_dir, tagged_ext):
    """Extract features for tokenization in LTF file and tag named entities.

    Inputs
    ------
    ltf : str
        LTF file.

    aligner : align.Aligner
        Aligner instance used to obtain character onsets/offsets of discovered
        mentions.

    enc : features.Encoder
        Encoder instance for feature extraction.

    chunker : chunk.ChunkEncoder
        ChunkEncoder instance for obtaining token onsets/offsets of discovered
        mentions from tag sequences.

    modelf : str
        CRFSuite model file.

    tagged_dir : str
        Directory to which to output2 LAF files.

    tagged_ext : str
        Extension to used for output2 LAF files.
    """
    # Create working directory.                                              
    temp_dir = tempfile.mkdtemp()
    # Load LTF.
    #print ltf  # todo
    ltf_doc = load_doc(ltf, LTFDocument, logger) 
    if ltf_doc is None:
        shutil.rmtree(temp_dir) 
        return
    # Attempt tagging.
    try:
        # Extract tokens.
        tokens, token_ids, token_onsets, token_offsets = ltf_doc.tokenized() 
        txt = ltf_doc.text() 
        spans = aligner.align(txt, tokens)
        # Extract features
        featsf = os.path.join(temp_dir, 'feats.txt')
        feats = enc.get_feats(tokens) 
        write_crfsuite_file(featsf, feats)
        # Tag.
        # print "tmep_dir"+temp_dir
        tagsf = os.path.join(temp_dir, 'tags.txt')
        #probf = os.path.join(temp_dir, 'probs.txt')
        cmd = ['/home/wangtianlu/local/bin/crfsuite', 'tag',
               '-m', modelf,
               featsf]
        with open(tagsf, 'w') as f:
            subprocess.call(cmd, stdout=f)
        # Load tagged output2.

        probf1 = ltf.replace('ltf', 'probs')
	probf = probf1.replace('test', 'probs')

        # print probf
        cmd_ = ['/home/wangtianlu/local/bin/crfsuite', 'tag',
               '-m', modelf, '-i',
               featsf]
        with open(probf, 'w') as f:
            subprocess.call(cmd_, stdout=f)

        # maxprobf = ltf.replace('ltf', 'maxprobs')
        #
        # cmd_ = ['/Users/koala/Documents/lab/Blender/LORELEI/active_learning/ne-tagger/lib/crf/bin/crfsuite','tag',
        #        '-m', modelf, '-i',
        #        featsf]
        # with open(maxprobf, 'w') as f:
        #     subprocess.call(cmd_, stdout=f)

        with open(tagsf, 'r') as f:
            tags = [line.strip() for line in f]
            # print len(tags)  # todo
            tags = tags[:len(tokens)]
            # print len(tags)  # todo
            # print 'this is tags'
            # print tags # todo
        # Chunk tags.
        chunks = chunker.tags_to_chunks(tags)  # todo:bughere
        # Construct mentions.
        doc_id = ltf_doc.doc_id
        mentions = []
        n = 1 
        for token_bi, token_ei, tag in chunks:
            if tag == 'O':
                continue 

            # Assign entity id.
            entity_id = '%s-NE%d' % (doc_id, n) 

            # Determine char onsets/offset for mention extent.
            start_char = token_onsets[token_bi] 
            end_char = token_offsets[token_ei] 

            # Finally, determine text of extent and append.
            extent_bi = spans[token_bi][0] 
            extent_ei = spans[token_ei][1] 
            extent = txt[extent_bi:extent_ei+1] 
            mentions.append([entity_id,           # entity id
                             tag,                 # NE type
                             extent,              # extent text
                             start_char,          # extent char onset
                             end_char,            # extent char offset
                            ]) 

            n += 1 

        # Write detected mentions to LAF file.
        bn = os.path.basename(ltf)
        laf = os.path.join(tagged_dir, bn.replace('.ltf.xml', tagged_ext)) 
        laf_doc = LAFDocument(mentions=mentions, lang=ltf_doc.lang, doc_id=doc_id) 
        laf_doc.write_to_file(laf) 
    except KeyError:
        logger.warn('Problem with %s. Skipping.' % ltf) 

    # Clean up.
    shutil.rmtree(temp_dir)


##########################
# Ye olde' main
##########################
if __name__ == '__main__':
    # parse command line args
    print 'tagger.py called'
    parser = argparse.ArgumentParser(description='Perform named entity tagging.',
                                     add_help=False,
                                     usage='%(prog)s [options] model ltfs') 
    parser.add_argument('model_dir', nargs='?',
                        help='Model dir')
    parser.add_argument('ltfs', nargs='*',
                        help='LTF files to be processed') 
    parser.add_argument('-S', nargs='?', default=None,
                        metavar='fn', dest='scpf',
                        help='Set script file (Default: None)') 
    parser.add_argument('-L', nargs='?', default='./',
                        metavar='dir', dest='tagged_dir',
                        help="Set output2 mentions dir (Default: current)")
    parser.add_argument('-X', nargs='?', default='.laf.xml',
                        metavar='ext', dest='ext',
                        help="Set output2 mentions file extension (Default: .laf.xml)")
    parser.add_argument('-j', nargs='?', default=1, type=int,
                        metavar='n', dest='n_jobs',
                        help='Set num threads to use (default: 1)') 
    args = parser.parse_args() 

    if len(sys.argv) == 1:
        parser.print_help() 
        sys.exit(1) 

    # Determine ltfs to process.
    if not args.scpf is None:
        with open(args.scpf, 'r') as f:
            args.ltfs = [l.strip() for l in f.readlines()] 

    # Initialize chunker, aligner, and encoder.
    chunker = BILOUChunkEncoder() 
    aligner = Aligner() 
    encf = os.path.join(args.model_dir, 'tagger.enc') 
    with open(encf, 'r') as f:
        enc = cPickle.load(f) 

    # Perform tagging in parallel, dumping results to args.tagged_dir.
    n_jobs = min(len(args.ltfs), args.n_jobs) 
    modelf = os.path.join(args.model_dir, 'tagger.crf') 
    f = delayed(tag_file) 
    Parallel(n_jobs=n_jobs, verbose=0)(f(ltf, aligner, enc, chunker,
                                         modelf,
                                         args.tagged_dir,
                                         args.ext) for ltf in args.ltfs) 
