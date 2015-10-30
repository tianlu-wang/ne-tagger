#!/usr/bin/env python
import re
import sys
import os
"""
translate English words(GPE,ORG,PER) to incident language with the PROB file provided by LDC
"""

def eng2il(input_file, parallel_data, output_file):
    f_in = open(input_file, 'r')
    words = []
    for line in f_in.readlines():
        words.append(line[:-1])
    f_parallel = open(parallel_data, 'r')
    f_output = open(output_file, 'w')

    last_one_eng = '***********'
    last_one_il = '----------'
    for line in f_parallel.readlines():
        match = re.match(r'(.*)\t(.*)\t(.*)\n', line)
        if not match is None:
            if match.group(1) in words:
                if last_one_eng != match.group(1):
                    f_output.write(last_one_il+'\n')
                    last_one_eng = match.group(1)
                    last_one_il = match.group(2)
                    score = match.group(3)
                else:
                    if match.group(3) > score:
                        score = match.group(3)
                        last_one_il = match.group(2)
        else:
            print'no match in this line:'
            print line
    f_in.close()
    f_output.close()
    f_parallel.close()


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print 'USAGE: python eng2il.py <input_dir> <parallel_data> <output_dir>'
    else:
        indir = sys.argv[1]
        parallel_data = sys.argv[2]
        outdir = sys.argv[3]
        for i in os.listdir(indir):
            eng2il('%s/%s' % (indir, i), parallel_data, '%s/%s' % (outdir, i))