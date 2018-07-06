#-*- coding: UTF-8 -*-
"""
Author : Lai Yuxuan
Email  : erutan@pku.edu.cn
"""
import sys

"""python3"""

import re, codecs

codecs_in = lambda x : codecs.open(x, 'r', 'utf-8')


def read_line(line) :
    line = line.strip()
    ret = {'line':line}

    try :
        m = re.match(r'^.*parse\((\[.*\]), *answer(\(.*\))\).*$', line)
        ret['sent']   = m.group(1)
        ret['answer'] = m.group(2)
    except :
        print('warning! %s'%(line))
        ret['sent']   = 'None'
        ret['answer'] = 'None'

    return ret
    

def evall(pred, gold) :
    # exact match
    pred_data = codecs_in(pred).readlines()
    pred_data = list(map(read_line, pred_data))
    gold_data = codecs_in(gold).readlines()
    gold_data = list(map(read_line, gold_data))
    assert len(pred_data)==len(gold_data)

    lent = len(pred_data)
    truth = len([i for i in range(lent) if gold_data[i]['answer']==pred_data[i]['answer']])

    print(truth, lent, '%.2f'%(100.*truth/lent))

    return [i for i in range(lent) if gold_data[i]['answer']!=pred_data[i]['answer']]

if __name__ == '__main__':
    print(evall('../data/d1_train_myout.txt', '../data/d1_train_out.txt'))
    print(evall('../data/d1_valid_myout.txt', '../data/d1_valid_out.txt'))
    print(evall('../data/geoqueries880_out', '../data/geoqueries880_myout'))

    #print(evall('../data/d2_train_repro.txt', '../data/d2_train_out.txt'))


