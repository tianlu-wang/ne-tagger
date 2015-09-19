#!/bin/bash

cd ../

<<<<<<< HEAD
 rm -r $MODEL_DIR

/Users/koala/Documents/lab/Blender/LORELEI/active_learning/ne-tagger/train.py -S $TRAIN_SCP $MODEL_DIR $LTF_DIR
/Users/koala/Documents/lab/Blender/LORELEI/active_learning/ne-tagger/tagger.py -S $TEST_SCP -L $SYS_LAF_DIR $MODEL_DIR
#/Users/koala/Documents/lab/Blender/LORELEI/active_learning/ne-tagger/tagger.py -S $TEST_SCP -L $SYS_LAF_DIR /Users/koala/Documents/lab/Blender/LORELEI/active_learning/ne-tagger/hausa_ne_model

/Users/koala/Documents/lab/Blender/LORELEI/active_learning/ne-tagger/score.py $REF_LAF_DIR $SYS_LAF_DIR $LTF_DIR
=======
MODEL_DIR=./example/model      # directory for trained model
LTF_DIR=./example/ltf          # directory containing LTF files
SYS_LAF_DIR=./example/output   # directory for tagger output (LAF files)
TRAIN_SCP=./example/train.scp  # script file containing paths to LAF files (one per line)
TEST_SCP=./example/test.scp    # script file containing paths to LTF files (one per line)
REF_LAF_DIR=./example/laf      # directory containing gold standard LAF files

#rm -r $MODEL_DIR

#./train.py -S $TRAIN_SCP $MODEL_DIR $LTF_DIR
./tagger.py -S $TEST_SCP -L $SYS_LAF_DIR $MODEL_DIR
# ./tagger.py -S $TEST_SCP -L $SYS_LAF_DIR ..//hausa_ne_model

#./score.py $REF_LAF_DIR $SYS_LAF_DIR $LTF_DIR
>>>>>>> 023ade4b4a7e6ef1f261e828c4637dd3f034ae34
