from sys import platform
import warnings

def warn_bluemuse_not_supported():
    warnings.warn('Operation not supported by bluemuse backend.', RuntimeWarning)

def resolve_backend(backend):
    if backend in ['auto', 'gatt', 'bgapi', 'bluemuse']:
        if backend == 'auto':
            if platform == "linux" or platform == "linux2":
                backend = 'gatt'
            else:
                backend = 'bgapi'
        return backend
    else:
        raise(ValueError('Backend must be one of: auto, gatt, bgapi, bluemuse.'))
