#!/usr/bin/env python
__author__ = 'koala'

import os
import random
import matplotlib.pyplot as plt
import numpy as np
from sklearn import metrics
import re
import operator
import subprocess
import math
import sys
from bs4 import BeautifulSoup


class ActiveLearning(object):

    def __init__(self, init_train_num=50, increment=10, work_dir=None, total_train_sentences=100):
        train_path = os.path.join(work_dir, 'data_path_laf')
        assert(os.path.exists(train_path))
        f_train = open(train_path, 'r')
        all_set = [line for line in f_train.readlines()]  # get the list of ltf file
        self.train_set = []
        self.total_sentences = int(total_train_sentences)
        while len(self.train_set) < self.total_sentences:
            temp = all_set[random.randint(0, len(all_set) - 1)]
            if temp not in self.train_set:
                self.train_set.append(temp)  # get training files randomly

        print "%%%%%%%%%%%%%%%%this is the len of initial train set:%%%%%%%%%%%%%%%%%%"
        print len(self.train_set)

        self.frequency = dict()
        sum = 0.0
        for f in self.train_set:
            soup = BeautifulSoup(open(f.replace('laf', 'ltf')[:-1]).read(), 'html.parser')
            for token in soup.find_all('token'):
                tmp = token.string.encode('ascii', 'replace')
                if tmp in self.frequency.keys():
                    self.frequency[tmp] = self.frequency.get(tmp) + 1
                else:
                    self.frequency[tmp] = 1
                sum += 1
        self.frequency.update((k, v / sum) for (k, v) in self.frequency.iteritems())  # get frequency of every word

        f_fre = open('frequency.txt', 'w')  # take down the frequency to debug
        for key in self.frequency.keys():
            f_fre.write(key+'\t'+str(self.frequency.get(key))+'\n')
        f_fre.close()

        test_path = os.path.join(work_dir, 'test.scp')
        f_test = open(test_path, 'r')
        self.test_set = [line[:-1] for line in f_test.readlines()]  # get the list of test file
        #############
        print 'just to check that the test_set is normal: test_set[1] is ' + self.test_set[1]  # for debug
        #########

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
        self.tag_command = ['./src/name_tagger/tagger.py', '-L', self.SYS_LAF_DIR, self.MODEL_DIR] + self.test_set


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
        return self.init_train_set

    def do_training(self, sampling_method):
        """
        add increment part in every loop
        :return: tagged file in random_sampling or segment_entropy_sampling
        """
        while(len(self.current_train_set) <= self.total_sentences):
            if len(self.current_train_set) == 0:
                self.current_train_set = self.training_set_initialization()
                print 'the initial training set is:'
                print self.current_train_set
            subprocess.call(self.cmd_del_model)
            train_list = []
            for item in self.current_train_set:
                train_list.append(self.train_set[item].replace('ltf', 'laf')[:-1])  # get the name list of training set
            print '--------------------------------------------begin train------------------------------------'
            train_command = ['./src/name_tagger/train.py', self.MODEL_DIR, './frequency.txt', self.LTF_DIR] + train_list

            ## output train list: mainly for debug
            f = open('./train_list.txt', 'w+')
            f.write('len of current train set:'+str(len(self.current_train_set)))
            f.write('\n')
            for i in range(len(train_list)):
                f.write(train_list[i])
                f.write('\n')
            f.close()

            subprocess.call(train_command)
            subprocess.call(self.cmd_del_syslaf)
            subprocess.call(self.cmd_mk_syslaf)
            subprocess.call(self.cmd_del_probs)
            subprocess.call(self.cmd_mk_probs)
            print '--------------------------------------begin tag in doing traing---------------------------------------'
            subprocess.call(self.tag_command)
            for item in train_list:
                if item.replace('laf', 'ltf') in self.test_set:
                    print '*********************************overlap************************************'
                else:
                    pass
            new_dir = os.path.join(work_dir, sampling_method) + '/round' + str(len(self.current_train_set))
            subprocess.call(['mkdir', new_dir])
            subprocess.call(['cp', '-r', self.SYS_LAF_DIR, new_dir])
            print 'how many test file are analyzed:'
            subprocess.call('ls -l '+new_dir+'/output'+' | '+'wc -l', shell=True)


            if len(self.current_train_set) == self.total_sentences:
                return 0
            if sampling_method == 'segment_entropy_sampling':
                self.current_train_set += self.segment_entropy()
                print 'current training set is:'
                print self.current_train_set  # for debug
            elif sampling_method == 'random_sampling':
                self.current_train_set += self.random_sampling()
                print 'current training set is:'
                print self.current_train_set  # for debug


    def segment_entropy(self):
        print('\tgetting new training data in segment_entropy_sampling...')

        tag_list = []
        temp = list(self.train_set)
        for item in self.current_train_set:
            temp.remove(self.train_set[item])
        for item in temp:
            tag_list.append(item[:-1].replace('laf', 'ltf'))
        subprocess.call(self.cmd_del_syslaf)
        subprocess.call(self.cmd_mk_syslaf)
        subprocess.call(self.cmd_del_probs)
        subprocess.call(self.cmd_mk_probs)
        tag_command = ['./src/name_tagger/tagger.py', '-L', self.SYS_LAF_DIR, self.MODEL_DIR] + tag_list
        print '---------------------------------begin tag in segment entropy-----------------------------------'
        subprocess.call(tag_command)
        subprocess.call('ls -l '+self.SYS_LAF_DIR+' | '+'wc -l', shell=True)
        pattern1 = re.compile(r'(.*):(.*)')
        pattern2 = re.compile(r'\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s')
        sum_TK = dict()
        for root, dirs, files in os.walk(self.PROBS_DIR):
            for file in files:
                flag_num = 0
                entropy_num = 0
                f = open(self.PROBS_DIR+'/'+file, 'r')
                for line in f.readlines():
                    m1 = re.match(pattern1, line, flags=0)
                    if not m1 is None:
                        if len(m1.group(1)) > 2:
                            flag_num += 1
                        m2 = re.match(pattern2, m1.group(2), flags=0)
                        entropy = 0
                        for i in range(1, 18):
                            tmp = float(m2.group(i))
                            if tmp > 0:
                                entropy += -(tmp * math.log(tmp))
                        if entropy > math.pow(1, -21):
                            entropy_num += 1
                sum_TK[file] = entropy_num + flag_num
                f.close()
        sorted_entropy = sorted(sum_TK.items(), key=operator.itemgetter(1), reverse=True)
        ############################################
        training_set_to_add = []
        sample_size = self.increment
        if len(sorted_entropy) < self.increment:
            sample_size = len(sorted_entropy)
        for item in sorted_entropy[:sample_size]:
            sent_doc = item[0]
            sent_doc_xml = sent_doc[:-4].replace('ltf', 'laf')
            # print sent_doc_xml
            add_one = self.train_set.index(self.REF_LAF_DIR + '/'+sent_doc_xml + '\n')
            if add_one not in self.current_train_set:
                training_set_to_add.append(add_one)
            else:
                print 'add_one is in current_training_set'
            print training_set_to_add
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
        return training_set_to_add


def figure_plot(save_dir, learning_result):
    # plot figure
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    # determine major tick interval and minor tick interval
    x = learning_result.values()[0][0]
    y_acc = learning_result.values()[0][1]
    y_f = learning_result.values()[0][2]
    x_major_ticks = np.arange(min(x), max(x)+int(max(x)/10), int(max(x)/10))
    if max(y_acc) < min(y_f):
        y_major_ticks = np.arange(min(y_f), max(y_f)+0.05, 0.04)
    else:
        y_major_ticks = np.arange(min(y_f), max(y_acc)+0.05, 0.04)

    ax.set_xticks(x_major_ticks)
    # ax.set_xticks(x_minor_ticks, minor=True)
    ax.set_yticks(y_major_ticks)

    # and a corresponding grid
    ax.grid(which='both')

    # or if you want different settings for the grids:
    ax.grid(which='minor', alpha=0.8)
    ax.grid(which='major', alpha=1)

    colors = ['r', 'b', 'g', 'k']
    markers = ['o', '*', 'v', '+']
    i = 0
    for s in learning_result.keys():
        if 0 not in learning_result[s][1]:
            acc_auc = metrics.auc(learning_result[s][0], learning_result[s][1])
            max_auc = metrics.auc(learning_result[s][0], [1]*len(learning_result[s][0]))
            plt.plot(learning_result[s][0], learning_result[s][1], colors[i]+markers[i]+'-',
                     label=s + ' acc (auc = %.2f/%d)'% (acc_auc, max_auc), ms=5, linewidth=2.0)
        if 0 not in learning_result[s][2]:
            f_auc = metrics.auc(learning_result[s][0], learning_result[s][2])
            max_auc = metrics.auc(learning_result[s][0], [1]*len(learning_result[s][0]))
            plt.plot(learning_result[s][0], learning_result[s][2], colors[i]+markers[i]+':',
                     label=s + ' f-score (auc = %.2f/%d)'% (f_auc, max_auc), ms=5, linewidth=2.0)
        i += 1

    plt.title('active learng and random sampling comparison')
    plt.legend(loc='lower right', prop={'size': 6})

    plt.margins(0.2)
    plt.xticks(rotation='vertical')  # make x ticks vertical
    plt.subplots_adjust(bottom=0.15)

    plt.savefig(os.path.join(save_dir, 'comparison_curve.png'))
    plt.clf()

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print 'USAGE: ./src/activelearning_testdata.py <work dir> <sampling method(segment_entropy_sampling or random_sampling)> ' \
              '<total_train_sentences> <increment> <init_train_num>'
    else:
        work_dir = sys.argv[1]
        sampling_method = sys.argv[2]
        total_train_sentences = sys.argv[3]
        increment = sys.argv[4]
        init_train_num = sys.argv[5]
        iteration = 1
        for i in range(iteration):
            act = ActiveLearning(increment=increment, init_train_num=init_train_num, work_dir=work_dir,
                                 total_train_sentences=total_train_sentences)  # set the initial num and increment
            act.do_training(sampling_method)  # uncertainty sampling
            cmd = ['python', './src/utilities/eval.py', work_dir+'/'+sampling_method, './src/eval/output1', './src/eval/input']
            subprocess.call(cmd)



