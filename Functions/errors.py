class InvalidMode(Exception):
    pass

class InvalidResult(Exception):
    pass

class SolutionNotFeasible(Exception):
    pass

def check_mode(mode: str):
    '''Checks if the mode passed as argument is valid. Raises an InvalidMode exception if not valid.'''
    if mode != 'varying' and mode != 'fixed' and mode != 'single' and mode != 'tid' and \
       mode != 'aid' and mode != 'ga' and mode != 'pgwo' and mode != 'pgwo2' and mode != 'pgwo3' and mode != 'unif':
        raise(InvalidMode('Mode is not varying, fixed, single, ga, pgwo, pgwo2 or unif.'))

class ErrorPackage:
    def __init__(self, exc_info, pname, pid, **kwargs):
        self.exc_info = exc_info
        self.pname = pname
        self.pid = pid
        self.kwargs = kwargs

    def __str__(self):
        extra = ''
        for key in self.kwargs:
            extra += f' {key.capitalize()}: {self.kwargs[key]} ;'
        text = (f'Exc Info > {self.exc_info}'
                f'Process > Name: {self.pname} ; Pid: {self.pid}.\n'
                f'Extra >{extra[:-2]}.\n')
        return text