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
        ltf_path = os.path.join(work_dir, 'data_path_ltf')
        assert(os.path.exists(ltf_path))
        f_ltf = codecs.open(ltf_path, 'r', encoding='utf-8')
        all_ltf = [line for line in f_ltf.readlines()]  # get list of ltf file
        f_ltf.close()
        all_laf = [item.replace('ltf', 'laf') for item in all_ltf]  # get list of laf file

        self.train_set = all_laf[:int(total_train_sentence)]
        print "%%%%%%%%%%%%%%%%this is the len of initial train set:%%%%%%%%%%%%%%%%%%"
        print len(self.train_set)

        self.frequency = dict()
        sum = 0.0
        for f in self.train_set:
            soup = BeautifulSoup(open(f.replace('laf', 'ltf')[:-1]).read(), 'html.parser')
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
        # self.MAX_PROB = os.path.join(work_dir,'maxprobs')
        self.WIKI = os.path.join(work_dir, 'wiki')
        self.dics = os.path.join(work_dir, 'dics')
        self.cmd_del_model = ['rm', '-r', self.MODEL_DIR]
        self.cmd_del_syslaf = ['rm', '-r', self.SYS_LAF_DIR]
        self.cmd_mk_syslaf = ['mkdir', self.SYS_LAF_DIR]
        self.cmd_del_probs = ['rm', '-r', self.PROBS_DIR]
        self.cmd_mk_probs = ['mkdir', self.PROBS_DIR]
        # self.cmd_del_maxprobs = ['rm', '-r', self.MAX_PROB]
        # self.cmd_mk_maxprobs = ['mkdir', self.MAX_PROB]

        # ### get wiki resource
        # for file in os.listdir(self.WIKI):
        #     f = open(file, 'r')
        #     if file == 'per':
        #         self.wiki_per = [line[:-1] for line in f.readlines()]
        #     elif file == 'org':
        #         self.wiki_org = [line[:-1] for line in f.readlines()]
        #     elif file == 'loc':
        #         self.wiki_loc = [line[:-1] for line in f.readlines()]
        #     f.close()
        #
        # ##### get gazetteers resource
        # self.dic_name = []
        # self.dic_title = []
        # self.dic_country = []
        # self.dic_city = []
        # self.dic_locsuffix = []
        # self.dic_orgsuffix = []
        # self.dic_prep = []
        # for file in os.listdir(self.dics):
        #     f = open(file, 'r')
        #     if 'name' in file:
        #         self.dic_name.extend([line.split('\t')[0] for line in f.readlines()])
        #     elif 'title' in file:
        #         self.dic_title.extend([line.split('\t')[0] for line in f.readlines()])
        #     elif 'country' in file:
        #         self.dic_country.extend([line.split('\t')[0] for line in f.readlines()])
        #     elif 'city' in file:
        #         self.dic_city.extend([line.split('\t')[0] for line in f.readlines()])
        #     elif 'loc' in file:
        #         self.dic_locsuffix.extend([line.split('\t')[0] for line in f.readlines()])
        #     elif 'org' in file:
        #         self.dic_orgsuffix.extend([line.split('\t')[0] for line in f.readlines()])
        #     elif 'prep' in file:
        #         self.dic_prep.extend([line.split('\t')[0] for line in f.readlines()])
        #     f.close()



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
        while len(self.current_train_set) <= self.max_train_sentences:
            if len(self.current_train_set) == 0:
                self.current_train_set = self.training_set_initialization()
                print 'the initial training set is:'
                print self.current_train_set
            subprocess.call(self.cmd_del_model)
            train_list = []
            for item in self.current_train_set:
                train_list.append(self.train_set[item][:-1])  # get the name list of training set
            print '--------------------------------------------begin train------------------------------------'
            train_command = ['./src/name_tagger/train.py', self.MODEL_DIR, './frequency.txt', self.LTF_DIR] + train_list

            subprocess.call(train_command)
            subprocess.call(self.cmd_del_syslaf)
            subprocess.call(self.cmd_mk_syslaf)
            subprocess.call(self.cmd_del_probs)
            subprocess.call(self.cmd_mk_probs)
            # subprocess.call(self.cmd_del_maxprobs)
            # subprocess.call(self.cmd_mk_maxprobs)
            print '--------------------------------------begin tag in doing training-----------------------------------'
            test_set = [item.replace('laf', 'ltf')[:-1] for item in self.train_set if self.train_set.index(item) not in self.current_train_set]
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

            print '--------------------------------finish tag in doing training--------------------------------'
            print 'how many files in sys laf dir:'
            subprocess.call('ls -l '+self.SYS_LAF_DIR+' | '+'wc -l', shell=True)
            # self.post_processing(test_set)  # do post processing
            for item in train_list:
                if item.replace('laf', 'ltf') in test_set:
                    print '*********************************overlap************************************'
                    print item
                else:
                    pass
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
        pool = mp.Pool(processes=self.num_process)
        results = pool.map(prob_score, zip(repeat(self.PROBS_DIR), prob_mul_list))
	pool.close()
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
    #
    # def post_processing(self, test_list):  # in test_list is ltf file
    #     for test_file in test_list:
    #         # tokens:text & start char & end start & pos tag
    #         tokens = []
    #         soup = BeautifulSoup(open(test_file).read(), 'html.parser')
    #         for token in soup.find_all('token'):
    #             tokens.append((token.string, int(token['start_char']), int(token['end_char']), token['pos']))
    #
    #         # max_probs: max prob
    #         max_prob_file = test_file.replace('ltf', 'maxprobs')
    #         max_probs = [float(line[:-1]) for line in open(max_prob_file).readlines()]
    #
    #         # output: text & start_char & end char & type
    #         output = []
    #         output_file = test_file.replace('ltf', 'output').replace('output.xml', 'laf.xml')
    #         soup = BeautifulSoup(open(output_file).read(), 'html.parser')
    #         for annotation in soup.find_all('annotation'):
    #             output.append((annotation.find('extent').string,
    #                            annotation.find('extent')['start_char'],
    #                            annotation.find('extent')['end_char'], annotation['type']))
    #
    #         token_index = 0  # the end of last entity
    #         while token_index < len(tokens):
    #             # fix the boundary in the output
    #             for item in output:
    #                 if tokens[token_index][0] == item[0].split(' ')[0]:  # already exist in sys output
    #                     self.fix()  # fix function should return the end of the entity
    #
    # # fix boundary based on crf, dics, wiki and capitalized
    # def fix(self, file_name, tokens, maxprobs, crf, span_width):  # token:tuple, span:n tuple, crf:output entity, dics:tuple, wiki,tuple
    #     if not crf is None:
    #         entity = [crf[0].split(' ')]  # entity is a list, each element is word in sys laf
    #         old_start_token = self.get_token(tokens, entity[0])
    #         crf_type = crf[3]  # type get from crf model
    #         span = self.get_span(tokens, tokens.index(entity[0]), tokens.index(entity[-1]), span_width)  # set the span_width manually
    #         span_string = ' '.join(item[0] for item in span)
    #         # check wiki resource
    #         if crf_type is 'LOC':
    #             for item in self.wiki_loc:
    #                 if item in span_string and crf[0] in item:
    #                     entity = item.split(' ')  # update the result as the wiki entity
    #             for i in list(reversed(range(span_width))):
    #                 word = span[i]
    #                 if word[0].isupper() is True and word.lower() in self.dic_country+self.dic_city+self.dic_locsuffix:
    #                     entity.insert(0, word)
    #                     # if span[i] is capitalized and it's in loc dics, put it into entity
    #                 elif word.lower() in self.dic_locsuffix:  # TODO:lower() function is to assure
    #                     entity.insert(0, word)
    #                     # if word is in location suffix, put it into entity TODO: I am not sure about doing so
    #                 else:
    #                     token = self.get_token(tokens, word)
    #                     if token[3] in ['VERB', 'PREP','CONJ', 'punct']:
    #                         break
    #                     # if word is a prep or punctuation mark, then just stop here
    #             for i in range(span_width):
    #                 word = span[-i]
    #                 if word[0].isupper() is True and word.lower() in self.dic_country+self.dic_city+self.dic_locsuffix:
    #                     entity.insert(0, word)
    #                     # if span[i] is capitalized and it's in loc dics, put it into entity
    #                 elif word.lower() in self.dic_locsuffix:  # TODO:lower() function is to assure
    #                     entity.insert(0, word)
    #                     # if word is in location suffix, put it into entity TODO: I am not sure about doing so
    #                 else:
    #                     token = self.get_token(tokens, word)
    #                     if token[3] in ['VERB', 'PREP','CONJ', 'punct']:
    #                         break
    #                     # if word is a prep or punctuation mark, then just stop here
    #             start_token = self.get_token(tokens, entity[0])
    #             end_token = self.get_token(tokens, entity[-1])
    #             self.update_ann(file_name, 'LOC', start_token[2], end_token[2], ' '.join(item for item in entity), old_start_token[3])
    #         if crf_type is 'PER':
    #             for item in self.wiki_per:
    #                 if item in span_string and crf[0] in item:
    #                     entity = item.split(' ')  # update the result as the wiki entity
    #             for i in list(reversed(range(span_width))):
    #                 word = span[i]
    #                 if word[0].isupper() is True and word.lower() in self.dic_name:
    #                     entity.insert(0, word)
    #                 elif word.lower() in self.dic_title:
    #                     break
    #                 else:
    #                     token = self.get_token(tokens, word)
    #                     if token[3] in ['VERB', 'PREP','CONJ', 'punct']:
    #                         break
    #             for i in range(span_width):
    #                 word = span[-i]
    #                 if word[0].isupper() is True and word.lower() in self.dic_name:
    #                     entity.insert(0, word)
    #                 elif word.lower() in self.dic_title:
    #                     break
    #                 else:
    #                     token = self.get_token(tokens, word)
    #                     if token[3] in ['VERB', 'PREP','CONJ', 'punct']:
    #                         break
    #             start_token = self.get_token(tokens, entity[0])
    #             end_token = self.get_token(tokens, entity[-1])
    #             self.update_ann(file_name, 'PER', start_token[2], end_token[2], ' '.join(item for item in entity), old_start_token[3])
    #         if crf_type is 'ORG':
    #             for item in self.wiki_org:
    #                 if item in span_string and crf[0] in item:
    #                     entity = item.split(' ')  # update the result as the wiki entity
    #             for i in list(reversed(range(span_width))):
    #                 word = span[i]
    #                 if word[0].isupper() is True and word.lower() in self.dic_name:
    #                     entity.insert(0, word)
    #                 elif word.lower() in self.dic_title:
    #                     break
    #                 else:
    #                     token = self.get_token(tokens, word)
    #                     if token[3] in ['VERB', 'PREP', 'CONJ', 'punct']:
    #                         break
    #             for i in range(span_width):
    #                 word = span[-i]
    #                 if word[0].isupper() is True and word.lower() in self.dic_name:
    #                     entity.insert(0, word)
    #                 elif word.lower() in self.dic_title:
    #                     break
    #                 else:
    #                     token = self.get_token(tokens, word)
    #                     if token[3] in ['VERB', 'PREP','CONJ', 'punct']:
    #                         break
    #             start_token = self.get_token(tokens, entity[0])
    #             end_token = self.get_token(tokens, entity[-1])
    #             self.update_ann(file_name, 'PER', start_token[2], end_token[2], ' '.join(item for item in entity), old_start_token[3])
    #     if wiki
    #
    #
    #
    #
    # # to get a area in which may exist wiki or dic word
    # def get_span(self, tokens, token_start, token_end, span_width):
    #     span = []
    #     tmp = token_start - span_width
    #     while tmp < 0:
    #         span.append(None)
    #         tmp += 1
    #     span.extend(tokens[tmp:token_start])
    #     span.extend(tokens[token_start:token_end])
    #     tmp = token_end + span_width
    #     if tmp < len(tokens) - 1:
    #         span.extend(tokens[token_end:tmp])
    #     else:
    #         span.extend(tokens[token_end:])
    #         while tmp > len(tokens) - 1:
    #             span.append(None)
    #             tmp -= 1
    #     return span
    # def get_token(self, tokens, text):
    #     for token in tokens:
    #         if token[0] is text:
    #             return token
    #     print 'cannot find this token, the string is'
    #     print '***********'+text+'***************'
    #     return 0
    # # get the index of the token given the text
    # def get_token_index(self, tokens, text):
    #     for token in tokens:
    #         if token[0] is text:
    #             return tokens.index(token)
    #     print 'cannot find index of this token in tokens, the string is:'
    #     print '************'+text+'**************'
    #     return 0
    #
    # def insert_ann(self,file_name, type, start_char, end_char, string):
    #     soup = BeautifulSoup(open(file_name).read(), 'html.parser')
    #     new_ann = soup.new_tag('annotation')
    #     new_ann['id'] = os.path.basename(file_name)+'_inn'
    #     new_ann['task'] = 'NE'
    #     new_ann['type'] = type
    #     new_extent = soup.new_tag('extent')
    #     new_extent['start_char'] = start_char
    #     new_extent['end_char'] = end_char
    #     new_extent.string = string
    #     new_ann.append(new_extent)
    #     soup.annotation.insert_after(new_ann)
    #     out = open(file_name, 'w')
    #     out.write(soup.prettify())
    #     out.close()
    #
    # def update_ann(self,file_name, type, start_char, end_char, string, old_start):
    #     soup = BeautifulSoup(open(file_name).read(), 'html.parser')
    #     for annotation in soup.find_all('annotation'):
    #         if int(annotation.find('extent')['start_char']) == int(old_start):
    #             old_annotation = annotation
    #             break
    #     new_ann = soup.new_tag('annotation')
    #     new_ann['id'] = os.path.basename(file_name)+'_inn'
    #     new_ann['task'] = 'NE'
    #     new_ann['type'] = type
    #     new_extent = soup.new_tag('extent')
    #     new_extent['start_char'] = start_char
    #     new_extent['end_char'] = end_char
    #     new_extent.string = string
    #     new_ann.append(new_extent)
    #     old_annotation.replace_with(new_ann)
    #     out = open(file_name, 'w')
    #     out.write(soup.prettify())
    #     out.close()


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
        for line in f.readlines():
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
        sum_score[item] = entropy_num + flag_num
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



