#!/usr/bin/env python
import re
import sys
import os
"""
generate type of entities from wikipedia
"""


def wiki_type(input_file, out_per, out_org, out_loc):
    f_in = open(input_file, 'r')
    f_per = open(out_per, 'w')
    f_org = open(out_org, 'w')
    f_loc = open(out_loc, 'w')

    for line in f_in.readlines():
        m1 = re.match(r'(.*)\t(.*)\t(.*)\t(.*)\t(.*)\n', line)
        if not m1 is None:
            tmp = m1.group(4)
            if tmp == '[]':
                continue
            i = 3
            while tmp[i] != '\'':
                i += 1
            if tmp[3:i] in ['person']:
                m2 = re.match(r'(.*)\(.*\)', m1.group(2))
                if not m2 is None:
                    f_per.write(m2.group(1)+'\n')
                else:
                    f_per.write(m1.group(2)+'\n')
            elif tmp[3:i] in ['company','religious-group','criminal-organization','organization']:
                m2 = re.match(r'(.*)\(.*\)', m1.group(2))
                if not m2 is None:
                    f_org.write(m2.group(1)+'\n')
                else:
                    f_org.write(m1.group(2)+'\n')
            elif tmp[3:i] in ['worship-place','country','continent','airport','desert','city']:
                m2 = re.match(r'(.*)\(.*\)', m1.group(2))
                if not m2 is None:
                    f_loc.write(m2.group(1)+'\n')
                else:
                    f_loc.write(m1.group(2)+'\n')
        else:
            print'no match in this line:'
            print line
    f_in.close()
    f_per.close()
    f_loc.close()
    f_org.close()


if __name__ == '__main__':
    if len(sys.argv) != 5:
        print 'USAGE: python wiki_type.py <input_file> <per file> <org file> <loc file>'
    else:
        in_file = sys.argv[1]
        out_per = sys.argv[2]
        out_org = sys.argv[3]
        out_loc = sys.argv[4]
        wiki_type(in_file, out_per, out_org, out_loc)