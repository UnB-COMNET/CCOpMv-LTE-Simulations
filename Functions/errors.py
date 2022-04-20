class InvalidMode(Exception):
    pass

def check_mode(mode: str):
    if mode != 'varying' and mode != 'fixed' and mode != 'single':
        raise(InvalidMode('Mode is not varying, fixed or single.'))