__author__ = 'koala'
import sys
import os
import subprocess

def clean(dir):
    subprocess.call(['rm', '-r', dir])
    subprocess.call(['mkdir', dir])
    subprocess.call(['rm', '-r', 'src/eval/input'])
    subprocess.call(['mkdir', 'src/eval/input'])
    subprocess.call(['rm', '-r', 'src/eval/output1'])
    subprocess.call(['mkdir', 'src/eval/output1'])
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print 'USAGE: python clean.py <dir>'
    else:
        indir = sys.argv[1]
        clean(indir)
