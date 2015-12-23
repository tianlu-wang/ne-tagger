__author__ = 'koala'
import sys
import os
import subprocess

def clean(dir, work_dir):
    subprocess.call(['rm', '-r', dir])
    subprocess.call(['mkdir', dir])
    subprocess.call(['rm', '-r', 'src/eval/input'])
    subprocess.call(['mkdir', 'src/eval/input'])
    subprocess.call(['rm', '-r', 'src/eval/output1'])
    subprocess.call(['mkdir', 'src/eval/output1'])
    subprocess.call(['rm', os.path.join(work_dir, 'token_num.txt')])
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print 'USAGE: python clean.py <dir> <work_dir>'
    else:
        indir = sys.argv[1]
        work_dir = sys.argv[2]
        clean(indir, work_dir)
