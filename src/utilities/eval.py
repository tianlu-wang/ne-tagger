#-*- coding: utf-8 -*-
import sys
import os
import subprocess

if __name__ == '__main__':
    for i in range(100):
        attach = str((i+1)*10)
        in_dir = 'python laf2tab.py /Users/koala/Documents/lab/Blender/LORELEI/active_learning/ne-tagger/hausa_test/segment_entropy_sampling/'
        out_file = ' /Users/koala/Documents/code/lorelei-eval/outputs/active_1000/round'+attach
        s = in_dir+'round'+attach+'/output'+out_file
        print s
        subprocess.call(s, shell = True)
        in_file = 'python segment2document.py /Users/koala/Documents/code/lorelei-eval/outputs/active_1000/round'+attach
        out_file = ' /Users/koala/Documents/code/lorelei-eval/result/round'+attach+'_document.tab'
        s = in_file+out_file
        print s
        subprocess.call(s, shell = True)
