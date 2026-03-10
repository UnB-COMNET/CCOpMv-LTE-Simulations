from app.constants import SolutionType
class InvalidMode(Exception):
    pass

class InvalidResult(Exception):
    pass

class SolutionNotFeasible(Exception):
    pass

VALID_MODES = {
    SolutionType.PGWO,
    SolutionType.PGWO2,
    SolutionType.PGWO3,
    SolutionType.GA,
    SolutionType.ILP_FIXED,
    SolutionType.ILP_SINGLE,
    SolutionType.ILP_VARYING
}

def check_mode(mode: SolutionType):
    '''Checks if the mode passed as argument is valid. Raises an InvalidMode exception if not valid.'''
    if mode not in VALID_MODES:
        raise(InvalidMode('Mode is not varying, fixed, single, ga, pgwo or pgwo2.'))

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
