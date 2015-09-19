#!/bin/bash

MODEL_DIR=/Users/koala/Documents/lab/Blender/LORELEI/active_learning/ne-tagger/example/model    # directory for trained model
LTF_DIR=/Users/koala/Documents/lab/Blender/LORELEI/active_learning/ne-tagger/example/ltf      # directory containing LTF files
SYS_LAF_DIR=/Users/koala/Documents/lab/Blender/LORELEI/active_learning/ne-tagger/example/output  # directory for tagger output (LAF files)
TRAIN_SCP=/Users/koala/Documents/lab/Blender/LORELEI/active_learning/ne-tagger/example/train.scp    # script file containing paths to LAF files (one per line)
TEST_SCP=/Users/koala/Documents/lab/Blender/LORELEI/active_learning/ne-tagger/example/test.scp     # script file containing paths to LTF files (one per line)
REF_LAF_DIR=/Users/koala/Documents/lab/Blender/LORELEI/active_learning/ne-tagger/example/laf  # directory containing gold standard LAF files

 rm -r $MODEL_DIR

/Users/koala/Documents/lab/Blender/LORELEI/active_learning/ne-tagger/train.py -S $TRAIN_SCP $MODEL_DIR $LTF_DIR
/Users/koala/Documents/lab/Blender/LORELEI/active_learning/ne-tagger/tagger.py -S $TEST_SCP -L $SYS_LAF_DIR $MODEL_DIR
#/Users/koala/Documents/lab/Blender/LORELEI/active_learning/ne-tagger/tagger.py -S $TEST_SCP -L $SYS_LAF_DIR /Users/koala/Documents/lab/Blender/LORELEI/active_learning/ne-tagger/hausa_ne_model

/Users/koala/Documents/lab/Blender/LORELEI/active_learning/ne-tagger/score.py $REF_LAF_DIR $SYS_LAF_DIR $LTF_DIR