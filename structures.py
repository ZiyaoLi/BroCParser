import re

MULTIFILE = 'base\\multi.txt'


def read_list(filename):
    f = open(filename, 'r')
    s = f.read().strip().split('\n')
    f.close()
    return s


def read_multi(filename):
    s = read_list(filename)
    s = [t.strip().split(' ') for t in s]
    return s


MULTILIST = read_multi(MULTIFILE)


def match_list(pattern, data):
    for i in range(len(data) - len(pattern) + 1):
        sign = 1
        for j in range(len(pattern)):
            if pattern[j] != data[i + j]:
                sign = 0
                break
        if sign:
            return i
    return -1


class Sent:

    multi_list = MULTILIST

    def __init__(self, string):
        self.words = string.strip().strip('[]').split(',')

    def to_str(self):
        return '[%s]' % ','.join(self.words)

    def __getitem__(self, item):
        return self.words[item]

    def __len__(self):
        return len(self.words)

    def reduce_multi_names(self):
        for pat in self.multi_list:
            t = match_list(pat, self.words)
            while t >= 0:
                self.words[t] = "'" + ' '.join(pat) + "'"
                for i in range(len(pat) - 1):
                    self.words.pop(t + 1)
                t = match_list(pat, self.words)

    def remove_top(self):
        self.words.pop(0)


def solve_sub(typ, arg_str):
    if arg_str == ',':
        return []
    layer = 0
    pos = 0
    args = []
    for i, ci in enumerate(arg_str):
        if ci == ',':  # possible separation
            if layer == 0:
                args.append(Func(arg_str[pos: i]))
                pos = i + 1
        elif ci == '(':  # enter a sub-structure
            layer += 1
        elif ci == ')':  # exit a sub-structure
            layer -= 1
    if typ == 'meta':
        if args[-1].type != 'goal':
            args[-1] = Func('(%s)' % args[-1].to_str())
    return args


class Func:

    meta_preds = (
        'answer',
        'largest',
        'smallest',
        'highest',
        'lowest',
        'longest',
        'shortest',
        'count',
        'most',
        'fewest',
        'sum'
    )

    def __init__(self, string=None, typ=None, cate=None, args=[]):
        if string is None:
            self.type = typ
            self.cate = cate
            self.args = args
            return
        string = string.strip()
        m = re.match(r'^(.*?)\((.*)\)$', string)
        if m is None:
            self.type = 'arg'
            self.cate = string
            self.args = []
            return
        self.cate = m.group(1)
        if self.cate in self.meta_preds:
            self.type = 'meta'
        elif self.cate == '':
            self.type = 'goal'
        elif self.cate == '\\+':
            self.type = 'not'
        else:
            self.type = 'pred'
        arg_str = m.group(2) + ','
        self.args = solve_sub(self.type, arg_str)

    def __getitem__(self, item):
        return self.args[item]

    def have_no_arg(self, string):
        if self.type == 'arg':
            if self.cate == string:
                return False
            else:
                return True
        for son in self.args:
            if not son.have_no_arg(string):
                return False
        return True

    def to_str(self):
        if self.type in ('goal', 'not'):
            if len(self.args) > 1:
                return '%s(%s)' % (self.cate, ','.join([t.to_str() for t in self.args]))
            elif len(self.args) == 1:
                if self.type == 'goal':
                    return self.args[0].to_str()
                else:
                    return '\\+%s' % self.args[0].to_str()
            else:
                return '()'
        elif self.type != 'arg':
            return '%s(%s)' % (self.cate,
                ','.join([t.to_str() for t in self.args]))
        else:
            return self.cate


class Sample:

    def __init__(self, string=None, sent=None, ans=None):
        if string is None:
            self.sent = sent
            self.ans = ans
        else:
            try:
                m = re.match(r'^.*parse\((\[.*\]), *answer(\(.*\))\).*$', string)
                self.sent = Sent(m.group(1))
                self.ans = Func('answer' + m.group(2))
            except:
                print('Warning: fail to parse logic %s' % string)
                self.sent = None
                self.ans = None

    def to_str(self):
        if self.sent is None or self.ans is None:
            return 'Warning: sent or ans is empty in sample.'
        else:
            return 'parse(%s, %s).' % \
               (self.sent.to_str(), self.ans.to_str())


