class InvalidMode(Exception):
    pass

def check_mode(mode: str):
    '''Checks if the mode passed as argument is valid. Raises an InvalidMode exception if not valid.'''
    if mode != 'varying' and mode != 'fixed' and mode != 'single':
        raise(InvalidMode('Mode is not varying, fixed or single.'))