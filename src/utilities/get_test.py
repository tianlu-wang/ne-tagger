__author__ = 'koala'
#-*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import sys
import os
import subprocess

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print 'USAGE: python get_test.py <language_dir> <language_name>'
        print 'selectall test file from train file'
    else:
        indir = sys.argv[1]
        lang_name = sys.argv[2]
        filelist_f = open(indir+'/filelist/'+lang_name+'/'+'test_filelist', 'r')
        file_list = [i for i in filelist_f.readlines()]
        source_addr = indir+'/'+lang_name+'/train_ltf'+'/'
        des_addr = indir+'/'+lang_name+'/test_ltf/'
        for i in file_list[:-1]:
            cmd1 = ['mv', source_addr+i[:-1], des_addr]
            print cmd1
            subprocess.call(cmd1)
            cmd2 = ['mv', (source_addr+i[:-1]).replace('ltf', 'laf'), (des_addr).replace('ltf', 'laf')]
            print cmd2
            subprocess.call(cmd2)
        cmd1 = ['mv', source_addr+file_list[-1], des_addr]
        print cmd1
        subprocess.call(cmd1)
        cmd2 = ['mv', (source_addr+file_list[-1]).replace('ltf', 'laf'), (des_addr).replace('ltf', 'laf')]
        print cmd2
        subprocess.call(cmd2)
