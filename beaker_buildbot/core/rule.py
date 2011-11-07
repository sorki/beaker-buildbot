from beaker_buildbot.core import scheduler

class RuleSchedule(object):
    '''
    Parse and check scheduling rule
    '''
    def __init__(self, rule_str):
        self._parsed = self._parse_rule(rule_str)
        self.rule = map(self._map_classes, self._parsed)

    def _parse_rule(self, rule_str):
        '''
        Parse string representing scheduling rule:

        input: ((BeakerLoadAvare)) && ((Nightly || Cumulative[3]))
        output: ['&', [['BeakerLoadAvare']], [['|', 'Nightly', 'Cumulative[3]']]]
        '''
        rule_str = rule_str.strip()

        refs = []
        parsed = []

        while True:

            a = rule_str.find('(')
            if a == -1:
                break

            b = rule_str.find(')')
            while rule_str.count('(', a, b+1) != rule_str.count(')', a, b+1):
                b = rule_str.find(')', b+1)
                if b == -1:
                    raise Exception('Brace mismatch')

            ref = self._parse_rule(rule_str[a+1:b])
            rule_str = '%s%%%d%s' % (rule_str[0:a], len(refs), rule_str[b+1:])
            refs.append(ref)

        def fix_refs(ref):
            ref = ref.strip()
            if ref[0] == '%':
                return refs[int(ref[1])]
            else:
                return ref

        if '&&' in rule_str and '||' in rule_str:
            raise Exception('No support for and/or combination, use braces')
        elif '&&' in rule_str:
            parts = map(lambda x: x.strip(), rule_str.split('&&'))
            if len(parts) != 2:
                raise Exception('AND of more then two elements or single element')

            parsed = ['&'] + parts

        elif '||' in rule_str:
            parts = map(lambda x: x.strip(), rule_str.split('||'))
            if len(parts) != 2:
                raise Exception('OR of more then two elements or single element')

            parsed = ['|'] + parts
        else:
            parsed = [rule_str]

        return map(fix_refs, parsed)

    def _map_classes(self, elem):
        '''
        Map class name with parameters to instance.
        '''
        if elem == '&' or elem == '|':
            return elem
        if type(elem) == list:
            return map(self._map_classes, elem)
        if type(elem) == str:
            params = False
            if '[' in elem:
                if elem[-1] != ']':
                    raise Exception('Parameter brace mismatch')
                [cls, params] = elem[:-1].split('[')
                params = map(lambda x: x.strip(), params.split(','))
            else:
                cls = elem

            cls += 'Scheduler'

            if hasattr(scheduler, cls):
                obj = getattr(scheduler, cls)()
                if params:
                    obj.take_params(params)
                return obj
            else:
                raise Exception('Unknown scheduler: %s' % cls)

    def schedule(self):
        task_q = []
        def get_state(elem):
            '''
            Calls schedule function of each instance
            '''
            if elem == '&' or elem == '|':
                return elem
            if type(elem) == list:
                return map(get_state, elem)
            return elem.schedule(task_q)

        print self.rule
        states = map(get_state, self.rule)
        print states

        # outcome
        def get_outcome(slist):
            '''
            Resolves AND/OR operators
            '''
            if type(slist) == list:
                if type(slist[0]) == list:
                    return get_outcome(slist[0])
                if slist[0] == '&':
                    return get_outcome(slist[1]) and get_outcome(slist[2])
                if slist[0] == '|':
                    return get_outcome(slist[1]) or get_outcome(slist[2])
                return get_outcome(slist[0])
            return slist

        return get_outcome(states)

