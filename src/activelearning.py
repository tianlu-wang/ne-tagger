#!/usr/bin/env python
__author__ = 'koala'

import os
import random
import copy
import matplotlib.pyplot as plt
import numpy as np
from sklearn import metrics
import re
import operator
import subprocess


class ActiveLearning(object):

    def __init__(self, folder_num=1, init_training_num=50, increment=1, data_path=None ):
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

        self.data_path = data_path
        ###### prepare three list
        raw_path = os.path.join('./test_split', 'data_path_ltf')
        assert(os.path.exists(raw_path))
        f_raw = open(raw_path, 'r')
        self.raw_set = [line for line in f_raw.readlines()]  # get the list of ltf file

        #########

        self.init_training_num = init_training_num
        self.folder_num = folder_num
        self.increment = increment

        self.training_set = []
        self.test_set = []
        self.init_training_set = []
        self.incremental_training_set = []
        self.current_training_set = []
        for i in range(folder_num):
            self.current_training_set[i] = []
        ##############################################################
        self.MODEL_DIR ='./test_split/model'      # directory for trained model
        self.LTF_DIR ='./test_split/ltf'         # directory containing LTF files
        self.SYS_LAF_DIR ='./test_split/output'   # directory for tagger output (LAF files)
        self.REF_LAF_DIR ='./test_split/laf'      # directory containing gold standard LAF files
        self.PROBS_DIR = './test_split/probs'
        ########################
        self.cmd_del_model = ['rm', '-r', self.MODEL_DIR]
        self.cmd_del_syslaf = ['rm', '-r', self.SYS_LAF_DIR]
        self.cmd_mk_syslaf = ['mkdir', self.SYS_LAF_DIR]
        self.cmd_del_probs = ['rm', '-r', self.PROBS_DIR]
        self.cmd_mk_probs = ['mkdir', self.PROBS_DIR]
        self.score_command = ['./score.py', self.REF_LAF_DIR, self.SYS_LAF_DIR, self.LTF_DIR]
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

    def test_set_initialization(self, fold_order):
        test_begin = len(self.raw_set)/self.folder_num*fold_order
        test_end = len(self.raw_set)/self.folder_num*(fold_order+1)
        self.test_set = list(self.raw_set[test_begin:test_end])
        if test_begin == 0:
            self.training_set = list(self.raw_set[test_end:])  # leave some samples as test data
        elif test_end == len(self.raw_set):
            self.training_set = list(self.raw_set[:test_begin])
        else:
            # print 'middle'
            self.training_set = list(self.raw_set[:test_begin] + self.raw_set[test_end:])
        #####################################
        for item in self.test_set:
            if item in self.training_set:
                print "++++++++++++++duplicate+++++++++++++++"
        ######################################
        # gold_path = os.path.join('./test_split', 'data_path_laf_600')
        # assert(os.path.exists(gold_path))
        # f_gold = open(gold_path, 'r')
        # self.gold_set = [line for line in f_gold.readlines()]

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
        for i in range(int((len(self.raw_set))/self.increment)):
            ###################################
            subprocess.call(self.cmd_del_syslaf)
            subprocess.call(self.cmd_mk_syslaf)
            subprocess.call(self.cmd_del_probs)
            subprocess.call(self.cmd_mk_probs)
            #####################################
            print('\tcurrent iteration training set size: ' + str((i+1)*self.increment))
            # x = []
            # index = []
            for j in range(self.folder_num):
                self.test_set_initialization(j)
                if i == 0:
                    self.current_training_set[j] = self.training_set_initialization()
                else:
                    if sampling_method == 'uncertainty sampling':
                        self.current_training_set[j] += self.uncertainty_sampling(j)
                    elif sampling_method == 'random sampling':
                        self.current_training_set[j] += self.random_sampling(j)
                subprocess.call(self.cmd_del_model)
                train_list = []
                for item in self.current_training_set[j]:
                    train_list.append(self.train_set[item].replace('ltf', 'laf')[:-1])  # get the name list of training set
                train_command = ['./train.py', self.MODEL_DIR, self.LTF_DIR] + train_list
                subprocess.call(train_command)
                tag_list = []
                for item in self.test_set:
                    tag_list.append(item[:-1])
                tag_command = ['./tagger.py', '-L', self.SYS_LAF_DIR, self.MODEL_DIR] + tag_list
                subprocess.call(tag_command)
            subprocess.call(self.score_command)
            # x.append(len(self.current_training_set))
            # index.append(self.current_training_set)

            # =========================add new training samples========================
            # self.rest_training_set = [d for d in self.training_set if self.training_set.index(d) not in self.current_training_set]

            # choose sampling method
            # if sampling_method == 'uncertainty sampling':
            #     self.incremental_training_set = self.uncertainty_sampling()
            #
            # elif sampling_method == 'random sampling':
            #     self.incremental_training_set = self.random_sampling()
            #
            # elif sampling_method == 'uncertainty k-means':
            #     self.incremental_training_set = self.uncertainty_k_means()
            # elif sampling_method == 'ne density':
            #     self.incremental_training_set = self.named_entity_density(i)
            # elif sampling_method == 'features based density':
            #     self.incremental_training_set = self.feature_based_density(i)

            # self.current_training_set += self.incremental_training_set


        # return x, index

    def uncertainty_sampling(self, folder_order):
        print('\tgetting new training data...')

        tag_list = []
        temp = list(self.train_set)  # bug here
        for item in self.current_training_set[folder_order]:
            temp.remove(self.train_set[item])  # rest of training set is test
        for item in temp:
            tag_list.append(item[:-1])
        #############################
        subprocess.call(self.cmd_del_syslaf)
        subprocess.call(self.cmd_mk_syslaf)
        subprocess.call(self.cmd_del_probs)
        subprocess.call(self.cmd_mk_probs)
        #################################
        tag_command = ['./tagger.py', '-L', self.SYS_LAF_DIR, self.MODEL_DIR] + tag_list
        subprocess.call(tag_command)
        entropy = dict()
        #####################################
        pattern = re.compile(r'(.*):(.*)')
        for root, dirs, files in os.walk(self.PROBS_DIR):
            for file in files:
                sum_prob = 0
                f = open(self.PROBS_DIR+'/'+file, 'r')
                i = 0
                for line in f.readlines():
                    m = re.match(pattern, line, flags=0)
                    if not m is None:
                        sum_prob += float(m.group(2))
                    # else:
                    #     print "regular expression wrong"
                    i += 1
                mean_prob = sum_prob / float(i)  # take the mean of all tokens' probability as the entropy of a document
                entropy[file] = mean_prob
                f.close()
        sorted_entropy = sorted(entropy.items(), key=operator.itemgetter(1))

        training_set_to_add = []
        sample_size = self.increment
        if len(entropy) < self.increment:
            sample_size = len(entropy)
        for item in sorted_entropy[:sample_size]:
            sent_doc = item[0]
            sent_doc_xml = sent_doc.replace('_probs.txt', 'ltf.xml')
            # print sent_doc_xml
            add_one = self.train_set.index('./test_split/ltf/' + sent_doc_xml + '\n')
            if add_one not in self.current_training_set[folder_order]:
                training_set_to_add.append(add_one)
            else:
                print 'add_one is in current_training_set'
        print training_set_to_add
        return training_set_to_add

    def random_sampling(self, folder_order):
        print('\tgetting new training data...')

        training_set_to_add = []
        sample_size = self.increment
        sub = len(self.train_set) - len(self.current_training_set[folder_order])
        if sub < self.increment:
            sample_size = sub
        while len(training_set_to_add) < sample_size:
            temp = random.randint(0, len(self.train_set) - 1)  # actually it is not a good method
            if temp not in self.current_training_set:
                training_set_to_add.append(temp)
        print training_set_to_add
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

    iteration = 2
    for i in range(iteration):
        f = open('./result.txt', 'a')
        f.write('**********iteration time = ' + str(i) + '\n')
        f.close()
        act = ActiveLearning(increment=20, data_path=data_path, init_training_num=20, folder_num=10)  # set the initial num and increment
        act.do_training('uncertainty sampling')  # uncertainty sampling





