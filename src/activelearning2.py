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


class ActiveLearning(object):

    def __init__(self, init_training_num=50, increment=1):
        """
        initialize the activelearning class, classifier includes llama, svm and crf
        actually it's going to combine with other team and just add llama and svm;
        iteration_times is used to minimize the error;
        data_path_ltf temporarily don't know why
        :param iteration_times:
        :param init_training_num:
        :param increment:
        :param data_path:
        :return:
        """
        train_path = os.path.join('./hausa_test', 'data_path_ltf')
        assert(os.path.exists(train_path))
        f_train = open(train_path, 'r')
        self.train_set = [line for line in f_train.readlines()]  # get the list of ltf file
        self.train_set = self.train_set[:300]  # select part of train files
        f_test = open('./hausa_test/test.scp', 'r')
        self.test_set = [line[:-1] for line in f_test.readlines()]  # get the list of test file
        #############
        print 'test_set[1]' + self.test_set[1]  # for debug
        #########

        self.init_training_num = init_training_num
        self.increment = increment
        self.init_training_set = []
        self.incremental_training_set = []
        self.current_training_set = []
        ##############################################################
        self.MODEL_DIR ='./hausa_test/model'      # directory for trained model
        self.LTF_DIR ='./hausa_test/ltf'         # directory containing LTF files
        self.SYS_LAF_DIR ='./hausa_test/output'   # directory for tagger output (LAF files)
        self.REF_LAF_DIR ='./hausa_test/laf'      # directory containing gold standard LAF files
        self.PROBS_DIR = './hausa_test/probs'
        ########################
        self.cmd_del_model = ['rm', '-r', self.MODEL_DIR]
        self.cmd_del_syslaf = ['rm', '-r', self.SYS_LAF_DIR]
        self.cmd_mk_syslaf = ['mkdir', self.SYS_LAF_DIR]
        self.cmd_del_probs = ['rm', '-r', self.PROBS_DIR]
        self.cmd_mk_probs = ['mkdir', self.PROBS_DIR]
        self.tag_command = ['./src/name_tagger/tagger.py', '-L', self.SYS_LAF_DIR, self.MODEL_DIR] + self.test_set
        # self.score_command = ['./src/name_tagger/score.py', self.REF_LAF_DIR, self.SYS_LAF_DIR, self.LTF_DIR]
        ##############################

        ################################################################

    def training_set_initialization(self):
        """
        randomly select several documents as the start point
        :return: index of the start point
        """
        print('===========================generating initial training set===============================')
        while len(self.init_training_set) < self.init_training_num:
            temp = random.randint(0, len(self.train_set) - 1)
            if temp not in self.init_training_set:
                self.init_training_set.append(temp)
        assert(index > 0 for index in self.init_training_set)
        # print self.init_training_set  # this line is for debug
        return self.init_training_set

    def do_training(self, sampling_method):
        """
        add increment part in every loop
        :return:
        index: indexes of training files in every loop
        x[]: capacity of training set in every loop
        y_p[]: precision in every loop(write in file)
        y_r[]: recall in every loop(write in file)
        y_f[]: f1 score in every loop(write in file)
        """
        for i in range(len(self.train_set)/self.increment):
        # for i in range(7):

            print('\tcurrent iteration training set size: ' + str((i+1)*self.increment))
            if i == 0:
                self.current_training_set = self.training_set_initialization()
                print len(self.current_training_set)
            else:
                if sampling_method == 'token entropy sampling':
                    self.current_training_set += self.token_entropy()
                    print 'current training set is:'
                    print self.current_training_set  # for debug
                elif sampling_method == 'random sampling':
                    self.current_training_set += self.random_sampling()
                    print 'current training set is:'
                    print self.current_training_set  # for debug
            subprocess.call(self.cmd_del_model)
            train_list = []
            for item in self.current_training_set:
                train_list.append(self.train_set[item].replace('ltf', 'laf')[:-1])  # get the name list of training set
            train_command = ['./src/name_tagger/train.py', self.MODEL_DIR, self.LTF_DIR] + train_list
            subprocess.call(train_command)
            ###################################
            subprocess.call(self.cmd_del_syslaf)
            subprocess.call(self.cmd_mk_syslaf)
            subprocess.call(self.cmd_del_probs)
            subprocess.call(self.cmd_mk_probs)
            #####################################
            subprocess.call(self.tag_command)
            ################################################
            for item in train_list:
                if item.replace('laf', 'ltf') in self.test_set:
                    print '*********************************overlap************************************'
                else:
                    pass
            new_dir = './hausa_test/activelearning/' + 'round' + str(i)
            subprocess.call(['mkdir', new_dir])
            subprocess.call(['cp', '-r', './hausa_test/output', new_dir])

    def token_entropy(self):
        print('\tgetting new training data in token entropy...')

        tag_list = []
        temp = list(self.train_set)  # bug here
        for item in self.current_training_set:
            temp.remove(self.train_set[item])  # rest of training set is test
        for item in temp:
            tag_list.append(item[:-1])
        #############################
        subprocess.call(self.cmd_del_syslaf)
        subprocess.call(self.cmd_mk_syslaf)
        subprocess.call(self.cmd_del_probs)
        subprocess.call(self.cmd_mk_probs)
        #################################
        tag_command = ['./src/name_tagger/tagger.py', '-L', self.SYS_LAF_DIR, self.MODEL_DIR] + tag_list
        subprocess.call(tag_command)

        #####################################
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
                            # print i
                            # print tmp
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
            sent_doc_xml = sent_doc.replace('_probs.txt', 'ltf.xml')
            print sent_doc_xml  # todo: for Tongtao
            # print sent_doc_xml
            add_one = self.train_set.index('./hausa_test/ltf/' + sent_doc_xml + '\n')
            if add_one not in self.current_training_set:
                training_set_to_add.append(add_one)
            else:
                print 'add_one is in current_training_set'
        return training_set_to_add

    def random_sampling(self):
        training_set_to_add = []
        sample_size = self.increment
        sub = len(self.train_set) - len(self.current_training_set)
        if sub < self.increment:
            sample_size = sub
        while len(training_set_to_add) < sample_size:
            temp = random.randint(0, len(self.train_set) - 1)  # actually it is not a good method
            if temp not in self.current_training_set:
                training_set_to_add.append(temp)
        # print training_set_to_add
        return training_set_to_add  # return a list of number...


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
    data_path = '/Users/koala/Documents/lab/Blender/LORELEI/active_learning/ne-tagger'

    iteration = 1
    for i in range(iteration):
        f = open('./result2.txt', 'a')
        f.write('**********iteration time = ' + str(i) + '\n')
        f.close()
        act = ActiveLearning(increment=10, init_training_num=10)  # set the initial num and increment
        act.do_training('token entropy sampling')  # uncertainty sampling





