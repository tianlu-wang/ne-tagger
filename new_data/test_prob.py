__author__ = 'koala'

import os
import re
import operator


def uncertainty_sampling(probs_dir):
    print('\tgetting new training data...')

    entropy = dict()
    pattern = re.compile(r'(.*):(.*)')
    for root, dirs, files in os.walk(probs_dir):
        for file in files:
            print file
            sum_prob = 0
            f = open(probs_dir+'/'+file, 'r')
            i = 0
            for line in f.readlines():
                print 'i = ' + str(i)
                m = re.match(pattern, line, flags=0)
                if not m is None:
                    sum_prob += float(m.group(2))
                i += 1
            mean_prob = sum_prob / float(i)  # take the mean of all tokens' probability as the entropy of a document
            entropy[file] = mean_prob

    sorted_entropy = sorted(entropy.items(), key=operator.itemgetter(1))

    training_set_to_add = []
    sample_size = 2
    if len(entropy) < 2:
        sample_size = len(entropy)
    for item in sorted_entropy[:sample_size]:
        sent_doc = item[0]
        print sent_doc
        #training_set_to_add.append(self.raw_set.index(sent_doc.replace('_prob.txt', 'ltf.xml')))

    return training_set_to_add

uncertainty_sampling('./new_data/probs')
