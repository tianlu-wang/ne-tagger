#-*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import sys
import os
import re

def segment2document(in_file, out_file):
    f_in = open(in_file, 'r')
    f_out = open(out_file, 'w')
    for line in f_in.readlines():
        m1 = re.search(r'(.*)\t(.*)\t(.*)\t(.*)\t(.*)\t(.*)\t(.*)\t(.*)', line)
        m2 = re.search(r'(.*)_segment(.*):(.*)', m1.group(4))
        f_out.write(m1.group(1)+'\t'+m1.group(2)+'\t'+m1.group(3)+'\t'+m2.group(1)+':'+m2.group(3)+'\t'+m1.group(5)+'\t'+m1.group(6)+'\t'+m1.group(7)+'\t'+m1.group(8)+'\n')
    f_in.close()
    f_out.close()



if __name__ == '__main__':
    if len(sys.argv) != 3:
        print 'USAGE: python segment2document.py <input file> <output2 file>'
    else:
        indir = sys.argv[1]
        outdir = sys.argv[2]
        segment2document(indir, outdir)
