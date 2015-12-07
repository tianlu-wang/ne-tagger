#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'koala'
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import codecs
import os
import random
import re
import operator
import subprocess
import math
import sys
from bs4 import BeautifulSoup
import multiprocessing as mp
from subprocess import Popen
from itertools import repeat


class ActiveLearning(object):

    def __init__(self, init_train_num=50, increment=10, work_dir=None, total_train_sentence=2000,  max_train_sentences=100, num_process=2):

        self.num_process = int(num_process)
        self.max_train_sentences = int(max_train_sentences)
        self.init_train_num = int(init_train_num)
        self.increment = int(increment)
        self.init_train_set = []
        self.current_train_set = []
        self.MODEL_DIR = os.path.join(work_dir, 'model')      # directory for trained model
        self.LTF_DIR = os.path.join(work_dir, 'ltf')         # directory containing LTF files
        self.SYS_LAF_DIR = os.path.join(work_dir, 'output')   # directory for tagger result (LAF files)
        self.REF_LAF_DIR = os.path.join(work_dir, 'laf')      # directory containing gold standard LAF files
        self.PROBS_DIR = os.path.join(work_dir, 'probs')
        self.cmd_del_model = ['rm', '-r', self.MODEL_DIR]
        self.cmd_del_syslaf = ['rm', '-r', self.SYS_LAF_DIR]
        self.cmd_mk_syslaf = ['mkdir', self.SYS_LAF_DIR]
        self.cmd_del_probs = ['rm', '-r', self.PROBS_DIR]
        self.cmd_mk_probs = ['mkdir', self.PROBS_DIR]
        self.token_num = 0

        train_ltf = os.path.join(work_dir, 'ltf')
        assert(os.path.exists(train_ltf))
        all_ltf = [work_dir + '/ltf/' + i for i in os.listdir(train_ltf)]  # get list of ltf file
        train_laf = os.path.join(work_dir, 'laf')
        assert(os.path.join(train_laf))
        all_laf = [work_dir + '/laf/' + i for i in os.listdir(train_laf)]  # get list of laf train file

        test_ltf = os.path.join(work_dir, 'test')
        assert(os.path.exists(test_ltf))
        test_set = [work_dir + '/test/' + i for i in os.listdir(test_ltf)]  # get test file list
        self.tag_mul_list = [[]]
        len_chunk = len(test_set)/self.num_process
        for i in range(self.num_process):
            self.tag_mul_list.append(test_set[i*len_chunk:(i+1)*len_chunk])
        if (i+1)*len_chunk < len(test_set):
            self.tag_mul_list.append(test_set[(i+1)*len_chunk:])
        self.tag_mul_list.pop(0)

        ##### for debug TODO: should remove when running
       # for i in all_ltf:
        #    if not i.replace('ltf', 'laf') in all_laf:
         #       print 'not all file match in laf and ltf train file'
          #      print i
           #     print '!!!!!!!!!!!!!!!!!!'

        self.train_set = all_laf[:int(total_train_sentence)]
        print "%%%%%%%%%%%%%%%%this is the len of initial train set:%%%%%%%%%%%%%%%%%%"
        print len(self.train_set)

        self.frequency = dict()
        sum = 0.0
        for f in self.train_set:
            soup = BeautifulSoup(open(f.replace('laf', 'ltf')).read(), 'html.parser')
            for token in soup.find_all('token'):
                tmp = token.string
                if tmp in self.frequency.keys():
                    self.frequency[tmp] = self.frequency.get(tmp) + 1
                else:
                    self.frequency[tmp] = 1
                sum += 1
        self.frequency.update((k, v / sum) for (k, v) in self.frequency.iteritems())  # get frequency of every word

        f_fre = codecs.open('frequency.txt', 'w', encoding='utf-8')  # take down the frequency to debug
        for key in self.frequency.keys():
            f_fre.write(key+'\t'+str(self.frequency.get(key))+'\n')
        f_fre.close()





    def training_set_initialization(self):
        """
        randomly select several documents as the start point
        :return: index of the start point
        """
        print('===========================generating initial training set===============================')
        while len(self.init_train_set) < self.init_train_num:
            temp = random.randint(0, len(self.train_set) - 1)
            if temp not in self.init_train_set:
                self.init_train_set.append(temp)
        assert(index > 0 for index in self.init_train_set)
        self.cal_token(self.init_train_set)
        return self.init_train_set

    def do_training(self, sampling_method):
        """
        add increment part in every loop
        :return: tagged file in random_sampling or segment_entropy_sampling
        """
        while len(self.current_train_set) <= self.max_train_sentences:
            if len(self.current_train_set) == 0:
                self.current_train_set = self.training_set_initialization()
                print 'the initial training set is:'
                print self.current_train_set
            subprocess.call(self.cmd_del_model)
            train_list = []
            for item in self.current_train_set:
                train_list.append(self.train_set[item])  # get the name list of training set
            print '--------------------------------------------begin train------------------------------------'
            train_command = ['./src/name_tagger/train.py', self.MODEL_DIR, './frequency.txt', self.LTF_DIR] + train_list

            subprocess.call(train_command)
            subprocess.call(self.cmd_del_syslaf)
            subprocess.call(self.cmd_mk_syslaf)
            subprocess.call(self.cmd_del_probs)
            subprocess.call(self.cmd_mk_probs)
            print '--------------------------------------begin tag in doing training-----------------------------------'
            # test_set = [item.replace('laf', 'ltf')[:-1] for item in self.train_set if self.train_set.index(item) not in self.current_train_set]
            cmds = [[]]
            for item in self.tag_mul_list:
                cmds.append(['./src/name_tagger/tagger.py', '-L', self.SYS_LAF_DIR, self.MODEL_DIR] + item)
            cmds.pop(0)
            processes = [Popen(cmd) for cmd in cmds]
            for p in processes: p.wait()

            print '--------------------------------finish tag in doing training--------------------------------'
            print 'how many files in sys laf dir:'
            subprocess.call('ls -l '+self.SYS_LAF_DIR+' | '+'wc -l', shell=True)
            # for item in train_list:
            #     if item.replace('laf', 'ltf') in test_set:
            #         print '*********************************overlap************************************'
            #         print item
            #     else:
            #         pass
            new_dir = os.path.join(work_dir, sampling_method) + '/round' + str(len(self.current_train_set))
            subprocess.call(['mkdir', new_dir])
            subprocess.call(['cp', '-r', self.SYS_LAF_DIR, new_dir])
            print 'how many test file are analyzed:'
            subprocess.call('ls -l '+new_dir+'/output'+' | '+'wc -l', shell=True)

            if len(self.current_train_set) == self.max_train_sentences:
                return 0
            if sampling_method == 'segment_entropy_sampling':
                self.current_train_set += self.segment_entropy()
            elif sampling_method == 'random_sampling':
                self.current_train_set += self.random_sampling()
            elif sampling_method == 'sequential_sampling':
                self.current_train_set += self.sequential_sampling()

            print 'current training set size is(after adding):'
            print len(self.current_train_set)
            print 'current training set is(after adding):'
            print self.current_train_set  # for debug

    def segment_entropy(self):
        print('\tgetting new training data in segment_entropy_sampling...')
	subprocess.call(self.cmd_del_syslaf)
        subprocess.call(self.cmd_mk_syslaf)
        subprocess.call(self.cmd_del_probs)
        subprocess.call(self.cmd_mk_probs)
        test_set = [item.replace('laf', 'ltf') for item in self.train_set if self.train_set.index(item) not in self.current_train_set]
        tag_mul_list = [[]]
        len_chunk = len(test_set)/self.num_process
        for i in range(self.num_process):
            tag_mul_list.append(test_set[i*len_chunk:(i+1)*len_chunk])
        if (i+1)*len_chunk < len(test_set):
            tag_mul_list.append(test_set[(i+1)*len_chunk:])
        tag_mul_list.pop(0)
        cmds = [[]]
        for item in tag_mul_list:
            cmds.append(['./src/name_tagger/tagger.py', '-L', self.SYS_LAF_DIR, self.MODEL_DIR] + item)
        cmds.pop(0)
        processes = [Popen(cmd) for cmd in cmds]
        for p in processes: p.wait()
        print 'how many test file are in probs after segment entropy sampling:'
        subprocess.call('ls -l '+work_dir+'/probs'+' | '+'wc -l', shell=True)
        all_file = []
        for root, dirs, files in os.walk(self.PROBS_DIR):
            for file in files:
                all_file.append(file)
        prob_mul_list = [[]]
        len_chunk = len(all_file)/self.num_process
        for i in range(self.num_process):
            prob_mul_list.append(all_file[i*len_chunk:(i+1)*len_chunk])
        if (i+1)*len_chunk < len(all_file):
            prob_mul_list.append(all_file[(i+1)*len_chunk:])
        prob_mul_list.pop(0)
        # pool lists are prepared

        pool = mp.Pool(processes=self.num_process)
        results = pool.map(prob_score, zip(repeat(self.PROBS_DIR), prob_mul_list))
	pool.terminate()
	pool.join()
        sum_TK = results[0].copy()
        for item in results[1:]:
            sum_TK.update(item)
        sorted_entropy = sorted(sum_TK.items(), key=operator.itemgetter(1), reverse=True)
        ############################################
        print 'top 3 of sorted_entropy:'
        print sorted_entropy[:3]
        training_set_to_add = []
        sample_size = self.increment
        if len(sorted_entropy) < self.increment:
            sample_size = len(sorted_entropy)
        for item in sorted_entropy[:sample_size]:
            sent_doc = item[0]
            sent_doc_xml = sent_doc.replace('probs', 'laf')
            add_one = self.train_set.index(self.REF_LAF_DIR + '/'+sent_doc_xml)
            if add_one not in self.current_train_set:
                training_set_to_add.append(add_one)
            else:
                print 'add_one is in current_training_set'
        print training_set_to_add
        self.cal_token(training_set_to_add)
        return training_set_to_add

    def random_sampling(self):
        print('\tgetting new training data in random_sampling...')

        training_set_to_add = []
        sample_size = self.increment
        sub = len(self.train_set) - len(self.current_train_set)
        if sub < self.increment:
            sample_size = sub
        while len(training_set_to_add) < sample_size:
            temp = random.randint(0, len(self.train_set) - 1)  # actually it is not a good method
            if temp not in self.current_train_set:
                training_set_to_add.append(temp)
        print training_set_to_add
        return training_set_to_add

    def sequential_sampling(self):
        print '\tgetting new training data in sequential_sampling...'

        sample_size = self.increment
        sub = len(self.train_set) - len(self.current_train_set)
        if sub < self.increment:
            sample_size = sub
        tag_list = [item for item in range(len(self.train_set)) if item not in self.current_train_set]
        training_set_to_add = tag_list[:sample_size]
        print training_set_to_add
        return training_set_to_add

    def cal_token(self, set):
        temp_sum = 0
        for f in set:
            soup = BeautifulSoup(open(self.train_set[f].replace('laf', 'ltf')).read(), 'html.parser')
            for token in soup.find_all('token'):
                temp_sum += 1
        print "the temp_sum"
        print temp_sum
        self.token_num += temp_sum
        print "all_token_sum:"
        print self.token_num
        f = codecs.open('token_num.txt', 'a', encoding='utf-8') 
	f.write('training size'+ str(len(self.current_train_set))+'\n')
        f.write(str(self.token_num)+'\n')
        f.close()
	if self.token_num > 15000:
	    raw_input()

def prob_score((probs_dir, file_list)):
    print 'calculating prob score in every file...'
    print probs_dir
    pattern1 = re.compile(r'(.*):(.*)')
    pattern2 = re.compile(r'\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s')
    sum_score = dict()
    for item in file_list:
        flag_num = 0
        entropy_num = 0
        f = codecs.open(probs_dir +'/'+item, 'r', encoding='utf-8')
	token_num = 0
        for line in f.readlines():
	    token_num += 1
            m1 = re.match(pattern1, line, flags=0)
            if not m1 is None:
                if len(m1.group(1)) > 2:
                    flag_num += 1
                m2 = re.match(pattern2, m1.group(2), flags=0)
                if m2 is None:
                    print 'something wrong in probs file cause if m1 is not none then m2 is not none'
                entropy = 0
                for i in range(1, 18):
                    tmp = float(m2.group(i))
                    if tmp > 0:
                        entropy += -(tmp * math.log(tmp))
                if entropy > math.pow(1, -21):
                    entropy_num += 1
            else:
                pass
                # print line
#	print 'token_num is'+str(token_num)
        sum_score[item] = entropy_num + float(flag_num)/float(token_num)
        f.close()
    print 'finish calculate score'
    return sum_score

if __name__ == "__main__":
    if len(sys.argv) != 8:
        print 'USAGE: ./src/activelearning_eval.py <work dir> <sampling method(segment_entropy_sampling or ' \
              'random_sampling or sequential_sampling)> ' \
              '<total_training_sentences> <max_train_sentences> <increment> <init_train_num><num_process>'
    else:
        work_dir = sys.argv[1]
        sampling_method = sys.argv[2]
        total_train_sentence = sys.argv[3]
        max_train_sentences = sys.argv[4]
        increment = sys.argv[5]
        init_train_num = sys.argv[6]
        num_process = sys.argv[7]

        act = ActiveLearning(increment=increment, init_train_num=init_train_num, work_dir=work_dir,
                             total_train_sentence=total_train_sentence,
                             max_train_sentences=max_train_sentences, num_process=num_process)  # set the initial num and increment
        act.do_training(sampling_method)  # uncertainty sampling
        cmd = ['python', './src/utilities/eval.py', work_dir+'/'+sampling_method, './src/eval/output1', './src/eval/input']
        subprocess.call(cmd)
