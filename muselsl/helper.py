from sys import platform


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