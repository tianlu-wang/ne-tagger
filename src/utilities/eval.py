#!/usr/bin/python
#-*- coding: utf-8 -*-
import sys
import os
import subprocess

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print 'USAGE: eval.py <input_dir> <output_dir1> <output_dir2>'
    else:
        input_dir = sys.argv[1]
        output_dir1 = sys.argv[2]
        output_dir2 = sys.argv[3]
        for i in os.listdir(input_dir):
            cmd = ['python', './src/utilities/laf2tab.py', '%s/%s/output' % (input_dir, i), '%s/%s' % (output_dir1, i)]
            subprocess.call(cmd)
            cmd = ['python', './src/utilities/segment2document.py', '%s/%s' % (output_dir1, i), '%s/%s.tab' % (output_dir2, i)]
            subprocess.call(cmd)
