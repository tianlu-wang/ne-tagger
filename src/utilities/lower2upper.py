#!/usr/bin/env python
import sys


def lower2upper(input_file, output_file):
    input_f = open(input_file, 'r')
    output = open(output_file, 'w')

    for line in input_f.readlines():
        if line[0].isupper():
            output.write(line)
            output.write(line[0].lower()+line[1:])
        else:
            output.write(line[0].upper()+line[1:])
            output.write(line)
            pass
    input_f.close()
    output.close()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print 'USAGE: python lower2upper.py <input_file> <output_file>'
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        lower2upper(input_file, output_file)
