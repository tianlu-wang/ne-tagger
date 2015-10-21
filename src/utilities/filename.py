__author__ = 'koala'

# -*- coding: utf-8 -*-
import os


def check_single_file(rootDir):
    list_dirs = os.walk(rootDir)
    for root, dirs, files in list_dirs:
        for d in dirs:
            print os.path.join(root, d)
        for f in files:
            print os.path.join(root, f)


def check_two_files(dir_laf, dir_ltf):
    list_ltf = os.walk(dir_ltf)
    list_laf = os.walk(dir_laf)
    laf_name = []
    ltf_name = []

    for root, dirs, files in list_ltf:
        for f in files:
            ltf_name.append(f)
    print 'len of ltf'+str(len(ltf_name))
    for root, dirs, files in list_laf:
        for f in files:
            laf_name.append(f)
    print 'len of laf'+str(len(laf_name))
    i = 0
    for laf in laf_name:
        i += 1
        print i
        print laf
        laf_replace = laf.replace('laf', 'ltf')
        print laf_replace
        if laf_replace in ltf_name:
            ##laf_name.remove(laf)
            ltf_name.remove(laf_replace)

    print 'len of laf'+str(len(laf_name))
    print("in laf_name")
    for laf in laf_name:
        print(laf)

    print 'len of ltf'+str(len(ltf_name))
    print("in ltf_name")
    for ltf in ltf_name:
        print(ltf)


def select(dir_ltf):
    list_ltf = os.walk(dir_ltf)
    train_file = open("./hausa_test/test.scp", "w")
    for root, dirs, files in list_ltf:
        for f in files:
            train_file.write('./hausa_test/'+'test/'+f+"\n")

select('./hausa_test/test')
