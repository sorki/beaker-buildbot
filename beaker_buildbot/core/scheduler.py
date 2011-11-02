import time
import subprocess

class BuildScheduler(object):
    '''
    Schedulers inherit this class
    '''
    def schedule(self, task_queue):
        '''
        Returns True if task_queue should be schedule
        '''
        raise NotImplemented

class NightlyScheduler(BuildScheduler):
    '''
    Runs the tasks during the night
    '''
    def __init__(self, night_since=23, night_till=5):
        self.night_since = night_since
        self.night_till = night_till

    def schedule(self, task_queue):
        cur = time.localtime()
        loc_hour = cur.tm_hour
        if loc_hour > self.night_since or loc_hour < self.night_till:
            return True

        return False


class CumulativeScheduler(BuildScheduler):
    ''' 
    Takes number of commits to accumulate
    before running the task
    '''
    def __init__(self, num_commits=3):
        self.num_commits = num_commits

    def schedule(self, task_queue):
        if len(task_queue) > self.num_commits:
            return True

        return False


class LoadAvareScheduler(BuildScheduler):
    '''
    Runs the tasks only when system load
    is low
    '''
    def __init__(self, method=lambda x: 2, high=1):
        self.method = method
        self.high = high

    def schedule(self, task_queue):
        cur = self.method()
        if cur < self.high:
            return True

        return False

class BeakerLoadAvareScheduler(LoadAvareScheduler):
    def __init__(self, free_systems = 15):
        super(BeakerLoadAvareScheduler, self).__init__(method=self.check_beaker,
            high = free_systems)

    def check_beaker(self):
        cmd = 'bkr list-systems --free'
        # TODO --type=TYPE?
        try:
            out = subprocess.check_output(cmd.split())
        except subprocess.CalledProcessError:
            return False

        # TODO: parse out
        return 20
