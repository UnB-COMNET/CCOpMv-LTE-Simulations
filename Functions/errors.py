class InvalidMode(Exception):
    pass

def check_mode(mode: str):
    '''Checks if the mode passed as argument is valid. Raises an InvalidMode exception if not valid.'''
    if mode != 'varying' and mode != 'fixed' and mode != 'single':
        raise(InvalidMode('Mode is not varying, fixed or single.'))

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
        text = (f'Exc Info > {self.exc_info}.\n'
                f'Process > Name: {self.pname} ; Pid: {self.pid}.\n'
                f'Extra >{extra[:-2]}.\n')
        return text