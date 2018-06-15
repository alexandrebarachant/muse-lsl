import platform
import warnings


def warn_bluemuse_not_supported():
    warnings.warn('Operation not supported by bluemuse backend.',
                  RuntimeWarning)


def resolve_backend(backend):
    if backend in ['auto', 'gatt', 'bgapi', 'bluemuse']:
        platformName = platform.system().lower()
        if backend == 'auto':
            if platformName == 'linux' or platformName == 'linux2':
                backend = 'gatt'
            elif platformName == 'windows' and int(platform.version().replace('.', '')) >= 10015063:
                backend = 'bluemuse'
            else:
                backend = 'bgapi'
        return backend
    else:
        raise(ValueError('Backend must be one of: auto, gatt, bgapi, bluemuse.'))
