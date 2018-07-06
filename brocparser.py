from structures import *

FILECITYNAME = 'base\\citynames.txt'
FILECITYSTATE = 'base\\citystates.txt'
FILECITYSHORT = 'base\\cityshorts.txt'
FILESTATENAME = 'base\\statenames.txt'
FILERIVERNAME = 'base\\rivernames.txt'
FILEPLACENAME = 'base\\places.txt'


class RuleParser:
    arguments = (
        'A', 'B', 'C', 'D', 'E',
        'F', 'G', 'H', 'I', 'J',
        'K', 'L', 'M', 'N', 'O'
    )

    def __init__(self, string, db_city, db_state, db_river, db_place):
        self.sent_origin = Sent(string)
        self.sent = Sent(string)
        self.sent.reduce_multi_names()
        self.answer = Func('answer(A,())')
        self.args = [Func(None, 'arg', 'A')]
        self.arg_bounded = [False]
        self.current_goal_meta = self.answer
        self.current_goal_list = self.answer[1].args
        self.current_arg = self.args[0]
        self.current_arg_max = 0

        self.db_city = db_city
        self.db_state = db_state
        self.db_river = db_river
        self.db_place = db_place

    def introduce_meta_naive(self, func_meta):
        assert(func_meta.type == 'meta')
        self.current_goal_list.append(func_meta)
        self.current_goal_meta = func_meta
        if func_meta.cate in ('count', 'sum'):
            self.current_goal_list = func_meta[1].args
        else:
            self.current_goal_list = func_meta[-1].args

    def introduce_not(self, func_not):
        assert(func_not.type == 'not')
        self.current_goal_list.append(func_not)
        self.current_goal_list = func_not.args

    def fetch_new_arg(self):
        self.current_arg_max += 1
        self.current_arg = Func(None, 'arg', self.arguments[self.current_arg_max])
        self.args.append(self.current_arg)
        self.arg_bounded.append(False)
        return self.current_arg

    def fetch_unbounded_arg(self, t):
        for i in range(self.current_arg_max - 1):
            if i == t:
                continue
            if not self.arg_bounded[i]:
                self.arg_bounded[i] = True
                return self.args[i]
        return self.fetch_new_arg()

    def match_pattern(self, pattern):
        if len(self.sent) < len(pattern):
            return False
        for i in range(len(pattern)):
            if isinstance(pattern[i], str) \
                    and self.sent[i] != pattern[i]:
                return False
            elif isinstance(pattern[i], tuple) \
                    and self.sent[i] not in pattern[i]:
                return False
        return True

    def p_object(self, patterns, cate):
        for pat in patterns:
            if self.match_pattern(pat):
                arg0 = self.current_arg
                self.arg_bounded[self.current_arg_max] = True
                arg1 = self.fetch_unbounded_arg(self.current_arg_max)
                func0 = Func(None, 'pred', cate, [arg1, arg0])
                self.current_goal_list.append(func0)
                for i in range(len(pat)):
                    self.sent.remove_top()
                return True
        return False

    def p_subject(self, patterns, cate):
        for pat in patterns:
            if self.match_pattern(pat):
                arg0 = self.current_arg
                self.arg_bounded[self.current_arg_max] = True
                arg1 = self.fetch_unbounded_arg(self.current_arg_max)
                func0 = Func(None, 'pred', cate, [arg0, arg1])
                self.current_goal_list.append(func0)
                for i in range(len(pat)):
                    self.sent.remove_top()
                return True
        return False

    def is_everything(self, id_func):
        if self.current_arg_max > 0:
            arg_func = self.current_arg
        else:
            arg_func = self.fetch_new_arg()
        self.arg_bounded[self.current_arg_max] = True
        self.current_goal_list.append(Func(None, 'pred', 'const', [arg_func, id_func]))

    def is_city(self):
        try:
            t = self.db_city['names'].index(self.sent[0])
        except ValueError:
            return False
        arg0 = Func(None, 'arg', self.db_city['names'][t])
        self.sent.remove_top()
        str1 = '_'
        if self.sent[0] in (self.db_city['states'][t], self.db_city['shorts'][t]):
            # city accompanied with a state
            str1 = self.db_city['shorts'][t]
            self.sent.remove_top()
        arg1 = Func(None, 'arg', str1)
        id_func = Func(None, 'pred', 'cityid', [arg0, arg1])
        self.is_everything(id_func)
        return True

    def is_river(self):
        if len(self.sent) < 2:
            return False
        if self.sent[0] == 'the':
            try:
                t = self.db_river.index(self.sent[1])
            except ValueError:
                return False
            self.sent.remove_top()
            self.sent.remove_top()
        elif self.sent[1] in ['river', 'rivers']:
            try:
                t = self.db_river.index(self.sent[0])
            except ValueError:
                return False
            self.sent.remove_top()
        else:
            return False
        arg0 = Func(None, 'arg', self.db_river[t])
        id_func = Func(None, 'pred', 'riverid', [arg0])
        self.is_everything(id_func)
        return True

    def is_state(self):
        try:
            t = self.db_state.index(self.sent[0])
        except ValueError:
            return False
        arg0 = Func(None, 'arg', self.db_state[t])
        self.sent.remove_top()
        id_func = Func(None, 'pred', 'stateid', [arg0])
        self.is_everything(id_func)
        return True

    def is_place(self):
        try:
            t = self.db_place.index(self.sent[0])
        except ValueError:
            return False
        arg0 = Func(None, 'arg', self.db_place[t])
        self.sent.remove_top()
        id_func = Func(None, 'pred', 'placeid', [arg0])
        self.is_everything(id_func)
        return True

    def is_country(self):
        if self.sent[0] not in ('us', 'usa', 'america', 'nation', 'country', "'united states'"):
            return False
        arg0 = Func(None, 'arg', 'usa')
        self.sent.remove_top()
        id_func = Func(None, 'pred', 'countryid', [arg0])
        self.is_everything(id_func)
        return True

    def p_capital(self):
        if self.sent[0] in ('capital', 'capitals'):
            func0 = Func(None, 'pred', 'capital', [self.current_arg])
            self.current_goal_list.append(func0)
            self.sent.remove_top()
        elif self.match_pattern((('state', 'states'), ('capital', 'capitals'))):
            func0 = Func(None, 'pred', 'capital', [self.current_arg])
            self.current_goal_list.append(func0)
            self.sent.remove_top()
        else:
            return False
        return True

    def p_city(self):
        if self.sent[0] in ('city', 'cities'):
            func0 = Func(None, 'pred', 'city', [self.current_arg])
            self.current_goal_list.append(func0)
            self.sent.remove_top()
        else:
            return False
        return True

    def p_major(self):
        if self.sent[0] in ('major', 'big'):
            func0 = Func(None, 'pred', 'major', [self.current_arg])
            self.current_goal_list.append(func0)
            self.sent.remove_top()
        else:
            return False
        return True

    def p_state(self):
        if self.sent[0] in ('state', 'states'):
            func0 = Func(None, 'pred', 'state', [self.current_arg])
            self.current_goal_list.append(func0)
            self.sent.remove_top()
            if self.sent[0] == 'of':
                self.sent.remove_top()
        else:
            return False
        return True

    def p_river(self):
        if self.sent[0] in ('river', 'rivers'):
            func0 = Func(None, 'pred', 'river', [self.current_arg])
            self.current_goal_list.append(func0)
            self.sent.remove_top()
        else:
            return False
        return True

    def p_lake(self):
        if self.sent[0] in ('lake', 'lakes'):
            func0 = Func(None, 'pred', 'lake', [self.current_arg])
            self.current_goal_list.append(func0)
            self.sent.remove_top()
        else:
            return False
        return True

    def p_mountain(self):
        if self.sent[0] in ('mountain', 'mountains'):
            func0 = Func(None, 'pred', 'mountain', [self.current_arg])
            self.current_goal_list.append(func0)
            self.sent.remove_top()
        else:
            return False
        return True

    def p_place(self):
        if self.sent[0] in ('point', 'points'):
            func0 = Func(None, 'pred', 'place', [self.current_arg])
            self.current_goal_list.append(func0)
            self.sent.remove_top()
        else:
            return False
        return True

    def p_area(self):
        patterns = (
            (('area', 'areas'), 'of'),
            (('area', 'areas'),),
            ('how', 'many', 'square', 'kilometers', 'in')
        )
        return self.p_object(patterns, 'area')

    def p_size(self):
        patterns = (
            (('size', 'sizes'), 'of'),
            (('size', 'sizes'),),
            ('how', 'big')
        )
        return self.p_object(patterns, 'size')

    def p_density(self):
        patterns = (
            (('density', 'densities'), ('in', 'of')),
            ('population', ('density', 'densities'), ('in', 'of')),
            ('average', 'population', ('in', 'of')),
            (('density', 'densities'),),
            ('population', ('density', 'densities'),),
            ('average', 'population',),
        )
        return self.p_object(patterns, 'density')

    def p_elevation(self):
        patterns = (
            (('height', 'heights'), 'of'),
            ('how', ('high', 'tall')),
            ('population', 'density'),
            ('average', 'population')
        )
        return self.p_object(patterns, 'elevation')

    def p_length(self):
        patterns = (
            (('length', 'lengths'), 'of'),
            ('how', 'long'),
        )
        return self.p_object(patterns, 'len')

    def p_population(self):
        verbs = ('stay', 'live', 'are', 'reside', 'stayed', 'lived', 'were', 'resided')
        nouns = ('people', 'inhabitants', 'citizens', 'residents', 'populations', 'population')
        patterns = (
            ('how', 'many', nouns, verbs, 'in'),
            ('how', 'many', nouns, 'are', 'there', 'in'),
            ('how', 'many', nouns, 'in'),
            ('number', 'of', nouns, 'in'),
            (nouns, ('in', 'of')),
            ('how', 'much', 'population'),
            ('how', 'many', nouns, 'does'),
            ('how', 'many', nouns, 'do'),
            ('the', 'population', ('in', 'of'))
        )
        return self.p_object(patterns, 'population')

    def p_highpointof(self):
        ret = self.match_pattern(('high', ('point', 'points'), 'of'))
        if not ret:
            return ret
        arg0 = self.current_arg
        self.arg_bounded[self.current_arg_max] = True
        arg1 = self.fetch_unbounded_arg(self.current_arg_max)
        func0 = Func(None, 'pred', 'high_point', [arg1, arg0])
        func1 = Func(None, 'pred', 'loc', [arg0, arg1])
        self.current_goal_list.append(func0)
        self.current_goal_list.append(func1)
        for i in range(3):
            self.sent.remove_top()
        return True

    def p_lowpointof(self):
        ret = self.match_pattern(('low', ('point', 'points'), 'of'))
        if not ret:
            return ret
        arg0 = self.current_arg
        self.arg_bounded[self.current_arg_max] = True
        arg1 = self.fetch_unbounded_arg(self.current_arg_max)
        func0 = Func(None, 'pred', 'low_point', [arg1, arg0])
        func1 = Func(None, 'pred', 'loc', [arg0, arg1])
        self.current_goal_list.append(func0)
        self.current_goal_list.append(func1)
        for i in range(3):
            self.sent.remove_top()
        return True

    def p_nextto(self):
        patterns = (
            ('surrounding',),
            ('border',),
            ('bordering',),
            ('next', 'to'),
            ('border', 'on'),
            ('neighboring',),
            ('adjacent',),
            ('borders',),
            ('surround',),
            ('surrounds',),
        )
        return self.p_subject(patterns, 'next_to')

    def p_traverse(self):
        patterns = (
            (('pass', 'passes'), 'through'),
            (('cross', 'crosses'),),
            (('traverse', 'traverses'),),
            (('run', 'runs'), 'through'),
            (('flow', 'flows'), 'through'),
            (('go', 'goes'), 'through'),
            (('run', 'runs'),),
            (('flow', 'flows'),)
        )
        return self.p_subject(patterns, 'traverse')

    def p_traverse_obj(self):
        patterns = (
            ('washed', 'by'),
        )
        return self.p_object(patterns, 'traverse')

    def p_higher(self):
        patterns = (
            ('higher',),
        )
        return self.p_subject(patterns, 'higher')

    def p_lower(self):
        patterns = (
            ('lower',),
        )
        return self.p_subject(patterns, 'lower')

    def p_does_which(self):
        if self.match_pattern((('do', 'does'),)) and not \
                self.match_pattern((('do', 'does'), 'not')):
            self.fetch_new_arg()
        if self.match_pattern(((('through', 'in'), ('which', 'what')),)):
            self.fetch_new_arg()
        return False  # silent move

    def p_locate(self):
        if self.match_pattern((('in', 'of'),)) and not \
                self.match_pattern((('in', 'of'), ('miles', 'population'))):
            arg0 = self.current_arg
            self.arg_bounded[self.current_arg_max] = True
            arg1 = self.fetch_unbounded_arg(self.current_arg_max)
            func0 = Func(None, 'pred', 'loc', [arg0, arg1])
            self.current_goal_list.append(func0)
            self.sent.remove_top()
            return True
        return False

    def p_locate_obj(self):
        if self.match_pattern((('has', 'have'),)):
            arg0 = self.current_arg
            self.arg_bounded[self.current_arg_max] = True
            arg1 = self.fetch_unbounded_arg(self.current_arg_max)
            func0 = Func(None, 'pred', 'loc', [arg1, arg0])
            self.current_goal_list.append(func0)
            self.sent.remove_top()
            return True
        return False

    def m_not(self):
        ret = self.match_pattern((('no', 'not', 'excluding'),))
        if not ret:
            return False
        func_not = Func(None, 'not', '\\+ ', [])
        self.introduce_not(func_not)
        self.sent.remove_top()
        return True

    def m_count(self):
        patterns = (
            ('count',),
            ('number', 'of'),
            ('how', 'many'),
        )
        for pat in patterns:
            if self.match_pattern(pat):
                arg0 = self.current_arg
                self.arg_bounded[self.current_arg_max] = True
                arg1 = self.fetch_unbounded_arg(self.current_arg_max)
                func_goal = Func(None, 'goal', '', [])
                func_meta = Func(None, 'meta', 'count', [arg1, func_goal, arg0])
                self.introduce_meta_naive(func_meta)
                for i in range(len(pat)):
                    self.sent.remove_top()
                return True
        return False

    def m_sum(self):
        patterns = (
            (('total', 'combined'),),
        )
        for pat in patterns:
            if self.match_pattern(pat):
                arg0 = self.current_arg
                self.arg_bounded[self.current_arg_max] = True
                arg1 = self.fetch_unbounded_arg(self.current_arg_max)
                func_goal = Func(None, 'goal', '', [])
                func_meta = Func(None, 'meta', 'sum', [arg1, func_goal, arg0])
                self.introduce_meta_naive(func_meta)
                for i in range(len(pat)):
                    self.sent.remove_top()
                return True
        return False

    def m_largestdensity(self):
        adjs = ('greatest', 'highest', 'biggest', 'largest')
        patterns = (
            ('has', 'the', adjs, 'density'),
            ('has', 'the', adjs, 'population', 'density'),
            (adjs, 'density'),
            (adjs, 'population', 'density')
        )
        for pat in patterns:
            if self.match_pattern(pat):
                arg1 = self.current_arg
                self.arg_bounded[self.current_arg_max] = True
                arg0 = self.fetch_new_arg()
                self.arg_bounded[self.current_arg_max] = True
                if len(self.sent) > 0:
                    func_pop = Func(None, 'pred', 'density', [arg1, arg0])
                    func_goal = Func(None, 'goal', '', [self.current_goal_list[-1], func_pop])
                    func_meta = Func(None, 'meta', 'largest', [arg0, func_goal])
                    if self.current_goal_meta.cate in ('count', 'sum'):
                        self.current_goal_meta[1].args[-1] = func_meta
                    else:
                        self.current_goal_meta[-1].args[-1] = func_meta
                    self.current_goal_meta = func_meta
                    self.current_goal_list = func_meta[-1].args
                else:
                    func_pop = Func(None, 'pred', 'density', [arg1, arg0])
                    func_goal = Func(None, 'goal', '', [func_pop])
                    func_meta = Func(None, 'meta', 'largest', [arg0, func_goal])
                    if self.current_goal_meta.cate in ('count', 'sum'):
                        self.current_goal_meta[1].append(func_meta)
                    else:
                        self.current_goal_meta[-1].append(func_meta)
                    self.current_goal_meta = func_meta
                    self.current_goal_list = func_meta[-1].args
                for i in range(len(pat)):
                    self.sent.remove_top()
                return True
        return False

    def m_largestpopulation(self):
        adjs = ('greatest', 'highest', 'biggest', 'largest')
        nouns = ('population', 'populations', 'number of citizens',)
        patterns = (
            ('has', 'the', adjs, nouns),
            (adjs, nouns),
            ('most', 'people'),
            ('most', 'inhabitants')
        )
        for pat in patterns:
            if self.match_pattern(pat):
                arg1 = self.current_arg
                self.arg_bounded[self.current_arg_max] = True
                arg0 = self.fetch_new_arg()
                self.arg_bounded[self.current_arg_max] = True
                if len(self.sent) > 0:
                    func_pop = Func(None, 'pred', 'population', [arg1, arg0])
                    func_goal = Func(None, 'goal', '', [self.current_goal_list[-1], func_pop])
                    func_meta = Func(None, 'meta', 'largest', [arg0, func_goal])
                    if self.current_goal_meta.cate in ('count', 'sum'):
                        self.current_goal_meta[1].args[-1] = func_meta
                    else:
                        self.current_goal_meta[-1].args[-1] = func_meta
                    self.current_goal_meta = func_meta
                    self.current_goal_list = func_meta[-1].args
                else:
                    func_pop = Func(None, 'pred', 'population', [arg1, arg0])
                    func_goal = Func(None, 'goal', '', [func_pop])
                    func_meta = Func(None, 'meta', 'largest', [arg0, func_goal])
                    if self.current_goal_meta.cate in ('count', 'sum'):
                        self.current_goal_meta[1].args.append(func_meta)
                    else:
                        self.current_goal_meta[-1].args.append(func_meta)
                    self.current_goal_meta = func_meta
                    self.current_goal_list = func_meta[-1].args
                for i in range(len(pat)):
                    self.sent.remove_top()
                return True
        return False

    def m_smallestdensity(self):
        adjs = ('smallest', 'least', 'lowest', 'sparsest')
        patterns = (
            ('has', 'the', adjs, 'density'),
            ('has', 'the', adjs, 'population', 'density'),
            ('has', 'the', adjs, 'average', 'urban', 'population'),
            (adjs, 'density'),
            (adjs, 'population', 'density'),
            (adjs, 'average', 'urban', 'population'),
        )
        for pat in patterns:
            if self.match_pattern(pat):
                arg1 = self.current_arg
                self.arg_bounded[self.current_arg_max] = True
                arg0 = self.fetch_new_arg()
                self.arg_bounded[self.current_arg_max] = True
                if len(self.sent) > 0:
                    func_pop = Func(None, 'pred', 'density', [arg1, arg0])
                    func_goal = Func(None, 'goal', '', [self.current_goal_list[-1], func_pop])
                    func_meta = Func(None, 'meta', 'smallest', [arg0, func_goal])
                    if self.current_goal_meta.cate in ('count', 'sum'):
                        self.current_goal_meta[1].args[-1] = func_meta
                    else:
                        self.current_goal_meta[-1].args[-1] = func_meta
                    self.current_goal_meta = func_meta
                    self.current_goal_list = func_meta[-1].args
                else:
                    func_pop = Func(None, 'pred', 'density', [arg1, arg0])
                    func_goal = Func(None, 'goal', '', [func_pop])
                    func_meta = Func(None, 'meta', 'smallest', [arg0, func_goal])
                    if self.current_goal_meta.cate in ('count', 'sum'):
                        self.current_goal_meta[1].append(func_meta)
                    else:
                        self.current_goal_meta[-1].append(func_meta)
                    self.current_goal_meta = func_meta
                    self.current_goal_list = func_meta[-1].args
                for i in range(len(pat)):
                    self.sent.remove_top()
                return True
        return False

    def m_smallestpopulation(self):
        adjs = ('smallest', 'least', 'lowest', 'sparsest')
        nouns = ('population', 'populations', 'number of citizens',)
        patterns = (
            ('has', 'the', adjs, nouns),
            (adjs, nouns)
        )
        for pat in patterns:
            if self.match_pattern(pat):
                arg1 = self.current_arg
                self.arg_bounded[self.current_arg_max] = True
                arg0 = self.fetch_new_arg()
                self.arg_bounded[self.current_arg_max] = True
                if len(self.sent) > 0:
                    func_pop = Func(None, 'pred', 'population', [arg1, arg0])
                    func_goal = Func(None, 'goal', '', [self.current_goal_list[-1], func_pop])
                    func_meta = Func(None, 'meta', 'smallest', [arg0, func_goal])
                    if self.current_goal_meta.cate in ('count', 'sum'):
                        self.current_goal_meta[1].args[-1] = func_meta
                    else:
                        self.current_goal_meta[-1].args[-1] = func_meta
                    self.current_goal_meta = func_meta
                    self.current_goal_list = func_meta[-1].args
                else:
                    func_pop = Func(None, 'pred', 'population', [arg1, arg0])
                    func_goal = Func(None, 'goal', '', [func_pop])
                    func_meta = Func(None, 'meta', 'smallest', [arg0, func_goal])
                    if self.current_goal_meta.cate in ('count', 'sum'):
                        self.current_goal_meta[1].append(func_meta)
                    else:
                        self.current_goal_meta[-1].append(func_meta)
                    self.current_goal_meta = func_meta
                    self.current_goal_list = func_meta[-1].args
                for i in range(len(pat)):
                    self.sent.remove_top()
                return True
        return False

    def m_largest(self):
        adjs = ('biggest', 'largest')
        patterns = (
            (adjs,),
        )
        for pat in patterns:
            if self.match_pattern(pat):
                arg0 = self.current_arg
                self.arg_bounded[self.current_arg_max] = True
                func_goal = Func(None, 'goal', '', [])
                func_meta = Func(None, 'meta', 'largest', [arg0, func_goal])
                self.introduce_meta_naive(func_meta)
                for i in range(len(pat)):
                    self.sent.remove_top()
                return True
        return False

    def m_smallest(self):
        adjs = ('smallest', 'least')
        patterns = (
            (adjs,),
        )
        for pat in patterns:
            if self.match_pattern(pat):
                arg0 = self.current_arg
                self.arg_bounded[self.current_arg_max] = True
                func_goal = Func(None, 'goal', '', [])
                func_meta = Func(None, 'meta', 'smallest', [arg0, func_goal])
                self.introduce_meta_naive(func_meta)
                for i in range(len(pat)):
                    self.sent.remove_top()
                return True
        return False

    def m_shortest(self):
        if self.match_pattern(('shortest',)):
            arg0 = self.current_arg
            self.arg_bounded[self.current_arg_max] = True
            func_goal = Func(None, 'goal', '', [])
            func_meta = Func(None, 'meta', 'shortest', [arg0, func_goal])
            self.introduce_meta_naive(func_meta)
            self.sent.remove_top()
            return True
        return False

    def m_longest(self):
        adjs = ('biggest', 'largest', 'longest')
        patterns = (
            (adjs, 'rivers'),
            ('longest',)
        )
        for pat in patterns:
            if self.match_pattern(pat):
                arg0 = self.current_arg
                self.arg_bounded[self.current_arg_max] = True
                func_goal = Func(None, 'goal', '', [])
                func_meta = Func(None, 'meta', 'longest', [arg0, func_goal])
                self.introduce_meta_naive(func_meta)
                self.sent.remove_top()
                return True
        return False

    def m_highestelevation(self):
        if self.match_pattern(('highest', 'elevation')):
            arg0 = self.current_arg
            self.arg_bounded[self.current_arg_max] = True
            func_goal = Func(None, 'goal', '', [])
            func_meta = Func(None, 'meta', 'highest', [arg0, func_goal])
            self.introduce_meta_naive(func_meta)
            func_place = Func(None, 'pred', 'place', [arg0])
            self.current_goal_list.append(func_place)
            self.sent.remove_top()
            self.sent.remove_top()
            return True
        return False

    def m_highest(self):
        if self.match_pattern(('highest',)):
            arg0 = self.current_arg
            self.arg_bounded[self.current_arg_max] = True
            func_goal = Func(None, 'goal', '', [])
            func_meta = Func(None, 'meta', 'highest', [arg0, func_goal])
            self.introduce_meta_naive(func_meta)
            self.sent.remove_top()
            return True
        return False

    def m_lowestelevation(self):
        if self.match_pattern(('lowest', 'elevation')):
            arg0 = self.current_arg
            self.arg_bounded[self.current_arg_max] = True
            func_goal = Func(None, 'goal', '', [])
            func_meta = Func(None, 'meta', 'lowest', [arg0, func_goal])
            self.introduce_meta_naive(func_meta)
            func_place = Func(None, 'pred', 'place', [arg0])
            self.current_goal_list.append(func_place)
            self.sent.remove_top()
            self.sent.remove_top()
            return True
        return False

    def m_lowest(self):
        if self.match_pattern(('lowest',)):
            arg0 = self.current_arg
            self.arg_bounded[self.current_arg_max] = True
            func_goal = Func(None, 'goal', '', [])
            func_meta = Func(None, 'meta', 'lowest', [arg0, func_goal])
            self.introduce_meta_naive(func_meta)
            self.sent.remove_top()
            return True
        return False

    # buggy
    def m_mostpopulous(self):
        if self.match_pattern(('most', ('populous', 'populated'))):
            arg1 = self.current_arg
            self.arg_bounded[self.current_arg_max] = True
            arg0 = self.fetch_new_arg()
            self.arg_bounded[self.current_arg_max] = True
            func_pop = Func(None, 'pred', 'population', [arg1, arg0])
            func_goal = Func(None, 'goal', '', [func_pop])
            func_meta = Func(None, 'meta', 'largest', [arg0, func_goal])
            if self.current_goal_meta.cate in ('count', 'sum'):
                self.current_goal_meta[1].args.append(func_meta)
            else:
                self.current_goal_meta[-1].args.append(func_meta)
            self.current_goal_meta = func_meta
            self.current_goal_list = func_meta[-1].args
            self.sent.remove_top()
            self.sent.remove_top()
            return True
        return False

    def m_leastpopulous(self):
        if self.match_pattern(('least', ('populous', 'populated'))):
            arg1 = self.current_arg
            self.arg_bounded[self.current_arg_max] = True
            arg0 = self.fetch_new_arg()
            self.arg_bounded[self.current_arg_max] = True
            func_pop = Func(None, 'pred', 'population', [arg1, arg0])
            func_goal = Func(None, 'goal', '', [func_pop])
            func_meta = Func(None, 'meta', 'smallest', [arg0, func_goal])
            if self.current_goal_meta.cate in ('count', 'sum'):
                self.current_goal_meta[1].args.append(func_meta)
            else:
                self.current_goal_meta[-1].args.append(func_meta)
            self.current_goal_meta = func_meta
            self.current_goal_list = func_meta[-1].args
            self.sent.remove_top()
            self.sent.remove_top()
            return True
        return False

    def m_most(self):
        if self.match_pattern(('most',)):
            arg0 = self.current_arg
            self.arg_bounded[self.current_arg_max] = True
            arg1 = self.fetch_unbounded_arg(self.current_arg_max)
            func_goal = Func(None, 'goal', '', [])
            func_meta = Func(None, 'meta', 'most', [arg0, arg1, func_goal])
            if len(self.current_goal_list) >= 2:
                func_meta[2].args = self.current_goal_list[-2:]
                if self.current_goal_meta.cate in ('count', 'sum'):
                    self.current_goal_meta[1].args = self.current_goal_list[:-2] + [func_meta]
                else:
                    self.current_goal_meta[-1].args = self.current_goal_list[:-2] + [func_meta]
                self.current_goal_list = func_meta[2].args
                self.current_goal_meta = func_meta
            else:
                func_meta[2].args = self.current_goal_list
                if self.current_goal_meta.cate in ('count', 'sum'):
                    self.current_goal_meta[1].args = [func_meta]
                else:
                    self.current_goal_meta[-1].args = [func_meta]
                self.current_goal_list = func_meta[2].args
                self.current_goal_meta = func_meta
            self.sent.remove_top()
            return True
        return False

    def m_fewest(self):
        if self.match_pattern((('least', 'fewest'),)):
            arg0 = self.fetch_unbounded_arg(-1)
            self.arg_bounded[self.current_arg_max] = True
            arg1 = self.fetch_unbounded_arg(ord(arg0.cate) - 65)
            func_goal = Func(None, 'goal', '', [])
            func_meta = Func(None, 'meta', 'fewest', [arg0, arg1, func_goal])
            if len(self.current_goal_list) >= 2:
                func_meta[2].args = self.current_goal_list[-2:]
                if self.current_goal_meta.cate in ('count', 'sum'):
                    self.current_goal_meta[1].args = self.current_goal_list[:-2] + [func_meta]
                else:
                    self.current_goal_meta[-1].args = self.current_goal_list[:-2] + [func_meta]
                self.current_goal_list = func_meta[2].args
                self.current_goal_meta = func_meta
            else:
                func_meta[2].args = self.current_goal_list
                if self.current_goal_meta.cate in ('count', 'sum'):
                    self.current_goal_meta[1].args = [func_meta]
                else:
                    self.current_goal_meta[-1].args = [func_meta]
                self.current_goal_list = func_meta[2].args
                self.current_goal_meta = func_meta
            self.sent.remove_top()
            return True
        return False

    def parse(self):
        rules = (
            self.is_city,
            self.is_state,
            self.is_river,
            self.is_place,
            self.is_country,
            self.p_capital,
            self.p_city,
            self.p_major,
            self.p_state,
            self.p_river,
            self.p_lake,
            self.p_mountain,
            self.p_place,
            self.p_size,
            self.p_area,
            self.p_density,
            self.p_elevation,
            self.p_length,
            self.p_population,
            self.p_highpointof,
            self.p_lowpointof,
            self.p_nextto,
            self.p_traverse,
            self.p_higher,
            self.p_lower,
            self.p_traverse_obj,
            self.p_does_which,
            self.p_locate,
            self.p_locate_obj,
            self.m_not,
            self.m_sum,
            self.m_count,
            self.m_largestdensity,
            self.m_largestpopulation,
            self.m_smallestdensity,
            self.m_smallestpopulation,
            self.m_largest,
            self.m_smallest,
            self.m_shortest,
            self.m_longest,
            self.m_highestelevation,
            self.m_highest,
            self.m_lowestelevation,
            self.m_lowest,
            self.m_mostpopulous,
            self.m_leastpopulous,
            self.m_most,
            self.m_fewest,
        )
        while len(self.sent) > 0:
            sign = False
            for t in rules:
                if t():
                    sign = True
                    break
            if not sign:
                self.sent.remove_top()
        return self.answer




class BroCParser:

    def __init__(self):
        self.city = {
            'names': read_list(FILECITYNAME),
            'states': read_list(FILECITYSTATE),
            'shorts': read_list(FILECITYSHORT)
        }
        self.state = read_list(FILECITYSTATE)
        self.river = read_list(FILERIVERNAME)
        self.place = read_list(FILEPLACENAME)

    def parse(self, string):
        parser = RuleParser(string, self.city, self.state, self.river, self.place)
        answer = parser.parse()
        return Sample(None, parser.sent_origin, answer).to_str()
