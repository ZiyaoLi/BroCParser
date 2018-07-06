from structures import read_list, Sample
from brocparser import BroCParser


t = read_list('data\\geoqueries880_out')
t = [Sample(k).sent.to_str() for k in t]
tt = BroCParser()
s = []
for a in t:
    s.append(tt.parse(a))
f = open('data\\geoqueries880_myout', 'w')
f.write('\n'.join(s))
f.close()

t = read_list('data\\d1_train_in.txt')
tt = BroCParser()
s = []
for a in t:
    s.append(tt.parse(a))
f = open('data\\d1_train_myout.txt', 'w')
f.write('\n'.join(s))
f.close()

t = read_list('data\\d1_valid_in.txt')
tt = BroCParser()
s = []
for a in t:
    s.append(tt.parse(a))
f = open('data\\d1_valid_myout.txt', 'w')
f.write('\n'.join(s))
f.close()
