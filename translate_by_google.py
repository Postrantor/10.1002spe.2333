# -*- coding: UTF-8 -*-

# https://github.com/ssut/py-googletrans
from docx import Document
from googletrans import Translator
import sys, getopt, os, time
"""
translate a word document type of file and save the result as document and keep the exactly same file format.
    :param file_input: word doc file
    :param destination='zh-CN':
    :param mix=True: if True, will have original language and target language into the same doc. paragraphs by paragraphs.
"""

# opts, args = getopt.getopt(sys.argv[1:], "hi:o:")
file_input = sys.argv[1]
file_output = '.temp'
destination = 'zh-CN'
mix = True


def tx(t):
    return Translator().translate(t, dest=destination).text


f_read = open(file_input, 'r', encoding='utf-8')
f_write = open(file_output, 'w', encoding='utf-8')
for line in f_read:
    if line == '\n' \
        or line == '> ===\n' \
        or line[:2] == '![' \
        or line[0] == '<' \
        or line[0] == '>':
        f_write.write(line)
        continue

    txd = tx(line)
    line_trans = line + ('\n> ' + txd if mix else '')
    f_write.write('\n' + line_trans + '\n')

f_write.close()
f_read.close()

#
os.remove(file_input)
os.rename(file_output, file_input)
